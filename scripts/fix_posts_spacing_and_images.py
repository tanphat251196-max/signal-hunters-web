#!/usr/bin/env python3
import base64
import io
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from PIL import Image

ROOT = Path('/home/shinyyume/.openclaw/workspace/signal-hunters-web')
POSTS_PATH = ROOT / 'data' / 'posts.json'
IMAGES_DIR = ROOT / 'images' / 'posts'
CONFIG_PATH = Path('/home/shinyyume/.openclaw/openclaw.json')
API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent'


def strip_html(text: str) -> str:
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
    text = re.sub(r'</p\s*>', '\n\n', text, flags=re.I)
    text = re.sub(r'</h[1-6]\s*>', '\n\n', text, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def normalize_markdown(content: str) -> str:
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    lines = content.split('\n')
    out = []
    prev_blank = True
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        if not line:
            if not prev_blank:
                out.append('')
            prev_blank = True
            i += 1
            continue

        is_heading = line.startswith('## ')
        if is_heading:
            if out and out[-1] != '':
                out.append('')
            out.append(line)
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                out.append('')
            prev_blank = False if not out or out[-1] != '' else True
            i += 1
            continue

        out.append(line)
        # add paragraph spacing if next non-empty line is normal text
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines):
            next_line = lines[j].strip()
            out.append('')
            if next_line.startswith('## ') and out[-2] != '':
                pass
        prev_blank = False
        i += 1

    text = '\n'.join(out)
    text = re.sub(r'(?<!\n)\n(##\s+)', r'\n\n\1', text)
    text = re.sub(r'(## .+)\n(?!\n)', r'\1\n\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def normalize_html(content: str) -> str:
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    content = re.sub(r'>\s*<', '><', content)
    content = re.sub(r'(?i)</p>\s*<p>', '</p>\n\n<p>', content)
    content = re.sub(r'(?i)</h2>\s*<p>', '</h2>\n\n<p>', content)
    content = re.sub(r'(?i)</p>\s*<h2>', '</p>\n\n<h2>', content)
    content = re.sub(r'(?i)</h2>\s*<h2>', '</h2>\n\n<h2>', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def normalize_content(content: str) -> str:
    if '<p' in content.lower() or '<h2' in content.lower():
        return normalize_html(content)
    return normalize_markdown(content)


def build_prompt(title: str, content: str) -> str:
    plain = strip_html(content)
    plain = plain.replace('#', ' ')
    plain = re.sub(r'\s+', ' ', plain).strip()
    summary = plain[:900]
    return (
        'Create a news illustration directly related to this crypto/finance article. '
        'Style: cyberpunk futuristic, vibrant neon lighting, cinematic, high detail, dramatic depth, '
        'NO TEXT, NO WORDS, NO LETTERS, NO LOGOS. '
        f'Title: {title}. '
        f'Article context: {summary}'
    )


def extract_image_b64(resp_json: dict):
    for cand in resp_json.get('candidates', []):
        parts = cand.get('content', {}).get('parts', [])
        for part in parts:
            inline = part.get('inlineData') or {}
            data = inline.get('data')
            if data:
                return data
    return None


def save_as_jpeg(image_b64: str, out_path: Path):
    raw = base64.b64decode(image_b64)
    img = Image.open(io.BytesIO(raw)).convert('RGB')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format='JPEG', quality=92)


def generate_image(api_key: str, prompt: str, out_path: Path):
    url = f'{API_URL}?key={api_key}'
    payload = {
        'contents': [{'parts': [{'text': f'Generate an image: {prompt}'}]}],
        'generationConfig': {'responseModalities': ['TEXT', 'IMAGE']},
    }
    for attempt in range(1, 4):
        resp = requests.post(url, json=payload, timeout=180)
        if resp.status_code == 429:
            if attempt == 3:
                raise RuntimeError('Gemini API rate limited after 3 attempts')
            time.sleep(10)
            continue
        if not resp.ok:
            raise RuntimeError(f'Gemini API error {resp.status_code}: {resp.text[:500]}')
        data = resp.json()
        image_b64 = extract_image_b64(data)
        if not image_b64:
            raise RuntimeError(f'No image data returned: {json.dumps(data)[:500]}')
        save_as_jpeg(image_b64, out_path)
        return


def main():
    posts = json.load(open(POSTS_PATH, 'r', encoding='utf-8'))
    cfg = json.load(open(CONFIG_PATH, 'r', encoding='utf-8'))
    api_key = cfg['models']['providers']['google']['apiKey']

    spacing_fixed = 0
    images_created = 0
    failures = []

    for post in posts:
        original = post.get('content', '')
        normalized = normalize_content(original)
        if normalized != original:
            post['content'] = normalized
            spacing_fixed += 1

        image_rel = f"images/posts/article-{post['id']}.jpg"
        image_abs = ROOT / image_rel
        if not image_abs.exists():
            prompt = build_prompt(post.get('title', ''), post.get('content', ''))
            try:
                generate_image(api_key, prompt, image_abs)
                images_created += 1
            except Exception as e:
                failures.append({'id': post['id'], 'stage': 'image', 'error': str(e)})
                continue
            time.sleep(3)

        post['image'] = image_rel
        post['thumbnail'] = image_rel

    with open(POSTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print(json.dumps({
        'spacing_fixed': spacing_fixed,
        'images_created': images_created,
        'failures': failures,
        'total_failures': len(failures),
    }, ensure_ascii=False, indent=2))

    if failures:
        sys.exit(2)


if __name__ == '__main__':
    main()
