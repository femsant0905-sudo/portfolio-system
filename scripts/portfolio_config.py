"""
portfolio_config.py
Central config for all tickers, entry targets, and positions.
Edit this file to update targets — everything else reads from here.
"""

import datetime

# ── Open positions (already bought) ──────────────────────────────────────────
OPEN_POSITIONS = {
    "MU": {
        "company":    "Micron Technology",
        "sector":     "Semis / AI",
        "entry_price": 730.00,
        "shares":      13.70,
        "buy_date":    datetime.date(2026, 5, 19),
        "target_12m":  1150.00,   # midpoint
        "target_18m":  1450.00,
        "stop_loss":    750.00,
        "next_event":  "Earnings Q3 — 24/jun/2026",
    },
    "ISRG": {
        "company":    "Intuitive Surgical",
        "sector":     "MedTech",
        "entry_price": 453.00,
        "shares":      22.08,
        "buy_date":    datetime.date(2026, 5, 19),
        "target_12m":  585.00,
        "target_18m":  700.00,
        "stop_loss":   380.00,
        "next_event":  "Earnings Q2 — 21/jul/2026",
    },
}

# ── Pending positions (watching for entry) ────────────────────────────────────
WATCHLIST = {
    "NVDA": {
        "company":      "NVIDIA Corp",
        "sector":       "AI / Semis",
        "alloc_usd":    15_000,
        "entry_ideal":  (190, 195),    # (low, high)
        "entry_good":   (200, 205),
        "entry_accept": (210, 215),
        "avoid_above":  225,
        "target_12m":   272.50,        # midpoint of 265-280
        "target_18m":   320.00,
        "stop_loss":    170.00,
        "next_event":   "Earnings Q2 FY27 — 26/ago/2026",
        "priority":     4,
    },
    "AMZN": {
        "company":      "Amazon.com",
        "sector":       "Cloud / Tech",
        "alloc_usd":    15_000,
        "entry_ideal":  (248, 255),
        "entry_good":   (258, 265),
        "entry_accept": (268, 272),
        "avoid_above":  275,
        "target_12m":   340.00,
        "target_18m":   387.50,
        "stop_loss":    220.00,
        "next_event":   "Earnings Q2 — 30/jul/2026",
        "priority":     2,
    },
    "META": {
        "company":      "Meta Platforms",
        "sector":       "Digital Ads",
        "alloc_usd":    12_000,
        "entry_ideal":  (590, 610),
        "entry_good":   (615, 625),
        "entry_accept": (630, 640),
        "avoid_above":  660,
        "target_12m":   780.00,
        "target_18m":   875.00,
        "stop_loss":    520.00,
        "next_event":   "Earnings Q2 — 29/jul/2026",
        "priority":     1,
    },
    "LLY": {
        "company":      "Eli Lilly",
        "sector":       "Pharma / GLP-1",
        "alloc_usd":    12_000,
        "entry_ideal":  (1000, 1050),
        "entry_good":   (1060, 1090),
        "entry_accept": (1100, 1120),
        "avoid_above":  1150,
        "target_12m":   1325.00,
        "target_18m":   1475.00,
        "stop_loss":     880.00,
        "next_event":   "Earnings Q2 — 05/ago/2026 | TRIUMPH-2 readout H2",
        "priority":     3,
    },
    "BRK-B": {
        "company":      "Berkshire Hathaway B",
        "sector":       "Value / Macro",
        "alloc_usd":    10_000,
        "entry_ideal":  (455, 465),
        "entry_good":   (466, 473),
        "entry_accept": (474, 480),
        "avoid_above":  490,
        "target_12m":   545.00,
        "target_18m":   590.00,
        "stop_loss":    420.00,
        "next_event":   "Earnings Q2 — ago/2026",
        "priority":     5,  # BUY NOW — already in range
    },
}

# ── Tax config ────────────────────────────────────────────────────────────────
TAX = {
    "short_term_rate": 0.515,   # Federal 37% + NIIT 3.8% + NJ 10.75%
    "long_term_rate":  0.346,   # Federal 20% + NIIT 3.8% + NJ 10.75%
    "lt_holding_days": 366,     # days to qualify for LT treatment
}

# ── Signal thresholds ─────────────────────────────────────────────────────────
def get_signal(ticker: str, price: float) -> str:
    """Return signal string for a watchlist ticker given current price."""
    if ticker not in WATCHLIST:
        return "—"
    cfg = WATCHLIST[ticker]
    if price <= cfg["entry_ideal"][1]:
        return "🟢 BUY NOW"
    elif price <= cfg["entry_good"][1]:
        return "🟡 GOOD"
    elif price <= cfg["entry_accept"][1]:
        return "🟠 OK"
    elif price <= cfg["avoid_above"]:
        return "🔴 WAIT"
    else:
        return "⛔ AVOID"

def get_open_signal(ticker: str, price: float) -> str:
    """Return signal string for an open position given current price."""
    if ticker not in OPEN_POSITIONS:
        return "—"
    cfg = OPEN_POSITIONS[ticker]
    if price >= cfg["target_12m"]:
        return "✅ AT TARGET"
    elif price <= cfg["stop_loss"]:
        return "🚨 STOP LOSS"
    elif price >= cfg["entry_price"]:
        return "📈 PROFIT"
    else:
        return "📉 LOSS"

ALL_TICKERS = list(OPEN_POSITIONS.keys()) + list(WATCHLIST.keys())
