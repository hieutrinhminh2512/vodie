import numpy as np
import scipy.signal as signal
from pydub import AudioSegment


class VocalMasteringChain:
    """
    Xử lý giọng người kể ở mức nhẹ, kiểu phòng thu podcast:
    - Cắt ù dưới 70Hz (tiếng rền, gió micro).
    - Ấm nhẹ dải ngực 120–250Hz (+~2dB).
    - Không lọc cắt dải cao, không bão hòa: bản cũ cắt hết trên 6.8kHz và bão hòa tanh
      làm giọng bị bí, đục và nghe "máy" hơn.
    """

    @classmethod
    def apply_horror_mastering(cls, voice: AudioSegment, speaker_style: str = "") -> AudioSegment:
        sr = voice.frame_rate
        nyq = sr / 2.0
        ch = voice.channels
        samples = np.array(voice.get_array_of_samples(), dtype=np.float64).reshape(-1, ch)
        max_val = float(1 << (8 * voice.sample_width - 1))

        b_hp, a_hp = signal.butter(2, 70.0 / nyq, btype="high")
        b_bd, a_bd = signal.butter(2, [120.0 / nyq, 250.0 / nyq], btype="band")
        out = np.empty_like(samples)
        for c in range(ch):
            x = signal.lfilter(b_hp, a_hp, samples[:, c])
            out[:, c] = x + 0.25 * signal.lfilter(b_bd, a_bd, x)

        peak = np.max(np.abs(out)) if out.size else 0.0
        limit = max_val * 0.95
        if peak > limit:
            out *= limit / peak
        dtype = {1: np.int8, 2: np.int16, 4: np.int32}[voice.sample_width]
        return voice._spawn(out.astype(dtype).tobytes())
