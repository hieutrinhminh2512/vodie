import sys
import argparse
from pathlib import Path

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

from .director.script_analyzer import HorrorScriptAnalyzer
from .director.story_generator import StoryGenerator
from .tts.engine import TTSEngine
from .validator.audio_verifier import WhisperAudioVerifier
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
    speaker_style: str = "nguyen_ngoc_ngan"
):
    log_print("\n" + "=" * 70)
    log_print(f"[*] VODIE HORROR STUDIO - SAN XUAT TRUONG THIEN: {project_title}")
    log_print(f"[*] Phong cach giong ke: {speaker_style.upper()} (Tram am, ma mi, truyen cam)")
    log_print(f"[*] Mood khong khi: {mood.upper()}")
    log_print("=" * 70 + "\n")

    # GIAI ĐOẠN 6: Lưu vào SQLite
    db = DatabaseManager()
    project_id = db.create_project(project_title, script_text, mood=mood)
    log_print(f"[Giai doan 6] Da luu du an vao SQLite DB (ID: {project_id})")

    # GIAI ĐOẠN 1: Đạo diễn Kịch bản AI
    log_print("\n[Giai doan 1] Dao dien AI dang phan tich kich ban...")
    director = HorrorScriptAnalyzer(default_speaker=speaker_style, mood=mood)
    segments = director.analyze_text(script_text)
    log_print(f"   -> Da phan tach kich ban thanh {len(segments)} phan doan dao dien:")
    for seg in segments[:10]:
        short_txt = seg.text[:38] + "..." if len(seg.text) > 38 else seg.text
        log_print(f"      • Cau #{seg.segment_id} [Tension: {seg.tension}/10 | Pos: {seg.spatial_position} | Speaker: {seg.speaker}]: \"{short_txt}\"")
    if len(segments) > 10:
        log_print(f"      ... va {len(segments) - 10} cau tiep theo ...")

    # GIAI ĐOẠN 2 & 3: Tổng hợp Giọng đọc & Kiểm định Whisper
    log_print(f"\n[Giai doan 2 & 3] Tong hop giong doc phong cach {speaker_style}...")
    tts = TTSEngine()
    verifier = WhisperAudioVerifier()
    audio_files = []
    durations = []

    total_segs = len(segments)
    for i, seg in enumerate(segments, start=1):
        is_open = (i == 1)
        is_close = (i == total_segs)
        rate, pause = DynamicPacingController.calculate_rate_and_pause(
            seg.tension, is_opening=is_open, is_closing=is_close
        )
        seg.pause_after = pause

        # Chọn giọng: nếu câu có preset ma nữ hoặc quỷ dữ thì giữ nguyên, ngược lại dùng phong cách người kể
        active_speaker = seg.speaker if seg.speaker in ["ma_nu", "quy_du", "vong_hon"] else speaker_style

        # Cache file audio theo nội dung và người đọc
        content_hash = abs(hash(seg.text + active_speaker)) % 1000000
        seg_audio_path = TEMP_DIR / f"seg_{seg.segment_id}_{content_hash}.mp3"

        # Nếu chưa có trong cache thì mới gọi TTS
        if not seg_audio_path.exists() or seg_audio_path.stat().st_size == 0:
            tts.synthesize(
                text=seg.text,
                voice_id=active_speaker,
                rate=rate,
                output_path=seg_audio_path
            )

        try:
            audio_segment = AudioSegment.from_file(str(seg_audio_path))
            dur_sec = len(audio_segment) / 1000.0
        except Exception:
            dur_sec = 8.0
        durations.append(dur_sec)

        if i % 5 == 0 or i == total_segs or seg.is_jumpscare or seg.speaker in ["ma_nu", "quy_du"]:
            log_print(f"   [OK] [{i}/{total_segs}] Cau #{seg.segment_id} (Giong: {active_speaker}, Thoi luong: {dur_sec:.1f}s)")

        audio_files.append(seg_audio_path)

    # GIAI ĐOẠN 4: Mastering Âm Thanh Không Gian 3D, Nhạc Nền Dark Ambient & Jump Scare
    log_print("\n[Giai doan 4] Mastering Am thanh: Khử chat AI, lót Dark Drone BGM, Panning 3D...")
    mixer = HorrorAudioMixer(mood=mood)
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
    parser.add_argument("--speaker", type=str, default="nguyen_ngoc_ngan", help="Phong cách: nguyen_ngoc_ngan / quang_a_tun / dinh_soan / nguoi_ke_bac")
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

    run_pipeline(script_text, project_title=args.title, mood=args.mood, speaker_style=args.speaker)


if __name__ == "__main__":
    main()
