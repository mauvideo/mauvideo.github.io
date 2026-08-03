#!/usr/bin/env python3
"""Download the useful text and photographs from a Vietnamese news article."""
import argparse, json, re, sys
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}

def clean(text): return re.sub(r"\s+", " ", text or "").strip()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--url", required=True); ap.add_argument("--output", default="assets/article.json")
    a = ap.parse_args(); out = Path(a.output); image_dir = out.parent / "images"; image_dir.mkdir(parents=True, exist_ok=True)
    for old in image_dir.glob("article-*.*"): old.unlink()
    response = requests.get(a.url, headers=HEADERS, timeout=30); response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = clean((soup.select_one("h1") or soup.select_one('meta[property="og:title"]')).get("content", "") if not soup.select_one("h1") else soup.select_one("h1").get_text())
    body = soup.select_one("article") or soup.select_one(".fck_detail") or soup.select_one(".article-content") or soup
    paragraphs = [clean(p.get_text(" ")) for p in body.select("p")]
    paragraphs = [p for p in paragraphs if len(p) > 45 and not p.lower().startswith(("ảnh:", "video:"))]
    date_el = soup.select_one("time, .date, .header-content .date")
    candidates = []
    for img in body.select("img"):
        src = img.get("data-src") or img.get("data-original") or img.get("src")
        srcset = img.get("srcset") or img.get("data-srcset")
        if srcset: src = srcset.split(",")[-1].strip().split()[0]
        if not src or src.startswith("data:"): continue
        w, h = int(img.get("width", 0) or 0), int(img.get("height", 0) or 0)
        if (w and w < 300) or (h and h < 200): continue
        src = urljoin(a.url, src)
        if src not in candidates: candidates.append(src)
    downloaded = []
    for src in candidates:
        if len(downloaded) >= 8: break
        try:
            r = requests.get(src, headers={**HEADERS, "Referer": a.url}, timeout=30); r.raise_for_status()
            if len(r.content) < 20_000: continue
            kind = "png" if "png" in r.headers.get("content-type", "") else "jpg"
            path = image_dir / f"article-{len(downloaded)+1:02}.{kind}"; path.write_bytes(r.content)
            downloaded.append(str(path))
        except requests.RequestException as exc: print(f"Bỏ qua ảnh {src}: {exc}", file=sys.stderr)
    # Images are optional: later stages reuse sparse images or make a title card.
    if not title or not paragraphs:
        raise SystemExit("Lỗi: không lấy được nội dung bài báo.")
    data = {"url": a.url, "title": title, "published_at": clean(date_el.get_text(" ")) if date_el else None,
            "content": "\n".join(paragraphs), "images": downloaded}
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã cào {len(paragraphs)} đoạn và {len(downloaded)} ảnh → {out}")
if __name__ == "__main__": main()
