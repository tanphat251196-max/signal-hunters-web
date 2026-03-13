#!/usr/bin/env python3
"""
Crawl lịch kinh tế quan trọng (≥3 sao) → lưu JSON cho web.
Chạy mỗi sáng thứ 2 bởi cron.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

OUTPUT_FILE = Path("/home/shinyyume/.openclaw/workspace/signal-hunters-web/data/economic-calendar.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def crawl_investing_calendar():
    """Crawl từ investing.com economic calendar."""
    events = []
    try:
        url = "https://vn.investing.com/economic-calendar/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"HTTP {resp.status_code}")
            return events

        soup = BeautifulSoup(resp.text, "html.parser")

        for row in soup.select("tr.js-event-item"):
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            bulls = row.select("i.grayFullBullishIcon, i.greenBullishIcon")
            stars = len(bulls)
            if stars < 3:
                continue

            time_cell = cols[0].get_text(strip=True)
            country_elem = row.select_one("td.flagCur span")
            country = country_elem.get("title", "") if country_elem else ""
            currency = cols[1].get_text(strip=True) if len(cols) > 1 else ""
            event_name = cols[3].get_text(strip=True) if len(cols) > 3 else ""

            actual = cols[4].get_text(strip=True) if len(cols) > 4 else ""
            forecast = cols[5].get_text(strip=True) if len(cols) > 5 else ""
            previous = cols[6].get_text(strip=True) if len(cols) > 6 else ""

            if not event_name:
                continue

            events.append(
                {
                    "time": time_cell,
                    "country": country or currency,
                    "event": event_name,
                    "stars": stars,
                    "actual": actual,
                    "forecast": forecast,
                    "previous": previous,
                }
            )
    except Exception as e:
        print(f"Error crawling: {e}")

    return events


def get_fallback_events():
    """Fallback: Google search cho sự kiện kinh tế tuần."""
    events = []
    try:
        query = "economic calendar this week important events Fed CPI GDP NFP PMI"
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        keywords = [
            "fed",
            "cpi",
            "gdp",
            "nfp",
            "pmi",
            "fomc",
            "rate",
            "employment",
            "inflation",
            "retail sales",
            "jobless",
            "housing",
            "manufacturing",
        ]

        for div in soup.select("div.BNeawe, span.BNeawe"):
            text = div.get_text(strip=True)
            if len(text) > 30 and any(k in text.lower() for k in keywords):
                events.append(
                    {
                        "time": "",
                        "country": "US",
                        "event": text[:120],
                        "stars": 3,
                        "actual": "",
                        "forecast": "",
                        "previous": "",
                    }
                )
                if len(events) >= 10:
                    break
    except Exception as e:
        print(f"Fallback error: {e}")
    return events


def main():
    today = datetime.now()

    monday_this = today - timedelta(days=today.weekday())
    sunday_this = monday_this + timedelta(days=6)
    monday_next = monday_this + timedelta(days=7)
    sunday_next = monday_next + timedelta(days=6)

    print("Crawling economic calendar...")
    events = crawl_investing_calendar()

    if not events:
        print("Main source failed, trying fallback...")
        events = get_fallback_events()

    print(f"Found {len(events)} events (≥3 stars)")

    data = {
        "updated": today.strftime("%Y-%m-%d %H:%M"),
        "this_week": {
            "label": f"Tuần này ({monday_this.strftime('%d/%m')} - {sunday_this.strftime('%d/%m')})",
            "events": events[:10],
        },
        "next_week": {
            "label": f"Tuần tới ({monday_next.strftime('%d/%m')} - {sunday_next.strftime('%d/%m')})",
            "events": [],
        },
    }

    if len(events) > 10:
        data["this_week"]["events"] = events[: len(events) // 2]
        data["next_week"]["events"] = events[len(events) // 2 :]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved to {OUTPUT_FILE}")
    print(f"   This week: {len(data['this_week']['events'])} events")
    print(f"   Next week: {len(data['next_week']['events'])} events")


if __name__ == "__main__":
    main()
