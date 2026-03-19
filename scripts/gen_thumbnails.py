#!/usr/bin/env python3
"""Generate AI thumbnails for posts missing custom images."""

import json
import requests
import base64
import time
import os
import sys

REPO_DIR = "/home/shinyyume/.openclaw/workspace/signal-hunters-web"
POSTS_FILE = os.path.join(REPO_DIR, "data/posts.json")
IMAGES_DIR = os.path.join(REPO_DIR, "images")

# Load API key
cfg = json.load(open("/home/shinyyume/.openclaw/openclaw.json"))
api_key = cfg["models"]["providers"]["google"]["apiKey"]

API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/nano-banana-pro-preview:generateContent?key={api_key}"
)

STYLE = (
    "Digital art, futuristic crypto news illustration, "
    "dark background with neon accents, cinematic 16:9 ratio, "
    "high quality, professional financial tech aesthetic, no text, no watermarks"
)


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


def build_prompt(title: str) -> str:
    """Alias for build_image_prompt."""
    return build_image_prompt(title)

def generate_image(prompt: str, output_path: str, retries: int = 3) -> bool:
    """Call Gemini API to generate and save an image."""
    payload = {
        "contents": [{"parts": [{"text": f"Generate an image: {prompt}"}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }

    for attempt in range(retries):
        try:
            resp = requests.post(API_URL, json=payload, timeout=60)
            if resp.status_code == 429:
                wait = 15 * (attempt + 1)
                print(f"  [RATE LIMIT] Sleeping {wait}s...")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()

            for c in data.get("candidates", []):
                for part in c.get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        img_bytes = base64.b64decode(part["inlineData"]["data"])
                        with open(output_path, "wb") as f:
                            f.write(img_bytes)
                        return True

            # No image in response
            print(f"  [WARN] No image in response. Response keys: {list(data.keys())}")
            if attempt < retries - 1:
                time.sleep(5)

        except requests.exceptions.Timeout:
            print(f"  [TIMEOUT] Attempt {attempt + 1}/{retries}")
            if attempt < retries - 1:
                time.sleep(10)
        except Exception as e:
            print(f"  [ERROR] {e}")
            if attempt < retries - 1:
                time.sleep(5)

    return False


def main():
    with open(POSTS_FILE) as f:
        posts = json.load(f)

    # Find posts missing thumbnails
    to_process = [p for p in posts if p.get("image") == "images/og-banner.jpg"]
    print(f"Found {len(to_process)} posts without thumbnails")

    updated = 0
    failed = 0

    for i, post in enumerate(to_process[:10]):  # max 10
        slug = post["slug"]
        title = post["title"]
        img_filename = f"post-{slug[:50]}.png"
        img_rel_path = f"images/{img_filename}"
        img_abs_path = os.path.join(IMAGES_DIR, img_filename)

        print(f"\n[{i+1}/{min(len(to_process), 10)}] Generating: {title[:70]}")
        prompt = build_prompt(title)
        print(f"  Prompt: {prompt[:100]}...")

        success = generate_image(prompt, img_abs_path)

        if success:
            print(f"  ✅ Created thumbnail for: {title[:60]}")
            # Update the post's image field
            for p in posts:
                if p["id"] == post["id"]:
                    p["image"] = img_rel_path
                    break
            updated += 1
        else:
            print(f"  ❌ Failed for: {title[:60]} — skipping")
            failed += 1

        # Rate limit: sleep between requests
        if i < min(len(to_process), 10) - 1:
            print("  Sleeping 5s before next request...")
            time.sleep(5)

    # Save updated posts.json
    if updated > 0:
        with open(POSTS_FILE, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Saved posts.json — {updated} updated, {failed} failed")
    else:
        print(f"\n⚠️ No posts updated ({failed} failed)")

    return updated, failed


if __name__ == "__main__":
    updated, failed = main()
    sys.exit(0 if updated > 0 else 1)
