from pydub import AudioSegment


class VocalMasteringChain:
    """
    Bộ Mastering âm sắc giọng kể chuyện ma chuyên nghiệp:
    Biến đổi giọng TTS thô ráp kỹ thuật số ("rất AI") thành chất giọng
    kể chuyện ma huyền thoại (phong cách Nguyễn Ngọc Ngạn / Quàng A Tũn):
    1. Analog Warmth EQ (Tăng độ dày dải trầm ấm 120Hz - 250Hz).
    2. De-harshing High-cut (Làm mềm các tần số kim loại sắc lạnh > 7000Hz).
    3. Dark Room Ambience (Không gian phòng thu u tịch, tiếng thở có độ ngân mờ).
    """

    @classmethod
    def apply_horror_mastering(cls, voice: AudioSegment) -> AudioSegment:
        # 1. Loại bỏ tiếng ồn kỹ thuật số tần số cực cao (> 7200Hz)
        mellowed = voice.low_pass_filter(7200)

        # 2. Tạo độ ấm (Vocal Body & Bass Boost)
        # Tách dải trầm dưới 350Hz để kích nhẹ âm lượng tạo độ dày
        bass_band = voice.low_pass_filter(350).apply_gain(2.8)

        # Trộn lại với track chính
        thickened = mellowed.overlay(bass_band)

        # 3. Tạo không gian phòng thu u tối (Dark Ambience / Subtle Plate)
        # Một lớp dội siêu mỏng (-16dB) trễ 45ms để giọng nói không bị khô khốc
        reflection = (thickened - 16).fade_in(20)
        silence_delay = AudioSegment.silent(duration=45)
        mastered = thickened.overlay(silence_delay + reflection)

        return mastered
