#!/usr/bin/env python3
"""
Signal Hunters — Facebook Auto-Post Script
==========================================
Tự động đăng bài mới từ web lên Facebook Page Signal Hunters.

Cách dùng:
    python3 scripts/facebook-auto-post.py

Cần thiết lập trước:
    1. Tạo file .env trong thư mục gốc với FB_PAGE_TOKEN và FB_PAGE_ID
    2. Xem .env.example để biết cách lấy token

Cron job (8h sáng hàng ngày):
    0 8 * * * cd /home/shinyyume/.openclaw/workspace/signal-hunters-web && python3 scripts/facebook-auto-post.py >> /tmp/fb-autopost.log 2>&1
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────────
ROOT_DIR   = Path(__file__).parent.parent
POSTS_FILE = ROOT_DIR / "data" / "posts.json"
POSTED_LOG = ROOT_DIR / "data" / "fb-posted.json"
ENV_FILE   = ROOT_DIR / ".env"

# ─── Config ──────────────────────────────────────────────────────────────────
# Base URL của website (không dấu slash cuối)
SITE_BASE_URL = "https://daututhongminh24h.com"
GRAPH_API_VERSION = "v19.0"

# Số giờ tối đa để coi bài là "mới" (default 48h)
MAX_AGE_HOURS = 48

# ─── Load .env ───────────────────────────────────────────────────────────────
def load_env(env_path: Path) -> dict:
    """Load key=value pairs from a .env file."""
    env = {}
    if not env_path.exists():
        return env
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip().strip('"').strip("'")
    return env


# ─── Posted Log ──────────────────────────────────────────────────────────────
def load_posted_log() -> set:
    """Return set of post IDs already posted to Facebook."""
    if not POSTED_LOG.exists():
        return set()
    try:
        data = json.loads(POSTED_LOG.read_text())
        return set(data if isinstance(data, list) else [])
    except Exception:
        return set()


def save_posted_log(posted: set) -> None:
    POSTED_LOG.write_text(json.dumps(sorted(posted), ensure_ascii=False, indent=2))


# ─── Helpers ─────────────────────────────────────────────────────────────────
def post_to_facebook(page_id: str, page_token: str, message: str, link: str | None = None) -> dict:
    """
    Post a message (+ optional link) to a Facebook Page.
    Returns the Graph API response dict.
    """
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}/feed"
    payload: dict = {"message": message, "access_token": page_token}
    if link:
        payload["link"] = link

    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Facebook API error {e.code}: {body}") from e


def build_post_message(post: dict) -> str:
    """Build the text body for a Facebook post — Identity: Thiên Kim."""
    title   = post.get("title", "")
    summary = post.get("summary") or post.get("excerpt") or ""
    category_map = {
        "analysis": "📊 Phân tích kỹ thuật", "phan-tich": "📊 Phân tích kỹ thuật",
        "news": "📰 Tin tức crypto",          "tin-tuc": "📰 Tin tức crypto",
        "commodity": "🏅 Hàng hóa",           "hang-hoa": "🏅 Hàng hóa",
        "altcoin": "🔷 Altcoin",
        "chinh-tri": "🏛️ Vĩ mô & Chính sách",
    }
    cat_label = category_map.get(post.get("category", ""), "💡 Đầu Tư Thông Minh")

    lines = [
        f"{cat_label}",
        f"",
        f"🔥 {title}",
        f"",
    ]
    if summary:
        # Trim to first 300 chars for readability
        short = summary[:300].rsplit(" ", 1)[0] + "..." if len(summary) > 300 else summary
        lines.append(short)
        lines.append("")

    lines += [
        "─────────────────────",
        "✨ Thiên Kim — Đầu Tư Thông Minh 24H",
        "👉 Đọc full bài phân tích tại link bên dưới nhé anh em~",
        "",
        "📌 Theo dõi để không bỏ lỡ tín hiệu quan trọng!",
        "",
        "#ThiênKim #Crypto #Bitcoin #DeFi #ĐầuTưThôngMinh #SignalHunters",
    ]
    return "\n".join(lines)


def build_post_url(post: dict) -> str:
    slug = post.get("slug") or post.get("id", "")
    return f"{SITE_BASE_URL}/{slug}.html"


def is_new_post(post: dict, max_age_hours: int = MAX_AGE_HOURS) -> bool:
    """Return True if post was published within max_age_hours."""
    date_str = post.get("date", "")
    if not date_str:
        return False
    try:
        # Support ISO format and date-only strings
        if "T" in date_str:
            pub = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            pub = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = datetime.now(tz=timezone.utc)
        return (now - pub) <= timedelta(hours=max_age_hours)
    except Exception:
        return True  # Unknown date → treat as new to be safe


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    now_str = datetime.now(tz=timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now_str}] 🚀 Facebook Auto-Post — Signal Hunters")

    # 1. Load .env
    env = load_env(ENV_FILE)
    # Also accept from environment
    FB_PAGE_TOKEN = env.get("FB_PAGE_TOKEN") or os.environ.get("FB_PAGE_TOKEN", "")
    FB_PAGE_ID    = env.get("FB_PAGE_ID")    or os.environ.get("FB_PAGE_ID", "")

    if not FB_PAGE_TOKEN or not FB_PAGE_ID:
        print("❌ Thiếu FB_PAGE_TOKEN hoặc FB_PAGE_ID!")
        print(f"   → Tạo file .env tại: {ENV_FILE}")
        print(f"   → Xem mẫu tại:       {ROOT_DIR / '.env.example'}")
        sys.exit(1)

    # 2. Load posts
    if not POSTS_FILE.exists():
        print(f"❌ Không tìm thấy file posts: {POSTS_FILE}")
        sys.exit(1)

    posts = json.loads(POSTS_FILE.read_text())
    if not isinstance(posts, list):
        print("❌ posts.json không hợp lệ (cần là array)")
        sys.exit(1)

    # Sort newest first
    posts.sort(key=lambda p: p.get("date", ""), reverse=True)

    # 3. Load posted log
    already_posted = load_posted_log()

    # 4. Find new posts to publish
    to_post = []
    for post in posts:
        pid = post.get("id") or post.get("slug", "")
        if not pid:
            continue
        if pid in already_posted:
            continue
        if not is_new_post(post, MAX_AGE_HOURS):
            print(f"   ⏭  Bỏ qua (quá cũ): {post.get('title', pid)[:60]}")
            continue
        to_post.append(post)

    if not to_post:
        print("ℹ️  Không có bài mới để đăng Facebook hôm nay.")
        return

    print(f"📋 Tìm thấy {len(to_post)} bài mới để đăng...")

    posted_count = 0
    failed_count = 0

    for post in to_post:
        pid   = post.get("id") or post.get("slug", "")
        title = post.get("title", pid)[:70]
        link  = build_post_url(post)
        msg   = build_post_message(post)

        print(f"\n   📝 Đang đăng: {title}")
        print(f"      Link: {link}")

        try:
            result = post_to_facebook(FB_PAGE_ID, FB_PAGE_TOKEN, msg, link)
            fb_post_id = result.get("id", "unknown")
            print(f"   ✅ Đăng thành công! FB post ID: {fb_post_id}")
            already_posted.add(pid)
            posted_count += 1
            # Respect rate limit: wait 3s between posts
            time.sleep(3)
        except Exception as e:
            print(f"   ❌ Lỗi khi đăng: {e}")
            failed_count += 1

    # 5. Save updated log
    save_posted_log(already_posted)

    print(f"\n🎉 Hoàn tất! Đã đăng {posted_count} bài, thất bại {failed_count} bài.")
    print(f"   Log được lưu tại: {POSTED_LOG}")


if __name__ == "__main__":
    main()
