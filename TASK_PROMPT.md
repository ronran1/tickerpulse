# Routine prompt — paste this as the prompt for the scheduled Routine

You are running as a scheduled cloud task in this repository. Each run starts
fresh with a clean clone of the default branch. Complete ALL steps in order,
then commit, push, and send the email digest. Do not ask for confirmation.

(Requires the Gmail connector to be enabled on this routine for step 7.)

## 1. Install dependencies
Run: `pip install -r requirements.txt`

## 2. Collect Reddit chatter
Run: `python collect.py`
This writes `raw_today.json` containing the busiest tickers with sample text
snippets. If it errors on Reddit auth, stop and report the error.

## 3. Score sentiment (this is your job — use your own judgment)
Read `raw_today.json`. For EACH ticker, read its snippets and judge how the
Reddit crowd feels about that stock *right now*. Account for sarcasm, slang
("puts" = bearish, "calls"/"tendies"/"to the moon" = bullish, "bag holder" =
trapped longs), hype, and FUD.

Write `sentiment_today.json` with EXACTLY this structure:
```json
{
  "scores": {
    "NVDA": { "sentiment": 0.62, "label": "bullish", "rationale": "Heavy call buying chatter ahead of earnings; few bears." },
    "TSLA": { "sentiment": -0.30, "label": "bearish", "rationale": "Mostly delivery-miss complaints and put positioning." }
  }
}
```
Rules:
- `sentiment` is a float from -1.0 (very bearish) to +1.0 (very bullish), 0 = neutral/mixed.
- `label` is one short word: bullish | bearish | neutral | mixed.
- `rationale` is ONE sentence (<= 18 words) grounded in the snippets.
- Include every ticker from `raw_today.json`. If a ticker has too little signal, use sentiment 0.0 and label "neutral".

## 4. Write the daily narrative
Write `narrative.txt`: 2–3 sentences summarizing the day's overall mood, the
standout ticker(s), and any notable divergence between chatter and price.
Plain prose, no markdown, no preamble.

## 5. Build the report
Run: `python build_report.py`
This fetches market data, appends today's record to `docs/data/history.json`,
and regenerates `docs/data/latest.json`.

## 6. Commit and push
Stage `docs/data/history.json` and `docs/data/latest.json`, commit with message
`report: <today's date>`, and push to the default branch so GitHub Pages
redeploys. (Requires "Allow unrestricted branch pushes" enabled on this routine.)

Report a one-line summary of what you pushed.

## 7. Email the digest (Gmail connector)
Read `docs/data/latest.json`. Send an email via the Gmail connector:
- **To:** `<your-email@example.com>`
- **Subject:** `Ticker Pulse — <date> · <top ticker> leads chatter`
- **Body (keep it phone-scannable):**
  - The `narrative` paragraph.
  - Then the top 8 items, one per line, formatted:
    `TICKER  ·  <label> (<sentiment, 2 decimals>)  ·  <pct_change>%`
  - A closing line: `Full dashboard: <your Pages URL>`

Use plain text or simple HTML. If `items` is empty (e.g. collection failed),
send a short note saying the run produced no data instead. Confirm the email
was sent in your final summary.
