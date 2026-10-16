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

# Setup output folders
OUTPUT_DIR = BASE_DIR / SETTINGS.get("storage", {}).get("output_dir", "output")
TEMP_DIR = BASE_DIR / SETTINGS.get("storage", {}).get("temp_dir", "temp")
DATA_DIR = BASE_DIR / "data"

for directory in [OUTPUT_DIR, TEMP_DIR, DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
