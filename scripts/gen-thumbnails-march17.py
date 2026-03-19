#!/usr/bin/env python3
"""
Generate AI thumbnails for 8 posts dated 2026-03-17 using Gemini 3.1 Flash Image API (Nano Banana 2).
"""

import json
import base64
import time
import re
import unicodedata
import requests
from pathlib import Path

REPO_DIR = Path("/home/shinyyume/.openclaw/workspace/signal-hunters-web")
POSTS_FILE = REPO_DIR / "data" / "posts.json"
IMAGES_DIR = REPO_DIR / "images"
CONFIG_FILE = Path("/home/shinyyume/.openclaw/openclaw.json")
TARGET_DATE = "2026-03-17"


def slugify(text: str) -> str:
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace('đ', 'd').replace('Đ', 'D')
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text[:40]


def build_image_prompt(title: str, category: str = "") -> str:
    """Build cyberpunk image prompt that flows with article content — NO fixed character."""
    title_lower = title.lower()
    cat_lower = category.lower()

    # Mood detection
    bearish_kw = ["crash","dump","giảm","sụt","lo ngại","rủi ro","cảnh báo",
                  "thanh lý","liquidat","phá sản","hack","tấn công","cấm","ban",
                  "kiện","lawsuit","bearish","sell-off","thua lỗ","sụp đổ"]
    bullish_kw = ["tăng","pump","rally","ath","kỷ lục","đầu tư","mua vào",
                  "phê duyệt","etf","institutional","bullish","breakout","lạc quan",
                  "thông qua","chấp nhận","hỗ trợ","phục hồi"]

    is_bearish = any(kw in title_lower for kw in bearish_kw)
    is_bullish = any(kw in title_lower for kw in bullish_kw)

    if is_bearish:
        mood = "dark dramatic tension, warning red signals, falling chart lines"
        palette = "deep crimson and electric purple with cyan warning highlights, dark atmosphere"
    elif is_bullish:
        mood = "energetic upward momentum, glowing green surge, victory energy"
        palette = "neon cyan and electric green with magenta accents, bright vibrant atmosphere"
    else:
        mood = "analytical calm, balanced data flow, professional precision"
        palette = "cyan purple and magenta balance, neutral-to-bright neon, clean composition"

    # Theme detection (theo nội dung bài)
    if any(w in title_lower for w in ["bitcoin","btc"]):
        subject = "massive golden Bitcoin coin with circuit engravings, floating blockchain network, price chart hologram"
    elif any(w in title_lower for w in ["ethereum","eth","defi","smart contract","aave","uniswap"]):
        subject = "Ethereum diamond crystal logo, DeFi protocol nodes, smart contract code streams, decentralized network"
    elif any(w in title_lower for w in ["xrp","ripple"]):
        subject = "XRP wave token in blue neon light, global payment network, interconnected financial nodes"
    elif any(w in title_lower for w in ["solana","sol"]):
        subject = "Solana high-speed network, purple light rays, ultra-fast transaction streams"
    elif any(w in title_lower for w in ["binance","bnb","cz"]):
        subject = "Binance golden logo, exchange trading terminal, crypto market depth visualization"
    elif any(w in title_lower for w in ["trump","white house","nhà trắng"]):
        subject = "US Capitol hologram, geopolitical digital globe, financial policy ripples across crypto markets"
    elif any(w in title_lower for w in ["iran","nga","russia","chiến tranh","war","địa chính trị"]):
        subject = "world map tension lines, geopolitical chess pieces, oil and financial markets under conflict"
    elif any(w in title_lower for w in ["fed","fomc","cpi","ppi","lãi suất","interest rate","macro","gdp"]):
        subject = "Federal Reserve building hologram, economic data dashboard, interest rate gauge, macro charts"
    elif any(w in title_lower for w in ["vàng","gold","silver","bạc","dầu","oil","commodity","hàng hóa"]):
        subject = "glowing gold bars and silver coins, commodity market ticker, oil barrels with price feeds"
    elif any(w in title_lower for w in ["hack","exploit","security","bảo mật","tấn công","rekt"]):
        subject = "digital vault being breached, red warning system alerts, cybersecurity breach visualization"
    elif any(w in title_lower for w in ["pháp lý","luật","sec","lawsuit","kiện","cấm","ban","regulate"]):
        subject = "scales of justice with crypto coins, legal gavel, regulatory framework hologram"
    elif any(w in title_lower for w in ["ai","artificial intelligence","agent","machine learning"]):
        subject = "AI neural network brain, autonomous trading agent, data processing streams"
    elif any(w in title_lower for w in ["stablecoin","usdt","usdc","thanh toán","payment"]):
        subject = "stablecoin coins floating, global payment network, digital dollar flow, banking integration"
    elif any(w in title_lower for w in ["nft","metaverse","gaming","game"]):
        subject = "NFT digital art gallery, metaverse landscape, virtual assets in cyberpunk space"
    elif any(w in title_lower for w in ["altcoin","meme","memecoin","doge","shib","pepe"]):
        subject = "constellation of altcoin tokens, meme coin rockets, diverse crypto ecosystem"
    elif any(w in title_lower for w in ["whale","cá voi","on-chain","blockchain data"]):
        subject = "massive whale silhouette in digital ocean, on-chain data streams, blockchain explorer"
    elif "hang-hoa" in cat_lower or "hàng hóa" in title_lower:
        subject = "commodity trading dashboard, gold silver oil holographic display, market data feeds"
    elif "altcoin" in cat_lower:
        subject = "diverse altcoin tokens orbiting, blockchain ecosystem, DeFi protocols connecting"
    elif "phan-tich" in cat_lower or "phân tích" in title_lower:
        subject = "advanced trading chart analysis, technical indicators, market pattern visualization"
    else:
        subject = "cryptocurrency market overview, blockchain data streams, financial technology convergence"

    return (
        f"Cinematic 16:9 cyberpunk illustration for a crypto/finance article about: \"{title}\". "
        f"Visual concept: {subject}. "
        f"Mood: {mood}. "
        f"Environment: futuristic cyberpunk cityscape or digital data space, holographic HUD displays, "
        f"neon-lit trading terminals, glowing circuit patterns. "
        f"Color palette: {palette}. "
        f"Style: high quality digital art, cinematic composition, dramatic neon rim lighting, "
        f"masterpiece quality, sharp focus, vibrant glow effects, professional illustration. "
        f"Absolutely no text, no letters, no words, no numbers, no labels anywhere. Pure visual only."
    )


