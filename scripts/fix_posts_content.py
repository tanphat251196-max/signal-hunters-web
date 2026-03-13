#!/usr/bin/env python3
import json
import re
from pathlib import Path

POSTS_PATH = Path('/home/shinyyume/.openclaw/workspace/signal-hunters-web/data/posts.json')

LOWER = 'a-zàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ'
UPPER = 'A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ'
PATTERN = re.compile(rf'([{LOWER}])([{UPPER}])')

PROTECTED_PATTERNS = [
    r'https?://\S+',
    r'@[^\s<)]+',
    r'#[A-Za-z0-9_]+',
]

RESTORE_MAP = {
    'De Fi': 'DeFi',
    'Game Fi': 'GameFi',
    'Coin Base': 'CoinBase',
    'You Tube': 'YouTube',
    'Git Hub': 'GitHub',
    'Bit Coin': 'Bitcoin',
    'Block Chain': 'Blockchain',
    'Alt Coin': 'Altcoin',
    'Stable Coin': 'Stablecoin',
    'Mc Donald': 'McDonald',
    'i Phone': 'iPhone',
    'i OS': 'iOS',
    'Ether Eum': 'Ethereum',
    'Po W': 'PoW',
    'Po S': 'PoS',
    'd App': 'dApp',
    'Layer Zero': 'LayerZero',
    'Usd T': 'UsdT',
    'No Vogratz': 'Novogratz',
    'Scar Amucci': 'Scaramucci',
    'Bing X': 'BingX',
    'Hyper EVM': 'HyperEVM',
    'Coin Market Cap': 'CoinMarketCap',
    'Pi DEX': 'PiDEX',
    'Wisdom Tree': 'WisdomTree',
    'Micro Strategy': 'MicroStrategy',
    'Pay Pal': 'PayPal',
    'Coin Desk': 'CoinDesk',
    'Crypto Quant': 'CryptoQuant',
    'Ripple X': 'RippleX',
    'Bank XRP': 'BankXRP',
    'Deep Snitch AI': 'DeepSnitch AI',
    'Ku Coin': 'KuCoin',
    'Po R': 'PoR',
    'wst ETH': 'wstETH',
    'i Shares': 'iShares',
}


ENTITY_REPLACEMENTS = {
    '&amp;amp;': '&amp;',
    '&amp;lt;': '&lt;',
    '&amp;gt;': '&gt;',
    '&amp;quot;': '&quot;',
}


def protect_patterns(text: str):
    protected = {}
    counter = 0
    for pattern in PROTECTED_PATTERNS:
        def repl(match):
            nonlocal counter
            key = f'__PROTECTED_{counter}__'
            protected[key] = match.group(0)
            counter += 1
            return key
        text = re.sub(pattern, repl, text)
    return text, protected


def restore_protected(text: str, protected: dict):
    for key, value in protected.items():
        text = text.replace(key, value)
    return text


def fix_content(content: str):
    total_changes = 0
    fixed = content

    for old, new in ENTITY_REPLACEMENTS.items():
        count = fixed.count(old)
        if count:
            fixed = fixed.replace(old, new)
            total_changes += count

    fixed, protected = protect_patterns(fixed)

    fixed, split_count = PATTERN.subn(r'\1 \2', fixed)
    total_changes += split_count

    for wrong, right in RESTORE_MAP.items():
        count = fixed.count(wrong)
        if count:
            fixed = fixed.replace(wrong, right)
            total_changes += count

    fixed = restore_protected(fixed, protected)

    if fixed == content:
        return content, 0
    return fixed, total_changes


def main():
    posts = json.loads(POSTS_PATH.read_text(encoding='utf-8'))

    posts_fixed = 0
    total_fixes = 0
    changed_ids = []

    for post in posts:
        original = post.get('content', '')
        fixed, change_count = fix_content(original)
        if fixed != original:
            post['content'] = fixed
            posts_fixed += 1
            total_fixes += change_count
            changed_ids.append(post.get('id'))

    POSTS_PATH.write_text(json.dumps(posts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print(f'Posts fixed: {posts_fixed}')
    print(f'Total fixes: {total_fixes}')
    print(f'Changed post IDs: {changed_ids}')


if __name__ == '__main__':
    main()
