#!/usr/bin/env python3
"""
Retry rewrite for articles that failed due to JSON parse errors.
"""
import sys, json, re, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

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

# Find the 2 posts that are still short (< 800 words, today's date)
failed_ids = []
for p in posts:
    if p.get("date") == "2026-03-16":
        stripped = re.sub(r'<[^>]+>', '', p["content"])
        wc = len(stripped.split())
        if wc < 800:
            failed_ids.append(p["id"])
            print(f"Need retry: id={p['id']} words={wc} title={p['title'][:60]}")

if not failed_ids:
    print("All articles already have >= 800 words! Nothing to retry.")
    sys.exit(0)

for i, post_id in enumerate(failed_ids):
    post = next(p for p in posts if p["id"] == post_id)
    print(f"\n{'='*60}")
    print(f"Retrying id={post_id}: {post['title'][:60]}")
    
    print(f"  Fetching: {post['url']}")
    content_data = mod.fetch_article_content(post["url"])
    text = content_data.get("text", "")
    print(f"  Fetched {len(text)} chars")
    
    rewritten = mod.rewrite_article(post["title"], text, "BlogTienAo", post["url"])
    category = mod.categorize_article(rewritten["title"], rewritten["content"])
    
    stripped = re.sub(r'<[^>]+>', '', rewritten["content"])
    wc = len(stripped.split())
    hc = len(re.findall(r'<h[23][^>]*>', rewritten["content"]))
    has_cta = "bingx.com" in rewritten["content"]
    title_ok = not (rewritten["title"].endswith("...") or rewritten["title"].endswith("…"))
    
    print(f"  Title: {rewritten['title']}")
    print(f"  Category: {category} | Words: {wc} | Headings: {hc} | CTA: {has_cta} | Title OK: {title_ok}")
    
    if wc >= 800 and hc >= 3 and has_cta:
        print(f"  ✅ Quality OK!")
    else:
        print(f"  ⚠️ Still below quality — keeping best available")
    
    post["title"] = rewritten["title"]
    post["summary"] = rewritten["summary"][:200]
    post["content"] = rewritten["content"]
    post["category"] = category
    post["slug"] = mod.slugify(rewritten["title"])
    
    if i < len(failed_ids) - 1:
        print("  Sleeping 8s...")
        time.sleep(8)

print(f"\nSaving posts.json...")
with open(POSTS_FILE, 'w', encoding='utf-8') as f:
    json.dump(posts, f, ensure_ascii=False, indent=2)
print("✅ Saved")

# Final summary
today_posts = [p for p in posts if p.get("date") == "2026-03-16"]
print(f"\n=== FINAL SUMMARY ===")
for p in today_posts:
    stripped = re.sub(r'<[^>]+>', '', p["content"])
    wc = len(stripped.split())
    hc = len(re.findall(r'<h[23][^>]*>', p["content"]))
    cta = "✅" if "bingx.com" in p["content"] else "❌"
    title_ok = "✅" if not (p["title"].endswith("...") or p["title"].endswith("…")) else "❌"
    ok = "✅" if wc >= 800 and hc >= 3 and "bingx.com" in p["content"] else "⚠️"
    print(f"  {ok} [{p['category']}] {p['title'][:55]} | {wc}w {hc}h CTA={cta} Title={title_ok}")
