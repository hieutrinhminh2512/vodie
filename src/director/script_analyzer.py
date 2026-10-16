from dataclasses import dataclass, field
from typing import List, Optional
import re


@dataclass
class ScriptSegment:
    segment_id: int
    text: str
    speaker: str = "nguoi_ke_bac"  # nguoi_ke_bac, nguoi_ke_nam, ma_nu, quy_du, vong_hon
    tension: float = 2.0  # Thang điểm căng thẳng 0.0 - 10.0
    spatial_position: str = "center"  # center, left, right, rear, left_to_right
    pause_after: float = 0.8  # Giây ngắt nghỉ sau câu
    is_jumpscare: bool = False
    sfx_cue: Optional[str] = None
    voice_preset: Optional[str] = None


class HorrorScriptAnalyzer:
    """
    AI Director Engine: Phân tích kịch bản văn bản thô, tự động nhận diện vai,
    chấm điểm độ căng thẳng (tension), điều phối âm thanh không gian và điểm Jump scare.
    """

    HORROR_KEYWORDS_HIGH = [
        "hét lên", "la hét", "kinh hoàng", "chết", "máu", "rợn người",
        "đột ngột", "bất thình lình", "chụp lấy", "vồ lấy", "bóng đen",
        "giật mình", "kinh hãi", "ám ảnh", "mặt trắng bệch", "xác chết"
    ]

    HORROR_KEYWORDS_MED = [
        "tiếng bước chân", "thì thầm", "lạnh gáy", "u tối", "đêm khuya",
        "gió rít", "bóng ma", "nghe ngóng", "rón rén", "lạnh buốt",
        "oan hồn", "nghĩa địa", "ngôi nhà hoang", "mờ ảo", "tiếng khóc"
    ]

    GHOST_PATTERNS = {
        "ma_nu": [r"tiếng con gái thì thầm", r"ma nữ", r"cô gái áo trắng", r"tiếng cười the thé"],
        "quy_du": [r"tiếng gầm", r"quỷ dữ", r"giọng ồm ồm", r"tiếng thở phì phò"],
        "vong_hon": [r"tiếng gọi tên", r"vọng từ xa", r"oan hồn", r"người âm"]
    }

    def __init__(self, default_speaker: str = "nguoi_ke_bac", mood: str = "kinh_di_nang"):
        self.default_speaker = default_speaker
        self.mood = mood

    def analyze_text(self, raw_text: str) -> List[ScriptSegment]:
        """Chia tách văn bản thành từng câu/phân đoạn và đạo diễn thông số kịch bản."""
        # Tách theo dấu chấm câu hoặc dòng mới
        sentences = [
            s.strip() for s in re.split(r'(?<=[.!?…\n])\s+', raw_text)
            if s.strip()
        ]

        segments: List[ScriptSegment] = []
        current_tension = 2.0

        for idx, sentence in enumerate(sentences, start=1):
            lower_text = sentence.lower()

            # 1. Tính toán điểm Tension
            tension_boost = 0.0
            for kw in self.HORROR_KEYWORDS_HIGH:
                if kw in lower_text:
                    tension_boost += 2.5
            for kw in self.HORROR_KEYWORDS_MED:
                if kw in lower_text:
                    tension_boost += 1.2

            # Smooth tension curve
            current_tension = min(10.0, max(1.0, current_tension * 0.7 + tension_boost))

            # 2. Nhận diện vai & Voice Preset
            speaker = self.default_speaker
            voice_preset = None
            for preset, patterns in self.GHOST_PATTERNS.items():
                if any(re.search(pat, lower_text) for pat in patterns):
                    speaker = preset
                    voice_preset = preset
                    break

            # 3. Gán vị trí âm thanh không gian (Binaural Panning)
            spatial = "center"
            if "thì thầm" in lower_text or "bên tai" in lower_text:
                spatial = "left_to_right" if idx % 2 == 0 else "right"
            elif "sau lưng" in lower_text or "phía sau" in lower_text:
                spatial = "rear"
            elif "bên trái" in lower_text:
                spatial = "left"
            elif "bên phải" in lower_text:
                spatial = "right"

            # 4. Phát hiện Jump scare (Tension đột ngột cao > 8.0)
            is_jumpscare = False
            sfx_cue = None
            if current_tension >= 8.0 and any(kw in lower_text for kw in ["đột ngột", "bất thình lình", "vồ lấy", "hét lên"]):
                is_jumpscare = True
                sfx_cue = "jumpscare_screech"
            elif "bước chân" in lower_text:
                sfx_cue = "footsteps_creak"
            elif "gió" in lower_text or "rít" in lower_text:
                sfx_cue = "wind_howl"

            # 5. Dynamic Pause Duration
            # Câu căng thẳng ngắn -> nghỉ ngắn; câu chốt đoạn -> ngắt dài
            pause = 1.0
            if current_tension > 7.0:
                pause = 0.5  # Dồn dập
            elif is_jumpscare:
                pause = 1.8  # Im lặng nín thở trước khi giật mình
            elif idx == len(sentences):
                pause = 2.5  # Kết thúc truyện dừng lâu

            segment = ScriptSegment(
                segment_id=idx,
                text=sentence,
                speaker=speaker,
                tension=round(current_tension, 1),
                spatial_position=spatial,
                pause_after=pause,
                is_jumpscare=is_jumpscare,
                sfx_cue=sfx_cue,
                voice_preset=voice_preset
            )
            segments.append(segment)

        return segments
