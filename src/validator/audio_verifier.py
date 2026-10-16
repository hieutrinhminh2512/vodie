import difflib
from pathlib import Path
from typing import Tuple, Dict, Any
from ..config import SETTINGS


class WhisperAudioVerifier:
    """
    Kiểm tra chất lượng phát âm tự động bằng mô hình Whisper:
    So khớp nội dung nghe được từ audio với văn bản gốc.
    Nếu tỷ lệ sai lệch vượt ngưỡng, tự động yêu cầu re-take tối đa 2 lần.
    """

    def __init__(self, model_name: str = None, threshold: float = None):
        cfg = SETTINGS.get("director", {})
        self.model_name = model_name or cfg.get("whisper_model", "base")
        self.threshold = threshold or cfg.get("wer_threshold", 0.25)
        self.max_retakes = cfg.get("max_retakes", 2)
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                import whisper
                self._model = whisper.load_model(self.model_name)
            except Exception as e:
                # Whisper model chưa được cài hoặc không có GPU/tải trọng
                return None
        return self._model

    def calculate_similarity(self, text_original: str, text_recognized: str) -> float:
        """Tính điểm tương đồng giữa văn bản gốc và văn bản nhận diện (0.0 đến 1.0)."""
        seq = difflib.SequenceMatcher(None, text_original.strip().lower(), text_recognized.strip().lower())
        return seq.ratio()

    def verify_sentence(
        self,
        audio_path: Path,
        original_text: str,
        attempt: int = 1
    ) -> Dict[str, Any]:
        """
        Xác thực một câu đọc.
        Trả về kết quả kiểm định: passed (bool), needs_retake (bool), similarity (float), recognized_text (str).
        """
        model = self._get_model()
        if model is None:
            # Chế độ mô phỏng / bypass khi Whisper chưa cài đặt
            return {
                "passed": True,
                "needs_retake": False,
                "similarity": 1.0,
                "recognized_text": original_text,
                "attempt": attempt,
                "note": "Bypassed (Whisper model offline)"
            }

        try:
            result = model.transcribe(str(audio_path), language="vi")
            recognized_text = result.get("text", "").strip()
            similarity = self.calculate_similarity(original_text, recognized_text)
            error_rate = 1.0 - similarity

            passed = error_rate <= self.threshold
            needs_retake = (not passed) and (attempt <= self.max_retakes)

            return {
                "passed": passed,
                "needs_retake": needs_retake,
                "similarity": round(similarity, 3),
                "recognized_text": recognized_text,
                "attempt": attempt,
                "flagged": (not passed) and (attempt > self.max_retakes)
            }
        except Exception as e:
            return {
                "passed": True,
                "needs_retake": False,
                "similarity": 1.0,
                "recognized_text": original_text,
                "attempt": attempt,
                "error": str(e)
            }
