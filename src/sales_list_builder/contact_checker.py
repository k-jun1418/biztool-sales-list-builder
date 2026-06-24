import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from sales_list_builder.app_logger import write_error_log, write_info_log

import re


# 優先度1: 問い合わせページ系
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

# 優先度2: 会社概要・店舗概要系
ABOUT_KEYWORDS = [
    "会社概要",
    "会社案内",
    "会社情報",
    "企業情報",
    "事業概要",
    "事業所概要",
    "店舗概要",
    "店舗情報",
    "店舗案内",
    "当店について",
    "私たちについて",
    "about us",
    "about",
    "company",
    "profile",
    "shop",
    "access",
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

# 優先度2: 会社概要・店舗概要系のURLパターン
ABOUT_COMMON_PATHS = [
    "/company",
    "/company/",
    "/about",
    "/about/",
    "/about-us",
    "/about-us/",
    "/aboutus",
    "/aboutus/",
    "/profile",
    "/profile/",
    "/corporate",
    "/corporate/",
    "/shop",
    "/shop/",
    "/access",
    "/access/",
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

# 会社概要系キーワードのうち、href への部分一致で誤検出しやすい短い英単語
# （URLパラメータ等に偶然含まれるケースを避けるため、リンクテキスト側のみで判定する）
_ABOUT_HREF_EXCLUDED_KEYWORDS = {"about us", "about", "company", "profile", "shop", "access"}


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

    # ③ 優先度3: トップページからメール抽出
    emails = extract_emails_from_url(website_url)

    # ① 優先度1: トップページ内のリンクから問い合わせページを探す
    contact_url, has_form, contact_emails = find_contact_from_links(website_url)
    emails.extend(contact_emails)

    # ① 優先度1: リンクで見つからない場合はよくあるURLパターンを直接探す
    if not contact_url:
        contact_url, has_form, contact_emails = find_contact_from_common_paths(website_url)
        emails.extend(contact_emails)

    # ② 優先度2: 会社概要・店舗概要系ページからメールを追加探索
    # （問い合わせURLの判定には使わず、メールアドレスの取得漏れ対策として加える）
    about_emails = find_about_page_emails(website_url, exclude_url=contact_url)
    emails.extend(about_emails)

    return contact_url, has_form, unique_emails(emails)


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
    return _link_matches_keyword(a_tag, CONTACT_KEYWORDS, _HREF_EXCLUDED_KEYWORDS)


def _link_matches_about_keyword(a_tag) -> bool:
    return _link_matches_keyword(a_tag, ABOUT_KEYWORDS, _ABOUT_HREF_EXCLUDED_KEYWORDS)


def _link_matches_keyword(a_tag, keywords: list[str], href_excluded_keywords: set[str]) -> bool:
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

    for keyword in keywords:
        kw = keyword.lower()
        search_text = text_no_href if kw in href_excluded_keywords else text_with_href
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


def find_about_page_emails(website_url: str, exclude_url: str = "") -> list[str]:
    """会社概要・店舗概要系ページからメールアドレスを探す（優先度2）。

    問い合わせURL・フォーム有無の判定には影響させず、メールアドレスの
    取得漏れを減らすための追加探索として使う。
    """
    try:
        response = requests.get(website_url, timeout=10, headers=HEADERS)
        response.encoding = response.apparent_encoding

        if response.status_code >= 400:
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        about_url = ""
        for a_tag in soup.find_all("a", href=True):
            href_raw = a_tag["href"].strip()
            href_lower = href_raw.lower()

            if is_invalid_href(href_lower):
                continue

            if _link_matches_about_keyword(a_tag):
                about_url = urljoin(website_url, href_raw)
                break

        if not about_url:
            for path in ABOUT_COMMON_PATHS:
                candidate_url = urljoin(website_url, path)
                if page_exists(candidate_url):
                    about_url = candidate_url
                    break

        if not about_url or about_url == exclude_url:
            return []

        emails = extract_emails_from_url(about_url)
        if emails:
            write_info_log(f"[メール取得] 会社概要ページからメールを取得: {about_url}")
        return emails

    except requests.RequestException as e:
        write_error_log(f"find_about_page_emails error: {website_url} / {e}")
        return []


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

# Rule D: システム由来キーワード（ローカル部 or ドメイン部への部分一致）
_SYSTEM_KEYWORDS = {"sentry"}

# Rule E: システム由来ドメイン（完全一致またはサブドメイン）
_SYSTEM_DOMAINS = {"wixpress.com"}


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

    # Rule D: システム由来キーワード（ローカル部 or ドメイン部に部分一致）
    if any(kw in local or kw in domain for kw in _SYSTEM_KEYWORDS):
        return True

    # Rule E: システム由来ドメイン（完全一致またはサブドメイン）
    if domain in _SYSTEM_DOMAINS or any(domain.endswith("." + d) for d in _SYSTEM_DOMAINS):
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


