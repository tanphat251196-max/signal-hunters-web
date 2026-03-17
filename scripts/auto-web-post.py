#!/usr/bin/env python3
"""
Auto Web Post - Crawl tin crypto → viết lại → đăng lên daututhongminh24h.com
Chạy: /home/shinyyume/.openclaw/venvs/crypto-tools/bin/python3 scripts/auto-web-post.py
"""

import json
import os
import re
import subprocess
import sys
import hashlib
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from difflib import SequenceMatcher

import requests
from bs4 import BeautifulSoup

# === CONFIG ===
REPO_DIR = Path("/home/shinyyume/.openclaw/workspace/signal-hunters-web")
POSTS_FILE = REPO_DIR / "data" / "posts.json"
IMAGES_DIR = REPO_DIR / "images"
DEPLOY_SCRIPT = REPO_DIR / "scripts" / "deploy.sh"
DEDUP_FILE = Path("/tmp/openclaw/web-post-last-date.txt")
MAX_ARTICLES = 8   # Tối đa 8 bài/ngày
MIN_ARTICLES = 4   # Tối thiểu 4 bài/ngày
# Bắt buộc mỗi ngày phải có ít nhất 1 bài mỗi category:
REQUIRED_CATEGORIES = ["tin-tuc", "phan-tich", "altcoin", "hang-hoa"]
MIN_TITLE_LEN = 15
SIMILARITY_THRESHOLD = 0.7
CONFIG_FILE = Path("/home/shinyyume/.openclaw/openclaw.json")

# === FILTER: Chỉ đăng tin quan trọng ===
# Tin liên quan BTC/ETH/vàng/bạc/dầu/macro/pháp lý/chính trị ảnh hưởng giá
IMPORTANT_KEYWORDS = [
    # Crypto chính
    "bitcoin", "btc", "ethereum", "eth", "crypto", "tiền điện tử", "tiền mã hóa",
    # Hàng hóa
    "vàng", "gold", "bạc", "silver", "dầu", "oil", "wti", "brent",
    # Macro/Kinh tế
    "fed", "lãi suất", "interest rate", "cpi", "lạm phát", "inflation",
    "gdp", "việc làm", "unemployment", "recession", "suy thoái",
    "etf", "spot etf", "quỹ", "fund", "institutional",
    "dxy", "dollar", "usd", "đô la",
    # Pháp lý
    "sec", "quy định", "regulation", "luật", "cấm", "ban", "kiện", "lawsuit",
    "giấy phép", "license", "tornado cash", "binance", "coinbase",
    "bộ tư pháp", "doj", "pháp lý",
    # Chính trị
    "trump", "biden", "tổng thống", "president", "quốc hội", "congress",
    "chiến tranh", "war", "iran", "nga", "russia", "trung quốc", "china",
    "trừng phạt", "sanction", "thuế", "tariff",
    # Biến động giá lớn
    "pump", "dump", "crash", "rally", "ath", "all-time", "kỷ lục",
    "thanh lý", "liquidat", "phá sản", "bankrupt",
    "whale", "cá voi", "tỷ đô", "billion",
]

# Tin KHÔNG quan trọng → loại bỏ
SPAM_KEYWORDS = [
    "airdrop", "testnet", "faucet", "giveaway", "bounty",
    "meme coin", "shitcoin", "nft collection", "game nft",
    "hướng dẫn đăng ký", "cách tạo ví", "tutorial",
    "review sàn", "so sánh sàn", "top 10 coin",
    "dự đoán giá.*2027", "dự đoán giá.*2028",
]

SOURCES = [
    {
        "name": "Coin68",
        "url": "https://coin68.com/",
        "selector": "article a, .post-title a, h2 a, h3 a",
        "base": "https://coin68.com"
    },
    {
        "name": "BeInCrypto",
        "url": "https://vn.beincrypto.com/",
        "selector": "article a, .post-title a, h2 a, h3 a",
        "base": "https://vn.beincrypto.com"
    },
    {
        "name": "Investing.com",
        "url": "https://vn.investing.com/news/cryptocurrency-news",
        "selector": "article a, .articleItem a, .js-article-item a, h2 a, h3 a",
        "base": "https://vn.investing.com"
    },
    {
        "name": "BlogTienAo",
        "url": "https://blogtienao.com/",
        "selector": "article a, .post-title a, h2 a, h3 a",
        "base": "https://blogtienao.com"
    },
]

