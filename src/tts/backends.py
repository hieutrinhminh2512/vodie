"""Các engine TTS dạng plugin. Engine nào cũng nhận 1 câu đã chuẩn hóa và trả về file audio.

- vieneu:     VieNeu-TTS v3 Turbo — giọng người Việt thật, clone giọng từ clip 3–8 giây,
              chạy local (CPU qua ONNX, hoặc GPU). Mặc định.
- elevenlabs: ElevenLabs eleven_v3 qua API (trả phí), có audio tag cảm xúc.
- edge:       Microsoft edge-tts. Chỉ dùng dự phòng khi chưa cài được VieNeu.
"""
from __future__ import annotations

import asyncio
import logging
import os
import threading
from pathlib import Path
from typing import Optional

from .voice_manager import VoiceProfile

logger = logging.getLogger(__name__)

# Cảm xúc trong kịch bản -> thẻ phi ngôn từ của từng engine.
# VieNeu v3 Turbo chỉ hiểu 3 thẻ (thử nghiệm): [cười], [thở dài], [hắng giọng].
VIENEU_NONVERBAL = {"thở dài", "cười", "hắng giọng"}
ELEVENLABS_EMOTION_TAGS = {
    "thi_tham": "[whispers]",
    "so_hai": "[nervous]",
    "het": "[shouts]",
    "buon": "[sad]",
    "ai_oan": "[sad]",
    "hoi_hop": "[nervous]",
    "lanh_lung": "[calm]",
}
ELEVENLABS_NONVERBAL = {"thở dài": "[sighs]", "cười": "[laughs]", "hắng giọng": "[clears throat]"}


class TTSBackend:
    name = "base"
    file_ext = ".wav"

    def synthesize(self, text: str, voice: VoiceProfile, out_path: Path,
                   emotion: str = "binh_thuong", nonverbal: Optional[str] = None) -> Path:
        raise NotImplementedError

    @staticmethod
    def is_available() -> bool:
        return True


class VieNeuBackend(TTSBackend):
    """VieNeu-TTS v3 Turbo. Model nặng nên chỉ nạp 1 lần cho cả tiến trình."""

    name = "vieneu"
    _model = None
    _lock = threading.Lock()
    _registered_clones: set[str] = set()

    def __init__(self, mode: str = "v3turbo", device: str = "auto", temperature: float = 0.7):
        self.mode = mode
        self.device = device
        self.temperature = temperature

    @staticmethod
    def is_available() -> bool:
        try:
            import vieneu  # noqa: F401
            return True
        except ImportError:
            return False

    def _get_model(self):
        with VieNeuBackend._lock:
            if VieNeuBackend._model is None:
                from vieneu import Vieneu
                logger.info("Đang nạp VieNeu-TTS (%s, device=%s)... lần đầu sẽ tải model về máy.",
                            self.mode, self.device)
                kwargs = {"device": self.device} if self.mode == "v3turbo" else {}
                VieNeuBackend._model = Vieneu(mode=self.mode, **kwargs)
            return VieNeuBackend._model

    def list_preset_voices(self) -> list[str]:
        return [vid for _, vid in self._get_model().list_preset_voices()]

    def _voice_arg(self, voice: VoiceProfile):
        model = self._get_model()
        if voice.ref_audio:
            key = f"clone::{voice.id}"
            if key not in VieNeuBackend._registered_clones:
                model.add_voice(key, voice.ref_audio, denoise=True)
                VieNeuBackend._registered_clones.add(key)
            return key
        return voice.vieneu_voice

    def synthesize(self, text, voice, out_path, emotion="binh_thuong", nonverbal=None):
        if nonverbal in VIENEU_NONVERBAL:
            text = f"{text} [{nonverbal}]" if nonverbal == "thở dài" else f"[{nonverbal}] {text}"
        model = self._get_model()
        audio = model.infer(text, voice=self._voice_arg(voice), temperature=self.temperature)
        out_path = out_path.with_suffix(".wav")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        model.save(audio, str(out_path))
        return out_path


