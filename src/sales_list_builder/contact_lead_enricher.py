from sales_list_builder.contact_checker import find_contact_info
from sales_list_builder.score_loader import load_score_config


score_config = load_score_config()


def enrich_leads(rows: list[dict]) -> list[dict]:
    enriched_rows = []

    for row in rows:
        try:
            enriched_row = row.copy()

            website_url = enriched_row.get("ホームページ", "")

            contact_url = ""
            has_form = False
            emails = []

            if website_url and score_config.get("enable_contact_check", True):
                contact_url, has_form, emails = find_contact_info(website_url)

            if not score_config.get("enable_email_extract", True):
                emails = []

            if score_config.get("enable_score", True):
                sales_score = calculate_sales_score(
                    website_url=website_url,
                    contact_url=contact_url,
                    has_form=has_form,
                    emails=emails,
                )
            else:
                sales_score = ""

            enriched_row["HP有無"] = "あり" if website_url else "なし"
            enriched_row["問い合わせURL"] = contact_url
            enriched_row["問い合わせ有無"] = "あり" if contact_url else "なし"
            enriched_row["フォーム有無"] = "あり" if has_form else "なし"
            enriched_row["メールアドレス"] = ", ".join(emails)
            enriched_row["メール有無"] = "あり" if emails else "なし"
            enriched_row["営業スコア"] = sales_score

            enriched_rows.append(enriched_row)

        except Exception:
            enriched_rows.append(row.copy())

    enriched_rows.sort(
        key=lambda x: x.get("営業スコア", 0),
        reverse=True,
    )

    return enriched_rows


def calculate_sales_score(
    website_url: str,
    contact_url: str,
    has_form: bool,
    emails: list[str],
) -> int:
    score = 0

    if website_url:
        score += score_config.get("website_score", 1)

    if contact_url:
        score += score_config.get("contact_url_score", 2)

    if has_form:
        score += score_config.get("form_score", 3)

    if emails:
        score += score_config.get("email_score", 2)

    return score