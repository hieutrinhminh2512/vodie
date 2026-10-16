import re
from typing import Dict
from ..config import PRONUNCIATION_DICT


class TextNormalizer:
    """
    Chuẩn hóa văn bản tiếng Việt dựa trên từ điển phát âm tùy chỉnh (YAML):
    Tên riêng, từ địa phương, thuật ngữ tiếng Anh, từ viết tắt.
    """

    def __init__(self, custom_dict: Dict = None):
        self.dict_data = custom_dict or PRONUNCIATION_DICT
        self.exact_replacements = self.dict_data.get("exact_replacements", {})
        self.acronyms = self.dict_data.get("acronyms", {})

    def normalize(self, text: str) -> str:
        """Thay thế các từ cần chuẩn hóa để TTS phát âm chuẩn nhất."""
        normalized = text

        # 1. Thay thế từ viết tắt
        for acronym, phoneme in self.acronyms.items():
            pattern = r'\b' + re.escape(acronym) + r'\b'
            normalized = re.sub(pattern, phoneme, normalized)

        # 2. Thay thế chính xác từ tiếng Anh, từ địa phương
        for phrase, phoneme in self.exact_replacements.items():
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            normalized = pattern.sub(phoneme, normalized)

        return normalized
