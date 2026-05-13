from pathlib import Path
from datetime import datetime
import pandas as pd


def export_csv(rows: list[dict], area: str, business_type: str) -> str:
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sales_list_{area}_{business_type}_{timestamp}.csv"
    filepath = output_dir / sanitize_filename(filename)

    df = pd.DataFrame(rows)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")

    return str(filepath)


def sanitize_filename(filename: str) -> str:
    invalid_chars = '\\/:*?"<>|'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename