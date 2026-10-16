from pathlib import Path
from typing import List, Dict
import json


class ChapterExporter:
    """
    Quản lý chia chương cho truyện dài:
    - Nhận diện các điểm mốc phân đoạn (Hồi 1, Hồi 2, Chương 1, Chương 2).
    - Tạo file siêu dữ liệu metadata FFMpeg để nhúng Chapter Markers vào tệp M4B / MP4.
    """

    @classmethod
    def generate_ffmetadata(
        cls,
        chapters: List[Dict[str, any]],
        output_file: Path
    ) -> Path:
        """
        Ghi tệp định dạng ffmetadata cho ffmpeg:
        [CHAPTER]
        TIMEBASE=1/1000
        START=0
        END=120000
        title=Chương 1: Tiếng Gọi Trong Đêm
        """
        content = [";FFMETADATA1"]

        for chap in chapters:
            start_ms = int(chap.get("start_sec", 0) * 1000)
            end_ms = int(chap.get("end_sec", 0) * 1000)
            title = chap.get("title", "Chương mới")

            content.append("[CHAPTER]")
            content.append("TIMEBASE=1/1000")
            content.append(f"START={start_ms}")
            content.append(f"END={end_ms}")
            content.append(f"title={title}\n")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        return output_file
