#!/usr/bin/env python3
"""Create a hang-hoa post about gold price for 2026-04-02."""
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
    today_str = "2/4/2026"
    today_date = "2026-04-02"

    source_title = f"Giá vàng hôm nay {today_str}: SJC và nhẫn trơn bứt phá, thế giới vượt 4.780 USD"
    source_url = "https://baodanang.vn/gia-vang-hom-nay-2-4-2026-gia-vang-sjc-vang-nhan-gia-vang-24k-va-vang-the-gioi-thu-nam-3330552.html"
    source_name = "Báo Đà Nẵng / VietnamNet"
    source_content = f"""Thị trường vàng ngày {today_str} tiếp tục ghi nhận đà tăng mạnh trên cả hai thị trường trong nước và quốc tế.

Giá vàng thế giới hôm nay {today_str} theo Kitco: 4.780,4 USD/ounce, tăng 112,6 USD (+2,41%) so với hôm qua. Quy đổi theo tỷ giá Vietcombank (26.360 VND/USD), vàng thế giới tương đương khoảng 149,9 triệu đồng/lượng chưa tính thuế, phí. Vàng miếng SJC đang cao hơn giá thế giới quy đổi khoảng 26,8 triệu đồng/lượng.

Giá vàng thế giới đêm 1/4 ở mức 4.739 USD/ounce (giao ngay) và 4.774 USD/ounce (giao tháng 6/2026 trên Comex). Cao hơn khoảng 9,1% (tương đương tăng 395 USD/ounce) so với cuối năm 2025.

Giá vàng SJC hôm nay {today_str}: Vàng miếng SJC tại SJC, DOJI, PNJ, Bảo Tín Mạnh Hải đồng loạt tăng 1,8 triệu đồng/lượng, chốt phiên ở mức 173,7 - 176,7 triệu đồng/lượng (mua vào - bán ra). Bảo Tín Minh Châu: 173,5 - 176,7 triệu đồng/lượng. Phú Quý: 173,7 - 176,7 triệu đồng/lượng. Mi Hồng: 174,2 - 176,5 triệu đồng/lượng (tăng 2 triệu đồng). Trong phiên sáng, vàng có lúc tăng lên 178 triệu đồng/lượng (giá bán).

Vàng nhẫn hôm nay {today_str}: SJC vàng nhẫn 1-5 chỉ: 173,5 - 176,5 triệu đồng/lượng (+1,8 triệu). Bảo Tín Mạnh Hải vàng nhẫn: 173 - 176 triệu đồng/lượng (+2 triệu).

Chỉ số DXY: 99,7 điểm, mất mốc 100, giảm 1,2% so với phiên trước. USD suy yếu góp phần hỗ trợ vàng tăng.

Tỷ giá USD/VND tự do ngày 1/4: 27.500 - 27.550 đồng/USD, giảm 530 đồng so với phiên trước.

Nguyên nhân vàng tăng: Đồng USD và lợi tức trái phiếu suy giảm; Doanh số bán lẻ Mỹ tháng 2 tăng 0,6% (tốt hơn dự báo -0,5%); Căng thẳng địa chính trị Trung Đông vẫn là yếu tố hỗ trợ; Lực mua vàng toàn cầu duy trì mạnh. 

Sau cú giảm về dưới 4.200 USD/ounce ngày 23/3, vàng đã phục hồi mạnh mẽ trở lại trên 4.700 USD/ounce. Chênh lệch giá trong nước và thế giới vẫn duy trì khoảng 26-27 triệu đồng/lượng, chưa có dấu hiệu thu hẹp trong ngắn hạn.

Về kỹ thuật: Vàng giữ vững trên vùng 4.600 USD - hỗ trợ quan trọng. Kháng cự gần: 4.800 USD/ounce. Mục tiêu tiếp theo nếu vượt: 5.000 USD/ounce."""

    cfg = json.load(open(CONFIG_FILE))
    api_key = cfg["models"]["providers"]["google"]["apiKey"]

    prompt = (
        f"Viết lại bài báo sau thành bài viết chuyên nghiệp bằng tiếng Việt, dài 1000-1500 từ, về thị trường hàng hóa và vàng ngày {today_str}.\n\n"
        "YÊU CẦU:\n"
        "- Viết lại hoàn toàn bằng ngôn ngữ của mình\n"
        f"- Tiêu đề hấp dẫn, đầy đủ về giá vàng ngày {today_str}\n"
        "- Mở bài thu hút\n"
        "- Thân bài chia thành 3-4 heading (dùng thẻ h2), phân tích kỹ\n"
        "- Đưa số liệu cụ thể: giá SJC (173,7-176,7 triệu), vàng nhẫn, giá thế giới (4.780 USD), DXY (99,7)\n"
        "- Phân tích kỹ thuật: ngưỡng hỗ trợ (4.600 USD), kháng cự (4.800 USD), mục tiêu (5.000 USD)\n"
        "- Đề cập nguyên nhân tăng: USD suy yếu, doanh số bán lẻ Mỹ tốt, địa chính trị\n"
        "- Kết bài có nhận định cho nhà đầu tư\n"
        "- Giọng văn: chuyên nghiệp, phong cách nhà phân tích hàng hóa\n\n"
        "THÔNG TIN GỐC:\n"
        f"Tiêu đề: {source_title}\n"
        f"Nguồn: {source_name} - {source_url}\n"
        f"Nội dung gốc:\n{source_content}\n\n"
        'TRA VE JSON (chi JSON, khong markdown, khong code fence):\n'
        '{"title": "tieu de moi day du", "summary": "tom tat 2-3 cau", "content": "noi dung HTML day du (dung h2, p, strong, ul, li)"}'
    )

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
    }

    print(f"Calling Gemini for hang-hoa article ({today_str})...")
    resp = requests.post(api_url, json=payload, timeout=90)
    print(f"Status: {resp.status_code}")

    new_title = source_title
    new_summary = f"Giá vàng SJC ngày {today_str} tăng 1,8 triệu đồng/lượng lên 176,7 triệu, vàng thế giới vượt 4.780 USD/ounce trong bối cảnh USD suy yếu."
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

    # Fallback content
    if not new_content or len(new_content) < 200:
        print("Using fallback content")
        new_content = f"""<p>Thị trường vàng ngày {today_str} ghi nhận đà tăng mạnh mẽ khi cả vàng trong nước lẫn thế giới đồng loạt bứt phá lên mốc cao mới. Sức mạnh của vàng được củng cố bởi sự suy yếu của đồng USD và bất ổn địa chính trị toàn cầu.</p>

<h2>Giá Vàng SJC Tăng 1,8 Triệu, Lên 176,7 Triệu Đồng/Lượng</h2>
<p>Phiên giao dịch ngày {today_str}, vàng miếng SJC tại các hệ thống lớn đồng loạt tăng <strong>1,8 triệu đồng/lượng</strong> ở cả hai chiều mua vào - bán ra:</p>
<ul>
<li><strong>SJC, DOJI, PNJ, Bảo Tín Mạnh Hải:</strong> 173,7 - 176,7 triệu đồng/lượng</li>
<li><strong>Bảo Tín Minh Châu:</strong> 173,5 - 176,7 triệu đồng/lượng</li>
<li><strong>Phú Quý:</strong> 173,7 - 176,7 triệu đồng/lượng</li>
<li><strong>Mi Hồng:</strong> 174,2 - 176,5 triệu đồng/lượng (tăng 2 triệu)</li>
</ul>
<p>Đáng chú ý, trong phiên buổi sáng, giá vàng có lúc tăng vọt lên <strong>178 triệu đồng/lượng</strong> (bán ra) trước khi hạ nhiệt về cuối phiên.</p>
<p>Vàng nhẫn cũng không kém cạnh: SJC vàng nhẫn 1-5 chỉ niêm yết <strong>173,5 - 176,5 triệu đồng/lượng</strong> (+1,8 triệu), Bảo Tín Mạnh Hải <strong>173 - 176 triệu đồng/lượng</strong> (+2 triệu).</p>

<h2>Vàng Thế Giới Vượt 4.780 USD/Ounce</h2>
<p>Theo Kitco, giá vàng giao ngay trên thị trường quốc tế ngày {today_str} đạt <strong>4.780,4 USD/ounce</strong>, tăng 112,6 USD (+2,41%) so với phiên trước. Đây là mức cao nhất trong nhiều tuần gần đây.</p>
<p>Trên sàn Comex New York, vàng giao tháng 6/2026 giao dịch ở mức <strong>4.774 USD/ounce</strong>. Tính từ đầu năm 2026, vàng đã tăng khoảng 9,1%, tương đương 395 USD/ounce — một hiệu suất ấn tượng.</p>
<p>Quy đổi theo tỷ giá Vietcombank (26.360 VND/USD), vàng thế giới tương đương khoảng <strong>149,9 triệu đồng/lượng</strong> chưa tính thuế và phí nhập khẩu. Khoảng cách giữa giá trong nước và quốc tế hiện duy trì ở mức khoảng <strong>26,8 triệu đồng/lượng</strong> — mức cao và chưa có dấu hiệu thu hẹp.</p>

<h2>Nguyên Nhân Vàng Tăng: USD Suy Yếu Và Địa Chính Trị</h2>
<p>Đợt tăng giá lần này được thúc đẩy bởi nhiều yếu tố hội tụ:</p>
<ul>
<li><strong>USD suy yếu mạnh:</strong> Chỉ số DXY giảm xuống 99,7 điểm, mất mốc tâm lý 100, giảm 1,2% so với phiên trước. Đây là tín hiệu hỗ trợ trực tiếp cho vàng.</li>
<li><strong>Dữ liệu kinh tế Mỹ tốt nhưng chưa đủ áp đảo vàng:</strong> Doanh số bán lẻ tháng 2 tăng 0,6%, vượt kỳ vọng (-0,5%), nhưng thị trường vàng đã bỏ qua tin này do kỳ vọng Fed vẫn nới lỏng.</li>
<li><strong>Căng thẳng địa chính trị Trung Đông:</strong> Bất ổn tại khu vực vẫn thúc đẩy nhu cầu trú ẩn an toàn vào vàng.</li>
<li><strong>Thiếu nguồn cung trong nước:</strong> Chưa có vàng nhập khẩu, nhu cầu cao trong khi lượng bán ra hạn chế, giữ chênh lệch giá ở mức cao.</li>
</ul>

<h2>Phân Tích Kỹ Thuật: Xu Hướng Tăng Dài Hạn Vẫn Vững</h2>
<p>Sau cú giảm mạnh về dưới <strong>4.200 USD/ounce</strong> vào ngày 23/3 do áp lực chốt lời và lo ngại địa chính trị, vàng đã hồi phục ấn tượng trở lại trên vùng <strong>4.700 USD/ounce</strong>. Điều này cho thấy xu hướng tăng dài hạn chưa bị phá vỡ.</p>
<p>Các ngưỡng kỹ thuật quan trọng:</p>
<ul>
<li><strong>Hỗ trợ mạnh:</strong> 4.600 USD/ounce — vùng này giữ vàng không giảm sâu hơn</li>
<li><strong>Kháng cự gần:</strong> 4.800 USD/ounce — nếu vượt qua, đà tăng có thể mạnh hơn</li>
<li><strong>Mục tiêu dài hạn:</strong> 5.000 USD/ounce — ngưỡng tâm lý lớn tiếp theo</li>
</ul>
<p>Tỷ giá USD/VND trên thị trường tự do ngày 1/4 ở mức 27.500 - 27.550 đồng/USD, giảm 530 đồng so với phiên trước — yếu tố này hỗ trợ nhu cầu mua vàng trong nước.</p>

<h2>Nhận Định Cho Nhà Đầu Tư</h2>
<p>Bức tranh vàng ngắn và trung hạn vẫn nghiêng về phía tích cực. Với vàng trong nước, mức chênh lệch 26-27 triệu đồng/lượng so với thế giới là rủi ro cần theo dõi — nếu nhập khẩu được mở lại, chênh lệch có thể thu hẹp nhanh.</p>
<p>Nhà đầu tư cần chú ý:</p>
<ul>
<li>Không mua đuổi ở đỉnh — chờ các nhịp điều chỉnh về vùng hỗ trợ</li>
<li>Quản lý rủi ro chặt chẽ, không đặt cược toàn bộ một lần</li>
<li>Theo dõi diễn biến DXY và quyết định của Fed về lãi suất</li>
<li>Chênh lệch trong nước/thế giới ở mức cao là cảnh báo rủi ro thanh khoản</li>
</ul>
<p>Nhìn tổng thể, vàng vẫn là kênh trú ẩn giá trị hiệu quả trong bối cảnh bất định toàn cầu. Tuy nhiên, kỷ luật giao dịch và quản lý vốn là yếu tố quyết định thành bại của nhà đầu tư.</p>"""

    new_content = new_content + "\n" + BINGX_CTA_HTML

    # Load and update posts
    with open(POSTS_FILE) as f:
        posts = json.load(f)

    # Check if hang-hoa already exists for today
    existing = [p for p in posts if p.get("date") == today_date and p.get("category") == "hang-hoa"]
    if existing:
        print(f"⚠️ Hang-hoa post already exists for {today_date}: {existing[0]['title'][:60]}")
        return existing[0]['title']

    slug = slugify(new_title)
    ts_id = datetime.now().strftime("%Y%m%d%H%M%S")
    existing_ids = {p.get("id") for p in posts}
    post_id = slug if slug not in existing_ids else f"{slug}-{ts_id}"

    post = {
        "id": post_id,
        "title": new_title,
        "summary": new_summary[:250],
        "content": new_content,
        "category": "hang-hoa",
        "image": "images/og-banner.jpg",
        "date": today_date,
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
