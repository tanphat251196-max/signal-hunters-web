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


def build_prompt(title: str) -> str:
    """Build an image generation prompt based on the post title."""
    title_lower = title.lower()

    details = ""

    if "bitcoin" in title_lower or "btc" in title_lower:
        details = "featuring a glowing golden Bitcoin coin with circuit patterns, price chart uptrend, neon blue/orange glow"
    if "ethereum" in title_lower or "eth" in title_lower:
        details = "featuring a shimmering diamond Ethereum crystal, blue-purple neon energy, futuristic blockchain nodes"
    if "xrp" in title_lower or "ripple" in title_lower:
        details = "featuring XRP wave token in blue neon light, global payment network visualization, interconnected nodes"
    if "binance" in title_lower or "bnb" in title_lower:
        details = "featuring Binance gold logo, trading platform interface, yellow neon glow, data streams"
    if "iran" in title_lower or "war" in title_lower or "chiến tranh" in title_lower:
        details = "featuring a geopolitical globe with tension lines, oil barrels, financial market volatility"
    if "trump" in title_lower:
        details = "featuring US flag, political podium silhouette, cryptocurrency chart impact, dramatic lighting"
    if "ai agent" in title_lower or "ai" in title_lower:
        details = "featuring AI robot trading agent, neural network connections, holographic crypto trading terminal"
    if "privacy" in title_lower or "tornado" in title_lower or "privacy coin" in title_lower:
        details = "featuring encrypted digital shield, privacy lock symbol, code matrix flowing through dark space"
    if "cryptoquant" in title_lower or "sàn" in title_lower or "exchange" in title_lower:
        details = "featuring multiple cryptocurrency exchange logos, transparency chart, ranking leaderboard visualization"
    if "phục hồi" in title_lower or "tăng" in title_lower or "recovery" in title_lower:
        details = "featuring green upward price arrows, bull market energy, rising crypto charts with neon glow"

    # fallback
    if not details:
        details = "featuring cryptocurrency coins, blockchain network, financial data streams, neon cyberpunk cityscape"

    return f"{STYLE}, {details}"


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
