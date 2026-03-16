#!/usr/bin/env python3
"""
Rewrite today's articles using the fixed rewrite_article() function.
Run: /home/shinyyume/.openclaw/venvs/crypto-tools/bin/python3 scripts/rewrite-today.py
"""
import sys, json, re, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Import needed functions from auto-web-post
import importlib.util
spec = importlib.util.spec_from_file_location(
    "auto_web_post",
    Path(__file__).parent / "auto-web-post.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

REPO_DIR = Path("/home/shinyyume/.openclaw/workspace/signal-hunters-web")
POSTS_FILE = REPO_DIR / "data" / "posts.json"

posts = json.load(open(POSTS_FILE))
today_posts = [p for p in posts if p.get("date") == "2026-03-16"]

print(f"Found {len(today_posts)} posts for 2026-03-16")

for i, post in enumerate(today_posts):
    print(f"\n{'='*60}")
    print(f"[{i+1}/{len(today_posts)}] Re-processing: {post['title'][:60]}")
    
    # Fetch fresh content from source
    print(f"  Fetching: {post['url']}")
    content_data = mod.fetch_article_content(post["url"])
    text = content_data.get("text", "")
    print(f"  Fetched {len(text)} chars of content")
    
    # Rewrite with Gemini
    source_name = "BlogTienAo"  # All are blogtienao today
    rewritten = mod.rewrite_article(post["title"], text, source_name, post["url"])
    
    # Categorize
    category = mod.categorize_article(rewritten["title"], rewritten["content"])
    
    # Validate
    stripped = re.sub(r'<[^>]+>', '', rewritten["content"])
    word_count = len(stripped.split())
    heading_count = len(re.findall(r'<h[23][^>]*>', rewritten["content"]))
    has_cta = "bingx.com" in rewritten["content"]
    title_ok = not (rewritten["title"].endswith("...") or rewritten["title"].endswith("…"))
    
    print(f"  Title: {rewritten['title']}")
    print(f"  Category: {category}")
    print(f"  Words: {word_count} | Headings: {heading_count} | CTA: {has_cta} | Title OK: {title_ok}")
    
    if word_count < 800:
        print(f"  ⚠️ WARNING: Only {word_count} words (min 800)")
    if heading_count < 3:
        print(f"  ⚠️ WARNING: Only {heading_count} headings (min 3)")
    if not has_cta:
        print(f"  ⚠️ WARNING: Missing BingX CTA")
    if not title_ok:
        print(f"  ⚠️ WARNING: Title ends with '...'")
    
    # Update post in-place
    post["title"] = rewritten["title"]
    post["summary"] = rewritten["summary"][:200]
    post["content"] = rewritten["content"]
    post["category"] = category
    
    # Re-slugify from new title
    post["slug"] = mod.slugify(rewritten["title"])
    
    if i < len(today_posts) - 1:
        print("  Sleeping 5s for rate limit...")
        time.sleep(5)

# Save updated posts
print(f"\n{'='*60}")
print("Saving posts.json...")
json_str = json.dumps(posts, ensure_ascii=False, indent=2)
with open(POSTS_FILE, 'w', encoding='utf-8') as f:
    f.write(json_str)
print("✅ posts.json saved")

# Quick summary
today_posts_after = [p for p in posts if p.get("date") == "2026-03-16"]
print(f"\n=== SUMMARY ===")
for p in today_posts_after:
    stripped = re.sub(r'<[^>]+>', '', p["content"])
    wc = len(stripped.split())
    hc = len(re.findall(r'<h[23][^>]*>', p["content"]))
    cta = "✅" if "bingx.com" in p["content"] else "❌"
    title_ok = "✅" if not p["title"].endswith("...") else "❌"
    print(f"  [{p['category']}] {p['title'][:55]}... | {wc}w {hc}h CTA={cta} Title={title_ok}")
