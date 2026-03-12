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
MAX_ARTICLES = 5
MIN_TITLE_LEN = 15
SIMILARITY_THRESHOLD = 0.7

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


def rewrite_article(title: str, content: str, source_name: str, source_url: str) -> dict:
    """Rewrite article content for the website."""
    # Clean and structure content
    if not content or len(content) < 100:
        # Short article - create summary style
        summary = f"Theo nguồn tin từ {source_name}, {title.lower()}."
        body = f"""## {title}

{summary}

Đây là một trong những tin tức đáng chú ý trong ngày hôm nay trên thị trường crypto. Các nhà đầu tư cần theo dõi sát diễn biến tiếp theo để đưa ra quyết định giao dịch phù hợp.

### Tác động đến thị trường

Thông tin này có thể ảnh hưởng đến tâm lý thị trường trong ngắn hạn. Traders nên:
- Theo dõi phản ứng giá của BTC và các altcoin liên quan
- Cập nhật thêm thông tin từ các nguồn uy tín
- Quản lý rủi ro chặt chẽ trong giai đoạn biến động

*Nguồn: [{source_name}]({source_url})*
{BINGX_CTA}"""
    else:
        # Has content - rewrite
        # Take first 800 chars of content as body
        content_trimmed = content[:2000]
        
        # Create summary from first paragraph
        first_para = content.split("\n\n")[0] if "\n\n" in content else content[:200]
        summary = first_para[:200].strip()
        if not summary.endswith('.'):
            summary = summary.rsplit(' ', 1)[0] + '...'
        
        body = f"""## {title}

{content_trimmed}

### Nhận định

Thông tin trên cho thấy thị trường crypto đang có nhiều biến động. Nhà đầu tư cần cân nhắc kỹ trước khi đưa ra quyết định giao dịch.

*Nguồn: [{source_name}]({source_url})*
{BINGX_CTA}"""
    
    return {
        "title": title,
        "summary": summary if 'summary' in dir() else title,
        "content": body,
    }


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
    
    # No daily dedup — chạy nhiều lần/ngày, dedup theo title bài
    DEDUP_FILE.parent.mkdir(parents=True, exist_ok=True)
    
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
    
    # Filter: dedup + quality
    new_articles = []
    for art in all_articles:
        if is_duplicate(art["title"], existing_titles + [a["title"] for a in new_articles]):
            continue
        new_articles.append(art)
        if len(new_articles) >= MAX_ARTICLES:
            break
    
    print(f"After dedup: {new_articles.__len__()} new articles")
    
    if not new_articles:
        print("Không có bài mới. Done.")
        DEDUP_FILE.write_text(today)
        return
    
    # Process each article
    published = 0
    next_id = max([p.get("id", 0) for p in posts], default=0) + 1 if posts else 1
    
    for art in new_articles:
        print(f"\n📝 Processing: {art['title'][:60]}...")
        
        # Fetch full content
        content_data = fetch_article_content(art["url"])
        
        # Rewrite
        rewritten = rewrite_article(art["title"], content_data["text"], art["source"], art["url"])
        
        # Download image
        slug = slugify(art["title"])
        image_path = download_image(content_data["image"], slug)
        
        # Create post entry
        post = {
            "id": next_id,
            "title": rewritten["title"],
            "summary": rewritten["summary"][:200],
            "content": rewritten["content"],
            "category": "tin-tuc",
            "image": image_path,
            "date": today,
            "url": art["url"],
            "slug": slug
        }
        
        # Insert at beginning (newest first)
        posts.insert(0, post)
        next_id += 1
        published += 1
        print(f"  ✅ Added: {slug}")
    
    # Save
    save_posts(posts)
    print(f"\n💾 Saved {published} new posts (total: {len(posts)})")
    
    # Deploy
    print("\n🚀 Deploying...")
    deploy()
    
    # Git
    print("\n📦 Git push...")
    git_push(published)
    
    print(f"\n✅ DONE: Published {published} bài mới lên daututhongminh24h.com")


if __name__ == "__main__":
    main()
