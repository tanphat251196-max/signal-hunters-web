#!/usr/bin/env python3
"""Create a hang-hoa post about gold price for today."""
import json
import re
import unicodedata
import requests
from pathlib import Path
from datetime import datetime

REPO_DIR = Path("/home/shinyyume/.openclaw/workspace/signal-hunters-web")
POSTS_FILE = REPO_DIR / "data" / "posts.json"
CONFIG_FILE = Path("/home/shinyyume/.openclaw/openclaw.json")

BINGX_CTA_HTML = """<div class="cta-box" style="background:#1a1a2e;border:1px solid #16213e;border-radius:12px;padding:20px;margin-top:30px;">
<h3>💰 Tiết kiệm phí giao dịch crypto?</h3>
<p>Đăng ký BingX qua link dưới đây để được <strong>hoàn phí 45% VĨNH VIỄN</strong>:</p>
<p><a href="https://bingx.com/vi-vn/partner/X7EZVIWI" target="_blank" rel="noopener">👉 Đăng ký BingX ngay (Code: X7EZVIWI)</a></p>
</div>"""


def slugify(text):
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.replace("đ", "d").replace("Đ", "D")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80]


def main():
    source_title = "Giá vàng hôm nay 1/4/2026: Đồng loạt tăng rất mạnh"
    source_url = "https://kinhtechungkhoan.vn/gia-vang-hom-nay-1-4-2026-dong-loat-tang-rat-manh-1437510.html"
    source_name = "Kinh tế Chứng khoán"
    source_content = """Khảo sát sáng sớm ngày 1/4/2026, giá vàng trong nước ghi nhận mức tăng rất mạnh ở các mặt hàng.

Đối với vàng miếng SJC, các thương hiệu DOJI, PNJ, Bảo Tín Minh Châu tăng 1,1 triệu đồng/lượng ở cả hai chiều so với phiên hôm qua, giao dịch ở mức 171,9 - 174,9 triệu đồng/lượng (mua vào - bán ra). Vàng miếng Phú Quý tăng 2,2 triệu đồng/lượng, giao dịch ở mức 173 - 176 triệu đồng/lượng.

Giá vàng thế giới sáng sớm ngày 1/4/2026 (giờ Việt Nam), thị trường vàng thế giới ghi nhận nhịp phục hồi mạnh mẽ khi giá vàng giao ngay tăng lên quanh 4.620 USD/ounce, tương đương mức tăng hơn 2,4% trong phiên gần nhất.

Theo dữ liệu từ Kitco, diễn biến trên biểu đồ ngày cho thấy vàng đang bật tăng trở lại sau khi kiểm định thành công vùng đáy ngắn hạn quanh 4.200-4.300 USD/ounce. Cây nến tăng mạnh đi kèm khối lượng giao dịch cải thiện phản ánh lực cầu quay trở lại rõ rệt, đặc biệt sau giai đoạn bán tháo trước đó.

Vùng 4.600-4.650 USD/ounce đang đóng vai trò là ngưỡng kháng cự gần. Nếu vượt qua, vàng có thể mở rộng đà tăng lên các mốc cao hơn quanh 4.800 USD/ounce, xa hơn là vùng tâm lý 5.000 USD/ounce. Vùng 4.400 USD/ounce hiện trở thành hỗ trợ quan trọng trong ngắn hạn.

Ông Marc Chandler, Giám đốc tại Bannockburn Global Forex, nhận định việc vàng duy trì trên đường trung bình động 200 ngày quanh 4.092 USD/ounce là tín hiệu kỹ thuật tích cực."""

    cfg = json.load(open(CONFIG_FILE))
    api_key = cfg["models"]["providers"]["google"]["apiKey"]

    prompt = (
        "Viết lại bài báo sau thành bài viết chuyên nghiệp bằng tiếng Việt, dài 1000-1500 từ, về thị trường hàng hóa và vàng.\n\n"
        "YÊU CẦU:\n"
        "- Viết lại hoàn toàn bằng ngôn ngữ của mình\n"
        "- Tiêu đề hấp dẫn, đầy đủ về giá vàng ngày 1/4/2026\n"
        "- Mở bài thu hút\n"
        "- Thân bài chia thành 3-4 heading (dùng thẻ h2), phân tích kỹ\n"
        "- Đưa số liệu cụ thể: giá SJC, vàng nhẫn, giá thế giới\n"
        "- Phân tích kỹ thuật: ngưỡng hỗ trợ, kháng cự\n"
        "- Kết bài có nhận định cho nhà đầu tư\n"
        "- Giọng văn: chuyên nghiệp, phong cách nhà phân tích hàng hóa\n\n"
        "THÔNG TIN GỐC:\n"
        f"Tiêu đề: {source_title}\n"
        f"Nguồn: {source_name} - {source_url}\n"
        f"Nội dung gốc:\n{source_content}\n\n"
        'TRA VE JSON (chi JSON, khong markdown):\n'
        '{"title": "tieu de moi day du", "summary": "tom tat 2-3 cau", "content": "noi dung HTML day du (dung h2, p, strong, ul, li)"}'
    )

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
    }

    print("Calling Gemini for hang-hoa article...")
    resp = requests.post(api_url, json=payload, timeout=90)
    print(f"Status: {resp.status_code}")

    new_title = source_title
    new_summary = "Giá vàng trong nước và thế giới đồng loạt tăng mạnh ngày 1/4/2026."
    new_content = ""

    if resp.status_code == 200:
        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Strip code fences
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
        raw_text = re.sub(r"\s*```$", "", raw_text, flags=re.MULTILINE)
        raw_text = raw_text.strip()

        try:
            result = json.loads(raw_text)
            new_title = result.get("title", source_title).strip()
            new_summary = result.get("summary", new_summary).strip()
            new_content = result.get("content", "").strip()
        except json.JSONDecodeError:
            print("JSON parse failed, using regex extraction")
            title_m = re.search(r'"title"\s*:\s*"([^"]+)"', raw_text)
            summary_m = re.search(r'"summary"\s*:\s*"([^"]+)"', raw_text)
            if title_m:
                new_title = title_m.group(1).strip()
            if summary_m:
                new_summary = summary_m.group(1).strip()
            # Extract HTML content
            html_m = re.search(r"(<(?:h2|h3|p|ul|div)[^>]*>.*)", raw_text, re.DOTALL)
            if html_m:
                new_content = html_m.group(1)
                new_content = re.sub(r'"\s*\}\s*$', "", new_content).strip()

        word_count = len(re.sub(r"<[^>]+>", "", new_content).split())
        heading_count = len(re.findall(r"<h[23][^>]*>", new_content))
        print(f"Generated: {word_count} words, {heading_count} headings")
        print(f"Title: {new_title}")
    else:
        print(f"Gemini error: {resp.text[:300]}")

    # Fallback content if generation failed
    if not new_content or len(new_content) < 200:
        print("Using fallback content")
        new_content = f"""<p>Thị trường vàng ngày 1/4/2026 ghi nhận diễn biến tích cực với đồng loạt tăng mạnh ở cả vàng trong nước lẫn thế giới.</p>
<h2>Giá Vàng Trong Nước Tăng Mạnh</h2>
<p>Khảo sát sáng sớm ngày 1/4/2026, giá vàng miếng SJC tại các thương hiệu DOJI, PNJ, Bảo Tín Minh Châu tăng 1,1 triệu đồng/lượng ở cả hai chiều so với phiên hôm qua, giao dịch ở mức <strong>171,9 - 174,9 triệu đồng/lượng</strong> (mua vào - bán ra).</p>
<p>Vàng miếng thương hiệu Phú Quý ghi nhận mức tăng mạnh hơn với 2,2 triệu đồng/lượng ở cả hai chiều, giao dịch ở mức 173 - 176 triệu đồng/lượng. Ở phân khúc vàng nhẫn, các thương hiệu PNJ, Phú Quý, DOJI tăng 1,1 triệu đồng/lượng, niêm yết 171,9 - 174,9 triệu đồng/lượng.</p>
<h2>Giá Vàng Thế Giới Phục Hồi Mạnh</h2>
<p>Trên thị trường quốc tế, giá vàng giao ngay tăng lên quanh <strong>4.620 USD/ounce</strong>, tương đương mức tăng hơn 2,4% trong phiên gần nhất. Theo dữ liệu từ Kitco, vàng đang bật tăng trở lại sau khi kiểm định thành công vùng đáy ngắn hạn quanh 4.200-4.300 USD/ounce.</p>
<h2>Phân Tích Kỹ Thuật: Kháng Cự Và Hỗ Trợ</h2>
<p>Vùng <strong>4.600-4.650 USD/ounce</strong> đang đóng vai trò là ngưỡng kháng cự gần. Nếu vượt qua khu vực này với thanh khoản duy trì tích cực, vàng có thể mở rộng đà tăng lên các mốc cao hơn quanh 4.800 USD/ounce, xa hơn là vùng tâm lý 5.000 USD/ounce.</p>
<p>Ở chiều ngược lại, vùng <strong>4.400 USD/ounce</strong> hiện trở thành hỗ trợ quan trọng trong ngắn hạn. Ông Marc Chandler, Giám đốc tại Bannockburn Global Forex, nhận định việc vàng duy trì trên đường trung bình động 200 ngày quanh 4.092 USD/ounce là tín hiệu kỹ thuật tích cực.</p>
<h2>Nhận Định Cho Nhà Đầu Tư</h2>
<p>Xu hướng tăng của vàng được hỗ trợ bởi các yếu tố cơ bản như lạm phát dai dẳng, căng thẳng địa chính trị và rủi ro hệ thống tài chính toàn cầu. Tuy nhiên, nhà đầu tư cần chú ý đến áp lực từ đồng USD mạnh trong ngắn hạn. Quản lý rủi ro và theo dõi các ngưỡng kỹ thuật quan trọng là điều cần thiết trước khi ra quyết định đầu tư.</p>"""

    new_content = new_content + "\n" + BINGX_CTA_HTML

    # Load and update posts
    with open(POSTS_FILE) as f:
        posts = json.load(f)

    today = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(new_title)
    ts_id = datetime.now().strftime("%Y%m%d%H%M%S")
    existing_ids = {p.get("id") for p in posts}
    post_id = slug if slug not in existing_ids else f"{slug}-{ts_id}"

    post = {
        "id": post_id,
        "title": new_title,
        "summary": new_summary[:200],
        "content": new_content,
        "category": "hang-hoa",
        "image": "images/og-banner.jpg",
        "date": today,
        "url": source_url,
        "slug": slug,
    }

    posts.insert(0, post)

    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved hang-hoa post: {new_title[:80]}")
    print(f"Total posts: {len(posts)}")
    return new_title


if __name__ == "__main__":
    main()