BINGX_CTA = """
---

💰 **Tiết kiệm phí trade?** Đăng ký BingX hoàn phí 45% vĩnh viễn: [Đăng ký ngay](https://bingx.com/vi-vn/partner/X7EZVIWI) ✨

*Theo dõi [Đầu Tư Thông Minh 24H](https://daututhongminh24h.com) để cập nhật tin tức crypto mới nhất!*
"""
# NOTE: BINGX_CTA (markdown) kept for backward compat but new code uses BINGX_CTA_HTML below

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def slugify(text: str) -> str:
    """Convert Vietnamese text to URL slug."""
    # Normalize unicode
    text = unicodedata.normalize('NFD', text)
    # Remove diacritics
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Vietnamese special chars
    text = text.replace('đ', 'd').replace('Đ', 'D')
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text[:80]


def load_posts() -> list:
    """Load existing posts."""
    if POSTS_FILE.exists():
        with open(POSTS_FILE) as f:
            return json.load(f)
    return []


def save_posts(posts: list):
    """Save posts to JSON."""
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def is_duplicate(title: str, existing_titles: list) -> bool:
    """Check if title is too similar to existing."""
    title_lower = title.lower().strip()
    for existing in existing_titles:
        ratio = SequenceMatcher(None, title_lower, existing.lower().strip()).ratio()
        if ratio > SIMILARITY_THRESHOLD:
            return True
    return False


def is_important(title: str) -> bool:
    """Chỉ giữ tin quan trọng: BTC/ETH/vàng/dầu/macro/pháp lý/chính trị."""
    title_lower = title.lower()
    
    # Loại spam trước
    for kw in SPAM_KEYWORDS:
        if re.search(kw, title_lower):
            return False
    
    # Phải chứa ít nhất 1 keyword quan trọng
    for kw in IMPORTANT_KEYWORDS:
        if kw in title_lower:
            return True
    
    return False


def crawl_source(source: dict) -> list:
    """Crawl a news source and extract article links + titles."""
    articles = []
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        seen_urls = set()
        for selector in source["selector"].split(", "):
            for link in soup.select(selector):
                href = link.get("href", "")
                title = link.get_text(strip=True)
                
                if not href or not title or len(title) < MIN_TITLE_LEN:
                    continue
                
                # Build full URL
                if href.startswith("/"):
                    href = source["base"] + href
                elif not href.startswith("http"):
                    continue
                
                # Skip non-article URLs
                if any(x in href for x in ["/tag/", "/category/", "/author/", "#", "javascript:", "/page/"]):
                    continue
                
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                
                articles.append({
                    "title": title,
                    "url": href,
                    "source": source["name"]
                })
        
        print(f"  [{source['name']}] Crawled {len(articles)} articles")
    except Exception as e:
        print(f"  [{source['name']}] Error: {e}")
    
    return articles


