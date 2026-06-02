#!/usr/bin/env python3
"""
Watches r/trackers and r/opensignups for open invite/signup posts
and sends a Discord webhook notification when one is found.

Environment variables:
    DISCORD_WEBHOOK   Discord webhook URL (required for notifications)
    CHECK_INTERVAL    Seconds between checks (default: 900 = 15 minutes)

State is persisted to /data/seen_posts.json.
"""

import json
import os
import sys
import time
from pathlib import Path

import requests

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 900))
SUBREDDITS = ["trackers", "opensignups"]
KEYWORDS = [
    "open signup", "open signups", "open registration", "now open",
    "invites", "invite", "recruiting", "recruitment", "free invite",
    "open applications", "applications open",
]
STATE_FILE = Path(os.environ.get("STATE_DIR", "/data")) / "seen_posts.json"
REDDIT_HEADERS = {"User-Agent": "tracker-watcher/1.0"}


def load_seen() -> set:
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()


def save_seen(seen: set):
    STATE_FILE.write_text(json.dumps(list(seen)))


def fetch_posts(subreddit: str) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=25"
    try:
        r = requests.get(url, headers=REDDIT_HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()["data"]["children"]
    except Exception as e:
        print(f"[error] fetching r/{subreddit}: {e}", file=sys.stderr)
        return []


def is_relevant(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in KEYWORDS)


def send_discord(post: dict):
    if not DISCORD_WEBHOOK:
        print(f"[no webhook] would notify: {post['title']}")
        return

    data = post["data"]
    payload = {
        "embeds": [{
            "title": data["title"],
            "url": f"https://reddit.com{data['permalink']}",
            "description": (data.get("selftext") or "")[:300] or "*No body*",
            "color": 0x00b0f4,
            "footer": {"text": f"r/{data['subreddit']} • u/{data['author']}"},
        }]
    }
    try:
        r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[error] sending Discord notification: {e}", file=sys.stderr)


def main():
    if not DISCORD_WEBHOOK:
        print("[warn] DISCORD_WEBHOOK not set — will print matches but not notify")

    seen = load_seen()
    new_seen = set()
    found = 0

    for subreddit in SUBREDDITS:
        posts = fetch_posts(subreddit)
        for post in posts:
            data = post["data"]
            post_id = data["id"]
            new_seen.add(post_id)

            if post_id in seen:
                continue

            if is_relevant(data["title"]):
                print(f"[match] r/{subreddit}: {data['title']}")
                send_discord(post)
                found += 1
                time.sleep(1)  # avoid Discord rate limits

    save_seen(seen | new_seen)
    print(f"[done] checked {sum(1 for _ in new_seen)} posts, found {found} matches")


if __name__ == "__main__":
    print(f"[start] checking every {CHECK_INTERVAL}s")
    while True:
        main()
        time.sleep(CHECK_INTERVAL)
