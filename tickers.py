"""
Ticker extraction from Reddit text.

Strategy (high precision, tunable recall):
  1. Cashtags ($AAPL) are always counted.
  2. Bare uppercase tokens (AAPL) are counted ONLY if they are in KNOWN_TICKERS
     and NOT in STOPWORDS. This kills the bulk of WSB false positives like
     "DD", "YOLO", "CEO", "ALL", "IT", "AI", etc.

Extend KNOWN_TICKERS freely -- it's just a set. If you want full-market
coverage later, load it from the SEC company_tickers.json file instead.
"""

import re
from collections import Counter

# Cashtag like $AAPL or $aapl (1-5 letters)
CASHTAG_RE = re.compile(r"\$([A-Za-z]{1,5})\b")
# Bare candidate symbol: a 1-5 char all-caps token
BARE_RE = re.compile(r"\b([A-Z]{1,5})\b")

# Curated set of frequently-discussed tickers. Add your own any time.
KNOWN_TICKERS = {
    # Mega cap / index favorites
    "AAPL", "MSFT", "NVDA", "GOOG", "GOOGL", "AMZN", "META", "TSLA", "AVGO",
    "SPY", "QQQ", "IWM", "DIA", "VOO", "VTI",
    # Semis
    "AMD", "INTC", "MU", "TSM", "ASML", "ARM", "SMCI", "QCOM", "TXN", "LRCX", "MRVL",
    # WSB perennials / high-volume names
    "GME", "AMC", "BB", "BBBY", "PLTR", "SOFI", "HOOD", "RIVN", "LCID", "NIO",
    "F", "GM", "NKLA", "RKLB", "ACHR", "JOBY", "CHPT", "RUN",
    # Big tech adjacent / growth
    "NFLX", "DIS", "UBER", "LYFT", "ABNB", "SHOP", "SQ", "PYPL", "COIN", "SNAP",
    "PINS", "RBLX", "U", "DKNG", "SNOW", "CRWD", "PANW", "NET", "DDOG", "MDB",
    "ZS", "OKTA", "TWLO", "DOCU", "ZM", "ROKU", "SPOT",
    # AI / data
    "ORCL", "IBM", "CRM", "ADBE", "NOW", "INTU", "DELL", "ANET",
    # EV / energy
    "ENPH", "SEDG", "FSLR", "PLUG", "BE", "XOM", "CVX", "OXY", "COP",
    # Finance
    "JPM", "BAC", "GS", "MS", "WFC", "C", "V", "MA", "AXP", "SCHW", "BRK",
    # Pharma / biotech
    "PFE", "MRNA", "LLY", "NVO", "JNJ", "ABBV", "UNH", "CVS",
    # Consumer
    "WMT", "TGT", "COST", "HD", "LOW", "MCD", "SBUX", "KO", "PEP", "NKE", "LULU",
    # Crypto-adjacent
    "MSTR", "MARA", "RIOT", "CLSK", "HUT",
    # Misc high-chatter
    "BABA", "PDD", "T", "VZ", "BA", "GE", "CAT", "DE", "UPS", "FDX",
}

# All-caps words that look like tickers but almost never are (in r/wsb etc.)
STOPWORDS = {
    "A", "I", "AM", "PM", "AN", "AS", "AT", "BE", "BY", "DO", "GO", "HE", "IF",
    "IN", "IS", "IT", "ME", "MY", "NO", "OF", "ON", "OR", "SO", "TO", "UP", "US",
    "WE", "ALL", "AND", "ANY", "ARE", "BUT", "CAN", "DID", "FOR", "GET", "GOT",
    "HAD", "HAS", "HER", "HIM", "HIS", "HOW", "ITS", "LET", "MAY", "NEW", "NOT",
    "NOW", "OUT", "OWN", "PUT", "SEE", "SHE", "THE", "TOO", "USE", "WAS", "WHO",
    "WHY", "YES", "YET", "YOU", "OMG", "LOL", "WTF", "IMO", "TBH", "FYI", "AKA",
    "ASAP", "ETA", "TLDR", "TLDR", "EDIT", "NSFW", "OP",
    # Trading / finance slang & acronyms
    "DD", "YOLO", "FD", "FOMO", "ATH", "ATL", "OTM", "ITM", "ATM", "IV", "DTE",
    "EPS", "PE", "PT", "ER", "PR", "CEO", "CFO", "COO", "CTO", "IPO", "ETF",
    "SEC", "FED", "FOMC", "CPI", "PPI", "GDP", "QE", "EOD", "EOW", "AH", "PM",
    "RH", "TA", "PDT", "HODL", "WSB", "GUH", "MOON", "BTFD", "BAGS", "EU", "UK",
    "USA", "AI", "ML", "EV", "VR", "AR", "API", "CD", "TV", "PC", "OS", "IT",
}


def extract(text):
    """Return a Counter of ticker -> mention count for one chunk of text."""
    if not text:
        return Counter()
    counts = Counter()
    # 1. Cashtags: always trusted.
    for m in CASHTAG_RE.findall(text):
        counts[m.upper()] += 1
    # 2. Bare uppercase tokens validated against the known list.
    for m in BARE_RE.findall(text):
        sym = m.upper()
        if sym in STOPWORDS:
            continue
        if sym in KNOWN_TICKERS:
            counts[sym] += 1
    return counts
