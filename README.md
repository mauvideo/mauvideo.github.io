# Mẫu Video

Trang giới thiệu và tổng hợp các mẫu video, được triển khai trực tiếp bằng GitHub Pages.

## Xem trang trên máy cục bộ

Từ thư mục gốc của dự án, chạy một web server tĩnh:

```bash
python3 -m http.server 8000
```

Sau đó mở `http://localhost:8000` trong trình duyệt. Việc dùng web server thay vì mở
trực tiếp tệp HTML giúp các liên kết và tài nguyên hoạt động giống môi trường GitHub Pages hơn.

## Cấu trúc chính

- `index.html`: trang danh sách mẫu video.
- `chi-tiet.html`: trang hiển thị thông tin chi tiết.
- `products.js`: dữ liệu sản phẩm được sử dụng trên trang chi tiết.
