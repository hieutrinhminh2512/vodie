import os
from pathlib import Path
from typing import Any, Dict
import yaml

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
