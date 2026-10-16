"""Đạo diễn AI dùng Claude: đọc hiểu truyện như một người kể chuyện ma Việt Nam thật.

Chỉ chạy khi có ANTHROPIC_API_KEY. Lỗi gì cũng rơi về HorrorScriptAnalyzer (luật).
Không viết lại nội dung truyện — chỉ chia câu và gắn chỉ dẫn đọc.
"""
from __future__ import annotations

import logging
import os
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel

from .script_analyzer import Character, DirectedScript, HorrorScriptAnalyzer, ScriptSegment

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-5-5"
CHUNK_CHARS = 4000

Emotion = Literal["binh_thuong", "hoi_hop", "so_hai", "thi_tham", "het", "buon", "ai_oan", "lanh_lung"]


class LineDirection(BaseModel):
    text: str
    speaker: str
    emotion: Emotion
    tension: float
    pause_after_ms: int
    speed: float
    spatial: Literal["center", "left", "right", "rear", "left_to_right"]
    nonverbal: Literal["none", "thở dài", "cười", "hắng giọng"]
    sfx: Literal["none", "footsteps_creak", "door_creak", "wind_howl", "rain_storm", "dog_howl", "owl",
                 "temple_bell", "funeral_horn", "water_drip", "jumpscare_screech"]
    is_jumpscare: bool


class CharacterSheet(BaseModel):
    key: str
    display_name: str
    gender: Literal["nam", "nu"]
    age_group: Literal["tre_em", "thanh_nien", "trung_nien", "gia"]
    ghost_preset: Literal["none", "ma_nu", "quy_du", "vong_hon"]


class ChunkScript(BaseModel):
    story_region: Literal["bac", "trung", "nam"]
    characters: List[CharacterSheet]
    lines: List[LineDirection]


SYSTEM_PROMPT = """Bạn là đạo diễn lồng tiếng cho kênh audio truyện ma tiếng Việt. Bạn hiểu sâu văn hóa \
và lối kể chuyện ma truyền miệng của người Việt. Nhiệm vụ: chia truyện thành từng câu đọc và ghi chỉ dẫn \
diễn xuất để máy đọc (TTS) nghe như người kể thật, không đều đều như AI.

QUY TẮC CỨNG
- Giữ NGUYÊN VĂN chữ của truyện. Không thêm, bớt, diễn giải, sửa giọng văn. Chỉ được tách một câu quá dài \
(> 40 chữ) ở dấu phẩy thành 2 dòng. Ghép các dòng lại phải ra đúng truyện gốc.
- Lời thoại tách riêng khỏi lời dẫn. Câu "- Ai đó? - bà cụ thều thào." thành 2 dòng: lời thoại (speaker = bà cụ) \
và lời dẫn "bà cụ thều thào." (speaker = narrator).
- speaker = "narrator" cho lời người kể; các nhân vật dùng key không dấu, ổn định suốt truyện \
(ví dụ ba_cu, thang_teo, ma_nu_ben_song) và phải có trong `characters`.

NGỮ CẢNH VIỆT NAM CẦN NẮM
- Xưng hô cho biết giới và tuổi: bà/cụ/lão (già), cô/chị/mợ/thím/dì (nữ), anh/chú/bác/cậu (nam), \
thằng/con bé/đứa nhỏ (trẻ con). Ma xưng "ta", gọi người sống là "mày/ngươi" thường lạnh lùng, ai oán.
- Thực thể dân gian: ma da (chết đuối, dưới sông/giếng, kéo chân người), ma lai, ma xó, ma trành, \
quỷ nhập tràng (xác chết bật dậy), vong/người âm/cô hồn (tháng bảy âm lịch, rằm tháng bảy, cúng cô hồn), \
trùng tang, bùa ngải. ghost_preset: ma nữ/ma da/ma lai -> ma_nu; quỷ, xác sống, ma trành -> quy_du; \
vong hồn, người âm, tiếng gọi từ xa -> vong_hon. Người sống luôn là "none".
- Không khí: canh ba/giờ Tý, đèn dầu tắt phụt, nhang khói, chó tru, cú kêu (điềm gở), kèn đám ma, \
tiếng mõ chùa, cây đa/cây gạo đầu làng, bến sông, giếng làng, nghĩa địa. Gắn sfx đúng lúc, không lạm dụng \
(trung bình 1 sfx mỗi 5-8 câu).
- story_region: bối cảnh miền Tây/Sài Gòn, từ "má, tía, hông, dzậy" -> nam; Huế/Quảng/Nghệ Tĩnh, \
"mô, răng, rứa, chừ" -> trung; còn lại -> bac.

CÁCH NGƯỜI KỂ CHUYỆN MA VIỆT GIỮ NHỊP
- Mở truyện chậm, trầm (speed 0.92-0.96, tension 1-3). Đoạn rình rập: chậm lại, câu ngắn, ngắt dài trước \
chi tiết rợn (pause 900-1600ms, emotion hoi_hop). Cao trào: nhanh, dồn (speed 1.05-1.12, pause 250-450ms).
- Ngay trước câu hù (is_jumpscare), câu trước đó phải ngắt dài 1200-1800ms. Tối đa 1 jump scare mỗi ~25 câu.
- Câu chốt cuối hoặc chi tiết lạnh gáy: ngắt rất dài (2000-3000ms).
- Câu kết thúc bằng "..." thì ngắt >= 1000ms. Lời thoại nối tiếp nhau thì ngắt 300-600ms.
- nonverbal: chỉ dùng "thở dài" ở câu buồn/ai oán của lời người kể hoặc nhân vật, "cười" cho tiếng cười \
rợn của ma, rất tiết chế (tối đa 1 lần mỗi 15 câu). Còn lại "none".
- spatial: tiếng thì thầm bên tai -> left_to_right/right; "sau lưng/phía sau" -> rear; còn lại center.
- tension 0-10, speed 0.85-1.15, pause_after_ms 150-3000."""