def fetch_article_content(url: str) -> dict:
    """Fetch full article content from URL."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Try to find main content
        content_selectors = [
            "article .entry-content", "article .post-content", ".article-content",
            ".entry-content", ".post-content", ".content-inner", "article",
            ".articlePage", "#article-body", ".detail-content"
        ]
        
        content_elem = None
        for sel in content_selectors:
            content_elem = soup.select_one(sel)
            if content_elem:
                break
        
        if not content_elem:
            content_elem = soup.find("article") or soup.find("main")
        
        if not content_elem:
            return {"text": "", "image": ""}
        
        # Extract text paragraphs
        paragraphs = []
        for p in content_elem.find_all(["p", "h2", "h3", "li"]):
            text = p.get_text(strip=True)
            if len(text) > 20:
                tag = p.name
                if tag in ["h2", "h3"]:
                    paragraphs.append(f"\n## {text}\n")
                else:
                    paragraphs.append(text)
        
        # Extract first image
        image = ""
        img = content_elem.find("img")
        if img:
            image = img.get("src", "") or img.get("data-src", "")
        
        # Also check OG image
        if not image:
            og = soup.find("meta", property="og:image")
            if og:
                image = og.get("content", "")
        
        return {
            "text": "\n\n".join(paragraphs),
            "image": image
        }
    except Exception as e:
        print(f"    Error fetching {url}: {e}")
        return {"text": "", "image": ""}


BINGX_CTA_HTML = """<div class="cta-box" style="background:#1a1a2e;border:1px solid #16213e;border-radius:12px;padding:20px;margin-top:30px;">
<h3>💰 Tiết kiệm phí giao dịch crypto?</h3>
<p>Đăng ký BingX qua link dưới đây để được <strong>hoàn phí 45% VĨNH VIỄN</strong>:</p>
<p><a href="https://bingx.com/vi-vn/partner/X7EZVIWI" target="_blank" rel="noopener">👉 Đăng ký BingX ngay (Code: X7EZVIWI)</a></p>
</div>"""


def categorize_article(title: str, content: str) -> str:
    """Categorize article based on title + content keywords.

    Priority order (highest to lowest):
    1. phan-tich  — analysis, technical, prediction
    2. hang-hoa   — commodities, macro, forex
    3. tin-tuc    — news, announcements, partnerships
    4. altcoin    — specific altcoin names (only if no higher match)
    5. chinh-tri  — politics, regulation, legal
    Default fallback: tin-tuc
    """
    text = (title + " " + content[:1000]).lower()  # Only use first 1000 chars of content for speed

    # 1. HIGHEST PRIORITY: Analysis / technical / prediction
    analysis_kw = [
        "phân tích kỹ thuật", "phân tích giá", "kỹ thuật", "technical analysis",
        "dự đoán giá", "dự báo giá", "price prediction", "price target", "mục tiêu giá",
        "hỗ trợ và kháng cự", "support resistance", "hỗ trợ kháng cự",
        "rsi", "macd", "bollinger", "fibonacci", "on-chain", "onchain",
        "bull run", "bear market", "bearish", "bullish",
        "dự đoán", "nhà phân tích", "phân tích chuyên sâu",
        "cryptoquant", "glassnode", "santiment", "chart"
    ]
    if any(kw in text for kw in analysis_kw):
        return "phan-tich"

    # 2. Commodities / macro / forex
    commodity_kw = [
        "vàng", "gold", "bạc", "silver", "dầu mỏ", "crude oil", "dầu wti", "brent",
        "khí đốt", "natural gas", "forex", "ngoại hối", "fed ", "lãi suất",
        "interest rate", "cpi", "lạm phát", "inflation", "gdp", "suy thoái", "recession",
        "dxy", "dollar index", "hàng hóa", "commodity", "commodities",
        "tỷ lệ thất nghiệp", "unemployment", "powell", "nonfarm"
    ]
    if any(kw in text for kw in commodity_kw):
        return "hang-hoa"

    # 3. News / announcements / partnerships / legal events
    news_kw = [
        "tin tức", "thông báo", "ra mắt", "hợp tác", "partnership",
        "pháp lý", "sec ", "cftc", "etf approval", "etf được phê duyệt",
        "quy định", "regulation", "luật",
        "hack", "tấn công", "bị hack", "stolen", "phát hành", "launch",
        "listing", "niêm yết", "update", "nâng cấp", "upgrade", "mainnet"
    ]
    if any(kw in text for kw in news_kw):
        return "tin-tuc"

    # 4. Altcoin — specific altcoins (only when no higher priority match)
    altcoin_kw = [
        "ethereum", " eth ", "eth,", "eth.", "xrp", "ripple", "solana", " sol ",
        "bnb", "cardano", "ada", "avalanche", "avax", "polkadot", "dot",
        "chainlink", "link", "polygon", "matic", "dogecoin", "doge",
        "shiba", "litecoin", "ltc", "tron", "trx", "cosmos", "atom",
        "near", "aptos", "apt", "sui", "pepe", "altcoin", "altseason",
        "ethereum classic", "etc", "uniswap", "uni", "aave", "defi"
    ]
    if any(kw in text for kw in altcoin_kw):
        return "altcoin"

    # 5. Politics / government / macro policy
    politics_kw = [
        "chính phủ", "government", "quốc hội", "congress", "chính trị",
        "trump", "biden", "tổng thống", "president",
        "trừng phạt", "sanction", "thuế", "tariff",
        "chiến tranh", "war", "iran", "nga", "russia", "trung quốc", "china",
        "kinh tế vĩ mô", "macroeconomics"
    ]
    if any(kw in text for kw in politics_kw):
        return "chinh-tri"

    return "tin-tuc"


def rewrite_article(title: str, content: str, source_name: str, source_url: str) -> dict:
    """Use Gemini AI to rewrite article into a high-quality 1000-2500 word Vietnamese article."""
    import time

    # Load API key
    try:
        cfg = json.load(open(CONFIG_FILE))
        api_key = cfg['models']['providers']['google']['apiKey']
    except Exception as e:
        print(f"    ⚠️ Cannot load Gemini API key: {e}")
        api_key = None

    # Trim content to avoid token overflow — keep up to 4000 chars
    content_trimmed = content[:4000].strip() if content else ""

    # Try Gemini rewrite if API key available
    if api_key and content_trimmed:
        prompt = f"""Viết lại bài báo sau thành bài viết chuyên nghiệp bằng tiếng Việt, dài 1000-2500 từ.

