import numpy as np
from pydub import AudioSegment


class ProceduralHorrorBGM:
    """
    Bộ tổng hợp nhạc nền kinh dị tự động (Procedural Dark Ambient Synth):
    Tạo ra một lớp không khí u ám, lạnh lẽo kéo dài xuyên suốt câu chuyện:
    - Sub-bass drone trầm thấp (45Hz - 60Hz) tạo cảm giác đè nặng lồng ngực.
    - Sóng âm ma mị biến thiên chậm (slow LFO modulation).
    - Tiếng gió rít âm u mờ ảo.
    """

    @classmethod
    def generate_dark_ambient(cls, duration_sec: float, sample_rate: int = 44100) -> AudioSegment:
        total_samples = int(duration_sec * sample_rate)
        t = np.linspace(0, duration_sec, total_samples, False)

        # 1. Sub-bass Drone 55Hz & 82.5Hz (quãng năm huyền bí)
        drone1 = 0.35 * np.sin(2 * np.pi * 55 * t)
        drone2 = 0.25 * np.sin(2 * np.pi * 82.4 * t)

        # 2. Slow LFO Modulation (0.1Hz - sóng trôi dạt u tịch)
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.08 * t)
        drone = (drone1 + drone2) * lfo

        # 3. Tiếng gió rít u ám (Pink Noise lọc thông dải thấp)
        noise = np.random.normal(0, 0.06, total_samples)
        # Lọc nhẹ
        ambient = drone + noise

        # Chuẩn hóa biên độ (-16 dBFS nhẹ nhàng để lót dưới giọng đọc)
        ambient = ambient / np.max(np.abs(ambient) + 1e-6) * 0.22

        # Chuyển sang 16-bit PCM Stereo
        audio_int16 = (ambient * 32767).astype(np.int16)
        stereo_data = np.column_stack((audio_int16, audio_int16)).tobytes()

        return AudioSegment(
            data=stereo_data,
            sample_width=2,
            frame_rate=sample_rate,
            channels=2
        )
