import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from sales_list_builder.app_logger import write_error_log

import re


CONTACT_KEYWORDS = [
    "お問い合わせ",
    "お問合せ",
    "問い合わせ",
    "問合せ",
    "contact",
    "inquiry",
    "mail",
    "フォーム",
    "相談",
    "資料請求",
]


COMMON_PATHS = [
    "/contact",
    "/contact/",
    "/contact-us",
    "/contact-us/",
    "/contact-form",
    "/contact-form/",
    "/contacts",
    "/contacts/",
    "/inquiry",
    "/inquiry/",
    "/form",
    "/form/",
    "/form/contact",
    "/form/contact/",
    "/mail",
    "/mail/",
    "/toiawase",
    "/toiawase/",
    "/otoiawase",
    "/otoiawase/",
    "/contact_form",
    "/contact_form/",
    "/formmail",
    "/formmail/",
    "/support",
    "/support/",
    "/pages/contact",
    "/pages/contact/",
    "/request",
    "/request/",
    "/contact/index.html",
    "/inquiry/index.html",
]


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

_SOFT_404_STRINGS = [
    "404",
    "not found",
    "お探しのページが見つかりません",
    "ページが見つかりません",
    "このページは存在しません",
    "見つかりませんでした",
]

# href のみへの部分一致で誤検出しやすいキーワード
# これらはリンクテキスト・title・aria-label・img alt のみを検索対象にする
_HREF_EXCLUDED_KEYWORDS = {"mail"}


def find_contact_info(website_url: str) -> tuple[str, bool, list[str]]:
    """
    戻り値:
    (
        問い合わせURL,
        フォーム有無,
        メールアドレス一覧
    )
    """

    if not website_url:
        return "", False, []

    # ① トップページからメール抽出
    emails = extract_emails_from_url(website_url)

    # ② トップページ内のリンクから問い合わせページを探す
    contact_url, has_form, contact_emails = find_contact_from_links(website_url)
    emails.extend(contact_emails)

    if contact_url:
        return contact_url, has_form, unique_emails(emails)

    # ③ よくあるURLパターンを直接探す
    contact_url, has_form, contact_emails = find_contact_from_common_paths(website_url)
    emails.extend(contact_emails)

    if contact_url:
        return contact_url, has_form, unique_emails(emails)

    return "", False, unique_emails(emails)


def find_contact_from_links(website_url: str) -> tuple[str, bool, list[str]]:
    try:
        response = requests.get(
            website_url,
            timeout=10,
            headers=HEADERS,
        )

        response.encoding = response.apparent_encoding

        if response.status_code >= 400:
            return "", False, []

        soup = BeautifulSoup(response.text, "html.parser")

        for a_tag in soup.find_all("a", href=True):
            href_raw = a_tag["href"].strip()
            href_lower = href_raw.lower()

            if is_invalid_href(href_lower):
                continue

            if _link_matches_contact_keyword(a_tag):
                contact_url = urljoin(website_url, a_tag["href"])
                has_form = check_form_exists(contact_url)
                emails = extract_emails_from_url(contact_url)

                if has_form:
                    return contact_url, True, emails

                child_contact_url = find_child_contact_page(contact_url)
                if child_contact_url:
                    child_emails = extract_emails_from_url(child_contact_url)
                    emails.extend(child_emails)
                    return child_contact_url, True, unique_emails(emails)

                return contact_url, False, emails

        return "", False, []

    except requests.RequestException as e:
        write_error_log(f"find_contact_from_links error: {website_url} / {e}")
        return "", False, []

def is_invalid_href(href: str) -> bool:
    if not href:
        return True

    invalid_prefixes = [
        "javascript:",
        "#",
        "tel:",
        "mailto:",
    ]

    return any(href.startswith(prefix) for prefix in invalid_prefixes)

def _link_matches_contact_keyword(a_tag) -> bool:
    texts_no_href = [
        a_tag.get_text(strip=True),
        a_tag.get("title", ""),
        a_tag.get("aria-label", ""),
    ]
    img_tag = a_tag.find("img")
    if img_tag:
        texts_no_href.append(img_tag.get("alt", ""))
        texts_no_href.append(img_tag.get("title", ""))
    text_no_href = " ".join(texts_no_href).lower()
    text_with_href = f"{text_no_href} {a_tag.get('href', '').lower()}"

    for keyword in CONTACT_KEYWORDS:
        kw = keyword.lower()
        search_text = text_no_href if kw in _HREF_EXCLUDED_KEYWORDS else text_with_href
        if kw in search_text:
            return True
    return False

def find_child_contact_page(contact_url: str) -> str:
    try:
        response = requests.get(
            contact_url,
            timeout=10,
            headers=HEADERS,
            allow_redirects=True,
        )

        response.encoding = response.apparent_encoding

        if response.status_code >= 400:
            return ""

        soup = BeautifulSoup(response.text, "html.parser")

        for a_tag in soup.find_all("a", href=True):
            href_raw = a_tag["href"].strip()
            href_lower = href_raw.lower()
            href_lower = href_raw.lower()

            if is_invalid_href(href_lower):
                continue

            if _link_matches_contact_keyword(a_tag):
                child_url = urljoin(contact_url, href_raw)

                if check_form_exists(child_url):
                    return child_url

        return ""

    except requests.RequestException as e:
        write_error_log(f"find_contact_from_links error: {contact_url} / {e}")
        return ""

def find_contact_from_common_paths(website_url: str) -> tuple[str, bool, list[str]]:
    for path in COMMON_PATHS:
        candidate_url = urljoin(website_url, path)

        if page_exists(candidate_url):
            has_form = check_form_exists(candidate_url)
            emails = extract_emails_from_url(candidate_url)

            if has_form:
                return candidate_url, True, emails

            child_contact_url = find_child_contact_page(candidate_url)
            if child_contact_url:
                child_emails = extract_emails_from_url(child_contact_url)
                emails.extend(child_emails)
                return child_contact_url, True, unique_emails(emails)

            return candidate_url, False, emails

    return "", False, []


def page_exists(url: str) -> bool:
    try:
        response = requests.get(
            url,
            timeout=10,
            headers=HEADERS,
            allow_redirects=True,
        )

        response.encoding = response.apparent_encoding

        if response.status_code >= 400:
            return False

        # 404ページなのに200を返すサイト対策
        text = response.text.lower()
        if any(s in text[:1000] for s in _SOFT_404_STRINGS):
            return False

        return True

    except requests.RequestException as e:
        write_error_log(f"find_contact_from_links error: {url} / {e}")
        return False


def check_form_exists(url: str) -> bool:
    try:
        response = requests.get(
            url,
            timeout=10,
            headers=HEADERS,
        )

        response.encoding = response.apparent_encoding

        if response.status_code >= 400:
            return False

        soup = BeautifulSoup(response.text, "html.parser")

        return soup.find("form") is not None

    except requests.RequestException as e:
        write_error_log(f"find_contact_from_links error: {url} / {e}")
        return False

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}"
)
MAILTO_REGEX = re.compile(
    r"mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})",
    re.IGNORECASE,
)

# Rule A: ダミードメイン完全一致リスト
_DUMMY_DOMAINS = {
    "example.com", "example.jp", "example.net", "example.org",
    "test.com", "test.jp", "test.net",
    "localhost", "localhost.com",
    "domain.com", "yourdomain.com",
    "sample.com", "sample.jp",
    "dummy.com", "dummy.jp",
    "xxx.com", "xxx.xxx",
    "hogehoge.com",
}

# Rule C: フェイクローカル部完全一致リスト
_FAKE_LOCAL_PARTS = {
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "hogehoge", "hoge",
    "xxx", "yyy", "zzz",
}


def _is_dummy_email(email: str) -> bool:
    if "@" not in email:
        return True
    local, domain = email.lower().rsplit("@", 1)

    # Rule A: ダミードメイン完全一致
    if domain in _DUMMY_DOMAINS:
        return True

    # Rule B: 対称パターン（ローカル部 == ドメイン第1ラベル）
    if local == domain.split(".")[0]:
        return True

    # Rule C: フェイクローカル部完全一致
    if local in _FAKE_LOCAL_PARTS:
        return True

    return False


def extract_emails_from_html(html: str) -> list[str]:
    emails = set()

    # 通常テキスト内のメール
    for email in EMAIL_REGEX.findall(html):
        emails.add(email)

    for email in MAILTO_REGEX.findall(html):
        emails.add(email)

    filtered = []
    for email in emails:
        if ".." in email.lower():
            continue
        if _is_dummy_email(email):
            continue
        filtered.append(email)

    return sorted(filtered)

def extract_emails_from_url(url: str) -> list[str]:
    try:
        response = requests.get(
            url,
            timeout=10,
            headers=HEADERS,
            allow_redirects=True,
        )

        if response.status_code >= 400:
            return []

        return extract_emails_from_html(response.text)

    except requests.RequestException as e:
        write_error_log(f"find_contact_from_links error: {url} / {e}")
        return []


def unique_emails(emails: list[str]) -> list[str]:
    return sorted(set(email.strip() for email in emails if email.strip()))


