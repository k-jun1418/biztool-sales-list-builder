import json
from pathlib import Path


CONFIG_PATH = Path("config.json")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError("config.json が見つかりません。")

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)