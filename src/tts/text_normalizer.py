"""Chuẩn hóa văn bản tiếng Việt thành dạng "đọc được" trước khi đưa vào TTS.

TTS đọc sai chủ yếu vì văn bản gốc có số, ngày giờ, đơn vị, viết tắt, teencode...
Module này đổi tất cả về chữ, theo đúng cách người Việt đọc, có phân biệt giọng
Bắc (nghìn, linh) và giọng Nam (ngàn, lẻ).
"""
import re
from typing import Dict, Optional

from ..config import PRONUNCIATION_DICT

DIGITS = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

# Viết tắt hay gặp trong truyện ma trên mạng / báo chí. Khóa phân biệt hoa thường.
DEFAULT_ABBREVIATIONS: Dict[str, str] = {
    "TP.HCM": "thành phố Hồ Chí Minh",
    "TP HCM": "thành phố Hồ Chí Minh",
    "TPHCM": "thành phố Hồ Chí Minh",
    "HCM": "Hồ Chí Minh",
    "TP.": "thành phố",
    "UBND": "ủy ban nhân dân",
    "HĐND": "hội đồng nhân dân",
    "THPT": "trung học phổ thông",
    "THCS": "trung học cơ sở",
    "ĐH": "đại học",
    "BV": "bệnh viện",
    "CSGT": "cảnh sát giao thông",
    "VN": "Việt Nam",
    "HN": "Hà Nội",
    "SG": "Sài Gòn",
    "QL": "quốc lộ",
    "ÔNG.": "ông",
}

# Teencode / viết tắt kiểu chat. Chỉ thay khi đứng riêng thành một từ.
DEFAULT_TEENCODE: Dict[str, str] = {
    "ko": "không", "k": "không", "kh": "không", "hok": "không", "khum": "không",
    "đc": "được", "dc": "được", "dk": "được", "vs": "với", "ng": "người",
    "j": "gì", "bít": "biết", "bik": "biết",
    "mn": "mọi người", "mk": "mình", "trc": "trước", "tr": "trời", "lm": "làm",
    "ntn": "như thế nào", "bn": "bao nhiêu", "nma": "nhưng mà", "nhg": "nhưng",
    "cx": "cũng", "ck": "chồng", "vk": "vợ",
}

UNITS: Dict[str, str] = {
    "km/h": "ki lô mét trên giờ",
    "km": "ki lô mét", "cm": "xen ti mét", "mm": "mi li mét", "m": "mét",
    "kg": "ki lô gam", "gr": "gam", "ha": "héc ta", "l": "lít", "ml": "mi li lít",
    "°C": "độ xê", "độ C": "độ xê", "°": "độ",
}

ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
ROMAN_CONTEXT = r"(thế kỷ|thế kỉ|chương|phần|hồi|tập|quyển|khóa|đời|vua)"


def _roman_to_int(s: str) -> Optional[int]:
    total, prev = 0, 0
    for ch in reversed(s.upper()):
        val = ROMAN.get(ch)
        if val is None:
            return None
        total = total - val if val < prev else total + val
        prev = max(prev, val)
    return total if 0 < total < 4000 else None


