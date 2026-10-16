import numpy as np
from pydub import AudioSegment


class SpatialAudioEngine:
    """
    Xử lý âm thanh vòm / không gian (Binaural / Stereo Panning):
    Mô phỏng vị trí không gian 3D (trái, phải, sau lưng, lướt từ trái sang phải)
    thông qua độ chênh lệch âm lượng giữa 2 tai (ILD) và độ trễ thời gian (ITD).
    """

    @staticmethod
    def apply_panning(sound: AudioSegment, position: str = "center") -> AudioSegment:
        """
        Gán vị trí không gian cho đoạn âm thanh:
        position: 'center', 'left', 'right', 'rear', 'left_to_right', 'right_to_left'
        """
        if sound.channels == 1:
            sound = sound.set_channels(2)

        if position == "center":
            return sound

        elif position == "left":
            # Tai trái rõ hơn tai phải (-6dB ở tai phải)
            left = sound.split_to_mono()[0]
            right = sound.split_to_mono()[1] - 8
            return AudioSegment.from_mono_audiosegments(left, right)

        elif position == "right":
            # Tai phải rõ hơn tai trái
            left = sound.split_to_mono()[0] - 8
            right = sound.split_to_mono()[1]
            return AudioSegment.from_mono_audiosegments(left, right)

        elif position == "rear":
            # Âm thanh sau lưng: giảm treble (lowpass filter nhẹ) và đảo pha nhẹ để tạo cảm giác phía sau
            muffled = sound.low_pass_filter(3500)
            left = muffled.split_to_mono()[0] - 2
            right = muffled.split_to_mono()[1] - 2
            return AudioSegment.from_mono_audiosegments(left, right)

        elif position == "left_to_right":
            # Tiếng thì thầm lướt từ tai trái sang tai phải
            left = sound.split_to_mono()[0]
            right = sound.split_to_mono()[1]
            # Fade out bên trái và Fade in bên phải
            left = left.fade(to_gain=-18, start=0, end=len(left))
            right = right.fade(from_gain=-18, start=0, end=len(right))
            return AudioSegment.from_mono_audiosegments(left, right)

        elif position == "right_to_left":
            # Tiếng lướt từ tai phải sang tai trái
            left = sound.split_to_mono()[0]
            right = sound.split_to_mono()[1]
            left = left.fade(from_gain=-18, start=0, end=len(left))
            right = right.fade(to_gain=-18, start=0, end=len(right))
            return AudioSegment.from_mono_audiosegments(left, right)

        return sound
