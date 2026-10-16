import asyncio
from pathlib import Path
from typing import Optional
import os

from .text_normalizer import TextNormalizer
from .voice_manager import VoiceManager
from ..config import TEMP_DIR


class TTSEngine:
    """Động cơ tổng hợp giọng đọc tiếng Việt chuyên nghiệp."""

    def __init__(self):
        self.normalizer = TextNormalizer()
        self.voice_manager = VoiceManager()

    async def synthesize_async(
        self,
        text: str,
        voice_id: str = "nguyen_ngoc_ngan",
        rate: str = None,
        pitch: str = None,
        output_path: Optional[Path] = None
    ) -> Path:
        """Tổng hợp một câu thành tệp audio theo phong cách nghệ sĩ kể chuyện ma."""
        normalized_text = self.normalizer.normalize(text)
        voice_profile = self.voice_manager.get_voice(voice_id)

        edge_voice = voice_profile.edge_voice if voice_profile else "vi-VN-NamMinhNeural"
        final_pitch = pitch or (voice_profile.pitch_offset if voice_profile else "-20Hz")
        final_rate = rate or (voice_profile.rate_offset if voice_profile else "-15%")

        if output_path is None:
            output_path = TEMP_DIR / f"tts_{hash(text)}_{os.getpid()}.mp3"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            import edge_tts
            communicate = edge_tts.Communicate(
                normalized_text,
                voice=edge_voice,
                rate=final_rate,
                pitch=final_pitch
            )
            await communicate.save(str(output_path))
        except Exception as e:
            print(f"[CẢNH BÁO TTS] edge-tts error: {e}. Tạo audio placeholder.")
            self._generate_silence_placeholder(output_path, duration_sec=1.5)

        return output_path

    def synthesize(
        self,
        text: str,
        voice_id: str = "nguyen_ngoc_ngan",
        rate: str = None,
        pitch: str = None,
        output_path: Optional[Path] = None
    ) -> Path:
        """Đồng bộ wrapper cho synthesize_async."""
        return asyncio.run(self.synthesize_async(text, voice_id, rate, pitch, output_path))

    def _generate_silence_placeholder(self, path: Path, duration_sec: float = 1.0):
        """Tạo file wav/mp3 trống khi cần fallback offline."""
        import wave
        import struct
        wav_path = path.with_suffix(".wav")
        sample_rate = 44100
        n_samples = int(sample_rate * duration_sec)
        with wave.open(str(wav_path), 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            for _ in range(n_samples):
                f.writeframes(struct.pack('<h', 0))
        if path.suffix != ".wav":
            try:
                os.replace(wav_path, path)
            except Exception:
                pass
