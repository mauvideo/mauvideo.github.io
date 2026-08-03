#!/usr/bin/env python3
"""Create a concise, deterministic narration from crawled article content."""
import argparse, html, json, math, re
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input",default="assets/article.json"); ap.add_argument("--output",default="assets/scenes.json"); a=ap.parse_args()
    article=json.loads(Path(a.input).read_text(encoding="utf-8")); raw=re.sub(r"\s+", " ", article.get("content", "")).strip()
    if not article.get("title") or not raw:
        raise SystemExit("Lỗi: không lấy được nội dung bài báo.")
    sentences=[s.strip() for s in re.split(r"(?<=[.!?])\s+", raw) if len(s.split()) >= 6]
    selected=[]; count=0
    intro=f"Sau đây là những thông tin đáng chú ý về {article['title'].rstrip('.')} ."
    selected.append(intro); count=len(intro.split())
    for sentence in sentences:
        words=sentence.split()
        if count + len(words) > 215: words=words[:max(0, 215-count)]
        if words: selected.append(" ".join(words)); count += len(words)
        if count >= 175: break
    if count < 150: raise SystemExit(f"Lỗi: không lấy được đủ nội dung bài báo để tạo kịch bản 60–90 giây ({count} từ).")
    # Scene count follows narration length, not the number of downloaded photos.
    n=max(3, min(8, math.ceil(count/30)))
    narration=" ".join(selected).split()
    buckets=[narration[i*len(narration)//n:(i+1)*len(narration)//n] for i in range(n)]
    images=article.get("images") or []
    if not images:
        fallback=Path(a.output).parent/"images"/"default-background.svg"
        fallback.parent.mkdir(parents=True,exist_ok=True)
        title=html.escape(article["title"])
        fallback.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="#172554"/><stop offset="1" stop-color="#991b1b"/></linearGradient></defs><rect width="1080" height="1080" fill="url(#g)"/><circle cx="900" cy="180" r="260" fill="#fff" opacity=".08"/><circle cx="130" cy="950" r="350" fill="#fff" opacity=".06"/><text x="90" y="470" fill="white" font-family="Arial,sans-serif" font-size="38" font-weight="700">TIN NỔI BẬT</text><foreignObject x="90" y="520" width="900" height="400"><div xmlns="http://www.w3.org/1999/xhtml" style="color:white;font:700 64px/1.15 Arial,sans-serif">{title}</div></foreignObject></svg>''',encoding="utf-8")
        images=[str(fallback)]
    scenes=[{"id":i+1,"text":" ".join(b),"image_path":images[i%len(images)],"visual_variant":i%6} for i,b in enumerate(buckets)]
    Path(a.output).write_text(json.dumps({"title":article["title"],"source":article["url"],"scenes":scenes},ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Đã tạo {len(scenes)} cảnh, {count} từ → {a.output}")
if __name__=="__main__": main()