class ElevenLabsBackend(TTSBackend):
    name = "elevenlabs"
    file_ext = ".mp3"
    URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    def __init__(self, model_id: str = "eleven_v3"):
        self.api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        self.model_id = model_id

    @staticmethod
    def is_available() -> bool:
        return bool(os.environ.get("ELEVENLABS_API_KEY"))

    def synthesize(self, text, voice, out_path, emotion="binh_thuong", nonverbal=None):
        import requests

        if not voice.elevenlabs_voice_id:
            raise ValueError(f"Giọng '{voice.id}' chưa có elevenlabs_voice_id trong config/voices.yaml")
        tags = " ".join(t for t in (ELEVENLABS_EMOTION_TAGS.get(emotion),
                                    ELEVENLABS_NONVERBAL.get(nonverbal or "")) if t)
        payload = {"text": f"{tags} {text}".strip(), "model_id": self.model_id}
        out_path = out_path.with_suffix(".mp3")
        last_err: Optional[Exception] = None
        for attempt in range(3):
            try:
                r = requests.post(
                    self.URL.format(voice_id=voice.elevenlabs_voice_id),
                    params={"output_format": "mp3_44100_128"},
                    headers={"xi-api-key": self.api_key, "Content-Type": "application/json"},
                    json=payload, timeout=120,
                )
                if r.status_code in (429, 500, 502, 503) and attempt < 2:
                    raise RuntimeError(f"ElevenLabs {r.status_code}")
                r.raise_for_status()
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(r.content)
                return out_path
            except Exception as e:  # noqa: BLE001 - thử lại lỗi mạng/API
                last_err = e
                import time
                time.sleep(2 ** attempt)
        raise RuntimeError(f"ElevenLabs lỗi sau 3 lần thử: {last_err}")


class EdgeBackend(TTSBackend):
    """Dự phòng. Đọc nguyên câu một lần (không cắt vế) để giữ ngữ điệu tự nhiên."""

    name = "edge"
    file_ext = ".mp3"
    EMOTION_RATE = {"thi_tham": "-12%", "buon": "-10%", "ai_oan": "-10%", "hoi_hop": "+6%",
                    "so_hai": "+8%", "het": "+10%"}

    @staticmethod
    def is_available() -> bool:
        try:
            import edge_tts  # noqa: F401
            return True
        except ImportError:
            return False

    def synthesize(self, text, voice, out_path, emotion="binh_thuong", nonverbal=None):
        import edge_tts

        out_path = out_path.with_suffix(".mp3")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        rate = self.EMOTION_RATE.get(emotion, "-4%")
        comm = edge_tts.Communicate(text, voice=voice.edge_voice, rate=rate)
        asyncio.run(comm.save(str(out_path)))
        return out_path


BACKENDS = {"vieneu": VieNeuBackend, "elevenlabs": ElevenLabsBackend, "edge": EdgeBackend}


def create_backend(name: str = "auto", **kwargs) -> TTSBackend:
    """name='auto': VieNeu nếu đã cài, không thì edge-tts (và cảnh báo rõ)."""
    if name == "auto":
        if VieNeuBackend.is_available():
            name = "vieneu"
        else:
            logger.warning("Chưa cài VieNeu-TTS -> tạm dùng edge-tts (giọng sẽ kém tự nhiên). "
                           "Cài bằng: pip install vieneu")
            name = "edge"
    cls = BACKENDS.get(name)
    if cls is None:
        raise ValueError(f"Engine TTS không hợp lệ: {name}. Chọn: auto, {', '.join(BACKENDS)}")
    if not cls.is_available():
        raise RuntimeError(f"Engine '{name}' chưa sẵn sàng (thiếu thư viện hoặc API key).")
    accepted = {"vieneu": {"mode", "device", "temperature"}, "elevenlabs": {"model_id"}}.get(name, set())
    return cls(**{k: v for k, v in kwargs.items() if k in accepted and v is not None})
