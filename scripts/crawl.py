#!/usr/bin/env python3
"""Download useful text and photographs from a Vietnamese news article."""

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
import trafilatura
from bs4 import BeautifulSoup

TIMEOUT = 30
MAX_ATTEMPTS = 3
CONTENT_SELECTORS = (
    "article",
    ".fck_detail",
    ".Normal",
    ".detail-content",
    ".article-content",
    ".content-detail",
)
NOISE_PATTERN = re.compile(
    r"menu|nav|advert|ads?|quảng[ -]?cáo|related|liên[ -]?quan|footer|social|share|"
    r"recommend|suggest|breadcrumb|comment|script|style",
    re.IGNORECASE,
)


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def browser_headers(url):
    parsed = urlparse(url)
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": f"{parsed.scheme}://{parsed.netloc}/",
    }


def download_html(url):
    session = requests.Session()
    session.headers.update(browser_headers(url))
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
            print(f"HTTP status: {response.status_code} (lần {attempt}/{MAX_ATTEMPTS})")
            print(f"URL sau redirect: {response.url}")
            response.raise_for_status()
            if response.text.strip():
                return response.text, response.url, session
            last_error = RuntimeError("máy chủ trả về nội dung rỗng")
        except requests.RequestException as exc:
            last_error = exc
            print(f"Tải trang thất bại lần {attempt}: {exc}", file=sys.stderr)
        if attempt < MAX_ATTEMPTS:
            time.sleep(attempt * 2)
    raise RuntimeError(f"Không tải được bài báo sau {MAX_ATTEMPTS} lần: {last_error}")


def is_noise(element):
    for parent in [element, *element.parents]:
        if getattr(parent, "name", None) in {"nav", "footer", "script", "style", "aside"}:
            return True
        attrs = " ".join(
            [str(parent.get("id", "")), " ".join(parent.get("class", []))]
        ) if hasattr(parent, "get") else ""
        if NOISE_PATTERN.search(attrs):
            return True
    return False


def reasonable_paragraphs(elements):
    result = []
    for element in elements:
        text = clean(element.get_text(" "))
        if 45 <= len(text) <= 5000 and not is_noise(element):
            if not text.lower().startswith(("ảnh:", "video:", "xem thêm:", "tin liên quan")):
                if text not in result:
                    result.append(text)
    return result


def title_from_soup(soup):
    heading = soup.select_one("h1")
    if heading and clean(heading.get_text(" ")):
        return clean(heading.get_text(" "))
    meta = soup.select_one('meta[property="og:title"], meta[name="twitter:title"]')
    return clean(meta.get("content")) if meta else ""


def extract_beautifulsoup(html):
    soup = BeautifulSoup(html, "html.parser")
    title = title_from_soup(soup)
    for selector in CONTENT_SELECTORS:
        bodies = soup.select(selector)
        paragraphs = reasonable_paragraphs(p for body in bodies for p in body.select("p"))
        if title and paragraphs:
            return title, paragraphs, soup
    # Generic fallback: only useful paragraphs, excluding common page chrome/noise.
    paragraphs = reasonable_paragraphs(soup.select("p"))
    return title, paragraphs, soup


def extract_trafilatura(html):
    result = trafilatura.bare_extraction(
        html, include_comments=False, include_tables=False, favor_precision=True
    )
    if not result:
        return "", []
    data = result.as_dict() if hasattr(result, "as_dict") else result
    text = data.get("text", "")
    paragraphs = [clean(p) for p in text.splitlines() if len(clean(p)) >= 45]
    return clean(data.get("title", "")), paragraphs


