import numpy as np
import scipy.signal as signal
from pydub import AudioSegment
import random


class BreathSynthesizer:
    """
    Bộ tổng hợp âm thanh lấy hơi / thở tự nhiên của con người (Physical Acoustic Breath Model).
    Giúp giọng đọc loại bỏ hoàn toàn cảm giác vô hồn cơ học của AI ("nghe phát biết AI"),
    tạo cảm giác người thật đang ngồi kề sát micro thì thầm và lấy hơi chân thực.
    """

    @classmethod
    def generate_breath(
        cls,
        breath_type: str = "inhale",
        duration_ms: int = 420,
        intensity: float = 0.07
    ) -> AudioSegment:
        """
        Tạo mẫu thở tự nhiên:
        - inhale: Lấy hơi khẽ trước khi bắt đầu câu chuyện hoặc vế câu dài.
        - gasp: Hít giật thót hoảng hốt ở những câu kinh dị, cao trào.
        - exhale / sigh: Thở dài não nề, u uất sau một trường đoạn căng thẳng.
        """
        sample_rate = 44100
        # Thêm một chút dao động ngẫu nhiên (human jitter) để mỗi tiếng thở đều độc bản
        actual_duration = duration_ms + random.randint(-40, 50)
        actual_duration = max(200, actual_duration)
        n_samples = int(sample_rate * (actual_duration / 1000.0))

        # 1. Tín hiệu nhiễu ngẫu nhiên mô phỏng luồng khí qua thanh quản
        noise = np.random.normal(0, 1, n_samples)

        # 2. Lọc dải tần số đặc trưng cho tiếng thở con người (Formants 550Hz - 2600Hz)
        nyquist = sample_rate / 2.0
        low = 550.0 / nyquist
        high = 2600.0 / nyquist
        b, a = signal.butter(3, [low, high], btype="band")
        filtered = signal.lfilter(b, a, noise)

        # 3. Đường bao biên độ thời gian (ADSR Envelope)
        t = np.linspace(0, 1, n_samples)
        if breath_type == "inhale":
            # Hít vào tự nhiên: tăng chậm rồi khép khẽ
            env = (t ** 1.9) * np.exp(-1.4 * (1 - t))
        elif breath_type == "gasp":
            # Hít mạnh hoảng hốt: tấn công cực nhanh rồi tan
            env = (t ** 0.6) * np.exp(-3.5 * t)
        else:  # exhale / sigh
            # Thở dài: mở nhẹ rồi trôi êm
            env = np.exp(-2.6 * t) * (1 - np.exp(-8 * t))

        env = env / (np.max(env) + 1e-6)
        breath_wave = filtered * env

        # 4. Chuẩn hóa và áp dụng âm lượng khẽ khàng (-24dB đến -28dBFS)
        breath_wave = breath_wave / (np.max(np.abs(breath_wave)) + 1e-6)
        pcm_data = (breath_wave * intensity * 32767).astype(np.int16)

        return AudioSegment(
            pcm_data.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )
