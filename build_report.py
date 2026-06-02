#!/usr/bin/env python3
"""
build_report.py  --  Join today's sentiment with market data, update the
rolling history, and write the JSON the dashboard reads.

Inputs (in the working dir):
  raw_today.json          (from collect.py)
  sentiment_today.json    (written by the Claude agent -- see TASK_PROMPT.md)
  narrative.txt           (optional, written by the agent: 2-3 sentence summary)

Outputs:
  docs/data/history.json  (appended; one record per date, idempotent per day)
  docs/data/latest.json   (today's snapshot + correlations for the dashboard)
"""

import json
import os
from datetime import datetime, timezone

import yfinance as yf

HISTORY = "docs/data/history.json"
LATEST = "docs/data/latest.json"
MIN_DAYS_FOR_CORR = 8   # need at least this many paired points to bother


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def market_snapshot(ticker):
    """Return (last_close, pct_change_pct) or (None, None) if it doesn't resolve."""
    try:
        h = yf.Ticker(ticker).history(period="5d")
        if len(h) < 2:
            return None, None
        closes = h["Close"].dropna().tolist()
        last, prev = closes[-1], closes[-2]
        pct = (last - prev) / prev * 100.0
        return round(float(last), 2), round(float(pct), 2)
    except Exception as e:
        print(f"  market data failed for {ticker}: {e}")
        return None, None


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return None
    return round(cov / (vx ** 0.5 * vy ** 0.5), 3)


def lead_lag_correlations(history):
    """Pearson r between sentiment(t) and next-day return(t+1), per ticker."""
    by_ticker = {}  # ticker -> list of (date, sentiment, pct_change)
    for rec in history:
        for it in rec["items"]:
            if it.get("sentiment") is None:
                continue
            by_ticker.setdefault(it["ticker"], []).append(
                (rec["date"], it["sentiment"], it.get("pct_change"))
            )

    results = []
    for tkr, rows in by_ticker.items():
        rows.sort(key=lambda r: r[0])
        sent, fwd = [], []
        for i in range(len(rows) - 1):
            s = rows[i][1]
            nxt = rows[i + 1][2]   # next day's return
            if s is not None and nxt is not None:
                sent.append(s)
                fwd.append(nxt)
        if len(sent) >= MIN_DAYS_FOR_CORR:
            r = pearson(sent, fwd)
            if r is not None:
                results.append({"ticker": tkr, "r": r, "n": len(sent)})
    results.sort(key=lambda d: abs(d["r"]), reverse=True)
    return results


def main():
    raw = load_json("raw_today.json", {})
    sentiment = load_json("sentiment_today.json", {}).get("scores", {})
    date = raw.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    items = []
    for tkr, info in raw.get("tickers", {}).items():
        last, pct = market_snapshot(tkr)
        s = sentiment.get(tkr, {})
        items.append({
            "ticker": tkr,
            "mentions": info.get("mentions", 0),
            "sentiment": s.get("sentiment"),
            "label": s.get("label"),
            "rationale": s.get("rationale"),
            "close": last,
            "pct_change": pct,
        })
    items.sort(key=lambda d: d["mentions"], reverse=True)

    record = {"date": date, "items": items}

    history = load_json(HISTORY, [])
    history = [r for r in history if r["date"] != date]   # idempotent re-runs
    history.append(record)
    history.sort(key=lambda r: r["date"])

    os.makedirs("docs/data", exist_ok=True)
    with open(HISTORY, "w") as f:
        json.dump(history, f, indent=2)

    narrative = ""
    if os.path.exists("narrative.txt"):
        with open("narrative.txt") as f:
            narrative = f.read().strip()

    latest = {
        "date": date,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "subreddits": raw.get("subreddits", []),
        "narrative": narrative,
        "items": items,
        "correlations": lead_lag_correlations(history),
        "days_tracked": len(history),
    }
    with open(LATEST, "w") as f:
        json.dump(latest, f, indent=2)

    print(f"Wrote report for {date}: {len(items)} tickers, "
          f"{len(history)} days tracked.")


if __name__ == "__main__":
    main()
