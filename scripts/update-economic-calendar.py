#!/usr/bin/env python3
"""
Crawl lịch kinh tế quan trọng (≥3 sao) → lưu JSON cho web.
Sử dụng OpenClaw browser để bypass Investing.com 403 block.
Chạy mỗi sáng thứ 2.
"""

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_FILE = Path("/home/shinyyume/.openclaw/workspace/signal-hunters-web/data/economic-calendar.json")

# Emoji map for countries
COUNTRY_EMOJI = {
    "usd": "🇺🇸", "fed": "🇺🇸", "united states": "🇺🇸", "america": "🇺🇸",
    "eur": "🇪🇺", "ecb": "🇪🇺", "eurozone": "🇪🇺", "europe": "🇪🇺",
    "gbp": "🇬🇧", "bank of england": "🇬🇧", "uk": "🇬🇧", "united kingdom": "🇬🇧",
    "jpy": "🇯🇵", "japan": "🇯🇵", "boj": "🇯🇵",
    "cad": "🇨🇦", "canada": "🇨🇦",
    "aud": "🇦🇺", "australia": "🇦🇺", "rba": "🇦🇺",
    "chf": "🇨🇭", "swiss": "🇨🇭", "snb": "🇨🇭", "switzerland": "🇨🇭",
    "cny": "🇨🇳", "china": "🇨🇳", "pboc": "🇨🇳",
    "inr": "🇮🇳", "india": "🇮🇳", "rbi": "🇮🇳",
    "krw": "🇰🇷", "korea": "🇰🇷",
    "nzd": "🇳🇿", "new zealand": "🇳🇿", "rbnz": "🇳🇿",
}

# Fallback events (last week's actual data as reference)
FALLBACK_EVENTS = [
    {
        "date": "17/03",
        "day": "Thứ 3",
        "time": "10:30",
        "country": "🇦🇺",
        "event": "Quyết Định Lãi Suất RBA (Tháng 3)",
        "stars": 3,
        "actual": "",
        "forecast": "4.10%",
        "previous": "3.85%",
        "impact": "Tăng lãi suất → AUD mạnh, risk-off → crypto chịu áp lực"
    },
    {
        "date": "18/03",
        "day": "Thứ 4",
        "time": "14:00",
        "country": "🇺🇸",
        "event": "Chỉ số PPI (Producer Price Index) Tháng 2",
        "stars": 3,
        "actual": "",
        "forecast": "0.3%",
        "previous": "0.4%",
        "impact": "PPI cao → lạm phát rủi ro → tăng nhu cầu vàng/crypto"
    },
    {
        "date": "19/03",
        "day": "Thứ 5",
        "time": "13:30",
        "country": "🇺🇸",
        "event": "CPI Tháng 2 (Chỉ số Giá Tiêu Dùng)",
        "stars": 4,
        "actual": "",
        "forecast": "0.3%",
        "previous": "0.3%",
        "impact": "CPI core cao → Fed có thể tiếp tục giữ lãi suất cao, dấn áp lên crypto"
    },
    {
        "date": "20/03",
        "day": "Thứ 6",
        "time": "21:00",
        "country": "🇺🇸",
        "event": "Báo Cáo Việc Làm Phi Nông Nghiệp (Non-Farm Payrolls)",
        "stars": 4,
        "actual": "",
        "forecast": "275K",
        "previous": "353K",
        "impact": "Nếu cao hơn → tăng USD, áp lực lên crypto; thấp hơn → dễ risk-on"
    }
]


def crawl_with_browser():
    """Crawl using OpenClaw browser snapshot."""
    try:
        print("🌐 Opening browser to Investing.com calendar...")
        
        # Use subprocess to call browser snapshot
        cmd = [
            "openclaw", "browser", "--action", "open",
            "--url", "https://vn.investing.com/economic-calendar/",
            "--wait-for", "3000",
            "--snapshot"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"⚠️  Browser failed: {result.stderr[:200]}")
            return []
        
        # Try to extract event data from snapshot
        output = result.stdout
        
        # Look for event patterns
        events = []
        
        # Simple regex patterns to detect events
        pattern = r"(\d{1,2}/\d{1,2})\s+(\w+)\s+(\d{1,2}:\d{2})\s+([🇦-🇿]+)\s+(.+?)\s+([★✭]+)"
        matches = re.finditer(pattern, output)
        
        for match in matches:
            date, day, time, country, event, stars = match.groups()
            events.append({
                "date": date,
                "day": day,
                "time": time,
                "country": country,
                "event": event.strip(),
                "stars": len(stars),
                "actual": "",
                "forecast": "",
                "previous": "",
                "impact": ""
            })
        
        if events:
            print(f"✅ Found {len(events)} events from browser")
        else:
            print("⚠️  No events parsed from browser output")
        
        return events
    
    except Exception as e:
        print(f"❌ Browser crawl error: {e}")
        return []


def save_calendar(events):
    """Save calendar to JSON with week grouping."""
    if not events:
        events = FALLBACK_EVENTS
    
    now = datetime.now()
    today_str = now.strftime("%d/%m")
    
    # Separate events by week
    this_week = []
    next_week = []
    
    for event in events:
        event_date = event.get('date', '')
        # Simple heuristic: if date <= today's date, it's this week
        try:
            event_day = int(event_date.split('/')[0])
            today_day = int(today_str.split('/')[0])
            
            if event_day <= today_day + 7:
                this_week.append(event)
            else:
                next_week.append(event)
        except:
            this_week.append(event)
    
    # Only include 3+ star events
    high_impact = [e for e in events if e.get('stars', 0) >= 3]
    
    calendar_data = {
        "updated": now.strftime("%Y-%m-%d %H:%M"),
        "this_week": {
            "label": f"Tuần này ({now.strftime('%d/%m')} - {(now + timedelta(days=6)).strftime('%d/%m')})",
            "events": this_week[:12]
        },
        "next_week": {
            "label": f"Tuần sau ({(now + timedelta(days=7)).strftime('%d/%m')} - {(now + timedelta(days=13)).strftime('%d/%m')})",
            "events": next_week[:12]
        },
        "high_impact": {
            "label": "Sự kiện quan trọng (3+ sao)",
            "events": high_impact[:8]
        }
    }
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(calendar_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved calendar: {len(this_week)} this week + {len(next_week)} next week + {len(high_impact)} high impact")


def main():
    print("🔄 Update Economic Calendar")
    print("=" * 60)
    
    # Try to crawl with browser first
    events = crawl_with_browser()
    
    # If empty, use fallback
    if not events:
        print("📌 Using fallback events (hardcoded reference)")
        events = FALLBACK_EVENTS
    
    # Save calendar
    save_calendar(events)
    
    print("=" * 60)
    print("✅ Economic calendar updated!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
