"""Thư viện giọng: giọng dựng sẵn của VieNeu (3 miền) + giọng clone từ file trong thư mục voices/.

Cấu hình ở config/voices.yaml. Thêm giọng clone:
  1. Bỏ file voices/ten_giong.wav (3–8 giây, nói rõ, ít tạp âm).
  2. Thêm vào config/voices.yaml mục cloned_voices với `consent: true`
     (xác nhận bạn có quyền dùng giọng đó).
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from ..config import BASE_DIR, VOICES_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class VoiceProfile:
    id: str
    name: str
    region: str = "bac"      # bac | trung | nam
    gender: str = "nam"      # nam | nu
    age_group: str = "trung_nien"
    vieneu_voice: Optional[str] = None
    edge_voice: str = "vi-VN-NamMinhNeural"
    elevenlabs_voice_id: Optional[str] = None
    ref_audio: Optional[str] = None   # giọng clone
    is_cloned: bool = False
    consent_confirmed: bool = False
    tags: List[str] = field(default_factory=list)

    def cache_key(self) -> str:
        if self.ref_audio and os.path.exists(self.ref_audio):
            return f"clone:{self.id}:{os.path.getmtime(self.ref_audio):.0f}"
        return f"{self.id}:{self.vieneu_voice}:{self.edge_voice}:{self.elevenlabs_voice_id}"

    # Giữ tương thích code cũ
    @property
    def source_audio_path(self) -> Optional[str]:
        return self.ref_audio


def _edge_for(gender: str) -> str:
    return "vi-VN-HoaiMyNeural" if gender == "nu" else "vi-VN-NamMinhNeural"


class VoiceManager:
    def __init__(self, config: Optional[dict] = None):
        cfg = config if config is not None else VOICES_CONFIG
        self.voices: Dict[str, VoiceProfile] = {}
        self.aliases: Dict[str, str] = dict(cfg.get("aliases", {}) or {})
        self.default_voice: str = cfg.get("default_narrator", "narrator_bac_nam")

        for vid, v in (cfg.get("voices", {}) or {}).items():
            gender = v.get("gender", "nam")
            self.voices[vid] = VoiceProfile(
                id=vid, name=v.get("name", vid), region=v.get("region", "bac"), gender=gender,
                age_group=v.get("age_group", "trung_nien"), vieneu_voice=v.get("vieneu"),
                edge_voice=v.get("edge", _edge_for(gender)),
                elevenlabs_voice_id=v.get("elevenlabs") or None, tags=v.get("tags", []) or [],
            )

        for vid, v in (cfg.get("cloned_voices", {}) or {}).items():
            path = Path(v.get("file", ""))
            path = path if path.is_absolute() else BASE_DIR / path
            if not v.get("consent"):
                logger.warning("Bỏ qua giọng clone '%s': chưa xác nhận consent: true", vid)
                continue
            if not path.exists():
                logger.warning("Bỏ qua giọng clone '%s': không thấy file %s", vid, path)
                continue
            gender = v.get("gender", "nam")
            self.voices[vid] = VoiceProfile(
                id=vid, name=v.get("name", vid), region=v.get("region", "bac"), gender=gender,
                age_group=v.get("age_group", "trung_nien"), ref_audio=str(path),
                edge_voice=_edge_for(gender), elevenlabs_voice_id=v.get("elevenlabs") or None,
                is_cloned=True, consent_confirmed=True, tags=v.get("tags", []) or [],
            )

        if not self.voices:
            self.voices[self.default_voice] = VoiceProfile(
                id=self.default_voice, name="Người kể (Bắc, nam)", vieneu_voice="Phạm Tuyên")

    def list_voices(self) -> List[VoiceProfile]:
        return list(self.voices.values())

    def get_voice(self, voice_id: str) -> VoiceProfile:
        voice_id = self.aliases.get(voice_id, voice_id)
        return self.voices.get(voice_id) or self.voices.get(self.default_voice) or next(iter(self.voices.values()))

    def register_cloned_voice(self, voice_id: str, name: str, source_audio_path: str,
                              consent_confirmed: bool, gender: str = "nam", region: str = "bac") -> VoiceProfile:
        """Đăng ký giọng clone lúc chạy (Web UI). Bắt buộc xác nhận quyền sử dụng giọng."""
        if not consent_confirmed:
            raise PermissionError(
                "Bạn phải xác nhận có quyền sử dụng giọng nói này (giọng của chính bạn, "
                "hoặc đã được chủ giọng đồng ý) trước khi clone.")
        if not os.path.exists(source_audio_path):
            raise FileNotFoundError(f"Không tìm thấy tệp âm thanh mẫu: {source_audio_path}")
        profile = VoiceProfile(id=voice_id, name=name, region=region, gender=gender,
                               ref_audio=source_audio_path, edge_voice=_edge_for(gender),
                               is_cloned=True, consent_confirmed=True)
        self.voices[voice_id] = profile
        return profile

    # ------------------------------------------------------------ casting
    def pick(self, gender: str, region: str, age_group: str = "trung_nien",
             exclude: Optional[List[str]] = None) -> VoiceProfile:
        """Chọn giọng hợp nhất cho 1 vai: đúng giới > đúng miền > đúng tuổi > chưa ai dùng."""
        exclude = exclude or []

        def score(v: VoiceProfile) -> tuple:
            return (v.gender == gender, v.id not in exclude, "narrator" not in v.tags,
                    v.region == region, v.age_group == age_group, not v.is_cloned)

        return max(self.voices.values(), key=score)

    def cast(self, narrator_id: str, characters: dict, region: str) -> Dict[str, VoiceProfile]:
        """Phân vai: narrator + mỗi nhân vật 1 giọng khác nhau, ưu tiên cùng miền với truyện."""
        narrator = self.get_voice(narrator_id)
        casting: Dict[str, VoiceProfile] = {"narrator": narrator}
        used = [narrator.id]
        for key, ch in characters.items():
            voice = self.pick(ch.gender, region, ch.age_group, exclude=used)
            casting[key] = voice
            used.append(voice.id)
        return casting
