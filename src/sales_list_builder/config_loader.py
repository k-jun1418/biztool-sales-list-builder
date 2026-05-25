import json
import sys
from pathlib import Path


def get_base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

    return Path(__file__).resolve().parent.parent.parent


CONFIG_PATH = get_base_path() / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError("config.json が見つかりません。")

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)