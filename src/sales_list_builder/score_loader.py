import json
import sys
from pathlib import Path


def get_base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

    return Path(__file__).resolve().parent.parent.parent


SCORE_CONFIG_PATH = (
    get_base_path()
    / "config"
    / "score_config.json"
)


def load_score_config() -> dict:
    if not SCORE_CONFIG_PATH.exists():
        raise FileNotFoundError(
            "score_config.json が見つかりません"
        )

    with SCORE_CONFIG_PATH.open(
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)