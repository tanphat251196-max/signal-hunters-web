#!/usr/bin/env python3
"""
Normalize article categories from mixed formats to 5 standard categories:
- tin-tuc (news)
- phan-tich (analysis)
- altcoin
- hang-hoa (commodities)
- chinh-tri (politics)
"""

import json
import sys
from pathlib import Path

# Mapping old categories to new ones
CATEGORY_MAP = {
    "news": "tin-tuc",
    "tin-tuc": "tin-tuc",
    "analysis": "phan-tich",
    "phan-tich": "phan-tich",
    "altcoin": "altcoin",
    "commodity": "hang-hoa",
    "hang-hoa": "hang-hoa",
    "politics": "chinh-tri",
    "chinh-tri": "chinh-tri",
}

VALID_CATEGORIES = {"tin-tuc", "phan-tich", "altcoin", "hang-hoa", "chinh-tri"}


def normalize_categories(posts_file):
    """Normalize all posts to valid categories."""
    with open(posts_file, 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    changed = 0
    invalid = []
    
    for idx, post in enumerate(posts):
        if not isinstance(post, dict):
            print(f"⚠️  Post {idx} is not a dict: {type(post)}")
            continue
        
        old_cat = post.get("category", "tin-tuc")
        new_cat = CATEGORY_MAP.get(old_cat, "tin-tuc")
        
        post_id = post.get("id", f"post_{idx}")
        if old_cat != new_cat:
            print(f"  [{post_id[:30]}...] {old_cat} → {new_cat}")
            post["category"] = new_cat
            changed += 1
        
        if post["category"] not in VALID_CATEGORIES:
            invalid.append(post_id)
    
    # Save back
    with open(posts_file, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Normalized {changed} posts")
    if invalid:
        print(f"⚠️  {len(invalid)} posts still have invalid categories")
    
    return posts


if __name__ == "__main__":
    posts_file = Path(__file__).parent.parent / "data" / "posts.json"
    print(f"Normalizing categories from {posts_file}")
    posts = normalize_categories(str(posts_file))
    
    # Summary
    stats = {}
    for p in posts:
        cat = p.get("category", "unknown")
        stats[cat] = stats.get(cat, 0) + 1
    
    print("\n📊 Final category distribution:")
    for cat in sorted(VALID_CATEGORIES):
        count = stats.get(cat, 0)
        print(f"  {cat}: {count}")
    print(f"  Total: {sum(stats.values())}")
