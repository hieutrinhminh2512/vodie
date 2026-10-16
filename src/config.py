import sys
import os
import shutil
from pathlib import Path
from typing import Any, Dict
import yaml

# 1. Đảm bảo UTF-8 cho Windows console
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 2. Tự động phát hiện FFmpeg trên Windows và gắn vào PATH trước khi load bất kỳ thư viện âm thanh nào
if not shutil.which("ffmpeg"):
    potential_dirs = [
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\ffmpeg\bin"),
        r"C:\Program Files\ffmpeg\bin",
    ]
    for p in potential_dirs:
        if os.path.exists(p):
            os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
            break

# 2b. Không có FFmpeg trong máy -> dùng bản FFmpeg đóng gói sẵn của imageio-ffmpeg (pip)
if not shutil.which("ffmpeg"):
    try:
        import imageio_ffmpeg

        _ff = Path(imageio_ffmpeg.get_ffmpeg_exe())
        _alias_dir = Path(__file__).resolve().parent.parent / "cache" / "ffmpeg_bin"
        _alias_dir.mkdir(parents=True, exist_ok=True)
        _alias = _alias_dir / ("ffmpeg.exe" if sys.platform.startswith("win") else "ffmpeg")
        if not _alias.exists():
            shutil.copyfile(_ff, _alias)
            _alias.chmod(0o755)
        os.environ["PATH"] = str(_alias_dir) + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass

# 3. Import pydub an toàn
try:
    from pydub import AudioSegment
    ffmpeg_exe = shutil.which("ffmpeg")
    if ffmpeg_exe:
        AudioSegment.converter = ffmpeg_exe
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"


def _load_dotenv(path: Path) -> None:
    """Nạp file .env (KEY=VALUE) vào biến môi trường, không ghi đè biến đã có."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        if value:
            os.environ.setdefault(key.strip(), value)


_load_dotenv(BASE_DIR / ".env")


def load_yaml(file_name: str) -> Dict[str, Any]:
    file_path = CONFIG_DIR / file_name
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# Load configurations
SETTINGS = load_yaml("settings.yaml")
VOICE_PRESETS = load_yaml("voice_presets.yaml").get("presets", {})
PRONUNCIATION_DICT = load_yaml("pronunciation_dict.yaml")
MOODS = load_yaml("moods.yaml").get("moods", {})
VOICES_CONFIG = load_yaml("voices.yaml")

# Setup output folders
OUTPUT_DIR = BASE_DIR / SETTINGS.get("storage", {}).get("output_dir", "output")
TEMP_DIR = BASE_DIR / SETTINGS.get("storage", {}).get("temp_dir", "temp")
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
CACHE_DIR = BASE_DIR / SETTINGS.get("storage", {}).get("cache_dir", "cache")
VOICES_DIR = BASE_DIR / "voices"

for directory in [OUTPUT_DIR, TEMP_DIR, DATA_DIR, ASSETS_DIR, CACHE_DIR, VOICES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