def generate_thumbnail(title: str, category: str, api_key: str) -> bytes | None:
    """Call Gemini 3.1 Flash Image API (Nano Banana 2) to generate a thumbnail. Returns image bytes or None."""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key={api_key}"

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
        mood = "concerned analytical expression, hand on chin"
        scene_color = "crimson red and electric purple with cyan highlights, warning holographic indicators"
    elif is_bullish:
        mood = "excited confident smile, victory gesture"
        scene_color = "neon cyan and electric green with soft magenta, upward glowing price charts"
    else:
        mood = "professional thoughtful expression, arms crossed"
        scene_color = "balanced cyan purple and magenta, holographic market data"

    # Category context
    cat_context = {
        "phan-tich": "cryptocurrency technical analysis charts, RSI MACD indicators on holographic screens",
        "hang-hoa": "gold bars, oil barrels, forex currency symbols, commodity market data",
        "altcoin": "multiple cryptocurrency coins floating, altcoin market visualization",
        "tin-tuc": "breaking news holographic headlines, crypto news ticker",
        "chinh-tri": "government building holographic overlay, regulatory document symbols",
    }.get(category, "cryptocurrency market data and charts")

    prompt = build_image_prompt(title)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
    }

    resp = requests.post(api_url, json=payload, timeout=120)
    if resp.status_code == 200:
        data = resp.json()
        for part in data.get('candidates', [{}])[0].get('content', {}).get('parts', []):
            if 'inlineData' in part:
                return base64.b64decode(part['inlineData']['data'])
        print(f"  ⚠️ No image in response: {str(data)[:200]}")
    elif resp.status_code == 429:
        print(f"  ⏳ Rate limited (429), waiting 30s...")
        time.sleep(30)
        return None
    else:
        print(f"  ❌ HTTP {resp.status_code}: {resp.text[:300]}")
    return None


def main():
    cfg = json.load(open(CONFIG_FILE))
    api_key = cfg['models']['providers']['google']['apiKey']

    posts = json.load(open(POSTS_FILE))
    march17 = [p for p in posts if p.get('date') == TARGET_DATE]
    print(f"Found {len(march17)} posts for {TARGET_DATE}")

    updated = 0
    for i, post in enumerate(march17):
        title = post['title']
        category = post.get('category', 'tin-tuc')
        post_id = post.get('id', slugify(title))
        slug = post.get('slug') or slugify(title)

        print(f"\n[{i+1}/{len(march17)}] {title[:70]}")
        print(f"  Category: {category} | Slug: {slug}")

        # Generate with retries
        img_bytes = None
        for attempt in range(3):
            if attempt > 0:
                print(f"  Retry {attempt}...")
                time.sleep(10)
            img_bytes = generate_thumbnail(title, category, api_key)
            if img_bytes:
                break

        if not img_bytes:
            print(f"  ❌ Failed to generate after 3 attempts, keeping og-banner.jpg")
            continue

        # Save image
        filename = f"post-{slug}.png"
        filepath = IMAGES_DIR / filename
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        size_kb = filepath.stat().st_size // 1024
        print(f"  ✅ Saved: {filename} ({size_kb}KB)")

        # Update post in posts list (find by id)
        for p in posts:
            if p.get('id') == post_id and p.get('date') == TARGET_DATE:
                p['image'] = f"images/{filename}"
                break

        updated += 1

        # Rate limit: wait between requests (except last)
        if i < len(march17) - 1:
            print(f"  ⏳ Waiting 8s (rate limit)...")
            time.sleep(8)

    # Save updated posts
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Updated {updated}/{len(march17)} posts with new thumbnails")

    return updated


if __name__ == "__main__":
    updated = main()
    if updated > 0:
        print("\n✅ Done! Run deploy.sh to publish.")
    else:
        print("\n⚠️ No posts updated.")
