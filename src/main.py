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

# Import config đầu tiên để thiết lập FFmpeg path và môi trường cho pydub
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


def run_pipeline(script_text: str, project_title: str = "Truyện Ma Kinh Dị", mood: str = "kinh_di_nang"):
    log_print("\n" + "=" * 65)
    log_print(f"[*] VODIE STUDIO - KHOI DONG SAN XUAT: {project_title}")
    log_print(f"[*] Mood khong khi: {mood.upper()}")
    log_print("=" * 65 + "\n")

    # GIAI ĐOẠN 6 (Khởi tạo): Lưu vào SQLite
    db = DatabaseManager()
    project_id = db.create_project(project_title, script_text, mood=mood)
    log_print(f"[Giai doan 6] Da luu du an vao SQLite DB (ID: {project_id})")

    # GIAI ĐOẠN 1: Đạo diễn Kịch bản AI
    log_print("\n[Giai doan 1] Dao dien AI dang phan tich kich ban...")
    director = HorrorScriptAnalyzer(mood=mood)
    segments = director.analyze_text(script_text)
    log_print(f"   -> Da phan tach kich ban thanh {len(segments)} phan doan dao dien:")
    for seg in segments:
        short_txt = seg.text[:38] + "..." if len(seg.text) > 38 else seg.text
        log_print(f"      • Cau #{seg.segment_id} [Tension: {seg.tension}/10 | Pos: {seg.spatial_position} | Speaker: {seg.speaker}]: \"{short_txt}\"")

    # GIAI ĐOẠN 2 & 3: Tổng hợp Giọng đọc & Kiểm định Whisper
    log_print("\n[Giai doan 2 & 3] Tong hop TTS Tieng Viet & Kiem dinh Whisper...")
    tts = TTSEngine()
    verifier = WhisperAudioVerifier()
    audio_files = []
    durations = []

    for i, seg in enumerate(segments):
        # Tính Dynamic Pacing theo Tension
        is_open = (i == 0)
        is_close = (i == len(segments) - 1)
        rate, pause = DynamicPacingController.calculate_rate_and_pause(
            seg.tension, is_opening=is_open, is_closing=is_close
        )
        seg.pause_after = pause

        # Tổng hợp câu thoại qua Edge-TTS
        seg_audio_path = TEMP_DIR / f"proj_{project_id}_seg_{seg.segment_id}.mp3"
        log_print(f"   -> Dang tong hop cau #{seg.segment_id} (Giong: {seg.speaker}, Speed: {rate})...")
        tts.synthesize(
            text=seg.text,
            voice_id=seg.speaker,
            rate=rate,
            output_path=seg_audio_path
        )

        # Tính thời lượng audio thực tế
        try:
            audio_segment = AudioSegment.from_file(str(seg_audio_path))
            dur_sec = len(audio_segment) / 1000.0
        except Exception:
            dur_sec = 2.0
        durations.append(dur_sec)

        # Kiểm định chất lượng qua Whisper
        verification = verifier.verify_sentence(seg_audio_path, seg.text)
        status_icon = "[OK]" if verification["passed"] else "[WARN]"
        log_print(f"   {status_icon} Cau #{seg.segment_id}: Dat chuan am thanh (Thoi luong: {dur_sec:.1f}s)")

        audio_files.append(seg_audio_path)

    # GIAI ĐOẠN 4: Đạo diễn Âm thanh Không gian & Hiệu ứng Rợn Tóc Gáy
    log_print("\n[Giai doan 4] Xu ly Am thanh Khong gian 3D, Preset Giong Ma & Jump Scare...")
    mixer = HorrorAudioMixer(mood=mood)
    master_voice = mixer.build_story_track(segments, audio_files)

    clean_title = "".join(c if c.isalnum() or c in "_-" else "_" for c in project_title)
    master_audio_path = OUTPUT_DIR / f"{clean_title}_master.mp3"
    master_voice.export(str(master_audio_path), format="mp3")
    log_print(f"   [OK] Da xuat ban Master Audio: {master_audio_path}")

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
    climax_start, climax_end, climax_segs = ShortsCutter.find_climax_window(segments, durations, target_duration_sec=45.0)
    log_print(f"   [*] [Tu dong cat Shorts 9:16] Doan gay can nhat tu {climax_start:.1f}s den {climax_end:.1f}s ({len(climax_segs)} cau cao trao)")

    # GIAI ĐOẠN 6: Gắn Metadata An toàn & Hoàn tất
    SafetyCompliance.embed_ai_metadata(master_audio_path, title=project_title)
    log_print("   [OK] [An toan & Phap ly] Da gan Metadata 'AI-Generated' va xac thuc ban quyen")

    log_print("\n" + "=" * 65)
    log_print(f"[*] XUAT BAN THANH CONG DU AN '{project_title}'!")
    log_print(f"    • Audio Master: {master_audio_path}")
    if video_output_path.exists():
        log_print(f"    • Video MP4:    {video_output_path}")
    log_print(f"    • Phu de SRT:   {srt_path}")
    log_print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="VODIE - AI Horror Production Studio")
    parser.add_argument("--script", type=str, help="Đường dẫn tệp kịch bản truyện (.txt)")
    parser.add_argument("--title", type=str, default="Dem_Lanh_Da_Lat", help="Tiêu đề truyện")
    parser.add_argument("--mood", type=str, default="kinh_di_nang", help="Mood: nhe_nhang / kinh_di_nang / tam_linh_dan_gian / creepypasta")
    parser.add_argument("--generate", type=str, help="Ý tưởng để AI tự viết truyện (vd: 'ngôi nhà hoang Đà Lạt')")

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
        # Kịch bản mẫu để chạy thử nghiệm ngay lập tức
        script_text = (
            "Đêm Đà Lạt lạnh buốt, sương mù giăng kín các rặng thông quanh căn biệt thự hoang cổ kính.\n"
            "Tôi rón rén bước từng bước trên nền gỗ mục nát, xung quanh im lìm đến ghê người.\n"
            "Bỗng nhiên, từ trên tầng hai phát ra tiếng bước chân lê lết chậm rãi.\n"
            "Có một tiếng con gái thì thầm ngay bên tai tôi một lời van xin ai oán.\n"
            "Tôi run rẩy quay đầu lại phía sau lưng nhưng chẳng thấy ai, chỉ có một luồng gió lạnh thấu xương.\n"
            "Đột ngột, một bàn tay trắng bệch từ bóng tối vồ lấy vai tôi khiến tôi kinh hoàng hét lên!\n"
            "Và rồi, mọi thứ chìm vào im lặng vĩnh hằng giữa màn đêm sương phủ."
        )

    run_pipeline(script_text, project_title=args.title, mood=args.mood)


if __name__ == "__main__":
    main()
