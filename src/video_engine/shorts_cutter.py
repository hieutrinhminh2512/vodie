from pathlib import Path
from typing import List, Tuple
from ..director.script_analyzer import ScriptSegment


class ShortsCutter:
    """
    Tự động cắt bản ngắn 30–60 giây, khổ dọc 9:16 cho TikTok/Shorts/Reels:
    - Quét kịch bản để tìm ra cửa sổ thời gian (time window) có điểm Tension trung bình cao nhất.
    - Cắt và trích xuất đoạn cao trào nhất để làm video viral ngắn.
    """

    @classmethod
    def find_climax_window(
        cls,
        segments: List[ScriptSegment],
        durations: List[float],
        target_duration_sec: float = 60.0
    ) -> Tuple[float, float, List[ScriptSegment]]:
        """
        Tìm đoạn có Tension cao trào nhất trong phạm vi target_duration_sec.
        Trả về: (start_time_sec, end_time_sec, climax_segments)
        """
        best_score = -1.0
        best_start = 0.0
        best_end = 0.0
        best_segs = []

        total_segs = len(segments)

        for i in range(total_segs):
            curr_dur = 0.0
            curr_score = 0.0
            sub_segs = []

            for j in range(i, total_segs):
                seg = segments[j]
                seg_dur = durations[j] + seg.pause_after
                if curr_dur + seg_dur > target_duration_sec and curr_dur > 20.0:
                    break
                curr_dur += seg_dur
                curr_score += seg.tension
                sub_segs.append(seg)

            avg_score = curr_score / max(1, len(sub_segs))
            if avg_score > best_score:
                best_score = avg_score
                best_segs = sub_segs
                # Tính thời điểm bắt đầu
                best_start = sum(durations[k] + segments[k].pause_after for k in range(i))
                best_end = best_start + curr_dur

        return best_start, best_end, best_segs
