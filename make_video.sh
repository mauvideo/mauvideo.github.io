#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"; cd "$ROOT"
URL=""; VOICE="vi-VN-NamMinhNeural"; STYLE="news"
while (($#)); do case "$1" in --url) URL="${2:-}"; shift 2;; --voice) VOICE="${2:-}"; shift 2;; --style) STYLE="${2:-}"; shift 2;; *) echo "Tham số không hợp lệ: $1" >&2; exit 2;; esac; done
[[ -n "$URL" ]] || { echo "Cách dùng: $0 --url <URL> [--style news|nightfall|editorial] [--voice VOICE]" >&2; exit 2; }
[[ "$STYLE" =~ ^(news|nightfall|editorial)$ ]] || { echo "--style phải là news, nightfall hoặc editorial" >&2; exit 2; }
command -v ffmpeg >/dev/null || { echo "Thiếu ffmpeg trong PATH" >&2; exit 1; }
mkdir -p assets/images assets/audio output
python3 scripts/crawl.py --url "$URL"; python3 scripts/generate_script.py; python3 scripts/tts.py --voice "$VOICE"
python3 - "$STYLE" <<'PY'
import json,sys
p=json.load(open('assets/scenes.json')); p['style']=sys.argv[1]
json.dump(p,open('assets/render-props.json','w'),ensure_ascii=False)
PY
rm -rf remotion/public/assets; mkdir -p remotion/public/assets
cp -R assets/images assets/audio remotion/public/assets/
[[ -d remotion/node_modules ]] || npm --prefix remotion install
BROWSER_ARGS=(); BROWSER="$(command -v google-chrome || command -v chromium || true)"
[[ -z "$BROWSER" ]] || BROWSER_ARGS=(--browser-executable="$BROWSER")
npx --prefix remotion remotion render remotion/src/index.ts ArticleVideo output/video.mp4 --props=assets/render-props.json --public-dir=remotion/public --codec=h264 "${BROWSER_ARGS[@]}"
ffmpeg -y -ss 00:00:05 -i output/video.mp4 -frames:v 1 output/preview.png
echo "Hoàn tất: output/video.mp4 (phong cách $STYLE, giọng $VOICE)"
