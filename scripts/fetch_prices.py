"""
fetch_prices.py
Fetches current prices from Yahoo Finance.
Returns a dict: { "NVDA": {"price": 212.34, "change_pct": -1.2, "prev_close": 215.0} }
"""

import json
import datetime
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    raise SystemExit("Run: pip install yfinance")

PRICES_FILE = Path(__file__).parent.parent / "data" / "prices.json"


def fetch(tickers: list[str]) -> dict:
    results = {}
    for ticker in tickers:
        try:
            t    = yf.Ticker(ticker)
            fi   = t.fast_info
            price = round(float(fi.last_price), 2)
            prev  = round(float(fi.previous_close), 2)
            chg   = round((price - prev) / prev * 100, 2) if prev else 0.0
            results[ticker] = {
                "price":      price,
                "prev_close": prev,
                "change_pct": chg,
                "timestamp":  datetime.datetime.utcnow().isoformat(),
                "status":     "ok",
            }
        except Exception as e:
            results[ticker] = {"price": None, "status": "error", "error": str(e)}
    return results


def fetch_and_save(tickers: list[str]) -> dict:
    prices = fetch(tickers)
    PRICES_FILE.parent.mkdir(parents=True, exist_ok=True)
    PRICES_FILE.write_text(json.dumps(prices, indent=2))
    return prices


def load_cached() -> dict:
    if PRICES_FILE.exists():
        return json.loads(PRICES_FILE.read_text())
    return {}
