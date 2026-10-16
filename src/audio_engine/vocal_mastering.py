import numpy as np
import scipy.signal as signal
from pydub import AudioSegment


class VocalMasteringChain:
    """
    Bộ Mastering âm sắc giọng kể chuyện ma chuyên nghiệp:
    Biến đổi giọng TTS vô hồn, thô ráp kỹ thuật số ("rất AI") thành chất giọng
    kể chuyện ma huyền thoại của các nghệ sĩ gạo cội Việt Nam:
    1. Analog Warmth EQ (Tăng độ dày dải trầm ấm 130Hz - 220Hz đặc trưng giọng Paris By Night).
    2. De-essing & High-Cut (Khử âm xì chói tai, làm mịn dải cao > 6800Hz).
    3. Tape Saturation (Bão hòa băng cối analog làm ấm tiếng, xóa bỏ cảm giác tổng hợp máy tính).
    4. Proximity Room Ambience (Không gian buồng thu kín, tiếng thì thầm có chiều sâu rợn người).
    """

    @classmethod
    def apply_horror_mastering(
        cls,
        voice: AudioSegment,
        speaker_style: str = "nguyen_ngoc_ngan"
    ) -> AudioSegment:
        # Chuyển đổi sang mẫu dữ liệu numpy để xử lý DSP chính xác
        samples = np.array(voice.get_array_of_samples(), dtype=np.float32)
        sample_rate = voice.frame_rate
        channels = voice.channels
        nyquist = sample_rate / 2.0

        # Nếu là stereo thì làm phẳng tạm thời để lọc
        if channels == 2:
            left = samples[0::2]
            right = samples[1::2]
        else:
            left = samples
            right = samples

        # 1. Bộ lọc De-harshing (Low-pass lọc các tần số kim loại thô ráp trên 6800Hz)
        cutoff = min(6800.0, nyquist - 100)
        b_low, a_low = signal.butter(2, cutoff / nyquist, btype="low")
        left_filtered = signal.lfilter(b_low, a_low, left)
        right_filtered = signal.lfilter(b_low, a_low, right) if channels == 2 else left_filtered

        # 2. Chest Resonance Boost (Tăng độ trầm ấm ngực 120Hz - 240Hz)
        # Giọng Nguyễn Ngọc Ngạn nổi tiếng với âm sắc trầm ấm đầy ma mị
        b_band, a_band = signal.butter(2, [120.0 / nyquist, 260.0 / nyquist], btype="band")
        left_chest = signal.lfilter(b_band, a_band, left_filtered)
        right_chest = signal.lfilter(b_band, a_band, right_filtered)

        boost_gain = 1.35 if "ngan" in speaker_style else 1.2
        left_warmed = left_filtered + (left_chest * boost_gain)
        right_warmed = right_filtered + (right_chest * boost_gain)

        # 3. Tape Saturation (Mô phỏng bão hòa từ tính băng cối bằng hàm tanh phi tuyến)
        drive = 1.15
        left_sat = np.tanh(left_warmed * (drive / 32767.0)) * 32767.0
        right_sat = np.tanh(right_warmed * (drive / 32767.0)) * 32767.0

        # Chuẩn hóa tránh clipping
        peak = max(np.max(np.abs(left_sat)), np.max(np.abs(right_sat)), 1.0)
        if peak > 31500.0:
            scale = 31500.0 / peak
            left_sat *= scale
            right_sat *= scale

        if channels == 2:
            interleaved = np.empty((left_sat.size + right_sat.size,), dtype=np.int16)
            interleaved[0::2] = left_sat.astype(np.int16)
            interleaved[1::2] = right_sat.astype(np.int16)
            mastered_seg = AudioSegment(
                interleaved.tobytes(),
                frame_rate=sample_rate,
                sample_width=2,
                channels=2
            )
        else:
            mastered_seg = AudioSegment(
                left_sat.astype(np.int16).tobytes(),
                frame_rate=sample_rate,
                sample_width=2,
                channels=1
            )

        # 4. Proximity Room Ambience (Không gian dội phòng thu u tịch)
        reflection = (mastered_seg - 18).fade_in(25)
        silence_delay = AudioSegment.silent(duration=42)
        final_mastered = mastered_seg.overlay(silence_delay + reflection)

        return final_mastered
