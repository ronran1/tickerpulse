#!/usr/bin/env python3
"""
collect.py  --  Pull recent Reddit activity and aggregate it by ticker.

Output: raw_today.json
{
  "date": "2026-06-02",
  "subreddits": ["wallstreetbets", "stocks", ...],
  "tickers": {
    "NVDA": {
      "mentions": 42,
      "snippets": ["text ...", "text ...", ...]   # up to MAX_SNIPPETS, truncated
    },
    ...
  }
}

Auth: read-only mode needs only a Reddit "script" app's client id + secret.
Set these as environment variables (in the Routine environment):
  REDDIT_CLIENT_ID
  REDDIT_CLIENT_SECRET
  REDDIT_USER_AGENT      (optional, e.g. "sentiment-bot by u/yourname")
  SUBREDDITS             (optional, comma-separated; default below)
"""

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone

import praw

from tickers import extract

# ---- Tunables -------------------------------------------------------------
DEFAULT_SUBS = ["wallstreetbets", "stocks", "investing", "StockMarket", "options"]
POSTS_PER_SUB = 40          # how many hot posts to scan per subreddit
COMMENTS_PER_POST = 12      # top-level comments to read per post
MAX_TICKERS = 25            # keep the busiest N tickers (caps file size / tokens)
MAX_SNIPPETS = 10           # sample texts kept per ticker for the sentiment step
SNIPPET_CHARS = 320         # truncate each snippet
# ---------------------------------------------------------------------------


def clean(text):
    return " ".join((text or "").split())[:SNIPPET_CHARS]


def main():
    subs = os.environ.get("SUBREDDITS")
    subs = [s.strip() for s in subs.split(",")] if subs else DEFAULT_SUBS

    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ.get("REDDIT_USER_AGENT", "reddit-sentiment-bot/1.0"),
    )
    reddit.read_only = True

    mentions = Counter()
    snippets = defaultdict(list)

    for sub in subs:
        try:
            for post in reddit.subreddit(sub).hot(limit=POSTS_PER_SUB):
                if post.stickied:
                    continue
                body = f"{post.title}. {getattr(post, 'selftext', '')}"
                found = extract(body)
                for tkr, n in found.items():
                    mentions[tkr] += n
                    if len(snippets[tkr]) < MAX_SNIPPETS:
                        snippets[tkr].append(clean(body))
                # Scan a few top comments without expanding "load more".
                try:
                    post.comments.replace_more(limit=0)
                    for c in post.comments[:COMMENTS_PER_POST]:
                        found_c = extract(getattr(c, "body", ""))
                        for tkr, n in found_c.items():
                            mentions[tkr] += n
                            if len(snippets[tkr]) < MAX_SNIPPETS:
                                snippets[tkr].append(clean(c.body))
                except Exception as e:
                    print(f"  comment fetch failed on a post in r/{sub}: {e}")
        except Exception as e:
            print(f"subreddit r/{sub} failed: {e}")

    top = [t for t, _ in mentions.most_common(MAX_TICKERS)]
    out = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "subreddits": subs,
        "tickers": {
            t: {"mentions": mentions[t], "snippets": snippets[t]} for t in top
        },
    }

    with open("raw_today.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"Collected {len(top)} tickers from {len(subs)} subreddits.")
    print("Top:", ", ".join(f"{t}({mentions[t]})" for t in top[:10]))


if __name__ == "__main__":
    main()
