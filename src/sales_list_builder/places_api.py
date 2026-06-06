import json
import time
from datetime import datetime
from pathlib import Path

import requests

from sales_list_builder.app_logger import write_error_log
from sales_list_builder.config_loader import load_config


TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

config = load_config()

FIELD_MASK = ",".join(config.get("field_mask", []))
REQUEST_TIMEOUT = config.get("request_timeout", 30)
RETRY_COUNT = config.get("request_retry_count", 3)
RETRY_WAIT_SECONDS = config.get("request_retry_wait_seconds", 2)
SAVE_RAW_RESPONSE = config.get("save_raw_response", False)
OUTPUT_FIELDS = config.get("output_fields", {})


def build_query(area: str, business_type: str) -> str:
    return f"{area} {business_type}".strip()


def post_with_retry(url: str, headers: dict, payload: dict) -> requests.Response:
    last_error = None

    for _ in range(RETRY_COUNT):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 429:
                last_error = RuntimeError(
                    "Google APIの利用上限、または一時的な制限に達しました。"
                )
                time.sleep(RETRY_WAIT_SECONDS)
                continue

            if response.status_code in [500, 502, 503, 504]:
                last_error = RuntimeError(
                    f"Google APIの一時エラーです: {response.status_code}"
                )
                time.sleep(RETRY_WAIT_SECONDS)
                continue

            return response

        except requests.RequestException as e:
            last_error = e
            time.sleep(RETRY_WAIT_SECONDS)

    raise RuntimeError(
        "Google Places APIへの接続に失敗しました。"
        f"時間をおいて再試行してください。詳細: {last_error}"
    )


def search_places(
    area: str,
    business_type: str,
    api_key: str,
    max_pages: int = 1,
) -> dict:
    if not api_key:
        raise ValueError("Google APIキーが設定されていません。")

    query = build_query(area, business_type)

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    payload = {
        "textQuery": query,
        "languageCode": "ja",
        "regionCode": "JP",
        "pageSize": 20,
    }

    all_places = []
    page_token = None

    for page in range(max_pages):
        if page_token:
            payload["pageToken"] = page_token
            time.sleep(2)

        response = post_with_retry(
            TEXT_SEARCH_URL,
            headers,
            payload,
        )

        if response.status_code == 403:
            raise PermissionError("Google APIキーが無効です。")

        if response.status_code != 200:
            error_message = (
                f"Places API error: {response.status_code}\n"
                f"{response.text}"
            )
            write_error_log(error_message)
            raise RuntimeError(error_message)

        data = response.json()

        save_raw_response(
            data=data,
            area=area,
            business_type=business_type,
            page=page,
        )

        places = data.get("places", [])

        for place in places:
            try:
                all_places.append(normalize_place(place))
            except Exception as e:
                place_name = place.get("displayName", {}).get("text", "不明")
                write_error_log(f"normalize_place error: {place_name} / {e}")
                continue

        page_token = data.get("nextPageToken")

        if not page_token:
            break

    rows = remove_duplicates(all_places)

    return {
        "rows": rows,
        "total_count": len(rows),
    }


def normalize_place(place: dict) -> dict:
    display_name = place.get("displayName", {}).get("text", "")
    website_url = place.get("websiteUri", "")

    row = {
        "place_id": place.get("id", ""),
        "会社名": display_name,
        "住所": place.get("formattedAddress", ""),
        "電話番号": place.get("nationalPhoneNumber", ""),
        "ホームページ": website_url,
        "業種タイプ": ",".join(place.get("types", [])),
        "評価": place.get("rating", ""),
        "口コミ数": place.get("userRatingCount", ""),
    }

    return filter_output_fields(row)


def filter_output_fields(row: dict) -> dict:
    if not OUTPUT_FIELDS:
        return row

    return {
        key: value
        for key, value in row.items()
        if OUTPUT_FIELDS.get(key, False)
    }


def remove_duplicates(rows: list[dict]) -> list[dict]:
    seen = set()
    unique_rows = []

    for row in rows:
        key = row.get("place_id") or f"{row.get('会社名')}|{row.get('住所')}"

        if key in seen:
            continue

        seen.add(key)
        unique_rows.append(row)

    return unique_rows


def save_raw_response(
    data: dict,
    area: str,
    business_type: str,
    page: int,
):
    if not SAVE_RAW_RESPONSE:
        return

    raw_dir = Path("raw")
    raw_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = (
        f"places_raw_{area}_{business_type}_"
        f"page{page + 1}_{timestamp}.json"
    )
    filepath = raw_dir / sanitize_filename(filename)

    with filepath.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def sanitize_filename(filename: str) -> str:
    invalid_chars = '\\/:*?"<>|'

    for char in invalid_chars:
        filename = filename.replace(char, "_")

    return filename