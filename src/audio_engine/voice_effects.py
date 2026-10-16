from pydub import AudioSegment
from ..config import VOICE_PRESETS


class VoiceEffectsProcessor:
    """
    Bộ hiệu ứng âm thanh DSP giả lập giọng ma mị:
    - ma_nu: thì thầm, vang (reverb), pitch the thé
    - quy_du: trầm sâu, méo tiếng ghê rợn (distortion)
    - vong_hon: vọng từ xa (echo xa, lowpass)
    """

    @classmethod
    def apply_preset(cls, sound: AudioSegment, preset_name: str) -> AudioSegment:
        if preset_name not in VOICE_PRESETS:
            return sound

        cfg = VOICE_PRESETS[preset_name]
        processed = sound

        # 1. Pitch Shift giả lập (thay đổi sample rate và speed)
        pitch_semitones = cfg.get("pitch_semitones", 0.0)
        if pitch_semitones != 0.0:
            octaves = pitch_semitones / 12.0
            new_sample_rate = int(processed.frame_rate * (2.0 ** octaves))
            processed = processed._spawn(processed.raw_data, overrides={
                "frame_rate": new_sample_rate
            }).set_frame_rate(44100)

        # 2. Lowpass / Highpass Filter
        lowpass = cfg.get("lowpass_cutoff_hz")
        if lowpass:
            processed = processed.low_pass_filter(int(lowpass))

        highpass = cfg.get("highpass_cutoff_hz")
        if highpass:
            processed = processed.high_pass_filter(int(highpass))

        # 3. Echo / Reverb giả lập
        echo_cfg = cfg.get("echo")
        if echo_cfg:
            delay_ms = echo_cfg.get("delay_ms", 250)
            decay = echo_cfg.get("decay", 0.4)
            echo_track = (processed - 6).fade_in(50)
            silence_delay = AudioSegment.silent(duration=delay_ms)
            processed = processed.overlay(silence_delay + (echo_track * decay))

        # 4. Whisper / Reverb Mix
        reverb_cfg = cfg.get("reverb")
        if reverb_cfg:
            # Tạo hiệu ứng vang mờ bằng 2 lớp delay nhẹ
            wet1 = (processed - 7)
            wet2 = (processed - 12)
            d1 = AudioSegment.silent(duration=70)
            d2 = AudioSegment.silent(duration=140)
            processed = processed.overlay(d1 + wet1).overlay(d2 + wet2)

        return processed
