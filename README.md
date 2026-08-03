# Công cụ tạo video bài báo

Pipeline biến một bài báo tiếng Việt thành video dọc **1080 × 1920, 30 fps**: Python tải nội dung/ảnh, tạo kịch bản 150–220 từ, Edge TTS đọc từng cảnh và Remotion dựng video H.264 đồng bộ theo giọng đọc.

## Cài đặt

Yêu cầu Python 3.10+, Node.js 20+, `ffmpeg`, Chrome/Chromium và mạng.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm --prefix remotion install
```

## Sử dụng

`--url` bắt buộc. Giọng mặc định `vi-VN-HoaiMyNeural`; phong cách mặc định `news`.

```bash
./make_video.sh --url "https://vnexpress.net/duong-dan-bai-bao" --style nightfall --voice vi-VN-NamMinhNeural
```

Kết quả ở `output/video.mp4`, ảnh xem trước ở `output/preview.png`. Pipeline tự tạo các cảnh zoom/pan/crop khi chỉ có một ảnh, xen kẽ khi có hai ảnh và dùng thẻ tiêu đề mặc định khi bài không có ảnh.

| `--style` | Thiết kế |
|---|---|
| `news` | Bản tin nền trắng, điểm nhấn đỏ, ảnh Ken Burns và phụ đề rõ ràng. |
| `nightfall` | Nền tối điện ảnh, bảng kính mờ, chữ trắng. |
| `editorial` | Lưới timeline, số thứ tự lớn, khung thông tin cho bài nhiều mốc. |

Có thể chạy riêng: `python scripts/crawl.py --url ...`, `python scripts/generate_script.py`, `python scripts/tts.py --voice ...`.

## Cấu trúc

- `scripts/`: crawler, kịch bản và Edge TTS có retry.
- `remotion/src/`: composition, ba Scene component độc lập và phụ đề dùng chung.
- `assets/`: ảnh, metadata, âm thanh trung gian; `output/`: MP4 và preview.

> Kiểm tra quyền sử dụng nội dung và hình ảnh nguồn trước khi xuất bản.
