import sys
import time
import argparse
import logging
from pathlib import Path
from typing import Optional

# Đảm bảo console UTF-8 trên Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Import config đầu tiên để inject FFmpeg path và môi trường cho pydub
from .config import SETTINGS, OUTPUT_DIR, TEMP_DIR
from pydub import AudioSegment

from .director.llm_director import direct_story
from .director.story_generator import StoryGenerator
from .tts.engine import TTSEngine
from .audio_engine.dynamic_pacing import DynamicPacingController
from .audio_engine.mixer import HorrorAudioMixer
from .video_engine.video_generator import VideoGenerator
from .video_engine.shorts_cutter import ShortsCutter
from .storage.db import DatabaseManager
from .safety.compliance import SafetyCompliance


def log_print(msg: str):
    print(msg, flush=True)


def run_pipeline(
    script_text: str,
    project_title: str = "Chuyen_Xe_Dem_Hai_Van",
    mood: str = "tam_linh_dan_gian",
    speaker_style: str = "auto",
    engine: Optional[str] = None,
    use_llm: Optional[bool] = None,
):
    log_print("\n" + "=" * 70)
    log_print(f"[*] VODIE HORROR STUDIO - SAN XUAT: {project_title}")
    log_print(f"[*] Mood khong khi: {mood.upper()}")
    log_print("=" * 70 + "\n")

    # GIAI ĐOẠN 6: Lưu vào SQLite
    db = DatabaseManager()
    project_id = db.create_project(project_title, script_text, mood=mood)
    log_print(f"[Giai doan 6] Da luu du an vao SQLite DB (ID: {project_id})")

    # GIAI ĐOẠN 1: Đạo diễn kịch bản (Claude nếu có ANTHROPIC_API_KEY, không thì theo luật)
    log_print("\n[Giai doan 1] Dao dien dang phan tich kich ban...")
    directed = direct_story(script_text, mood=mood, use_llm=use_llm)
    segments = directed.segments

    # Phân vai: người kể theo miền của truyện (nếu chọn auto) + mỗi nhân vật 1 giọng riêng
    tts = TTSEngine(engine=engine, dialect=directed.story_region)
    vm = tts.voice_manager
    narrator_id = f"narrator_{directed.story_region}_nam" if speaker_style in ("auto", "", None) else speaker_style
    casting = vm.cast(narrator_id, directed.characters, directed.story_region)
    log_print(f"   -> {len(segments)} cau | Boi canh: mien {directed.story_region} | Engine: {tts.backend.name}")
    for role, voice in casting.items():
        label = "Nguoi ke" if role == "narrator" else directed.characters[role].display_name
        log_print(f"      • {label}: {voice.name}")

    # GIAI ĐOẠN 2: Tổng hợp giọng đọc (có cache theo nội dung — chạy lại chỉ đọc câu đã sửa)
    log_print("\n[Giai doan 2] Tong hop giong doc...")
    audio_files = []
    durations = []
    total_segs = len(segments)
    started = time.time()
    for i, seg in enumerate(segments, start=1):
        voice = casting.get(seg.speaker, casting["narrator"])
        # Nhịp theo độ căng (khi kịch bản chưa chỉ định speed riêng)
        if seg.speed == 1.0 and SETTINGS.get("director", {}).get("enable_dynamic_pacing", True):
            seg.speed = DynamicPacingController.speed_for(seg.tension, is_opening=(i == 1),
                                                         is_closing=(i == total_segs))
        try:
            path = tts.synthesize(seg.text, voice=voice, emotion=seg.emotion,
                                  nonverbal=seg.nonverbal, speed=seg.speed)
            dur_sec = len(AudioSegment.from_file(str(path))) / 1000.0
        except Exception as e:  # noqa: BLE001 - 1 câu lỗi không làm hỏng cả truyện
            log_print(f"   [LOI] Cau #{seg.segment_id}: {e}")
            path = TEMP_DIR / f"missing_{seg.segment_id}.wav"
            AudioSegment.silent(duration=500).export(str(path), format="wav")
            dur_sec = 0.5
        audio_files.append(path)
        durations.append(dur_sec)
        if i % 5 == 0 or i == total_segs:
            elapsed = time.time() - started
            eta = elapsed / i * (total_segs - i)
            log_print(f"   [{i}/{total_segs}] con lai ~{eta:.0f}s")

    # GIAI ĐOẠN 4: Mastering Âm Thanh Không Gian 3D, Nhạc Nền Dark Ambient & Jump Scare
    log_print("\n[Giai doan 4] Mastering Am thanh: Khử chat AI, lót Dark Drone BGM, Panning 3D...")
    mixer = HorrorAudioMixer(mood=mood, speaker_style=narrator_id)
    master_voice = mixer.build_story_track(segments, audio_files)

    clean_title = "".join(c if c.isalnum() or c in "_-" else "_" for c in project_title)
    master_audio_path = OUTPUT_DIR / f"{clean_title}_master.mp3"
    master_voice.export(str(master_audio_path), format="mp3")
    total_audio_min = (len(master_voice) / 1000.0) / 60.0
    log_print(f"   [OK] Da xuat ban Master Audio: {master_audio_path} (Thoi luong: {total_audio_min:.2f} phut)")

    # GIAI ĐOẠN 5: Render Video MP4 & Cắt Shorts
    log_print("\n[Giai doan 5] Render Video MP4 (16:9) & Phan doan Shorts (9:16)...")
    video_gen = VideoGenerator()
    srt_path = OUTPUT_DIR / f"{clean_title}_subtitles.srt"
    video_gen.generate_subtitles_srt(segments, durations, srt_path)
    log_print(f"   [OK] Da xuat tep phu de chay chu: {srt_path}")

    # Render video MP4 với sóng âm
    video_output_path = OUTPUT_DIR / f"{clean_title}_video.mp4"
    log_print("   [*] Dang render Video MP4 kem song am chuyen dong qua FFmpeg...")
    rendered = video_gen.render_mp4(master_audio_path, video_output_path, srt_path=srt_path)
    if rendered:
        log_print(f"   [OK] Da render Video MP4 thanh cong: {video_output_path}")

    # Tìm đoạn cao trào làm Shorts TikTok/Reels
    climax_start, climax_end, climax_segs = ShortsCutter.find_climax_window(segments, durations, target_duration_sec=55.0)
    log_print(f"   [*] [Tu dong cat Shorts 9:16] Doan gay can nhat tu {climax_start:.1f}s den {climax_end:.1f}s ({len(climax_segs)} cau cao trao)")

    # GIAI ĐOẠN 6: Gắn Metadata An toàn & Hoàn tất
    SafetyCompliance.embed_ai_metadata(master_audio_path, title=project_title)
    log_print("   [OK] [An toan & Phap ly] Da gan Metadata 'AI-Generated' va xac thuc ban quyen")

    log_print("\n" + "=" * 70)
    log_print(f"[*] XUAT BAN THANH CONG DU AN '{project_title}'!")
    log_print(f"    • Thoi luong tong the: {total_audio_min:.2f} phut")
    log_print(f"    • Audio Master:        {master_audio_path}")
    if video_output_path.exists():
        log_print(f"    • Video MP4:           {video_output_path}")
    log_print(f"    • Phu de SRT:          {srt_path}")
    log_print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="VODIE - AI Horror Production Studio")
    parser.add_argument("--script", type=str, help="Đường dẫn tệp kịch bản truyện (.txt)")
    parser.add_argument("--title", type=str, default="Chuyen_Xe_Dem_Hai_Van", help="Tiêu đề truyện")
    parser.add_argument("--mood", type=str, default="tam_linh_dan_gian", help="Mood: nhe_nhang / kinh_di_nang / tam_linh_dan_gian / creepypasta")
    parser.add_argument("--speaker", type=str, default="auto",
                        help="Giọng người kể (xem config/voices.yaml), 'auto' = theo miền của truyện")
    parser.add_argument("--engine", type=str, default=None, help="auto / vieneu / elevenlabs / edge")
    parser.add_argument("--no-llm", action="store_true", help="Không dùng Claude, chỉ đạo diễn theo luật")
    parser.add_argument("--generate", type=str, help="Ý tưởng để AI tự viết truyện")

    args = parser.parse_args()

    if args.generate:
        log_print(f"[*] Dang dung AI de sang tac truyen tu y tuong: '{args.generate}'...")
        story_gen = StoryGenerator()
        script_text = story_gen.generate_story(args.generate, mood=args.mood)
        log_print("--- Kich ban duoc tao ---")
        log_print(script_text)
        log_print("-------------------------")
    elif args.script and Path(args.script).exists():
        with open(args.script, "r", encoding="utf-8") as f:
            script_text = f.read()
    else:
        sample_path = Path("stories/chuyen_xe_dem_hai_van.txt")
        if sample_path.exists():
            with open(sample_path, "r", encoding="utf-8") as f:
                script_text = f.read()
        else:
            script_text = "Đêm mưa bão đèo Hải Vân lạnh buốt..."

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    for noisy in ("httpx", "httpx2", "huggingface_hub", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    run_pipeline(script_text, project_title=args.title, mood=args.mood, speaker_style=args.speaker,
                 engine=args.engine, use_llm=False if args.no_llm else None)


if __name__ == "__main__":
    main()
