import subprocess
from pathlib import Path
from typing import Optional
import shutil
from ..config import SETTINGS


class VideoGenerator:
    """
    Tạo Video MP4 đăng YouTube (16:9):
    - Nền đen / u ám chuẩn điện ảnh
    - Sóng âm chuyển động (Dynamic Audio Waveform Visualizer)
    - Tối ưu hóa tốc độ render cho truyện dài 15-20 phút
    """

    def __init__(self):
        self.cfg = SETTINGS.get("video", {})
        self.resolution = self.cfg.get("resolution_horizontal", "1920x1080")
        self.fps = 15  # 15 fps mượt mà cho sóng âm, render siêu nhanh
        self.wave_color = self.cfg.get("waveform_color", "red")

    def generate_subtitles_srt(self, segments, audio_durations, srt_path: Path):
        """Tạo tệp phụ đề SRT từ danh sách câu và thời lượng thực tế."""
        current_time = 0.0
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, (seg, dur) in enumerate(zip(segments, audio_durations), start=1):
                start_sec = current_time
                end_sec = current_time + dur
                current_time = end_sec + seg.pause_after

                start_str = self._format_timestamp(start_sec)
                end_str = self._format_timestamp(end_sec)

                f.write(f"{i}\n{start_str} --> {end_str}\n{seg.text}\n\n")

    def _format_timestamp(self, seconds: float) -> str:
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    def render_mp4(
        self,
        audio_path: Path,
        output_mp4: Path,
        bg_image_path: Optional[Path] = None,
        srt_path: Optional[Path] = None
    ) -> bool:
        """Render video hoàn chỉnh bằng FFmpeg tối ưu cho truyện dài."""
        ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"

        # Lọc sóng âm mượt mà trên nền đen 1280x720 (chuẩn HD render cực nhanh)
        filter_str = (
            f"[0:a]showwaves=s=1280x300:mode=line:r=15:colors={self.wave_color}[waves]; "
            f"color=c=0x080808:s=1280x720:r=15[bg]; "
            f"[bg][waves]overlay=(W-w)/2:(H-h)/2:shortest=1[v]"
        )

        cmd = [
            ffmpeg_bin, "-y",
            "-i", str(audio_path),
            "-filter_complex", filter_str,
            "-map", "[v]",
            "-map", "0:a",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-threads", "0",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_mp4)
        ]

        try:
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except Exception as e:
            print(f"[FFmpeg Warning] Không thể render video trực tiếp: {e}")
            return False
