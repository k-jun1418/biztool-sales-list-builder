import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.googleMapsUri",
    "places.types",
    "places.rating",
    "places.userRatingCount",
    "nextPageToken",
])


def search_places(area: str, business_type: str, max_pages: int = 1) -> list[dict]:
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY が .env に設定されていません。")

    query = f"{area} {business_type}"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
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

        response = requests.post(
            TEXT_SEARCH_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Places API error: {response.status_code}\n{response.text}"
            )

        data = response.json()
        places = data.get("places", [])

        for place in places:
            all_places.append(normalize_place(place))

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return remove_duplicates(all_places)


def normalize_place(place: dict) -> dict:
    display_name = place.get("displayName", {}).get("text", "")

    return {
        "place_id": place.get("id", ""),
        "会社名": display_name,
        "住所": place.get("formattedAddress", ""),
        "電話番号": place.get("nationalPhoneNumber", ""),
        "ホームページ": place.get("websiteUri", ""),
        "Googleマップ": place.get("googleMapsUri", ""),
        "評価": place.get("rating", ""),
        "口コミ数": place.get("userRatingCount", ""),
        "業種タイプ": ",".join(place.get("types", [])),
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