YÊU CẦU:
- Viết lại HOÀN TOÀN bằng ngôn ngữ của mình, KHÔNG copy paste
- Tiêu đề hấp dẫn, đầy đủ (KHÔNG cắt ngắn, KHÔNG dấu "...")
- Mở bài thu hút, giới thiệu vấn đề
- Thân bài chia thành 3-5 heading (<h2> hoặc <h3>), mỗi phần phân tích sâu
- Đưa số liệu cụ thể, trích dẫn nguồn
- Liên hệ tác động đến nhà đầu tư Việt Nam
- Kết bài có nhận định riêng, không generic
- Giọng văn: chuyên nghiệp nhưng dễ hiểu, phong cách nhà phân tích crypto

THÔNG TIN GỐC:
Tiêu đề: {title}
Nguồn: {source_name} - {source_url}
Nội dung gốc:
{content_trimmed}

TRẢ VỀ JSON (chỉ JSON, không markdown):
{{
  "title": "tiêu đề mới đầy đủ",
  "summary": "tóm tắt 2-3 câu",
  "content": "nội dung HTML đầy đủ (dùng <h2>, <h3>, <p>, <strong>, <ul><li>)"
}}"""

        for model in ["gemini-2.5-flash", "gemini-2.0-flash-exp", "gemini-1.5-flash"]:
            try:
                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 8192
                    }
                }
                resp = requests.post(api_url, json=payload, timeout=90)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

                    # Strip markdown code fences if present
                    raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text, flags=re.MULTILINE)
                    raw_text = re.sub(r'\s*```$', '', raw_text, flags=re.MULTILINE)
                    raw_text = raw_text.strip()

                    # Robust JSON extraction: Gemini HTML often has unescaped quotes
                    # Strategy: try standard parse first, then regex fallback
                    new_title = title
                    new_summary = ""
                    new_content = ""
                    try:
                        result = json.loads(raw_text)
                        new_title = result.get("title", title).strip()
                        new_summary = result.get("summary", "").strip()
                        new_content = result.get("content", "").strip()
                    except json.JSONDecodeError:
                        # Fallback: extract fields with regex (handles unescaped quotes in HTML)
                        title_m = re.search(r'"title"\s*:\s*"([^"]+)"', raw_text)
                        summary_m = re.search(r'"summary"\s*:\s*"([^"]+)"', raw_text)
                        # Content: everything between "content": " ... " (last closing quote before })
                        content_m = re.search(r'"content"\s*:\s*"(.*?)"\s*\}', raw_text, re.DOTALL)
                        if not content_m:
                            # Try: content is rest of the string after "content": "
                            content_m2 = re.search(r'"content"\s*:\s*"(.*)', raw_text, re.DOTALL)
                            if content_m2:
                                raw_content = content_m2.group(1)
                                # Remove trailing JSON closing
                                raw_content = re.sub(r'"\s*\}\s*$', '', raw_content).strip()
                                new_content = raw_content.replace('\\"', '"').replace('\\n', '\n')
                        else:
                            new_content = content_m.group(1).replace('\\"', '"').replace('\\n', '\n')
                        if title_m:
                            new_title = title_m.group(1).strip()
                        if summary_m:
                            new_summary = summary_m.group(1).strip()
                        # If content still empty or too short, try extracting all HTML tags from raw
                        if len(new_content) < 500:
                            html_m = re.search(r'(<(?:h2|h3|p|ul|li|strong|div)[^>]*>.*)', raw_text, re.DOTALL)
                            if html_m:
                                new_content = html_m.group(1)
                                # Clean trailing JSON artifacts
                                new_content = re.sub(r'"\s*\}\s*$', '', new_content).strip()

                    # Validate title — no trailing "..."
                    if new_title.endswith("...") or new_title.endswith("…"):
                        new_title = new_title.rstrip(".…").strip()
                    if len(new_title) > 80:
                        # Truncate at last space before 80 chars (must be full sentence)
                        new_title = new_title[:80].rsplit(' ', 1)[0].rstrip('.,;:')

                    # Append BingX CTA
                    new_content = new_content + "\n" + BINGX_CTA_HTML

                    # Validate minimum quality
                    stripped = re.sub(r'<[^>]+>', '', new_content)
                    word_count = len(stripped.split())
                    heading_count = len(re.findall(r'<h[23][^>]*>', new_content))
                    has_cta = "bingx.com" in new_content

                    print(f"    ✅ Gemini ({model}): {word_count} words, {heading_count} headings, CTA={has_cta}")

                    if word_count >= 800 and heading_count >= 3 and has_cta:
                        return {
                            "title": new_title,
                            "summary": new_summary[:300],
                            "content": new_content,
                        }
                    else:
                        print(f"    ⚠️ Quality check failed (words={word_count}, headings={heading_count}), retrying...")
                        time.sleep(3)
                        continue

                elif resp.status_code == 429:
                    print(f"    ⚠️ Rate limit on {model}, waiting 15s...")
                    time.sleep(15)
                else:
                    print(f"    ⚠️ Gemini {model} HTTP {resp.status_code}: {resp.text[:200]}")
            except json.JSONDecodeError as e:
                print(f"    ⚠️ JSON parse error from {model}: {e}")
            except Exception as e:
                print(f"    ⚠️ Gemini error ({model}): {e}")
            time.sleep(2)

    # Fallback: structured rewrite without AI (better than old version)
    print(f"    ⚠️ Gemini unavailable — using structured fallback")
    first_para = content_trimmed.split("\n\n")[0] if content_trimmed else title
    summary = first_para[:250].strip().rstrip('.') + '.'

    # Clean title — no "..."
    clean_title = title.rstrip(".…").strip()
    if clean_title.endswith("..."):
        clean_title = clean_title[:-3].strip()

    body_html = f"""<p>{first_para[:500]}</p>
