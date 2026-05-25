from pathlib import Path
from datetime import datetime
import pandas as pd


CORE_COLUMNS = [
    "place_id",
    "会社名",
    "住所",
    "電話番号",
    "ホームページ",
    "業種タイプ",
]


def export_csv(
    rows: list[dict],
    area: str,
    business_type: str,
    column_order: list[str] | None = None,
) -> str:
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cleaned_rows = []

    for row in rows:
        cleaned_row = row.copy()

        cleaned_row["検索地域"] = area
        cleaned_row["検索業種"] = business_type
        cleaned_row["取得日時"] = fetched_at

        cleaned_rows.append(normalize_row(cleaned_row))

    df = pd.DataFrame(cleaned_rows)

    df = apply_column_order(
        df,
        column_order=column_order,
    )
    df = df.fillna("")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sales_list_{area}_{business_type}_{timestamp}.csv"
    filepath = output_dir / sanitize_filename(filename)

    df.to_csv(filepath, index=False, encoding="utf-8-sig")

    return str(filepath)


def normalize_row(row: dict) -> dict:
    normalized = {}

    for key, value in row.items():
        if value is None:
            value = ""

        value = str(value).strip()

        if key in ["ホームページ", "問い合わせURL"]:
            value = normalize_url(value)

        normalized[key] = value

    return normalized


def normalize_url(url: str) -> str:
    if not url:
        return ""

    return url.strip()


def apply_column_order(
    df: pd.DataFrame,
    column_order: list[str] | None = None,
) -> pd.DataFrame:

    if not column_order:
        return df

    existing_columns = [
        column for column in column_order
        if column in df.columns
    ]

    extra_columns = [
        column for column in df.columns
        if column not in existing_columns
    ]

    return df[existing_columns + extra_columns]


def sanitize_filename(filename: str) -> str:
    invalid_chars = '\\/:*?"<>|'

    for char in invalid_chars:
        filename = filename.replace(char, "_")

    return filename