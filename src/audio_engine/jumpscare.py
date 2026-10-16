from pydub import AudioSegment
from ..config import SETTINGS


class JumpScareController:
    """
    Điều khiển Jump scare an toàn:
    1. Tạo khoảng lặng nín thở 1–2 giây trước khi kích hoạt âm thanh bất ngờ.
    2. Giới hạn âm lượng True Peak tối đa -1 dBTP chống sốc âm thính giác.
    3. Hỗ trợ Chế độ dịu tai (Gentle Ear Mode) giảm biên độ cho người nhạy cảm.
    """

    def __init__(self, gentle_mode: bool = False, peak_limit_db: float = -1.0):
        audio_cfg = SETTINGS.get("audio", {})
        self.gentle_mode = gentle_mode or audio_cfg.get("gentle_ear_mode", False)
        self.peak_limit_db = peak_limit_db or audio_cfg.get("true_peak_limit_dbtp", -1.0)
        self.silence_duration_ms = int(audio_cfg.get("silence_before_jumpscare_sec", 1.5) * 1000)

    def create_jumpscare_segment(
        self,
        sfx_sound: AudioSegment,
        custom_silence_ms: int = None
    ) -> AudioSegment:
        """
        Tạo phân đoạn Jump scare hoàn chỉnh:
        [Khoảng lặng 1-2s] + [SFX bất ngờ đã được kiểm soát True Peak]
        """
        silence_len = custom_silence_ms or self.silence_duration_ms
        silence = AudioSegment.silent(duration=silence_len)

        # 1. Đo mức đỉnh max dBFS hiện tại của SFX
        current_peak = sfx_sound.max_dBFS

        # 2. Giới hạn True Peak (Peak Limiter)
        target_peak = self.peak_limit_db
        if self.gentle_mode:
            target_peak -= 4.0  # Giảm thêm 4dB cho chế độ dịu tai

        gain_adjustment = target_peak - current_peak
        if gain_adjustment < 0:
            # Nếu âm thanh quá lớn, hạ xuống ngưỡng an toàn
            safe_sfx = sfx_sound.apply_gain(gain_adjustment)
        else:
            safe_sfx = sfx_sound

        return silence + safe_sfx
