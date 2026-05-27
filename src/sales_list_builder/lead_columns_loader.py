import json
import sys
from pathlib import Path


def get_base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

    return Path(__file__).resolve().parent.parent.parent


LEAD_COLUMNS_PATH = (
    get_base_path()
    / "config"
    / "lead_columns.json"
)


def load_base_columns() -> list[str]:
    if not LEAD_COLUMNS_PATH.exists():
        raise FileNotFoundError(
            "lead_columns.json が見つかりません"
        )

    with LEAD_COLUMNS_PATH.open(
        "r",
        encoding="utf-8"
    ) as f:
        config = json.load(f)

    return config.get("base_columns", [])