def walk_jsonld(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_jsonld(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_jsonld(child)


def extract_jsonld(soup):
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            payload = json.loads(tag.string or tag.get_text())
        except (json.JSONDecodeError, TypeError):
            continue
        for item in walk_jsonld(payload):
            body = clean(item.get("articleBody", ""))
            title = clean(item.get("headline", "") or item.get("name", ""))
            if title and len(body) >= 45:
                paragraphs = [clean(p) for p in re.split(r"\n+", body) if len(clean(p)) >= 45]
                return title, paragraphs or [body]
    return "", []


def extract_meta(soup):
    title = title_from_soup(soup)
    meta = soup.select_one(
        'meta[property="og:description"], meta[name="description"], '
        'meta[name="twitter:description"]'
    )
    description = clean(meta.get("content")) if meta else ""
    return title, [description] if len(description) >= 45 else []


def extract_playwright(url):
    """Render JavaScript as the final fallback, using the workflow's Chromium."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        print(f"Không thể dùng Playwright: {exc}", file=sys.stderr)
        return "", url
    try:
        with sync_playwright() as playwright:
            chromium = shutil.which("chromium-browser") or shutil.which("chromium")
            browser = playwright.chromium.launch(headless=True, executable_path=chromium)
            page = browser.new_page(extra_http_headers=browser_headers(url))
            response = page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT * 1000)
            print(f"HTTP status (Playwright): {response.status if response else 'không rõ'}")
            page.wait_for_timeout(2000)
            html, final_url = page.content(), page.url
            print(f"URL sau redirect (Playwright): {final_url}")
            browser.close()
            return html, final_url
    except Exception as exc:  # Playwright has several runtime-specific error classes.
        print(f"Playwright thất bại: {exc}", file=sys.stderr)
        return "", url


def extract_article(html, url):
    soup = BeautifulSoup(html, "html.parser")
    methods = [
        ("requests + BeautifulSoup", lambda: extract_beautifulsoup(html)[:2]),
        ("trafilatura", lambda: extract_trafilatura(html)),
        ("JSON-LD", lambda: extract_jsonld(soup)),
        ("meta og:title/description", lambda: extract_meta(soup)),
    ]
    for method, extractor in methods:
        title, paragraphs = extractor()
        if title and paragraphs:
            return title, paragraphs, soup, method, url

    rendered_html, final_url = extract_playwright(url)
    if rendered_html:
        rendered_soup = BeautifulSoup(rendered_html, "html.parser")
        for method, extractor in (
            ("Playwright + BeautifulSoup", lambda: extract_beautifulsoup(rendered_html)[:2]),
            ("Playwright + JSON-LD", lambda: extract_jsonld(rendered_soup)),
            ("Playwright + meta", lambda: extract_meta(rendered_soup)),
        ):
            title, paragraphs = extractor()
            if title and paragraphs:
                return title, paragraphs, rendered_soup, method, final_url
    return "", [], soup, "không có", url


def download_images(soup, article_url, image_dir, session):
    body = next((soup.select_one(selector) for selector in CONTENT_SELECTORS if soup.select_one(selector)), soup)
    candidates = []
    for img in body.select("img"):
        src = img.get("data-src") or img.get("data-original") or img.get("src")
        srcset = img.get("srcset") or img.get("data-srcset")
        if srcset:
            src = srcset.split(",")[-1].strip().split()[0]
        if not src or src.startswith("data:"):
            continue
        try:
            width, height = int(img.get("width", 0) or 0), int(img.get("height", 0) or 0)
        except ValueError:
            width = height = 0
        if (width and width < 300) or (height and height < 200):
            continue
        src = urljoin(article_url, src)
        if src not in candidates:
            candidates.append(src)

    downloaded = []
    for src in candidates:
        if len(downloaded) >= 8:
            break
        try:
            response = session.get(src, headers={"Referer": article_url}, timeout=TIMEOUT)
            response.raise_for_status()
            if len(response.content) < 20_000:
                continue
            kind = "png" if "png" in response.headers.get("content-type", "") else "jpg"
            path = image_dir / f"article-{len(downloaded) + 1:02}.{kind}"
            path.write_bytes(response.content)
            downloaded.append(str(path))
        except requests.RequestException as exc:
            print(f"Bỏ qua ảnh {src}: {exc}", file=sys.stderr)
    return downloaded


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", default="assets/article.json")
    args = parser.parse_args()
    if urlparse(args.url).scheme not in {"http", "https"}:
        raise SystemExit("Lỗi: URL bài báo phải dùng http hoặc https.")

    output = Path(args.output)
    image_dir = output.parent / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    for old in image_dir.glob("article-*.*"):
        old.unlink()

    try:
        html, final_url, session = download_html(args.url)
        title, paragraphs, soup, method, final_url = extract_article(html, final_url)
    except RuntimeError as exc:
        raise SystemExit(f"Lỗi: {exc}") from exc

    print(f"Tiêu đề: {title or '(không tìm thấy)'}")
    print(f"Số đoạn văn: {len(paragraphs)}")
    print(f"Số ký tự nội dung: {len(chr(10).join(paragraphs))}")
    print(f"Phương pháp thành công: {method}")
    if not title or not paragraphs:
        raise SystemExit("Lỗi: không lấy được nội dung bài báo; không ghi nội dung rỗng.")

    images = download_images(soup, final_url, image_dir, session)
    date_el = soup.select_one("time, .date, .header-content .date")
    data = {
        "url": final_url,
        "title": title,
        "published_at": clean(date_el.get_text(" ")) if date_el else None,
        "content": "\n".join(paragraphs),
        "images": images,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã cào {len(paragraphs)} đoạn và {len(images)} ảnh → {output}")


if __name__ == "__main__":
    main()
