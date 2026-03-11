# Thiết kế Signal Hunters Web

## Mục tiêu
Tạo landing/news homepage static cho Signal Hunters theo phong cách dark theme cyberpunk, ưu tiên đọc tin nhanh, cảm giác premium và deploy trực tiếp lên GitHub Pages.

## Bố cục
- Header sticky với logo, navigation, CTA Telegram.
- Hero 2 cột: trái là copy định vị thương hiệu, phải là featured article lớn có ảnh và CTA BingX.
- Main content chia 2 phần:
  - Cột chính: grid bài viết 3 cột desktop, 1 cột mobile.
  - Sidebar desktop: widget BTC/ETH, trending, banner BingX, Telegram join box.
- Footer 3 cột: thương hiệu, liên kết cộng đồng, referral.

## Ngôn ngữ thiết kế
- Nền đen/xanh đậm, dùng glow cyan + magenta + purple.
- Card kính mờ (glassmorphism nhẹ), viền gradient để tạo cảm giác công nghệ.
- Typography Inter đậm cho headline, sáng rõ trên nền tối.
- Hover nâng card + neon shadow để tạo cảm giác sống động nhưng không lòe loẹt.

## Kỹ thuật
- Pure HTML/CSS/JS, không framework.
- Responsive mobile-first, nav collapse bằng JS nhẹ.
- Nội dung placeholder tiếng Việt, dễ tách dữ liệu thành JSON/API sau.
- Phù hợp GitHub Pages vì không có build step.