class TextNormalizer:
    """Chuẩn hóa tiếng Việt: số, ngày, giờ, đơn vị, tiền, viết tắt, từ điển phát âm."""

    def __init__(self, custom_dict: Optional[Dict] = None, dialect: str = "bac"):
        self.dict_data = custom_dict or PRONUNCIATION_DICT
        self.exact_replacements: Dict[str, str] = self.dict_data.get("exact_replacements", {}) or {}
        self.acronyms: Dict[str, str] = self.dict_data.get("acronyms", {}) or {}
        self.abbreviations = {**DEFAULT_ABBREVIATIONS, **(self.dict_data.get("abbreviations", {}) or {})}
        self.teencode = {**DEFAULT_TEENCODE, **(self.dict_data.get("teencode", {}) or {})}
        self.dialect = dialect  # "bac" | "trung" | "nam"

    # ------------------------------------------------------------------ số
    @property
    def _thousand(self) -> str:
        return "ngàn" if self.dialect == "nam" else "nghìn"

    @property
    def _odd(self) -> str:
        return "lẻ" if self.dialect == "nam" else "linh"

    def _read_triple(self, n: int, full: bool) -> str:
        """Đọc số 0-999. full=True khi phía trước còn nhóm khác (phải đọc 'không trăm')."""
        hundreds, rest = divmod(n, 100)
        tens, units = divmod(rest, 10)
        words = []
        if hundreds or full:
            words += [DIGITS[hundreds], "trăm"]
        if tens == 0:
            if units and (hundreds or full):
                words.append(self._odd)
            if units:
                words.append(DIGITS[units])
        elif tens == 1:
            words.append("mười")
            if units == 5:
                words.append("lăm")
            elif units:
                words.append(DIGITS[units])
        else:
            words += [DIGITS[tens], "mươi"]
            if units == 1:
                words.append("mốt")
            elif units == 4:
                words.append("tư")
            elif units == 5:
                words.append("lăm")
            elif units:
                words.append(DIGITS[units])
        return " ".join(words)

    def number_to_words(self, n: int) -> str:
        if n == 0:
            return "không"
        if n < 0:
            return "âm " + self.number_to_words(-n)
        if n >= 10**18:
            return " ".join(DIGITS[int(d)] for d in str(n))
        scales = ["", self._thousand, "triệu", "tỷ", self._thousand + " tỷ", "triệu tỷ"]
        groups = []
        while n:
            n, g = divmod(n, 1000)
            groups.append(g)
        words = []
        for idx in range(len(groups) - 1, -1, -1):
            g = groups[idx]
            if g == 0:
                continue
            words.append(self._read_triple(g, full=idx < len(groups) - 1))
            if scales[idx]:
                words.append(scales[idx])
        return " ".join(words)

    def _digits_each(self, s: str) -> str:
        return " ".join(DIGITS[int(c)] for c in s if c.isdigit())

    def _parse_number(self, raw: str) -> str:
        """'1.000.000' -> một triệu; '3,5' -> ba phẩy năm; '0912345678' -> đọc từng số."""
        if re.fullmatch(r"0\d{8,}", raw):
            return self._digits_each(raw)
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", raw):
            return self.number_to_words(int(raw.replace(".", "")))
        m = re.fullmatch(r"(\d+)[,.](\d+)", raw)
        if m:
            int_part, frac = m.groups()
            frac_words = self.number_to_words(int(frac)) if len(frac) <= 2 and not frac.startswith("0") \
                else self._digits_each(frac)
            return f"{self.number_to_words(int(int_part))} phẩy {frac_words}"
        if raw.isdigit():
            if len(raw) > 1 and raw.startswith("0"):
                return self._digits_each(raw)
            return self.number_to_words(int(raw))
        return raw

    def _month(self, m: int) -> str:
        return "tư" if m == 4 else self.number_to_words(m)

    # ------------------------------------------------------------- các bước
    def _expand_dates_times(self, t: str) -> str:
        def date_full(m: re.Match) -> str:
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if not (1 <= d <= 31 and 1 <= mo <= 12):
                return m.group(0)
            return f"{self.number_to_words(d)} tháng {self._month(mo)} năm {self.number_to_words(y)}"

        t = re.sub(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})\b", date_full, t)

        def date_short(m: re.Match) -> str:
            d, mo = int(m.group(2)), int(m.group(3))
            if not (1 <= d <= 31 and 1 <= mo <= 12):
                return m.group(0)
            return f"{m.group(1)}{self.number_to_words(d)} tháng {self._month(mo)}"

        t = re.sub(r"\b(ngày |đêm |rằm |mùng |mồng )?(\d{1,2})/(\d{1,2})\b", date_short, t, flags=re.I)

        def month_year(m: re.Match) -> str:
            mo, y = int(m.group(1)), int(m.group(2))
            if not 1 <= mo <= 12:
                return m.group(0)
            return f"tháng {self._month(mo)} năm {self.number_to_words(y)}"

        t = re.sub(r"\btháng (\d{1,2})[/\-](\d{4})\b", month_year, t, flags=re.I)
        t = re.sub(r"\b(tháng) (\d{1,2})\b",
                   lambda m: f"{m.group(1)} {self._month(int(m.group(2)))}" if 1 <= int(m.group(2)) <= 12
                   else m.group(0), t, flags=re.I)

        def clock(m: re.Match) -> str:
            h, mi = int(m.group(1)), m.group(2)
            if h > 24:
                return m.group(0)
            out = f"{self.number_to_words(h)} giờ"
            if mi and int(mi):
                out += f" {self.number_to_words(int(mi))} phút"
            return out

        t = re.sub(r"\b(\d{1,2})[:hg](\d{2})(?:p|ph|')?\b", clock, t)
        t = re.sub(r"\b(\d{1,2})[hg]\b", clock, t)
        return t

    def _expand_ordinals(self, t: str) -> str:
        def ordinal(m: re.Match) -> str:
            n = int(m.group(2))
            word = {1: "nhất", 4: "tư"}.get(n, self.number_to_words(n))
            return f"{m.group(1)} {word}"

        return re.sub(r"\b(thứ|Thứ) (\d{1,2})\b", ordinal, t)

    def _expand_roman(self, t: str) -> str:
        def roman(m: re.Match) -> str:
            val = _roman_to_int(m.group(2))
            return f"{m.group(1)} {self.number_to_words(val)}" if val else m.group(0)

        return re.sub(ROMAN_CONTEXT + r"\s+([IVXLCDM]+)\b", roman, t, flags=re.I)

    def _expand_money_units_percent(self, t: str) -> str:
        num = r"(\d+(?:[.,]\d+)*)"
        t = re.sub(num + r"\s?%", lambda m: f"{self._parse_number(m.group(1))} phần trăm", t)
        t = re.sub(num + r"\s?(k|K|nghìn|ngàn)\b(?!m)",
                   lambda m: f"{self._parse_number(m.group(1))} {self._thousand}", t)
        t = re.sub(num + r"\s?(tr|triệu)\b", lambda m: f"{self._parse_number(m.group(1))} triệu", t)
        t = re.sub(num + r"\s?(đ|₫|VNĐ|VND|đồng)(?=\W|$)", lambda m: f"{self._parse_number(m.group(1))} đồng", t)
        t = re.sub(r"\$\s?" + num, lambda m: f"{self._parse_number(m.group(1))} đô la", t)
        t = re.sub(num + r"\s?(USD|usd|\$)", lambda m: f"{self._parse_number(m.group(1))} đô la", t)
        for unit in sorted(UNITS, key=len, reverse=True):
            t = re.sub(num + r"\s?" + re.escape(unit) + r"(?![\wÀ-ỹ])",
                       lambda m, u=unit: f"{self._parse_number(m.group(1))} {UNITS[u]}", t)
        return t

    def _expand_ranges(self, t: str) -> str:
        return re.sub(r"\b(\d+)\s?[-–]\s?(\d+)\b",
                      lambda m: f"{self._parse_number(m.group(1))} đến {self._parse_number(m.group(2))}", t)

    def _expand_numbers(self, t: str) -> str:
        return re.sub(r"\d+(?:[.,]\d+)*", lambda m: self._parse_number(m.group(0)), t)

    def _replace_words(self, t: str, table: Dict[str, str], ignore_case: bool) -> str:
        flags = re.I if ignore_case else 0
        for src in sorted(table, key=len, reverse=True):
            pattern = r"(?<![\wÀ-ỹ])" + re.escape(src) + r"(?![\wÀ-ỹ])"
            t = re.sub(pattern, table[src], t, flags=flags)
        return t

    def _clean_punctuation(self, t: str) -> str:
        t = t.replace("…", "...")
        t = re.sub(r"\.{4,}", "...", t)
        t = re.sub(r"([!?])\1+", r"\1", t)
        # Dấu thoại không đọc thành tiếng: bỏ gạch đầu dòng, ngoặc kép; gạch giữa câu -> ngắt phẩy
        t = re.sub(r"^\s*[-–—]+\s*", "", t)
        t = re.sub(r"\s+[-–—]+\s+", ", ", t)
        t = re.sub(r"[\"“”«»„]", "", t)
        t = re.sub(r"[‘’]", "'", t)
        t = re.sub(r"[*#_~^|<>]", " ", t)
        t = re.sub(r"\s+([,.!?;:])", r"\1", t)
        return re.sub(r"\s{2,}", " ", t).strip()

    def normalize(self, text: str) -> str:
        """Chạy toàn bộ chuỗi chuẩn hóa. An toàn khi gọi nhiều lần."""
        t = self._clean_punctuation(text)
        t = self._replace_words(t, self.abbreviations, ignore_case=False)
        t = self._replace_words(t, self.acronyms, ignore_case=False)
        t = self._replace_words(t, self.exact_replacements, ignore_case=True)
        t = self._expand_roman(t)
        t = self._expand_dates_times(t)
        t = self._expand_ordinals(t)
        t = self._expand_money_units_percent(t)
        t = self._expand_ranges(t)
        t = self._expand_numbers(t)
        t = self._replace_words(t, self.teencode, ignore_case=True)
        return re.sub(r"\s{2,}", " ", t).strip()
