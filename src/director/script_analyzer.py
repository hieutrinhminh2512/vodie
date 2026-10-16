"""Đạo diễn kịch bản theo luật (không cần API key).

Hiểu ngữ cảnh truyện ma Việt Nam:
- Tách lời người kể và lời thoại (ngoặc kép, gạch đầu dòng kiểu "- Ai đó?").
- Đoán vai người nói qua cách xưng hô/kể ("bà cụ thều thào", "thằng Tèo hét")
  để chọn giọng nam/nữ, già/trẻ — thay vì để một giọng đọc hết.
- Nhận diện thực thể dân gian (ma da, ma lai, vong, người âm, quỷ nhập tràng...)
  để gán giọng ma và hiệu ứng phù hợp.
- Chấm cảm xúc + độ căng để engine đọc có nhấn nhá.

Nếu có ANTHROPIC_API_KEY thì dùng LLMDirector (llm_director.py) cho kết quả tốt hơn;
module này vẫn là phương án dự phòng.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ScriptSegment:
    segment_id: int
    text: str
    speaker: str = "narrator"          # "narrator" hoặc key nhân vật trong `characters`
    tension: float = 2.0                # 0.0 - 10.0
    spatial_position: str = "center"    # center, left, right, rear, left_to_right
    pause_after: float = 0.8            # giây
    is_jumpscare: bool = False
    sfx_cue: Optional[str] = None
    voice_preset: Optional[str] = None  # ma_nu, quy_du, vong_hon (hiệu ứng hậu kỳ)
    emotion: str = "binh_thuong"        # binh_thuong, hoi_hop, so_hai, thi_tham, het, buon, ai_oan, lanh_lung
    speed: float = 1.0                  # 0.85 - 1.15
    nonverbal: Optional[str] = None     # "thở dài", "cười", "hắng giọng"


@dataclass
class Character:
    key: str
    display_name: str
    gender: str = "nam"          # nam | nu
    age_group: str = "trung_nien"  # tre_em | thanh_nien | trung_nien | gia
    is_ghost: bool = False
    ghost_preset: Optional[str] = None


@dataclass
class DirectedScript:
    segments: List[ScriptSegment]
    characters: Dict[str, Character] = field(default_factory=dict)
    story_region: str = "bac"  # bac | trung | nam — giọng người kể phù hợp bối cảnh


# Từ xưng hô / gọi người -> (giới tính, nhóm tuổi). Thứ tự: cụm dài trước.
KINSHIP: List[tuple] = [
    ("bà ngoại", "nu", "gia"), ("bà nội", "nu", "gia"), ("ông ngoại", "nam", "gia"), ("ông nội", "nam", "gia"),
    ("bà cụ", "nu", "gia"), ("ông cụ", "nam", "gia"), ("cụ bà", "nu", "gia"), ("cụ ông", "nam", "gia"),
    ("bà lão", "nu", "gia"), ("ông lão", "nam", "gia"), ("bà già", "nu", "gia"), ("lão", "nam", "gia"),
    ("con bé", "nu", "tre_em"), ("cô bé", "nu", "tre_em"), ("bé gái", "nu", "tre_em"),
    ("thằng bé", "nam", "tre_em"), ("cậu bé", "nam", "tre_em"), ("bé trai", "nam", "tre_em"),
    ("đứa bé", "nu", "tre_em"), ("đứa trẻ", "nu", "tre_em"),
    ("cô gái", "nu", "thanh_nien"), ("người phụ nữ", "nu", "trung_nien"), ("người đàn bà", "nu", "trung_nien"),
    ("người đàn ông", "nam", "trung_nien"), ("gã", "nam", "trung_nien"), ("thằng", "nam", "thanh_nien"),
    ("mẹ", "nu", "trung_nien"), ("má", "nu", "trung_nien"),
    ("bố", "nam", "trung_nien"), ("ba", "nam", "trung_nien"), ("tía", "nam", "trung_nien"),
    ("thím", "nu", "trung_nien"), ("mợ", "nu", "trung_nien"), ("dì", "nu", "trung_nien"),
    ("cô", "nu", "thanh_nien"), ("chị", "nu", "thanh_nien"), ("bà", "nu", "gia"),
    ("chú", "nam", "trung_nien"), ("bác", "nam", "trung_nien"), ("cậu", "nam", "thanh_nien"),
    ("anh", "nam", "thanh_nien"), ("ông", "nam", "gia"), ("thầy", "nam", "trung_nien"),
    ("sư", "nam", "gia"), ("vợ", "nu", "thanh_nien"), ("chồng", "nam", "thanh_nien"),
]

SPEECH_VERBS = (r"nói|hỏi|đáp|gọi|kêu|hét|thét|la|gào|rít|thì thầm|thều thào|lẩm bẩm|"
                r"thút thít|khóc|cười|quát|bảo|lên tiếng|cất tiếng|rên|van|nạt|than")

# Thực thể ma quỷ dân gian -> preset hiệu ứng giọng
GHOST_ENTITIES = {
    "ma_nu": [r"ma nữ", r"ma da", r"cô gái áo trắng", r"người đàn bà áo trắng", r"ma lai",
              r"tiếng cười the thé", r"tiếng con gái", r"hồn ma cô"],
    "quy_du": [r"quỷ", r"ác quỷ", r"quỷ nhập tràng", r"ma trành", r"giọng ồm ồm", r"tiếng gầm",
               r"ma cọp", r"yêu tinh"],
    "vong_hon": [r"vong", r"oan hồn", r"người âm", r"cô hồn", r"hồn ma", r"vọng từ xa",
                 r"tiếng gọi tên", r"linh hồn"],
}

HIGH = ["hét lên", "la hét", "thét", "kinh hoàng", "máu", "rợn người", "đột ngột", "bất thình lình",
        "chụp lấy", "vồ lấy", "túm lấy", "giật mình", "kinh hãi", "trắng bệch", "xác chết", "chết",
        "quan tài", "lè lưỡi", "trợn mắt", "không có mặt", "không có chân"]
MED = ["tiếng bước chân", "thì thầm", "lạnh gáy", "nổi da gà", "u tối", "đêm khuya", "nửa đêm",
       "canh ba", "giờ tý", "gió rít", "bóng", "rón rén", "lạnh buốt", "nghĩa địa", "mộ", "nhà hoang",
       "tiếng khóc", "chó tru", "cú kêu", "nhang", "hương khói", "đám ma", "kèn đám", "giếng",
       "cây đa", "cây gạo", "bến sông", "rằm tháng bảy", "tháng cô hồn", "đèn dầu", "tắt phụt"]

EMOTION_CUES = [
    ("het", ["hét", "thét", "gào", "la lên", "quát"]),
    ("thi_tham", ["thì thầm", "thều thào", "khẽ", "lẩm bẩm", "nói nhỏ", "rít qua kẽ răng"]),
    ("ai_oan", ["ai oán", "nỉ non", "oan ức", "than khóc", "van xin"]),
    ("buon", ["khóc", "nghẹn", "buồn", "đau đớn", "tủi", "thở dài", "mất rồi"]),
    ("so_hai", ["run rẩy", "sợ", "hoảng", "kinh hãi", "chết điếng", "lạnh toát"]),
    ("hoi_hop", ["bỗng", "chợt", "đột nhiên", "nín thở", "rón rén", "từ từ", "hình như"]),
]

SFX_CUES = [
    ("footsteps_creak", ["bước chân", "tiếng chân", "sàn gỗ", "cọt kẹt"]),
    ("door_creak", ["cánh cửa", "mở cửa", "gõ cửa", "then cửa"]),
    ("wind_howl", ["gió rít", "gió lùa", "gió hú", "cơn gió"]),
    ("rain_storm", ["mưa", "sấm", "chớp"]),
    ("dog_howl", ["chó tru", "chó sủa", "tiếng chó"]),
    ("owl", ["cú kêu", "cú mèo", "tiếng cú"]),
    ("temple_bell", ["chuông chùa", "tiếng mõ", "mõ gõ"]),
    ("funeral_horn", ["kèn đám ma", "kèn đưa tang", "trống đám"]),
    ("water_drip", ["giếng", "nước nhỏ giọt", "bến sông", "dưới nước"]),
]

REGION_HINTS = {
    "nam": ["miền tây", "sài gòn", "cà mau", "cần thơ", "bạc liêu", "châu đốc", "an giang", "bến tre",
            "đồng tháp", "sóc trăng", "trà vinh", "vĩnh long", "tây ninh", "má", "tía", "dzậy", "hông"],
    "trung": ["huế", "đà nẵng", "quảng nam", "quảng ngãi", "quảng trị", "quảng bình", "nghệ an",
              "hà tĩnh", "bình định", "hải vân", "mô", "răng", "rứa", "chừ", "tê"],
    "bac": ["hà nội", "hải phòng", "nam định", "thái bình", "bắc ninh", "tây bắc", "sơn la",
            "lào cai", "hà giang", "phú thọ", "thầy u", "đồng bằng bắc bộ"],
}

DIALOGUE_RE = re.compile(r'^\s*[-–—]\s*(.+)$|"([^"]+)"|“([^”]+)”')


def detect_region(text: str) -> str:
    lower = f" {text.lower()} "
    scores = {r: sum(lower.count(f" {w} ") + lower.count(f" {w},") for w in words)
              for r, words in REGION_HINTS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "bac"


DASH = r"[-–—]"
_INLINE_DASH_DIALOGUE = re.compile(r"^\s*" + DASH + r"\s*(.+?[.?!…]+)\s+" + DASH + r"\s+(.+)$")
_QUOTE_SPLIT = re.compile(r'["“]([^"”]+)["”]')
SELF_PRONOUNS = r"(?:tôi|mình|tui|tao)"


def _split_para_sentences(para: str) -> List[str]:
    parts = re.split(r'(?<=[.!?…])\s+(?=[A-ZÀ-Ỹ"“])', para)
    return [p.strip() for p in parts if p.strip()]


def split_units(raw_text: str) -> List[tuple]:
    """Tách truyện thành (câu, là_lời_thoại). Dòng thoại '- Ai đó? - bà thều thào.' được tách
    thành lời thoại 'Ai đó?' và lời dẫn 'bà thều thào.'"""
    out: List[tuple] = []
    for para in re.split(r"\n+", raw_text):
        para = para.strip()
        if not para:
            continue
        if re.match(r"^" + DASH, para):
            m = _INLINE_DASH_DIALOGUE.match(para)
            if m:
                out.append((m.group(1).strip(), True))
                out.extend((s, False) for s in _split_para_sentences(m.group(2)))
            else:
                out.append((re.sub(r"^" + DASH + r"\s*", "", para), True))
            continue
        # Thoại trong ngoặc kép, ở đầu hoặc giữa đoạn: 'Tía thì thầm: "Đừng nhìn." rồi im bặt.'
        for i, piece in enumerate(_QUOTE_SPLIT.split(para)):
            if i % 2:  # phần trong ngoặc
                out.extend((s, True) for s in _split_para_sentences(piece.strip()))
                continue
            piece = re.sub(r"^\s*(?:" + DASH + r"|,)\s*", "", piece)
            piece = re.sub(r"\s*" + DASH + r"\s*$", "", piece).strip()
            if re.search(r"[\wÀ-ỹ]", piece):
                out.extend((s, False) for s in _split_para_sentences(piece))
    return out


def split_sentences(raw_text: str) -> List[str]:
    return [t for t, _ in split_units(raw_text)]


class HorrorScriptAnalyzer:
    """Đạo diễn theo luật. `analyze_text` giữ API cũ; `direct` trả về cả danh sách nhân vật."""

    def __init__(self, default_speaker: str = "narrator", mood: str = "kinh_di_nang"):
        self.default_speaker = default_speaker
        self.mood = mood

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _match_any(text: str, words: List[str]) -> bool:
        return any(w in text for w in words)

    @staticmethod
    def _ghost_preset(lower: str) -> Optional[str]:
        for preset, patterns in GHOST_ENTITIES.items():
            if any(re.search(r"(?<![\wÀ-ỹ])" + p, lower) for p in patterns):
                return preset
        return None

    @staticmethod
    def _speaker_from_context(context: str) -> Optional[tuple]:
        """Tìm 'bà cụ thều thào', 'tiếng thằng Tèo hét' ... gần câu thoại."""
        lower = context.lower()
        gap = r"\s+(?:[\wÀ-ỹ,]+\s+){0,5}?(?:" + SPEECH_VERBS + r")"
        # "tôi run rẩy kêu lên" -> chính người kể đang nói
        if re.match(r"^\s*" + SELF_PRONOUNS + gap, lower):
            return ("narrator", "", "", "")
        for word, gender, age in KINSHIP:
            pat = r"(?<![\wÀ-ỹ])" + re.escape(word) + r"(?:\s+[A-ZÀ-Ỹ][\wÀ-ỹ]*)?" + gap
            m = re.search(pat, lower)
            if m:
                name_m = re.search(re.escape(word) + r"\s+([A-ZÀ-Ỹ][\wÀ-ỹ]*)", context, flags=re.I)
                name = name_m.group(1) if name_m and name_m.group(1)[0].isupper() else ""
                return word, gender, age, name
        return None

    def _emotion(self, lower: str, is_dialogue: bool, text: str) -> str:
        for emo, cues in EMOTION_CUES:
            if self._match_any(lower, cues):
                return emo
        if is_dialogue and text.rstrip().endswith("!"):
            return "het"
        return "binh_thuong"

    # ------------------------------------------------------------ main
    def direct(self, raw_text: str) -> DirectedScript:
        units = split_units(raw_text)
        sentences = [t for t, _ in units]
        characters: Dict[str, Character] = {}
        segments: List[ScriptSegment] = []
        tension = 2.0
        last_speaker_ctx: Optional[tuple] = None

        for idx, (sentence, is_dialogue) in enumerate(units, start=1):
            lower = sentence.lower()

            # 1. Độ căng: cộng dồn theo từ khóa, giảm dần nếu yên ả
            boost = 2.5 * sum(k in lower for k in HIGH) + 1.2 * sum(k in lower for k in MED)
            tension = min(10.0, max(1.0, tension * 0.7 + boost))

            # 2. Người nói
            speaker = "narrator"
            ghost = self._ghost_preset(lower)
            if is_dialogue and not ghost and idx < len(sentences):
                ghost = self._ghost_preset(sentences[idx].lower())
            if is_dialogue:
                # Lời dẫn ngay sau câu thoại ("bà cụ thều thào") thường cho biết ai nói
                nxt = units[idx][0] if idx < len(units) and not units[idx][1] else ""
                prev = units[idx - 2][0] if idx >= 2 and not units[idx - 2][1] else ""
                ctx = (self._speaker_from_context(sentence) or self._speaker_from_context(nxt)
                       or self._speaker_from_context(prev) or last_speaker_ctx)
                if ghost:
                    key = ghost
                    characters.setdefault(key, Character(
                        key=key, display_name={"ma_nu": "Ma nữ", "quy_du": "Quỷ",
                                               "vong_hon": "Vong hồn"}[ghost],
                        gender="nu" if ghost == "ma_nu" else "nam", age_group="thanh_nien",
                        is_ghost=True, ghost_preset=ghost))
                    speaker = key
                elif ctx and ctx[0] == "narrator":
                    speaker = "narrator"
                    last_speaker_ctx = ctx
                elif ctx:
                    word, gender, age, name = ctx
                    key = re.sub(r"\W+", "_", f"{word}_{name}".strip("_").lower())
                    characters.setdefault(key, Character(
                        key=key, display_name=f"{word} {name}".strip(), gender=gender, age_group=age))
                    speaker = key
                    last_speaker_ctx = ctx
                else:
                    speaker = "nhan_vat"
                    characters.setdefault("nhan_vat", Character(key="nhan_vat", display_name="Nhân vật"))

            # 3. Vị trí âm thanh
            spatial = "center"
            if "thì thầm" in lower or "bên tai" in lower:
                spatial = "left_to_right" if idx % 2 == 0 else "right"
            elif "sau lưng" in lower or "phía sau" in lower:
                spatial = "rear"
            elif "bên trái" in lower:
                spatial = "left"
            elif "bên phải" in lower:
                spatial = "right"

            # 4. Jump scare + SFX
            is_jumpscare = tension >= 8.0 and self._match_any(
                lower, ["đột ngột", "bất thình lình", "vồ lấy", "chụp lấy", "túm lấy", "hét lên"])
            sfx = "jumpscare_screech" if is_jumpscare else next(
                (cue for cue, words in SFX_CUES if self._match_any(lower, words)), None)

            # 5. Cảm xúc & nhịp
            emotion = self._emotion(lower, is_dialogue, sentence)
            # Lời thoại lấy cảm xúc từ lời dẫn ngay sau: "- Ai đó? - bà thều thào." -> thì thầm
            # hoặc từ câu dẫn phía trước 'tía chỉ thì thầm: "..."', hoặc câu thoại liền trước cùng người nói.
            if is_dialogue and emotion == "binh_thuong":
                prev_seg = segments[-1] if segments else None
                if prev_seg and prev_seg.text.rstrip().endswith(":"):
                    emotion = prev_seg.emotion
                elif prev_seg and prev_seg.speaker == speaker and speaker != "narrator" \
                        and units[idx - 2][1]:
                    emotion = prev_seg.emotion
                elif idx < len(units) and not units[idx][1]:
                    emotion = self._emotion(units[idx][0].lower(), False, units[idx][0])
            if speaker in GHOST_ENTITIES and emotion == "binh_thuong":
                emotion = "thi_tham" if ghost == "ma_nu" else "lanh_lung"
            nonverbal = "thở dài" if emotion in ("buon", "ai_oan") and "thở dài" in lower else None

            if idx == len(sentences):
                pause = 2.5
            elif is_jumpscare:
                pause = 1.8
            elif sentence.rstrip().endswith(("...", "…")):
                pause = 1.4
            elif tension > 7.0:
                pause = 0.45
            elif is_dialogue:
                pause = 0.6
            else:
                pause = 0.9

            segments.append(ScriptSegment(
                segment_id=idx, text=sentence, speaker=speaker, tension=round(tension, 1),
                spatial_position=spatial, pause_after=pause, is_jumpscare=is_jumpscare,
                sfx_cue=sfx, voice_preset=ghost if speaker in GHOST_ENTITIES else None,
                emotion=emotion, nonverbal=nonverbal,
            ))

        return DirectedScript(segments=segments, characters=characters, story_region=detect_region(raw_text))

    def analyze_text(self, raw_text: str) -> List[ScriptSegment]:
        return self.direct(raw_text).segments
