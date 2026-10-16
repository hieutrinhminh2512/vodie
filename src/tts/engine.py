"""Điểm vào tổng hợp giọng: chuẩn hóa -> engine (VieNeu/ElevenLabs/edge) -> cắt lặng, chỉnh tốc độ -> cache."""
from __future__ import annotations

import hashlib
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from pydub import AudioSegment
from pydub.silence import detect_leading_silence

from ..config import CACHE_DIR, SETTINGS
from .backends import TTSBackend, create_backend
from .text_normalizer import TextNormalizer
from .voice_manager import VoiceManager, VoiceProfile

logger = logging.getLogger(__name__)
CACHE_VERSION = "v3"


def _trim_silence(seg: AudioSegment, keep_ms: int = 60) -> AudioSegment:
    """Bỏ khoảng lặng thừa đầu/cuối do engine sinh ra; ngắt nghỉ do đạo diễn quyết định."""
    thresh = seg.dBFS - 30 if seg.dBFS != float("-inf") else -60
    start = max(0, detect_leading_silence(seg, silence_threshold=thresh) - keep_ms)
    end = max(0, detect_leading_silence(seg.reverse(), silence_threshold=thresh) - keep_ms)
    trimmed = seg[start: len(seg) - end]
    return trimmed if len(trimmed) > 200 else seg


def _change_tempo(path: Path, speed: float) -> None:
    """Đổi tốc độ không đổi cao độ (ffmpeg atempo). Không có ffmpeg thì bỏ qua."""
    ffmpeg = AudioSegment.converter if shutil.which(str(AudioSegment.converter)) else shutil.which("ffmpeg")
    if not ffmpeg or abs(speed - 1.0) < 0.02:
        return
    tmp = path.with_name(path.stem + "_tempo" + path.suffix)
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(path), "-filter:a",
                    f"atempo={speed:.3f}", str(tmp)], check=True)
    tmp.replace(path)


class TTSEngine:
    def __init__(self, engine: Optional[str] = None, dialect: str = "bac",
                 voice_manager: Optional[VoiceManager] = None):
        tts_cfg = SETTINGS.get("tts", {})
        self.engine_name = engine or tts_cfg.get("engine", "auto")
        self.backend: TTSBackend = create_backend(
            self.engine_name,
            mode=tts_cfg.get("vieneu_mode"),
            device=tts_cfg.get("device"),
            temperature=tts_cfg.get("temperature"),
        )
        self.normalizer = TextNormalizer(dialect=dialect)
        self.voice_manager = voice_manager or VoiceManager()
        logger.info("Engine giọng đọc: %s", self.backend.name)

    def cache_path(self, text: str, voice: VoiceProfile, emotion: str, nonverbal: Optional[str],
                   speed: float) -> Path:
        key = "|".join([CACHE_VERSION, self.backend.name, voice.cache_key(), emotion, nonverbal or "",
                        f"{speed:.2f}", text])
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:20]
        return CACHE_DIR / "tts" / f"{digest}{self.backend.file_ext}"

    def synthesize(
        self,
        text: str,
        voice: VoiceProfile | str = "narrator_bac_nam",
        emotion: str = "binh_thuong",
        nonverbal: Optional[str] = None,
        speed: float = 1.0,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Đọc 1 câu. Trả về đường dẫn file audio (đã cache — đọc lại câu cũ không tốn thời gian)."""
        if isinstance(voice, str):
            voice = self.voice_manager.get_voice(voice)
        spoken = self.normalizer.normalize(text)
        if not spoken.strip():
            spoken = "..."
        cached = self.cache_path(spoken, voice, emotion, nonverbal, speed)
        if not (cached.exists() and cached.stat().st_size > 0):
            raw = self.backend.synthesize(spoken, voice, cached, emotion=emotion, nonverbal=nonverbal)
            seg = _trim_silence(AudioSegment.from_file(str(raw)))
            fmt = raw.suffix.lstrip(".")
            seg.export(str(raw), format=fmt)
            _change_tempo(raw, speed)
            if raw != cached:
                raw.replace(cached)
        if output_path is not None:
            output_path = output_path.with_suffix(cached.suffix)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(cached, output_path)
            return output_path
        return cached