class LLMDirector:
    def __init__(self, model: Optional[str] = None, mood: str = "kinh_di_nang"):
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = model or os.environ.get("VODIE_LLM_MODEL", DEFAULT_MODEL)
        self.mood = mood

    @staticmethod
    def is_available() -> bool:
        if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
            return False
        try:
            import anthropic  # noqa: F401
            return True
        except ImportError:
            return False

    @staticmethod
    def _chunks(text: str) -> List[str]:
        chunks, buf = [], ""
        for para in text.split("\n"):
            if buf and len(buf) + len(para) > CHUNK_CHARS:
                chunks.append(buf)
                buf = ""
            buf += para + "\n"
        if buf.strip():
            chunks.append(buf)
        return chunks

    def _direct_chunk(self, chunk: str, known: Dict[str, Character], idx: int, total: int) -> ChunkScript:
        cast = "\n".join(f"- {c.key}: {c.display_name} ({c.gender}, {c.age_group}, "
                         f"ma={c.ghost_preset or 'none'})" for c in known.values()) or "(chưa có)"
        user = (f"Mood của truyện: {self.mood}. Đây là phần {idx}/{total}.\n"
                f"Nhân vật đã xác định ở các phần trước (dùng lại đúng key):\n{cast}\n\n"
                f"<truyen>\n{chunk}\n</truyen>")
        resp = self.client.messages.parse(
            model=self.model,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user}],
            output_format=ChunkScript,
        )
        if resp.stop_reason == "refusal" or resp.parsed_output is None:
            raise RuntimeError(f"LLM không trả kịch bản (stop_reason={resp.stop_reason})")
        return resp.parsed_output

    def direct(self, raw_text: str) -> DirectedScript:
        characters: Dict[str, Character] = {}
        segments: List[ScriptSegment] = []
        regions: List[str] = []
        chunks = self._chunks(raw_text)
        for i, chunk in enumerate(chunks, start=1):
            logger.info("Đạo diễn AI đang xử lý phần %d/%d...", i, len(chunks))
            out = self._direct_chunk(chunk, characters, i, len(chunks))
            regions.append(out.story_region)
            for c in out.characters:
                preset = None if c.ghost_preset == "none" else c.ghost_preset
                characters.setdefault(c.key, Character(
                    key=c.key, display_name=c.display_name, gender=c.gender, age_group=c.age_group,
                    is_ghost=preset is not None, ghost_preset=preset))
            for line in out.lines:
                if not line.text.strip():
                    continue
                spk = line.speaker if line.speaker == "narrator" or line.speaker in characters else "narrator"
                ch = characters.get(spk)
                segments.append(ScriptSegment(
                    segment_id=len(segments) + 1,
                    text=line.text.strip(),
                    speaker=spk,
                    tension=round(min(10.0, max(0.0, line.tension)), 1),
                    spatial_position=line.spatial,
                    pause_after=min(3000, max(150, line.pause_after_ms)) / 1000.0,
                    is_jumpscare=line.is_jumpscare,
                    sfx_cue=None if line.sfx == "none" else line.sfx,
                    voice_preset=ch.ghost_preset if ch else None,
                    emotion=line.emotion,
                    speed=min(1.15, max(0.85, line.speed)),
                    nonverbal=None if line.nonverbal == "none" else line.nonverbal,
                ))
        region = max(set(regions), key=regions.count) if regions else "bac"
        return DirectedScript(segments=segments, characters=characters, story_region=region)


def direct_story(raw_text: str, mood: str = "kinh_di_nang", use_llm: Optional[bool] = None) -> DirectedScript:
    """Dùng Claude nếu có key (hoặc use_llm=True), lỗi thì rơi về đạo diễn theo luật."""
    if use_llm is None:
        use_llm = LLMDirector.is_available()
    if use_llm:
        try:
            return LLMDirector(mood=mood).direct(raw_text)
        except Exception as e:  # noqa: BLE001 - luôn có phương án dự phòng
            logger.warning("Đạo diễn AI lỗi (%s) -> dùng đạo diễn theo luật.", e)
    return HorrorScriptAnalyzer(mood=mood).direct(raw_text)
