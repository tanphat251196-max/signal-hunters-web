# Signal Hunters Web

Website tin tức crypto static cho Signal Hunters với giao diện dark theme cyberpunk, xây bằng HTML/CSS/JS thuần và tối ưu để deploy GitHub Pages.

## Cấu trúc

- `index.html` — trang chủ
- `css/style.css` — toàn bộ giao diện responsive, neon glow, card layout
- `js/main.js` — mobile menu và hiệu ứng tương tác nhẹ

## Tính năng chính

- Dark theme cyberpunk với accent neon cyan / magenta / electric purple
- Hero section có bài viết nổi bật
- Grid tin tức 3 cột desktop, 1 cột mobile
- Sidebar gồm giá BTC/ETH placeholder, trending, BingX banner, Telegram widget
- Footer đầy đủ link cộng đồng + BingX referral
- Tất cả nội dung tiếng Việt, dễ thay bằng dữ liệu tự động sau này

## Chạy local

Mở trực tiếp `index.html` hoặc dùng server tĩnh đơn giản:

```bash
cd /home/shinyyume/.openclaw/workspace/signal-hunters-web
python3 -m http.server 8080
```

Truy cập: `http://localhost:8080`

## Deploy GitHub Pages

```bash
cd /home/shinyyume/.openclaw/workspace/signal-hunters-web
git init
git add -A
git commit -m "Initial: Signal Hunters crypto news website"
gh repo create signal-hunters-web --public --source=. --push
```

Sau đó bật GitHub Pages (nếu cần):

```bash
gh api repos/tanphat251196-max/signal-hunters-web/pages \
  -X POST \
  -f "build_type=legacy" \
  -f "source[branch]=main" \
  -f "source[path]=/"
```

## Gợi ý mở rộng tiếp theo

- Thay placeholder giá bằng CoinGecko API hoặc widget realtime
- Tách dữ liệu bài viết ra file JSON
- Tạo thêm các trang con: phân tích, tin tức, altcoin, hàng hóa
- Tối ưu SEO bằng Open Graph image và schema chi tiết hơn
