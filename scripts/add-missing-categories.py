#!/usr/bin/env python3
"""
Bổ sung bài cho các category còn thiếu hôm nay.
Chạy: /home/shinyyume/.openclaw/venvs/crypto-tools/bin/python3 scripts/add-missing-categories.py
"""
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# === CONFIG (copy từ auto-web-post.py) ===
REPO_DIR = Path("/home/shinyyume/.openclaw/workspace/signal-hunters-web")
POSTS_FILE = REPO_DIR / "data" / "posts.json"
IMAGES_DIR = REPO_DIR / "images"
CONFIG_FILE = Path("/home/shinyyume/.openclaw/openclaw.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

BINGX_CTA_HTML = """<div class="cta-box" style="background:#1a1a2e;border:1px solid #16213e;border-radius:12px;padding:20px;margin-top:30px;">
<h3>💰 Tiết kiệm phí giao dịch crypto?</h3>
<p>Đăng ký BingX qua link dưới đây để được <strong>hoàn phí 45% VĨNH VIỄN</strong>:</p>
<p><a href="https://bingx.com/vi-vn/partner/X7EZVIWI" target="_blank" rel="noopener">👉 Đăng ký BingX ngay (Code: X7EZVIWI)</a></p>
</div>"""

SOURCES = [
    {"name": "Coin68", "url": "https://coin68.com/", "selector": "article a, .post-title a, h2 a, h3 a", "base": "https://coin68.com"},
    {"name": "BeInCrypto", "url": "https://vn.beincrypto.com/", "selector": "article a, .post-title a, h2 a, h3 a", "base": "https://vn.beincrypto.com"},
    {"name": "BlogTienAo", "url": "https://blogtienao.com/", "selector": "article a, .post-title a, h2 a, h3 a", "base": "https://blogtienao.com"},
]

# Extra sources for hang-hoa
SOURCES_HANGHOA = [
    {"name": "Investing.com", "url": "https://vn.investing.com/news/commodities-news", "selector": "article a, .articleItem a, h2 a, h3 a", "base": "https://vn.investing.com"},
    {"name": "Cafef", "url": "https://cafef.vn/thi-truong/hang-hoa.chn", "selector": "article a, h2 a, h3 a, .title a", "base": "https://cafef.vn"},
]

ALTCOIN_KEYWORDS = [
    "ethereum", " eth ", "eth,", "eth.", "xrp", "ripple", "solana", " sol ",
    "bnb", "cardano", "ada", "avalanche", "avax", "polkadot", "dot",
    "chainlink", "link", "polygon", "matic", "dogecoin", "doge",
    "shiba", "litecoin", "ltc", "tron", "trx", "cosmos", "atom",
    "near", "aptos", "apt", "sui", "pepe", "altcoin", "altseason",
    "ethereum classic", "etc", "uniswap", "uni", "aave", "defi", "layer 2", "layer2",
    "arbitrum", "arb", "op", "optimism", "base coin", "sei", "injective", "inj",
]

HANGHOA_KEYWORDS = [
    "vàng", "gold", "bạc", "silver", "dầu mỏ", "crude oil", "dầu wti", "brent",
    "khí đốt", "natural gas", "forex", "ngoại hối", "fed ", "lãi suất",
    "interest rate", "cpi", "lạm phát", "inflation", "gdp", "suy thoái", "recession",
    "dxy", "dollar index", "hàng hóa", "commodity", "commodities",
    "tỷ lệ thất nghiệp", "unemployment", "powell", "nonfarm",
    "giá vàng", "giá dầu", "giá bạc", "giá hàng hóa",
]

def slugify(text):
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace('đ', 'd').replace('Đ', 'D')
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text[:80]

def load_posts():
    if POSTS_FILE.exists():
        with open(POSTS_FILE) as f:
            return json.load(f)
    return []

def save_posts(posts):
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

def crawl_source(source):
    """Crawl headlines from a source."""
    articles = []
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            print(f"  ⚠️ {source['name']}: HTTP {resp.status_code}")
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select(source["selector"])
        seen = set()
        for a in links:
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if not href or not title or len(title) < 15:
                continue
            if any(x in href for x in ["/tag/", "/category/", "/author/", "#", "javascript:", "/page/"]):
                continue
            if not href.startswith("http"):
                href = source["base"] + href
            if href in seen:
                continue
            seen.add(href)
            articles.append({"title": title, "url": href, "source": source["name"]})
            if len(articles) >= 30:
                break
        print(f"  {source['name']}: {len(articles)} articles")
    except Exception as e:
        print(f"  ⚠️ {source['name']}: {e}")
    return articles

def fetch_article_content(url):
    """Fetch full text of an article."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            return {"text": "", "image": None, "publish_date": None}
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove script/style
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        # Try article body
        body = soup.select_one("article") or soup.select_one(".post-content") or soup.select_one(".entry-content") or soup.select_one("main")
        if body:
            text = body.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)
        # Clean up
        lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 20]
        text = "\n\n".join(lines[:50])
        # Try to get image
        og_img = soup.find("meta", property="og:image")
        image = og_img["content"] if og_img else None
        # Try date
        pub_date = None
        for meta_name in ["article:published_time", "datePublished", "pubdate"]:
            m = soup.find("meta", {"property": meta_name}) or soup.find("meta", {"name": meta_name}) or soup.find("meta", {"itemprop": meta_name})
            if m and m.get("content"):
                try:
                    from dateutil import parser as dparser
                    pub_date = dparser.parse(m["content"])
                    break
                except:
                    pass
        # Also try time tag
        if not pub_date:
            t = soup.find("time")
            if t and t.get("datetime"):
                try:
                    from dateutil import parser as dparser
                    pub_date = dparser.parse(t["datetime"])
                except:
                    pass
        return {"text": text[:4000], "image": image, "publish_date": pub_date}
    except Exception as e:
        print(f"    ⚠️ Fetch error: {e}")
        return {"text": "", "image": None, "publish_date": None}

def rewrite_article(title, content, source_name, source_url, category_hint=""):
    """Use Gemini to rewrite the article."""
    import time
    try:
        cfg = json.load(open(CONFIG_FILE))
        api_key = cfg['models']['providers']['google']['apiKey']
    except Exception as e:
        print(f"    ⚠️ Cannot load API key: {e}")
        api_key = None

    content_trimmed = content[:4000].strip() if content else ""

    if api_key and content_trimmed:
        prompt = f"""Viết lại bài báo sau thành bài viết chuyên nghiệp bằng tiếng Việt, dài 1000-2000 từ.

YÊU CẦU:
- Viết lại HOÀN TOÀN bằng ngôn ngữ của mình, KHÔNG copy paste
- Tiêu đề hấp dẫn, đầy đủ (KHÔNG cắt ngắn, KHÔNG dấu "...")
- Mở bài thu hút, giới thiệu vấn đề
- Thân bài chia thành 3-4 heading (<h2>), mỗi phần phân tích sâu
- Đưa số liệu cụ thể nếu có
- Kết bài có nhận định riêng
- Giọng văn: chuyên nghiệp nhưng dễ hiểu, phong cách nhà phân tích

THÔNG TIN GỐC:
Tiêu đề: {title}
Nguồn: {source_name} - {source_url}
Nội dung gốc:
{content_trimmed}

TRẢ VỀ JSON (chỉ JSON, không markdown):
{{"title": "tiêu đề mới đầy đủ", "summary": "tóm tắt 2-3 câu", "content": "nội dung HTML đầy đủ (dùng <h2>, <p>, <strong>, <ul><li>)"}}"""

        for model in ["gemini-2.5-flash", "gemini-2.0-flash-exp", "gemini-1.5-flash"]:
            try:
                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192}
                }
                resp = requests.post(api_url, json=payload, timeout=90)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text, flags=re.MULTILINE)
                    raw_text = re.sub(r'\s*```$', '', raw_text, flags=re.MULTILINE)
                    raw_text = raw_text.strip()

                    new_title = title
                    new_summary = ""
                    new_content = ""
                    try:
                        result = json.loads(raw_text)
                        new_title = result.get("title", title).strip()
                        new_summary = result.get("summary", "").strip()
                        new_content = result.get("content", "").strip()
                    except json.JSONDecodeError:
                        title_m = re.search(r'"title"\s*:\s*"([^"]+)"', raw_text)
                        summary_m = re.search(r'"summary"\s*:\s*"([^"]+)"', raw_text)
                        content_m = re.search(r'"content"\s*:\s*"(.*?)"\s*\}', raw_text, re.DOTALL)
                        if not content_m:
                            content_m2 = re.search(r'"content"\s*:\s*"(.*)', raw_text, re.DOTALL)
                            if content_m2:
                                raw_content = content_m2.group(1)
                                raw_content = re.sub(r'"\s*\}\s*$', '', raw_content).strip()
                                new_content = raw_content.replace('\\"', '"').replace('\\n', '\n')
                        else:
                            new_content = content_m.group(1).replace('\\"', '"').replace('\\n', '\n')
                        if title_m:
                            new_title = title_m.group(1).strip()
                        if summary_m:
                            new_summary = summary_m.group(1).strip()
                        if len(new_content) < 500:
                            html_m = re.search(r'(<(?:h2|h3|p|ul|li|strong|div)[^>]*>.*)', raw_text, re.DOTALL)
                            if html_m:
                                new_content = html_m.group(1)
                                new_content = re.sub(r'"\s*\}\s*$', '', new_content).strip()

                    if new_title.endswith("...") or new_title.endswith("…"):
                        new_title = new_title.rstrip(".…").strip()

                    new_content = new_content + "\n" + BINGX_CTA_HTML

                    stripped = re.sub(r'<[^>]+>', '', new_content)
                    word_count = len(stripped.split())
                    heading_count = len(re.findall(r'<h[23][^>]*>', new_content))
                    has_cta = "bingx.com" in new_content

                    print(f"    ✅ Gemini ({model}): {word_count} words, {heading_count} headings")
                    if word_count >= 500 and heading_count >= 2 and has_cta:
                        return {"title": new_title, "summary": new_summary[:300], "content": new_content}
                    else:
                        print(f"    ⚠️ Quality low, retrying...")
                        time.sleep(3)
                        continue
                elif resp.status_code == 429:
                    print(f"    ⚠️ Rate limit, waiting 15s...")
                    time.sleep(15)
                else:
                    print(f"    ⚠️ HTTP {resp.status_code}: {resp.text[:100]}")
            except Exception as e:
                print(f"    ⚠️ Error: {e}")
            time.sleep(2)

    # Fallback
    print(f"    ⚠️ Using fallback rewrite")
    clean_title = title.rstrip(".…").strip()
    first_para = content_trimmed.split("\n\n")[0] if content_trimmed else title
    summary = first_para[:250].strip().rstrip('.') + '.'
    body_html = f"""<p>{first_para[:500]}</p>
<h2>Diễn biến thị trường</h2>
<p>{content_trimmed[500:1200] if len(content_trimmed) > 500 else content_trimmed}</p>
<h2>Phân tích và nhận định</h2>
<p>Thông tin trên có thể tác động đáng kể đến tâm lý nhà đầu tư trong ngắn hạn. Các chuyên gia khuyến nghị theo dõi sát diễn biến tiếp theo trước khi đưa ra quyết định giao dịch.</p>
<h2>Kết luận</h2>
<p>Đây là tin tức quan trọng cần theo dõi. Nhà đầu tư nên cập nhật liên tục để nắm bắt cơ hội và hạn chế rủi ro.</p>
""" + BINGX_CTA_HTML
    return {"title": clean_title, "summary": summary[:300], "content": body_html}

def find_articles_for_category(category, all_articles, existing_titles):
    """Find articles matching a category from the pool."""
    kw_map = {
        "altcoin": ALTCOIN_KEYWORDS,
        "hang-hoa": HANGHOA_KEYWORDS,
    }
    keywords = kw_map.get(category, [])
    candidates = []
    for art in all_articles:
        title_lower = " " + art["title"].lower() + " "
        if any(kw in title_lower for kw in keywords):
            # Check not duplicate with existing
            is_dup = any(
                len(set(art["title"].lower().split()) & set(et.lower().split())) / max(len(art["title"].split()), 1) > 0.6
                for et in existing_titles
            )
            if not is_dup:
                candidates.append(art)
    return candidates

def generate_simple_thumbnail(title, slug):
    """Try to generate thumbnail, fallback to default."""
    try:
        cfg = json.load(open(CONFIG_FILE))
        api_key = cfg['models']['providers']['google']['apiKey']
    except:
        return "images/og-banner.jpg"

    # Use Imagen via Gemini for image gen if available, else skip
    # For now just return default (image gen requires separate quota)
    return "images/og-banner.jpg"

def deploy():
    """Run deploy.sh."""
    deploy_script = REPO_DIR / "scripts" / "deploy.sh"
    if deploy_script.exists():
        import subprocess
        result = subprocess.run(
            ["bash", str(deploy_script)],
            cwd=str(REPO_DIR),
            capture_output=True, text=True, timeout=120
        )
        print(result.stdout[-2000:] if result.stdout else "")
        if result.stderr:
            print("STDERR:", result.stderr[-500:])
        print(f"Deploy exit code: {result.returncode}")
        return result.returncode == 0
    else:
        print("⚠️ deploy.sh not found")
        return False

def git_push(count):
    """Git commit and push."""
    import subprocess
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        subprocess.run(["git", "add", "-A"], cwd=str(REPO_DIR), check=True, capture_output=True)
        msg = f"feat: bổ sung {count} bài còn thiếu category ({today})"
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=str(REPO_DIR), capture_output=True, text=True
        )
        print(result.stdout)
        if "nothing to commit" in result.stdout:
            print("Nothing to commit.")
            return True
        push = subprocess.run(["git", "push"], cwd=str(REPO_DIR), capture_output=True, text=True)
        print(push.stdout)
        if push.returncode == 0:
            print("✅ Git push OK")
            return True
        else:
            print(f"⚠️ Git push failed: {push.stderr}")
            return False
    except Exception as e:
        print(f"⚠️ Git error: {e}")
        return False


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"=== Bổ sung bài thiếu category — {today} ===")

    # Load existing posts
    posts = load_posts()
    existing_titles = [p["title"] for p in posts]
    today_posts = [p for p in posts if p.get("date") == today]
    today_cats = set(p.get("category") for p in today_posts)

    REQUIRED_CATEGORIES = ["altcoin", "hang-hoa"]
    missing = [c for c in REQUIRED_CATEGORIES if c not in today_cats]

    if not missing:
        print(f"✅ Đã có đủ category hôm nay: {today_cats}")
        return

    print(f"📋 Hôm nay có {len(today_posts)} bài, thiếu: {missing}")

    # Crawl all sources
    print("\n📡 Crawling sources...")
    all_articles = []
    for source in SOURCES:
        articles = crawl_source(source)
        all_articles.extend(articles)
    # Also crawl hang-hoa specific sources if needed
    if "hang-hoa" in missing:
        for source in SOURCES_HANGHOA:
            articles = crawl_source(source)
            all_articles.extend(articles)

    print(f"Total crawled: {len(all_articles)}")

    # Process each missing category
    published = 0
    ts_id = datetime.now().strftime("%Y%m%d%H%M%S")
    now_utc = datetime.now(timezone.utc)
    cutoff_24h = now_utc - timedelta(hours=36)  # Slightly relaxed for supplement run

    for cat in missing:
        print(f"\n🎯 Tìm bài cho category: [{cat}]")
        candidates = find_articles_for_category(cat, all_articles, existing_titles + [p["title"] for p in posts])

        if not candidates:
            print(f"  ⚠️ Không tìm được bài phù hợp cho [{cat}] từ keyword matching")
            # Try broader search
            print(f"  🔍 Thử tìm bài bất kỳ cho [{cat}]...")
            # For altcoin: any crypto article that's not BTC
            # For hang-hoa: try direct url
            if cat == "hang-hoa":
                # Try direct gold/commodity crawl
                extra_urls = [
                    "https://vn.investing.com/news/commodities-news",
                    "https://cafef.vn/thi-truong/hang-hoa.chn",
                ]
                for url in extra_urls:
                    try:
                        resp = requests.get(url, headers=HEADERS, timeout=20)
                        soup = BeautifulSoup(resp.text, "html.parser")
                        for a in soup.find_all("a", href=True):
                            title = a.get_text(strip=True)
                            href = a["href"]
                            if len(title) < 15:
                                continue
                            if any(kw in title.lower() for kw in ["vàng", "gold", "dầu", "oil", "bạc", "silver", "hàng hóa"]):
                                if not href.startswith("http"):
                                    from urllib.parse import urlparse
                                    base = urlparse(url).scheme + "://" + urlparse(url).netloc
                                    href = base + href
                                candidates.append({"title": title, "url": href, "source": "Investing.com"})
                                if len(candidates) >= 5:
                                    break
                    except Exception as e:
                        print(f"  ⚠️ Extra crawl error: {e}")
                    if candidates:
                        break
            elif cat == "altcoin":
                # Find any article with ETH/XRP/SOL/altcoin in broader pool
                for art in all_articles:
                    tl = art["title"].lower()
                    if any(kw in tl for kw in ["eth", "sol", "xrp", "bnb", "ada", "doge", "defi", "altcoin", "layer"]):
                        candidates.append(art)
                        if len(candidates) >= 5:
                            break

        if not candidates:
            print(f"  ❌ Không thể tìm bài cho [{cat}] — bỏ qua")
            continue

        art = candidates[0]
        print(f"  📰 Chọn bài: {art['title'][:80]}")

        # Fetch content
        content_data = fetch_article_content(art["url"])

        # Check freshness (relaxed: 36h)
        pub_date = content_data.get("publish_date")
        if pub_date is not None:
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            if pub_date < cutoff_24h:
                age_h = (now_utc - pub_date).total_seconds() / 3600
                print(f"  ⚠️ Bài cũ ({age_h:.1f}h) nhưng vẫn dùng để bổ sung category")
        else:
            print(f"  ⚠️ Không xác định được ngày — vẫn dùng để bổ sung")

        # Rewrite
        print(f"  ✍️ Rewriting với Gemini...")
        rewritten = rewrite_article(art["title"], content_data.get("text", ""), art["source"], art["url"], cat)

        # Generate post
        slug = slugify(rewritten["title"])
        post_id = slug if slug else f"{ts_id}-{cat}"
        existing_ids = {p.get("id") for p in posts}
        if post_id in existing_ids:
            post_id = f"{slug}-{ts_id}"

        post = {
            "id": post_id,
            "title": rewritten["title"],
            "summary": rewritten["summary"][:200],
            "content": rewritten["content"],
            "category": cat,
            "image": "images/og-banner.jpg",
            "date": today,
            "url": art["url"],
            "slug": slug,
        }

        posts.insert(0, post)
        existing_titles.append(rewritten["title"])
        published += 1
        print(f"  ✅ Thêm [{cat}]: {rewritten['title'][:70]}")

        import time
        time.sleep(2)

    if published == 0:
        print("\n❌ Không thêm được bài nào mới.")
        return

    # Save
    save_posts(posts)
    print(f"\n💾 Saved {published} bài mới (total: {len(posts)})")

    # Deploy
    print("\n🚀 Deploying...")
    deploy_ok = deploy()

    # Git push
    print("\n📦 Git push...")
    git_ok = git_push(published)

    print(f"\n{'✅' if deploy_ok and git_ok else '⚠️'} DONE: {published} bài mới, deploy={'OK' if deploy_ok else 'FAIL'}, git={'OK' if git_ok else 'FAIL'}")


if __name__ == "__main__":
    main()
