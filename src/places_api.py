import os
import time
import requests
from dotenv import load_dotenv
from contact_checker import find_contact_info
from app_logger import write_error_log

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
            error_message = f"Places API error: {response.status_code}\n{response.text}"
            write_error_log(error_message)
            raise RuntimeError(error_message)

        data = response.json()
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

    return remove_duplicates(all_places)


def normalize_place(place: dict) -> dict:
    display_name = place.get("displayName", {}).get("text", "")
    website_url = place.get("websiteUri", "")

    contact_url = ""
    has_form = False
    emails = []

    if website_url:
        contact_url, has_form, emails = find_contact_info(website_url)

    rating = place.get("rating", "")
    user_rating_count = place.get("userRatingCount", "")

    sales_score = calculate_sales_score(
        website_url=website_url,
        contact_url=contact_url,
        has_form=has_form,
        emails=emails,
        rating=rating,
        user_rating_count=user_rating_count,
    )

    return {
        "place_id": place.get("id", ""),
        "会社名": display_name,
        "住所": place.get("formattedAddress", ""),
        "電話番号": place.get("nationalPhoneNumber", ""),
        "ホームページ": website_url,
        "HP有無": "あり" if website_url else "なし",
        "問い合わせURL": contact_url,
        "問い合わせ有無": "あり" if contact_url else "なし",
        "フォーム有無": "あり" if has_form else "なし",
        "メールアドレス": ", ".join(emails),
        "メール有無": "あり" if emails else "なし",
        "営業スコア": sales_score,
        "Googleマップ": place.get("googleMapsUri", ""),
        "評価": rating,
        "口コミ数": user_rating_count,
        "業種タイプ": ",".join(place.get("types", [])),
    }

def calculate_sales_score(
    website_url: str,
    contact_url: str,
    has_form: bool,
    emails: list[str],
    rating,
    user_rating_count,
) -> int:
    score = 0

    # HPがある
    if website_url:
        score += 1

    # 問い合わせページがある
    if contact_url:
        score += 2

    # 問い合わせフォームがある
    if has_form:
        score += 3

    # メールアドレスがある
    if emails:
        score += 2

    # 口コミが少ない会社は営業余地ありと仮定
    try:
        review_count = int(user_rating_count) if user_rating_count != "" else 0
        if review_count <= 10:
            score += 1
    except (ValueError, TypeError):
        pass

    # 評価が低めなら改善提案余地ありと仮定
    try:
        rating_value = float(rating) if rating != "" else 0
        if 0 < rating_value < 3.5:
            score += 1
    except (ValueError, TypeError):
        pass

    return score


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