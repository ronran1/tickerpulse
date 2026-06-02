# Ticker Pulse — Reddit stock sentiment, on autopilot

A daily report that scrapes Reddit chatter on the most-discussed tickers, has
Claude score the sentiment, joins it against market performance, accumulates a
running history, and publishes a mobile-friendly dashboard to GitHub Pages —
all run unattended as a **Claude Code Routine** (cloud scheduled task). No
server, no machine left on.

## How it works

Each scheduled run spins up a fresh Claude Code cloud session that:

1. clones this repo (the repo *is* the database — `docs/data/history.json`),
2. runs `collect.py` → pulls Reddit posts/comments, extracts tickers, saves snippets,
3. **reads the snippets and scores sentiment itself** (Claude's judgment, not a lexicon),
4. runs `build_report.py` → pulls Yahoo Finance closes, appends today's row to the
   history, recomputes a sentiment→next-day-return correlation, writes the dashboard data,
5. commits the updated data and pushes — GitHub Pages redeploys automatically.

Your phone just opens the Pages URL. Sentiment scoring runs under your Claude
subscription (one run/day is far under the Routine daily cap), so no separate
API key or billing is needed.

```
collect.py ──▶ raw_today.json ──▶ [Claude scores] ──▶ sentiment_today.json
                                                  └─▶ narrative.txt
                          build_report.py ──▶ docs/data/{history,latest}.json
                                          └─▶ GitHub Pages (docs/index.html)
```

## One-time setup

### 1. Reddit API credentials (free)
Create a **script** app at https://www.reddit.com/prefs/apps (type: "script").
Note the **client ID** (under the app name) and **secret**. Read-only access to
public subreddits needs nothing else. The free tier (100 queries/min) is plenty;
note it's for **non-commercial** use, which a personal report is.

### 2. This repo + GitHub Pages
- Push this folder to a new GitHub repo.
- Settings → Pages → Source: **Deploy from a branch**, branch = your default
  (e.g. `main`), folder = **`/docs`**. Your URL will be
  `https://<you>.github.io/<repo>/`.

### 3. Claude Code on the web
Enable Claude Code on the web and connect your GitHub account (required for
Routines — they don't run on the CLI alone). See the routine/web setup flow in
Claude Code.

### 4. Create the environment
In the Routine's environment, set:
- **Environment variables (secrets):**
  - `REDDIT_CLIENT_ID`
  - `REDDIT_CLIENT_SECRET`
  - `REDDIT_USER_AGENT` = `sentiment-bot by u/<yourname>` (optional)
  - `SUBREDDITS` = `wallstreetbets,stocks,investing,StockMarket,options` (optional)
- **Setup script:** `bash setup.sh` (installs Python deps)
- **Network access:** allow outbound to Reddit and Yahoo Finance:
  `oauth.reddit.com`, `www.reddit.com`, `query1.finance.yahoo.com`,
  `query2.finance.yahoo.com`, `fc.yahoo.com`.

### 5. Create the Routine
- Repo: this one. Schedule: **daily** (e.g. `30 21 * * *` UTC ≈ shortly after
  the US close; pick what you like).
- Prompt: paste the contents of **`TASK_PROMPT.md`**.
- **Enable "Allow unrestricted branch pushes"** in the routine settings so it can
  push the updated data to your Pages branch. (Default only allows `claude/*`
  branches, which Pages wouldn't be serving.)

That's it. Open your Pages URL on your phone; it refreshes each day.

## Notes & knobs
- **Ticker accuracy:** `tickers.py` trusts `$CASHTAGS` always and bare symbols
  only if they're in `KNOWN_TICKERS` and not in `STOPWORDS`. Extend the lists there.
- **Volume/cost:** tune `POSTS_PER_SUB`, `COMMENTS_PER_POST`, `MAX_TICKERS` in
  `collect.py`.
- **History is forward-only.** Pushshift (bulk historical Reddit) is gone, so the
  sentiment timeline builds from day one. Price history is fetched fresh each run,
  so the *market* side is always complete; the correlation panel fills in after
  ~2 weeks of runs.
- **Keeping `main` protected instead:** point GitHub Pages at a `claude/report`
  branch and have the prompt also `git fetch` that branch's history at the start.
  Slightly more fragile; the unrestricted-push route above is simpler.
- Routines are a research preview and may change; check Claude Code's docs if a
  setting has moved.

*Sentiment is an AI estimate of crowd mood, not investment advice.*
