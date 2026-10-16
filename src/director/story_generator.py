import random
from typing import Dict, Any


class StoryGenerator:
    """Tùy chọn AI sinh truyện kinh dị từ ý tưởng ngắn."""

    HORROR_TEMPLATES = {
        "da_lat": {
            "title": "Bóng Trắng Biệt Thự Cổ Đà Lạt",
            "plot": [
                "Đêm Đà Lạt lạnh buốt, sương mù giăng kín các rặng thông quanh căn biệt thự hoang cổ kính.",
                "Tôi rón rén bước từng bước trên nền gỗ mục nát, xung quanh im lìm đến ghê người.",
                "Bỗng nhiên, từ trên tầng hai phát ra tiếng bước chân lê lết chậm rãi.",
                "Có ai đó đang thì thầm ngay bên tai trái tôi một lời van xin ai oán.",
                "Tôi run rẩy quay đầu lại phía sau lưng nhưng chẳng thấy ai, chỉ có một luồng gió lạnh thấu xương.",
                "Đột ngột, một bàn tay trắng bệch từ bóng tối vồ lấy vai tôi khiến tôi kinh hoàng hét lên!",
                "Và rồi, mọi thứ chìm vào im lặng vĩnh hằng giữa màn đêm sương phủ."
            ]
        },
        "lang_que": {
            "title": "Bóng Ma Bên Bờ Sông Vắng",
            "plot": [
                "Đêm rằm tháng bảy, gió rít từng cơn thổi qua mái nhà tranh xiêu vẹo ven sông.",
                "Dưới bến nước tối om, tiếng khóc nỉ non của người phụ nữ vang lên như vọng từ xa xăm.",
                "Người làng đồn rằng nơi này từng có một oan hồn ma nữ bị chôn vùi dưới đáy bùn lạnh ngắt.",
                "Tôi nhìn chăm chú xuống mặt nước đen ngòm, thấy một bóng đen đang từ từ nhô lên.",
                "Đột ngột, một tiếng cười the thé rợn tóc gáy xé toạc màn đêm tĩnh mịch!",
                "Tiếng bước chân ướt sũng dồn dập đuổi theo ngay sau lưng tôi."
            ]
        }
    }

    def generate_story(self, prompt: str, mood: str = "kinh_di_nang") -> str:
        """Sinh nội dung truyện hoàn chỉnh từ từ khóa."""
        prompt_lower = prompt.lower()
        if "đà lạt" in prompt_lower or "biệt thự" in prompt_lower:
            story = self.HORROR_TEMPLATES["da_lat"]["plot"]
        else:
            story = self.HORROR_TEMPLATES["lang_que"]["plot"]

        return "\n".join(story)
