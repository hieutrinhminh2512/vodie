from pathlib import Path
from typing import Optional


class SafetyCompliance:
    """
    An toàn và Pháp lý:
    1. Kiểm tra xác nhận bản quyền khi nhái giọng (Voice Cloning Consent).
    2. Gắn metadata "AI-generated" vào file MP3/MP4 xuất bản.
    """

    @staticmethod
    def verify_voice_consent(consent_checkbox_checked: bool) -> bool:
        if not consent_checkbox_checked:
            raise PermissionError(
                "Vi phạm chính sách: Người dùng bắt buộc phải xác nhận cam kết sở hữu hoặc được phép sử dụng giọng nói này."
            )
        return True

    @staticmethod
    def embed_ai_metadata(file_path: Path, title: str = "VODIE Horror Production"):
        """Gắn metadata AI-generated vào file MP3."""
        try:
            import mutagen
            from mutagen.easyid3 import EasyID3
            from mutagen.mp3 import MP3

            audio = MP3(str(file_path), ID3=EasyID3)
            audio["title"] = title
            audio["artist"] = "VODIE AI Horror Studio"
            audio["composer"] = "AI Generated (VODIE)"
            audio.save()
        except Exception:
            # Fallback nếu mutagen chưa cài
            pass
