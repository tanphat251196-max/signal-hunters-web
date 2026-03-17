#!/usr/bin/env python3
"""
Generate AI thumbnails for 8 posts dated 2026-03-17 using Imagen 4.0 API.
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


def generate_thumbnail(title: str, category: str, api_key: str) -> bytes | None:
    """Call Imagen 4.0 API to generate a thumbnail. Returns image bytes or None."""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={api_key}"

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

    prompt = (
        f"Cinematic 16:9 thumbnail for crypto news article: \"{title}\". "
        f"Main subject: beautiful petite anime girl with short black bob hair with straight blunt bangs, "
        f"huge expressive sparkling anime eyes, two glowing white futuristic halo rings near ears, "
        f"black choker with silver ring, black strapless top with white geometric harness straps crossing chest, "
        f"vibrant neon cyberpunk lighting. She has a {mood}. "
        f"She stands prominently on the right side of the frame. "
        f"Background: futuristic cyberpunk trading room featuring {cat_context}. "
        f"Color palette: {scene_color}. "
        f"A glowing holographic sign reading 'Signal Hunters' appears in the background. "
        f"Left side has dark negative space for text overlay. "
        f"Style: high quality anime illustration, masterpiece, sharp focus, dramatic rim lighting, "
        f"vibrant neon glow, no watermark, no extra text in image."
    )

    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "16:9"}
    }

    resp = requests.post(api_url, json=payload, timeout=120)
    if resp.status_code == 200:
        data = resp.json()
        predictions = data.get("predictions", [])
        if predictions and "bytesBase64Encoded" in predictions[0]:
            return base64.b64decode(predictions[0]["bytesBase64Encoded"])
        else:
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
