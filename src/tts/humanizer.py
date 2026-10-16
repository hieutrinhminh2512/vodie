import asyncio
import re
from pathlib import Path
from typing import List, Tuple
from pydub import AudioSegment
import edge_tts

from ..audio_engine.breath_synthesizer import BreathSynthesizer
from .text_normalizer import TextNormalizer
from ..config import TEMP_DIR


class HorrorVoiceHumanizer:
    """
    Động cơ biểu cảm và nhân hóa giọng đọc (Humanized Storyteller Cadence Engine).
    Giải quyết triệt để vấn đề 'giọng đọc quá AI, không nhấn nhá':
    - Phân tách câu thành các vế câu biểu cảm tự nhiên (Expressive Clauses).
    - Biến thiên tốc độ (rate) và cao độ (pitch) linh hoạt theo từng vế câu.
    - Chèn hơi thở tự nhiên (inhalation / gasp / sigh) của con người trước và giữa các câu.
    - Áp dụng khoảng ngắt nghỉ vi mô (micro-pauses) chuẩn ngữ điệu kể chuyện ma truyền thống.
    """

    def __init__(self):
        self.normalizer = TextNormalizer()

    def split_into_expressive_clauses(self, text: str) -> List[Tuple[str, str]]:
        """Phân rã câu thành các vế câu kèm dấu câu biểu cảm."""
        # Tách theo dấu chấm lửng, phẩy, chấm than, hai chấm, gạch ngang
        tokens = re.split(r'([,;:\.?!…]+|\.{3,}|[-—])', text)
        clauses = []
        current_text = ""
        for tok in tokens:
            if not tok:
                continue
            if re.match(r'^[,;:\.?!…\-—]+$', tok):
                current_text += " " + tok
                if current_text.strip():
                    clauses.append((current_text.strip(), tok))
                current_text = ""
            else:
                current_text += " " + tok

        if current_text.strip():
            clauses.append((current_text.strip(), "."))

        # Nếu cả câu không có dấu, giữ nguyên 1 vế
        if not clauses:
            clauses = [(text.strip(), ".")]

        return clauses

    async def synthesize_clause_async(
        self,
        text: str,
        voice: str,
        rate: str,
        pitch: str,
        temp_file: Path
    ) -> AudioSegment:
        """Tổng hợp một vế câu với tham số ngữ điệu riêng."""
        cleaned_text = self.normalizer.normalize(text)
        if not cleaned_text.strip():
            return AudioSegment.silent(duration=200)

        comm = edge_tts.Communicate(
            cleaned_text,
            voice=voice,
            rate=rate,
            pitch=pitch
        )
        await comm.save(str(temp_file))
        return AudioSegment.from_file(str(temp_file))

    async def humanize_sentence_async(
        self,
        text: str,
        voice: str = "vi-VN-NamMinhNeural",
        base_rate: str = "-15%",
        base_pitch: str = "-20Hz",
        tension: int = 5,
        is_opening: bool = False,
        speaker_style: str = "nguyen_ngoc_ngan",
        segment_id: int = 0
    ) -> AudioSegment:
        """
        Nhân hóa trọn vẹn một câu chuyện kinh dị:
        - Lấy hơi tự nhiên mở đầu
        - Đọc từng vế có độ nhịp thong thả, nhấn nhá, kéo giọng ở dấu lửng
        - Chèn tiếng nín thở hoặc giật mình ở những đoạn rùng rợn
        """
        clauses = self.split_into_expressive_clauses(text)
        assembled_sentence = AudioSegment.empty()

        # 1. Hơi thở mở đầu (Natural breath intake)
        # Người thật luôn hít một hơi khẽ trước khi kể một đoạn chuyện u tịch
        if tension >= 7:
            # Đoạn rùng rợn: lấy hơi thắt nghẹn
            assembled_sentence += BreathSynthesizer.generate_breath("gasp", duration_ms=360, intensity=0.065)
            assembled_sentence += AudioSegment.silent(duration=120)
        else:
            # Đoạn u tịch: lấy hơi sâu, trầm
            assembled_sentence += BreathSynthesizer.generate_breath("inhale", duration_ms=420, intensity=0.055)
            assembled_sentence += AudioSegment.silent(duration=150)

        total_clauses = len(clauses)
        base_rate_val = int(base_rate.replace("%", "").replace("+", ""))
        base_pitch_val = int(base_pitch.replace("Hz", "").replace("+", ""))

        for idx, (clause_text, punct) in enumerate(clauses):
            # 2. Điều chỉnh ngữ điệu vi mô theo từng vế câu
            if "..." in punct or "…" in punct:
                # Dấu ba chấm: giọng trầm xuống, chậm rãi ma mị kéo dài
                c_rate = f"{base_rate_val - 6}%"
                c_pitch = f"{base_pitch_val - 4}Hz"
                pause_ms = 1100 + (tension * 60)
            elif "!" in punct:
                # Dấu chấm than: nhấn mạnh, dứt khoát
                c_rate = f"{base_rate_val + 4}%"
                c_pitch = f"{base_pitch_val + 2}Hz"
                pause_ms = 850
            elif "," in punct:
                # Dấu phẩy: ngắt nghỉ tự nhiên của con người (450ms - 650ms)
                c_rate = f"{base_rate_val}%"
                c_pitch = f"{base_pitch_val}Hz"
                pause_ms = 520
            elif idx == total_clauses - 1:
                # Vế kết câu: hạ thấp giọng (Cadence Drop) để câu nói có chiều sâu kết thúc
                c_rate = f"{base_rate_val - 4}%"
                c_pitch = f"{base_pitch_val - 3}Hz"
                pause_ms = 400
            else:
                c_rate = f"{base_rate_val}%"
                c_pitch = f"{base_pitch_val}Hz"
                pause_ms = 450

            temp_clause_file = TEMP_DIR / f"clause_{segment_id}_{idx}_{hash(clause_text) % 10000}.mp3"
            try:
                clause_audio = await self.synthesize_clause_async(
                    clause_text, voice, c_rate, c_pitch, temp_clause_file
                )
                assembled_sentence += clause_audio
            except Exception as e:
                # Fallback nếu mạng chập chờn
                pass

            # 3. Chèn khoảng dừng vi mô giữa các vế câu
            assembled_sentence += AudioSegment.silent(duration=pause_ms)

            # Nếu là vế câu trước một từ khoá rùng rợn, chèn thêm hơi thở nín bặt
            if any(k in clause_text.lower() for k in ["bỗng nhiên", "đột ngột", "kinh hoàng", "rùng mình"]):
                assembled_sentence += BreathSynthesizer.generate_breath("gasp", duration_ms=280, intensity=0.06)

        return assembled_sentence
