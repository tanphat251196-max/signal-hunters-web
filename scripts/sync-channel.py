#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

BASE_URL = "https://t.me/s/SignalHuntersCrypto"
CHANNEL_URL = "https://t.me/SignalHuntersCrypto"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
TIMEOUT = 20
ALTCOIN_KEYWORDS = {
    "altcoin",
    "eth",
    "ethereum",
    "xrp",
    "ripple",
    "sol",
    "solana",
    "bnb",
    "ton",
    "toncoin",
    "ada",
    "cardano",
    "doge",
    "dogecoin",
    "avax",
    "pol",
    "matic",
    "polygon",
    "link",
    "chainlink",
    "dot",
    "polkadot",
    "ltc",
    "litecoin",
    "trx",
    "tron",
    "sui",
    "apt",
    "aptos",
    "near",
    "arb",
    "arbitrum",
    "op",
    "optimism",
    "kas",
    "kaspa",
    "wif",
    "pepe",
    "shib",
    "memecoin",
}


@dataclass
class Post:
    id: int
    title: str
    summary: str
    content: str
    category: str
    image: str
    date: str
    url: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "content": self.content,
            "category": self.category,
            "image": self.image,
            "date": self.date,
            "url": self.url,
        }


class TelegramChannelSync:
    def __init__(self, root_dir: Path, max_pages: int = 10, pause: float = 0.0):
        self.root_dir = root_dir
        self.max_pages = max_pages
        self.pause = pause
        self.images_dir = root_dir / "images" / "posts"
        self.data_file = root_dir / "data" / "posts.json"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.placeholder_hits = 0
        self.downloaded_hits = 0

    def fetch_page(self, before: Optional[int] = None) -> str:
        url = BASE_URL if before is None else f"{BASE_URL}?before={before}"
        response = self.session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return response.text

    def extract_posts(self) -> list[Post]:
        seen_ids: set[int] = set()
        raw_posts: list[dict] = []
        before: Optional[int] = None

        for _ in range(self.max_pages):
            html = self.fetch_page(before=before)
            page_posts = self.parse_page(html)
            new_posts = [post for post in page_posts if post["id"] not in seen_ids]
            if not new_posts:
                break

            for post in new_posts:
                seen_ids.add(post["id"])
                raw_posts.append(post)

            oldest_id = min(post["id"] for post in new_posts)
            next_before = oldest_id
            if before == next_before:
                break
            before = next_before

        posts = [self.build_post(raw_post) for raw_post in raw_posts]
        posts.sort(key=lambda item: (item.date, item.id), reverse=True)
        return posts

    def parse_page(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        posts: list[dict] = []

        for wrap in soup.select("div.tgme_widget_message_wrap"):
            data_post = self.extract_data_post(wrap)
            if not data_post:
                continue

            message_id = self.extract_message_id(data_post)
            if message_id is None:
                continue

            text_block = wrap.select_one("div.tgme_widget_message_text")
            if text_block is None:
                continue

            date_value = self.extract_date(wrap)
            image_url = self.extract_image_url(wrap)

            posts.append(
                {
                    "id": message_id,
                    "date": date_value,
                    "content_html": self.normalize_html(text_block),
                    "content_text": self.normalize_text(text_block.get_text("\n", strip=True)),
                    "image_url": image_url,
                }
            )

        return posts

    @staticmethod
    def extract_data_post(wrap: Tag) -> Optional[str]:
        direct = wrap.get("data-post")
        if direct:
            return str(direct)
        inner = wrap.select_one("div.tgme_widget_message")
        return str(inner.get("data-post")) if inner and inner.get("data-post") else None

    @staticmethod
    def extract_message_id(data_post: str) -> Optional[int]:
        match = re.search(r"/(\d+)$", data_post)
        return int(match.group(1)) if match else None

    @staticmethod
    def extract_date(wrap: Tag) -> str:
        time_el = wrap.select_one("time[datetime]")
        if not time_el:
            return datetime.utcnow().date().isoformat()

        raw = time_el.get("datetime", "")
        raw = str(raw).strip()
        if raw.endswith("Z"):
            raw = raw.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(raw)
            return parsed.date().isoformat()
        except ValueError:
            return raw[:10] if len(raw) >= 10 else datetime.utcnow().date().isoformat()

    @staticmethod
    def extract_image_url(wrap: Tag) -> Optional[str]:
        photo = wrap.select_one("a.tgme_widget_message_photo_wrap")
        if not photo:
            return None
        style = str(photo.get("style", ""))
        match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
        if not match:
            return None
        return urljoin("https://t.me", match.group(1).replace("\\/", "/"))

    @staticmethod
    def normalize_html(text_block: Tag) -> str:
        html = text_block.decode_contents()
        html = html.replace("<br/>", "<br>").replace("<br />", "<br>")
        return html.strip()

    @staticmethod
    def normalize_text(text: str) -> str:
        text = text.replace("\xa0", " ")
        text = re.sub(r"\n{2,}", "\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()

    @staticmethod
    def clean_title_candidate(value: str) -> str:
        value = re.sub(r"\s+", " ", value).strip()
        value = re.sub(r"^[^\wÀ-ỹ$#]+", "", value, flags=re.UNICODE).strip()
        value = re.sub(r"\s*[|•·-]+\s*$", "", value).strip()
        return value

    @classmethod
    def extract_title(cls, content_html: str, content_text: str) -> str:
        soup = BeautifulSoup(content_html, "html.parser")
        for bold in soup.find_all(["b", "strong"]):
            bold_text = cls.clean_title_candidate(bold.get_text(" ", strip=True))
            if len(bold_text) >= 4:
                return bold_text[:140]

        for line in content_text.splitlines():
            cleaned_line = cls.clean_title_candidate(line)
            if len(cleaned_line) >= 4:
                return cleaned_line[:140]

        fallback = cls.clean_title_candidate(content_text[:140])
        return fallback or "Signal Hunters Update"

    @staticmethod
    def extract_summary(content_text: str, limit: int = 150) -> str:
        cleaned = re.sub(r"\s+", " ", content_text).strip()
        if len(cleaned) <= limit:
            return cleaned
        return cleaned[: limit - 1].rstrip() + "…"

    @staticmethod
    def classify_category(content_text: str) -> str:
        lowered = content_text.lower()
        upper = content_text.upper()

        if any(keyword in upper for keyword in ("DAILY ANALYSIS", "WEEKLY", "MONTHLY")):
            return "analysis"
        if "CRYPTO NEWS" in upper or "TIN TỨC" in upper:
            return "news"
        if any(keyword in lowered for keyword in ("hàng hóa", "commodity", "vàng", "dầu")):
            return "commodity"
        if "ALTCOIN" in upper or any(keyword in lowered for keyword in ALTCOIN_KEYWORDS):
            return "altcoin"
        return "news"

    def ensure_dirs(self) -> None:
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

    def download_image(self, image_url: Optional[str], message_id: int) -> str:
        destination = self.images_dir / f"{message_id}.jpg"
        relative = f"images/posts/{message_id}.jpg"
        placeholder = f"https://picsum.photos/800/450?random={message_id}"

        if not image_url:
            self.placeholder_hits += 1
            return placeholder

        try:
            response = self.session.get(image_url, timeout=TIMEOUT)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "image" not in content_type and not response.content:
                raise ValueError("invalid image response")
            destination.write_bytes(response.content)
            self.downloaded_hits += 1
            return relative
        except Exception:
            self.placeholder_hits += 1
            return placeholder

    def build_post(self, raw_post: dict) -> Post:
        content_text = raw_post["content_text"]
        title = self.extract_title(raw_post["content_html"], content_text)
        summary = self.extract_summary(content_text)
        category = self.classify_category(content_text)
        image_path = self.download_image(raw_post.get("image_url"), raw_post["id"])

        return Post(
            id=raw_post["id"],
            title=title,
            summary=summary,
            content=raw_post["content_html"],
            category=category,
            image=image_path,
            date=raw_post["date"],
            url=f"{CHANNEL_URL}/{raw_post['id']}",
        )

    def save_posts(self, posts: Iterable[Post]) -> None:
        payload = [post.to_dict() for post in posts]
        self.data_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync SignalHuntersCrypto posts to static website JSON")
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Project root directory (default: parent of scripts/)",
    )
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum preview pages to crawl")
    args = parser.parse_args()

    root_dir = Path(args.root).resolve()
    syncer = TelegramChannelSync(root_dir=root_dir, max_pages=max(1, args.max_pages))
    syncer.ensure_dirs()
    posts = syncer.extract_posts()
    syncer.save_posts(posts)

    print(f"Synced {len(posts)} posts")
    print(f"Downloaded images: {syncer.downloaded_hits}")
    print(f"Placeholder images: {syncer.placeholder_hits}")
    print(f"Output JSON: {syncer.data_file}")
    if posts:
        print("Sample post:")
        print(json.dumps(posts[0].to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
