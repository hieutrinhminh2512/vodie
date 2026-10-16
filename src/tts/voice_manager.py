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
    pitch_offset: str = "-0Hz"
    rate_offset: str = "+0%"
    is_cloned: bool = False
    source_audio_path: Optional[str] = None
    consent_confirmed: bool = False


class VoiceManager:
    """Quản lý thư viện giọng nói, giọng mô phỏng phong cách kể chuyện ma Việt Nam."""

    BUILTIN_VOICES = {
        "nguyen_ngoc_ngan": VoiceProfile(
            id="nguyen_ngoc_ngan",
            name="Phong cách Nguyễn Ngọc Ngạn (Trầm Ấm, Ma Mị Huyền Thoại)",
            region="bac",
            gender="nam",
            edge_voice="vi-VN-NamMinhNeural",
            pitch_offset="-22Hz",
            rate_offset="-16%"
        ),
        "quang_a_tun": VoiceProfile(
            id="quang_a_tun",
            name="Phong cách Quàng A Tũn (Kỳ Bí, Lạnh Lẽo)",
            region="bac",
            gender="nam",
            edge_voice="vi-VN-NamMinhNeural",
            pitch_offset="-16Hz",
            rate_offset="-10%"
        ),
        "dinh_soan": VoiceProfile(
            id="dinh_soan",
            name="Phong cách Đình Soạn (Xúc Động, Ly Kỳ)",
            region="bac",
            gender="nam",
            edge_voice="vi-VN-NamMinhNeural",
            pitch_offset="-12Hz",
            rate_offset="-12%"
        ),
        "nguoi_ke_bac": VoiceProfile(
            id="nguoi_ke_bac",
            name="Nam Minh (Giọng Kể Chuẩn Trầm)",
            region="bac",
            gender="nam",
            edge_voice="vi-VN-NamMinhNeural",
            pitch_offset="-18Hz",
            rate_offset="-12%"
        ),
        "nguoi_ke_nam": VoiceProfile(
            id="nguoi_ke_nam",
            name="Hoài My (Giọng Kể Truyền Cảm)",
            region="nam",
            gender="nu",
            edge_voice="vi-VN-HoaiMyNeural",
            pitch_offset="-8Hz",
            rate_offset="-10%"
        )
    }

    def __init__(self):
        self.voices = dict(self.BUILTIN_VOICES)

    def list_voices(self) -> List[VoiceProfile]:
        return list(self.voices.values())

    def get_voice(self, voice_id: str) -> Optional[VoiceProfile]:
        return self.voices.get(voice_id, self.voices.get("nguyen_ngoc_ngan"))

    def register_cloned_voice(
        self,
        voice_id: str,
        name: str,
        source_audio_path: str,
        consent_confirmed: bool
    ) -> VoiceProfile:
        """Đăng ký một giọng nhái mới vào thư viện kèm cam kết bản quyền."""
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
            pitch_offset="-20Hz",
            rate_offset="-15%",
            is_cloned=True,
            source_audio_path=source_audio_path,
            consent_confirmed=True
        )
        self.voices[voice_id] = profile
        return profile
