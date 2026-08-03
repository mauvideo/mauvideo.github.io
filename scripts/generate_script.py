#!/usr/bin/env python3
"""Create a concise, deterministic narration from crawled article content."""
import argparse, json, re
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input",default="assets/article.json"); ap.add_argument("--output",default="assets/scenes.json"); a=ap.parse_args()
    article=json.loads(Path(a.input).read_text(encoding="utf-8")); raw=re.sub(r"\s+", " ", article["content"])
    sentences=[s.strip() for s in re.split(r"(?<=[.!?])\s+", raw) if len(s.split()) >= 6]
    selected=[]; count=0
    intro=f"Sau đây là những thông tin đáng chú ý về {article['title'].rstrip('.')} ."
    selected.append(intro); count=len(intro.split())
    for sentence in sentences:
        words=sentence.split()
        if count + len(words) > 215: words=words[:max(0, 215-count)]
        if words: selected.append(" ".join(words)); count += len(words)
        if count >= 175: break
    if count < 150: raise SystemExit(f"Lỗi: nội dung nguồn quá ngắn để tạo kịch bản 60–90 giây ({count} từ).")
    n=min(8, len(article["images"])); buckets=[[] for _ in range(n)]
    for i,s in enumerate(selected): buckets[min(n-1, i*n//len(selected))].append(s)
    scenes=[{"id":i+1,"text":" ".join(b),"image_path":article["images"][i]} for i,b in enumerate(buckets) if b]
    Path(a.output).write_text(json.dumps({"title":article["title"],"source":article["url"],"scenes":scenes},ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Đã tạo {len(scenes)} cảnh, {count} từ → {a.output}")
if __name__=="__main__": main()

