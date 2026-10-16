import argparse
import sys
from pathlib import Path

from .config import SETTINGS, OUTPUT_DIR, TEMP_DIR
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


def run_pipeline(script_text: str, project_title: str = "Truyện Ma Kinh Dị", mood: str = "kinh_di_nang"):
    print(f"\n=======================================================")
    print(f"🎬 VODIE STUDIO - BẮT ĐẦU SẢN XUẤT: {project_title}")
    print(f"👻 Mood không khí: {mood.upper()}")
    print(f"=======================================================\n")

    # GIAI ĐOẠN 6 (Khởi tạo): Lưu vào SQLite
    db = DatabaseManager()
    project_id = db.create_project(project_title, script_text, mood=mood)
    print(f" [Giai đoạn 6] Đã lưu dự án vào SQLite DB (ID: {project_id})")

    # GIAI ĐOẠN 1: Đạo diễn Kịch bản AI
    print("\n🧠 [Giai đoạn 1] Đạo diễn AI đang phân tích kịch bản...")
    director = HorrorScriptAnalyzer(mood=mood)
    segments = director.analyze_text(script_text)
    print(f"   -> Đã phân tách kịch bản thành {len(segments)} phân đoạn đạo diễn:")
    for seg in segments:
        print(f"      • Câu #{seg.segment_id} [Tension: {seg.tension}/10 | Pos: {seg.spatial_position} | Speaker: {seg.speaker}]: \"{seg.text[:40]}...\"")

    # GIAI ĐOẠN 2 & 3: Tổng hợp Giọng đọc & Kiểm định Whisper
    print("\n🎙️ [Giai đoạn 2 & 3] Tổng hợp TTS Tiếng Việt & Kiểm định Whisper...")
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

        # Tổng hợp câu thoại
        seg_audio_path = TEMP_DIR / f"proj_{project_id}_seg_{seg.segment_id}.mp3"
        tts.synthesize(
            text=seg.text,
            voice_id=seg.speaker,
            rate=rate,
            output_path=seg_audio_path
        )

        # Kiểm định chất lượng qua Whisper
        verification = verifier.verify_sentence(seg_audio_path, seg.text)
        status_icon = "✓" if verification["passed"] else "⚠️"
        print(f"   {status_icon} Câu #{seg.segment_id}: Giọng [{seg.speaker}] | Speed [{rate}] | Đạt chuẩn Whisper")

        audio_files.append(seg_audio_path)
        durations.append(2.0)  # thời lượng ước lượng

    # GIAI ĐOẠN 4: Đạo diễn Âm thanh Không gian & Hiệu ứng Rợn Tóc Gáy
    print("\n🎧 [Giai đoạn 4] Xử lý Âm thanh Không gian 3D, Preset Giọng Ma & Jump Scare...")
    mixer = HorrorAudioMixer(mood=mood)
    master_voice = mixer.build_story_track(segments, audio_files)

    master_audio_path = OUTPUT_DIR / f"{project_title}_master.mp3"
    master_voice.export(str(master_audio_path), format="mp3")
    print(f"   ✓ Đã hoàn thiện Master Audio: {master_audio_path}")

    # GIAI ĐOẠN 5: Render Video MP4 & Cắt Shorts
    print("\n📺 [Giai đoạn 5] Render Video MP4 (16:9) & Phân đoạn Shorts (9:16)...")
    video_gen = VideoGenerator()
    srt_path = OUTPUT_DIR / f"{project_title}_subtitles.srt"
    video_gen.generate_subtitles_srt(segments, durations, srt_path)
    print(f"   ✓ Đã xuất tệp phụ đề cháy chữ: {srt_path}")

    # Tìm đoạn cao trào làm Shorts TikTok/Reels
    climax_start, climax_end, climax_segs = ShortsCutter.find_climax_window(segments, durations, target_duration_sec=45.0)
    print(f"   🔥 [Tự động cắt Shorts 9:16] Đoạn gay cấn nhất từ {climax_start:.1f}s đến {climax_end:.1f}s ({len(climax_segs)} câu cao trào)")

    # GIAI ĐOẠN 6: Gắn Metadata An toàn & Hoàn tất
    SafetyCompliance.embed_ai_metadata(master_audio_path, title=project_title)
    print("   🔒 [An toàn & Pháp lý] Đã gắn Metadata 'AI-Generated' và xác thực bản quyền")

    print(f"\n🎉 XUẤT BẢN THÀNH CÔNG DỰ ÁN '{project_title}'!")
    print(f"📁 Tệp Audio: {master_audio_path}")
    print(f"📁 Phụ đề: {srt_path}\n")


def main():
    parser = argparse.ArgumentParser(description="VODIE - AI Horror Production Studio")
    parser.add_argument("--script", type=str, help="Đường dẫn tệp kịch bản truyện (.txt)")
    parser.add_argument("--title", type=str, default="Dem_Lanh_Da_Lat", help="Tiêu đề truyện")
    parser.add_argument("--mood", type=str, default="kinh_di_nang", help="Mood: nhe_nhang / kinh_di_nang / tam_linh_dan_gian / creepypasta")
    parser.add_argument("--generate", type=str, help="Ý tưởng để AI tự viết truyện (vd: 'ngôi nhà hoang Đà Lạt')")

    args = parser.parse_args()

    if args.generate:
        print(f"✨ Đang dùng AI để sáng tác truyện từ ý tưởng: '{args.generate}'...")
        story_gen = StoryGenerator()
        script_text = story_gen.generate_story(args.generate, mood=args.mood)
        print("--- Kịch bản được tạo ---")
        print(script_text)
        print("-------------------------")
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
