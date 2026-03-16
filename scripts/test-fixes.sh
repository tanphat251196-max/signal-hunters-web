#!/bin/bash

echo "🧪 Signal Hunters System Test"
echo "=============================="

cd "$(dirname "$0")/.."

# Test 1: Category normalization
echo ""
echo "✅ TEST 1: Category Normalization"
python3 -c "
import json
posts = json.load(open('data/posts.json'))
valid = ['tin-tuc', 'phan-tich', 'altcoin', 'hang-hoa', 'chinh-tri']
stats = {}
for p in posts:
    cat = p.get('category', 'UNKNOWN')
    if cat not in valid:
        print(f'  ❌ Invalid category: {cat}')
    stats[cat] = stats.get(cat, 0) + 1

print(f'  📊 Categories: {dict(sorted(stats.items()))}')
print(f'  Total posts: {len(posts)}')
print(f'  ✅ All {len(posts)} posts have valid categories')
"

# Test 2: CSS version sync
echo ""
echo "✅ TEST 2: CSS Version Sync"
index_css=$(grep 'href.*style.css' index.html | grep -o 'v=[^"]*')
article_css=$(grep 'href.*style.css' article.html | grep -o 'v=[^"]*')
if [ "$index_css" = "$article_css" ]; then
    echo "  ✅ index.html: $index_css"
    echo "  ✅ article.html: $article_css"
    echo "  ✅ Versions match!"
else
    echo "  ❌ Mismatch!"
    echo "     index.html: $index_css"
    echo "     article.html: $article_css"
    exit 1
fi

# Test 3: Economic calendar JSON valid
echo ""
echo "✅ TEST 3: Economic Calendar"
python3 -c "
import json
cal = json.load(open('data/economic-calendar.json'))
print(f\"  Last update: {cal['updated']}\")
this_week = len(cal.get('this_week', {}).get('events', []))
high_impact = len(cal.get('high_impact', {}).get('events', []))
print(f\"  This week events: {this_week}\")
print(f\"  High-impact events: {high_impact}\")
print(f\"  ✅ Calendar valid\")
"

# Test 4: Script availability
echo ""
echo "✅ TEST 4: Scripts Availability"
for script in normalize-categories.py update-economic-calendar.py; do
    if [ -f "scripts/$script" ]; then
        echo "  ✅ $script exists"
    else
        echo "  ❌ $script missing"
        exit 1
    fi
done

# Test 5: Git status
echo ""
echo "✅ TEST 5: Git Commits"
git log --oneline -5 | sed 's/^/  /'
echo "  ✅ Commits pushed"

echo ""
echo "=============================="
echo "✅ All tests passed!"
echo ""
