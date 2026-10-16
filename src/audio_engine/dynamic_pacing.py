from typing import Tuple


class DynamicPacingController:
    """
    Điều khiển nhịp độ tự co giãn (Dynamic Pacing):
    - Tốc độ đọc (speed rate) và khoảng dừng (pause duration)
      thay đổi linh hoạt theo mức độ căng thẳng (tension 0–10).
    """

    @staticmethod
    def calculate_rate_and_pause(
        tension: float,
        is_opening: bool = False,
        is_climax: bool = False,
        is_closing: bool = False
    ) -> Tuple[str, float]:
        """
        Tính toán chuỗi rate cho TTS ('+0%', '+15%', '-10%') và số giây pause.
        """
        if is_opening:
            # Mở truyện đọc chậm rãi, u ám
            rate = "-8%"
            pause = 1.2
        elif is_closing:
            # Câu chốt hạ đọc chậm, ngắt lâu ám ảnh
            rate = "-12%"
            pause = 2.5
        elif tension >= 8.0:
            # Cao trào dồn dập
            rate = "+18%"
            pause = 0.4
        elif tension >= 6.0:
            # Gay cấn tăng dần
            rate = "+10%"
            pause = 0.6
        elif tension >= 4.0:
            rate = "+0%"
            pause = 0.9
        else:
            # Nhẹ nhàng, rùng rợn âm ỉ
            rate = "-5%"
            pause = 1.1

        return rate, pause