<h2>Diễn biến thị trường</h2>
<p>{content_trimmed[500:1200] if len(content_trimmed) > 500 else content_trimmed}</p>
<h2>Phân tích và nhận định</h2>
<p>Thông tin trên có thể tác động đáng kể đến tâm lý nhà đầu tư trong ngắn hạn. Các chuyên gia khuyến nghị theo dõi sát diễn biến tiếp theo trước khi đưa ra quyết định giao dịch.</p>
<h2>Tác động đến nhà đầu tư Việt Nam</h2>
<p>Với thị trường crypto ngày càng toàn cầu hóa, những biến động này không chỉ ảnh hưởng đến nhà đầu tư quốc tế mà còn tác động trực tiếp đến cộng đồng nhà đầu tư Việt Nam. Traders cần quản lý rủi ro chặt chẽ và theo dõi thêm thông tin từ các nguồn uy tín.</p>
<h2>Kết luận</h2>
<p>Đây là một trong những tin tức quan trọng cần theo dõi trong ngày. Nhà đầu tư nên cập nhật liên tục để nắm bắt cơ hội và hạn chế rủi ro.</p>
""" + BINGX_CTA_HTML

    return {
        "title": clean_title,
        "summary": summary[:300],
        "content": body_html,
    }


def generate_ai_thumbnail(title: str, slug: str) -> str:
    """Generate AI thumbnail using Imagen 4.0 API."""
    try:
        import base64
        cfg = json.load(open(CONFIG_FILE))
        api_key = cfg['models']['providers']['google']['apiKey']

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={api_key}"

        # Determine mood/theme from title keywords
        title_lower = title.lower()
        bearish_kw = ["crash", "dump", "giảm", "sụt", "lo ngại", "rủi ro", "cảnh báo",
                      "thanh lý", "liquidat", "phá sản", "bankrupt", "hack", "tấn công",
                      "cấm", "ban", "kiện", "lawsuit", "bearish", "sell-off", "thua lỗ"]
        bullish_kw = ["tăng", "pump", "rally", "ath", "kỷ lục", "đầu tư", "mua vào",
                      "phê duyệt", "etf", "institutional", "bullish", "breakout", "lạc quan",
                      "thông qua", "chấp nhận", "hỗ trợ"]

        is_bearish = any(kw in title_lower for kw in bearish_kw)
        is_bullish = any(kw in title_lower for kw in bullish_kw)

        if is_bearish:
            mood = "concerned analytical expression, hand on chin thinking"
            scene_color = "crimson red and electric purple with cyan highlights, warning holographic indicators in background"
        elif is_bullish:
            mood = "excited confident smile, victory fist pump gesture"
            scene_color = "neon cyan and electric green with soft magenta accents, upward glowing price charts in background"
        else:
            mood = "professional thoughtful expression, arms crossed confidently"
            scene_color = "balanced cyan purple and magenta, mixed holographic market data in background"

        # Clean, detailed Imagen prompt — NO TEXT in image
        prompt = (
            f"Cinematic 16:9 illustration for a crypto news article about: \"{title}\". "
            f"Main subject: beautiful petite anime girl with short black bob hair with straight blunt bangs, "
            f"huge expressive sparkling anime eyes, two glowing white futuristic halo rings near ears, "
            f"black choker with silver ring, black strapless top with white geometric harness straps, "
            f"neon cyberpunk lighting. She has a {mood}. "
            f"She is prominently featured on the right side of the frame. "
            f"Scene: futuristic cyberpunk trading room with holographic displays showing cryptocurrency charts and data. "
            f"Color palette: {scene_color}. "
            f"Style: high quality anime illustration, masterpiece, sharp focus, dramatic rim lighting, "
            f"vibrant neon glow. "
            f"IMPORTANT: absolutely no text, no letters, no words, no numbers, no labels, no signs, no captions anywhere in the image. Pure visual only."
        )

        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {"sampleCount": 1, "aspectRatio": "16:9"}
        }

        resp = requests.post(api_url, json=payload, timeout=90)
        if resp.status_code == 200:
            data = resp.json()
            predictions = data.get("predictions", [])
            if predictions and "bytesBase64Encoded" in predictions[0]:
                img_bytes = base64.b64decode(predictions[0]["bytesBase64Encoded"])
                filename = f"post-{slug[:40]}.png"
                filepath = IMAGES_DIR / filename
                with open(filepath, "wb") as f:
                    f.write(img_bytes)

                # Overlay logo watermark if PIL available
                try:
                    from PIL import Image
                    img = Image.open(filepath).convert("RGBA")
                    # Resize to FHD if needed
                    if img.width < 1920:
                        ratio = 1920 / img.width
                        img = img.resize((1920, int(img.height * ratio)), Image.LANCZOS)
                    logo_path = Path("/home/shinyyume/.openclaw/workspace/assets/sh-logo-watermark.png")
                    if logo_path.exists():
                        logo = Image.open(logo_path).convert("RGBA")
                        img.paste(logo, (20, 20), logo)
                    img.save(filepath, "PNG")
                    print(f"    🎨 AI thumbnail + logo: {filename} ({filepath.stat().st_size//1024}KB)")
                except ImportError:
                    print(f"    🎨 AI thumbnail (no logo - PIL missing): {filename} ({len(img_bytes)//1024}KB)")

                return f"images/{filename}"
            else:
                print(f"    ⚠️ AI thumbnail: no image in response predictions")
        else:
            print(f"    ⚠️ AI thumbnail failed: HTTP {resp.status_code}")
            try:
                print(f"    Response: {resp.text[:300]}")
            except:
                pass
    except Exception as e:
        print(f"    ⚠️ AI thumbnail error: {e}")

    return "images/og-banner.jpg"


def download_image(url: str, slug: str) -> str:
    """Download article image or use placeholder."""
    if not url or not url.startswith("http"):
        return "images/og-banner.jpg"  # Fallback
    
    try:
        ext = ".jpg"
        if ".png" in url.lower():
            ext = ".png"
        elif ".webp" in url.lower():
            ext = ".webp"
        
        filename = f"post-{slug[:40]}{ext}"
        filepath = IMAGES_DIR / filename
        
        if filepath.exists():
            return f"images/{filename}"
        
        resp = requests.get(url, headers=HEADERS, timeout=10, stream=True)
        resp.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        
        print(f"    Downloaded image: {filename}")
        return f"images/{filename}"
    except Exception as e:
        print(f"    Image download failed: {e}")
        return "images/og-banner.jpg"


def deploy():
    """Deploy to Hostinger via rsync."""
    try:
        result = subprocess.run(
            ["bash", str(DEPLOY_SCRIPT)],
            capture_output=True, text=True, timeout=120,
            cwd=str(REPO_DIR)
        )
        if result.returncode == 0:
            print("✅ Deploy successful!")
        else:
            print(f"⚠️ Deploy warning: {result.stderr[:200]}")
    except Exception as e:
        print(f"❌ Deploy failed: {e}")


def git_push(count: int):
    """Git commit and push."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        subprocess.run(["git", "add", "."], cwd=str(REPO_DIR), capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"Auto: thêm {count} bài mới [{today}]"],
            cwd=str(REPO_DIR), capture_output=True
        )
        subprocess.run(["git", "push"], cwd=str(REPO_DIR), capture_output=True, timeout=60)
        print("✅ Git push done!")
    except Exception as e:
        print(f"⚠️ Git push error: {e}")


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Daily dedup — chỉ chạy 1 lần/ngày
    DEDUP_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DEDUP_FILE.exists():
        last_date = DEDUP_FILE.read_text().strip()
        if last_date == today:
            print(f"Already posted today ({today}). Skip.")
            return
    
    print(f"=== Auto Web Post — {today} ===")
    
    # Load existing
    posts = load_posts()
    existing_titles = [p["title"] for p in posts]
    print(f"Existing posts: {len(posts)}")
    
    # Crawl all sources
    print("\n📡 Crawling sources...")
    all_articles = []
    for source in SOURCES:
        articles = crawl_source(source)
        all_articles.extend(articles)
    
    print(f"\nTotal crawled: {len(all_articles)}")
    
    # Filter: dedup + quality + importance
    new_articles = []
    skipped_unimportant = 0
    for art in all_articles:
        if is_duplicate(art["title"], existing_titles + [a["title"] for a in new_articles]):
            continue
        if not is_important(art["title"]):
            skipped_unimportant += 1
            continue
        new_articles.append(art)
        if len(new_articles) >= MAX_ARTICLES:
            break
    
    print(f"After filter: {len(new_articles)} important (skipped {skipped_unimportant} unimportant)")
    
    if not new_articles:
        print("Không có bài mới. Done.")
        DEDUP_FILE.write_text(today)
        return
    
    # === ĐẢM BẢO ĐỦ 4 CATEGORY BẮT BUỘC ===
    # Pre-categorize để kiểm tra coverage
    def quick_category(title):
        return categorize_article(title, "")
    
    categorized = [(art, quick_category(art["title"])) for art in new_articles]
    covered = set(cat for _, cat in categorized)
    missing = [c for c in REQUIRED_CATEGORIES if c not in covered]
    
    if missing:
        print(f"⚠️ Thiếu category bắt buộc: {missing} — crawl bổ sung...")
        # Crawl thêm từ all_articles để tìm bài thuộc category thiếu
        for needed_cat in missing:
            for art in all_articles:
                if art in new_articles:
                    continue
                if is_duplicate(art["title"], existing_titles + [a["title"] for a in new_articles]):
                    continue
                cat = quick_category(art["title"])
                if cat == needed_cat:
                    new_articles.append(art)
                    print(f"   ✅ Bổ sung [{needed_cat}]: {art['title'][:60]}")
                    break
    
    # Giới hạn MAX_ARTICLES
    if len(new_articles) > MAX_ARTICLES:
        new_articles = new_articles[:MAX_ARTICLES]
    
    print(f"Final articles to publish: {len(new_articles)} (min={MIN_ARTICLES}, max={MAX_ARTICLES})")
    
    # Process each article
    published = 0
    # IDs are string slugs — generate timestamp-based ID for new posts
    ts_id = datetime.now().strftime("%Y%m%d%H%M%S")
    next_id_counter = [0]  # mutable counter for multiple posts in same run
    
    for i, art in enumerate(new_articles):
        print(f"\n📝 [{i+1}/{len(new_articles)}] {art['title'][:60]}...")
        
        # Fetch full content
        content_data = fetch_article_content(art["url"])
        
        # Rewrite
        rewritten = rewrite_article(art["title"], content_data["text"], art["source"], art["url"])
        
        # AI thumbnail (chờ 3s giữa mỗi request tránh rate limit)
        slug = slugify(art["title"])
        image_path = generate_ai_thumbnail(art["title"], slug)
        if image_path == "images/og-banner.jpg" and content_data.get("image"):
            # Fallback: download ảnh từ nguồn nếu AI fail
            image_path = download_image(content_data["image"], slug)
        
        if i < len(new_articles) - 1:
            import time
            time.sleep(5)  # Rate limit Gemini
        
        # Categorize based on content
        category = categorize_article(rewritten["title"], rewritten["content"])

        # Create post entry — ID is slug-based (string, not int)
        post_id = slug if slug else f"{ts_id}-{next_id_counter[0]}"
        # Ensure uniqueness: append counter if slug already exists
        existing_ids = {p.get("id") for p in posts}
        if post_id in existing_ids:
            post_id = f"{slug}-{ts_id}" if slug else f"{ts_id}-{next_id_counter[0]}"
        post = {
            "id": post_id,
            "title": rewritten["title"],
            "summary": rewritten["summary"][:200],
            "content": rewritten["content"],
            "category": category,
            "image": image_path,
            "date": today,
            "url": art["url"],
            "slug": slug
        }
        
        # Insert at beginning (newest first)
        posts.insert(0, post)
        next_id_counter[0] += 1
        published += 1
        print(f"  ✅ Added: {slug}")
    
    # Save
    save_posts(posts)
    print(f"\n💾 Saved {published} new posts (total: {len(posts)})")
    
    # Mark done for today
    DEDUP_FILE.write_text(today)
    
    # Deploy
    print("\n🚀 Deploying...")
    deploy()
    
    # Git
    print("\n📦 Git push...")
    git_push(published)
    
    print(f"\n✅ DONE: Published {published} bài mới lên daututhongminh24h.com")


if __name__ == "__main__":
    main()
