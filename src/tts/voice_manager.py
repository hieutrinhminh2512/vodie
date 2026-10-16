import os
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class VoiceProfile:
    id: str
    name: str
    region: str  # "bac", "nam", "trung"
    gender: str  # "nam", "nu"
    edge_voice: str
    is_cloned: bool = False
    source_audio_path: Optional[str] = None
    consent_confirmed: bool = False


class VoiceManager:
    """Quản lý thư viện giọng nói, giọng vùng miền và voice cloning hợp pháp."""

    BUILTIN_VOICES = {
        "nguoi_ke_bac": VoiceProfile(
            id="nguoi_ke_bac",
            name="Nam Minh (Giọng Bắc Trầm Ấm)",
            region="bac",
            gender="nam",
            edge_voice="vi-VN-NamMinhNeural"
        ),
        "nguoi_ke_nam": VoiceProfile(
            id="nguoi_ke_nam",
            name="Hoài My (Giọng Nam Truyền Cảm)",
            region="nam",
            gender="nu",
            edge_voice="vi-VN-HoaiMyNeural"
        )
    }

    def __init__(self):
        self.voices = dict(self.BUILTIN_VOICES)

    def list_voices(self) -> List[VoiceProfile]:
        return list(self.voices.values())

    def get_voice(self, voice_id: str) -> Optional[VoiceProfile]:
        return self.voices.get(voice_id, self.voices.get("nguoi_ke_bac"))

    def register_cloned_voice(
        self,
        voice_id: str,
        name: str,
        source_audio_path: str,
        consent_confirmed: bool
    ) -> VoiceProfile:
        """
        Đăng ký một giọng nhái mới vào thư viện.
        BẮT BUỘC: consent_confirmed phải là True.
        """
        if not consent_confirmed:
            raise PermissionError(
                "Yêu cầu pháp lý: Bạn phải xác nhận cam kết có quyền sử dụng giọng nói này trước khi clone!"
            )

        if not os.path.exists(source_audio_path):
            raise FileNotFoundError(f"Không tìm thấy tệp âm thanh mẫu: {source_audio_path}")

        profile = VoiceProfile(
            id=voice_id,
            name=name,
            region="custom",
            gender="unknown",
            edge_voice="vi-VN-NamMinhNeural",
            is_cloned=True,
            source_audio_path=source_audio_path,
            consent_confirmed=True
        )
        self.voices[voice_id] = profile
        return profile
