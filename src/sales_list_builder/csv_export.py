from pathlib import Path
from datetime import datetime
import pandas as pd


def export_csv(rows: list[dict], area: str, business_type: str) -> str:
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for row in rows:
        row["検索地域"] = area
        row["検索業種"] = business_type
        row["取得日時"] = fetched_at

    df = pd.DataFrame(rows)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sales_list_{area}_{business_type}_{timestamp}.csv"
    filepath = output_dir / sanitize_filename(filename)

    df.to_csv(filepath, index=False, encoding="utf-8-sig")

    return str(filepath)


def sanitize_filename(filename: str) -> str:
    invalid_chars = '\\/:*?"<>|'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename