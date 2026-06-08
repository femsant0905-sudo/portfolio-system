#!/usr/bin/env python3
"""
monitor_prices.py
Runs every 15 minutes via GitHub Actions cron during market hours.
Fetches live prices, checks alert rules, sends Gmail alerts on signal changes.
Reads/writes state.json to avoid duplicate alerts.
"""

import json, os, smtplib, datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import yfinance as yf
except ImportError:
    raise SystemExit("pip install yfinance")

# ── Config ────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent.parent
STATE_FILE = ROOT / "data" / "state.json"
PRICES_FILE= ROOT / "data" / "prices.json"

GMAIL_USER     = os.environ["GMAIL_USER"]        # e.g. fernando@gmail.com
GMAIL_APP_PASS = os.environ["GMAIL_APP_PASS"]    # Gmail App Password (not login pwd)
ALERT_EMAIL    = os.environ["ALERT_EMAIL"]       # where to send alerts

# ── Portfolio data (mirrors app config) ──────────────────────────────────────
OPEN = {
    "MU":   {"entry": 730.00, "shares": 13.70, "target12m": 1150, "stop": 750,  "company": "Micron Technology"},
    "ISRG": {"entry": 453.00, "shares": 22.08, "target12m": 585,  "stop": 380,  "company": "Intuitive Surgical"},
}
WATCH = {
    "NVDA":  {"idealHi": 195, "goodHi": 205, "acceptHi": 215, "avoid": 225, "target12m": 272.5, "stop": 170,  "alloc": 15000, "company": "NVIDIA Corp"},
    "AMZN":  {"idealHi": 255, "goodHi": 265, "acceptHi": 272, "avoid": 275, "target12m": 340,   "stop": 220,  "alloc": 15000, "company": "Amazon.com"},
    "META":  {"idealHi": 610, "goodHi": 625, "acceptHi": 640, "avoid": 660, "target12m": 780,   "stop": 520,  "alloc": 12000, "company": "Meta Platforms"},
    "LLY":   {"idealHi":1050, "goodHi":1090, "acceptHi":1120, "avoid":1150, "target12m":1325,   "stop": 880,  "alloc": 12000, "company": "Eli Lilly"},
    "BRK-B": {"idealHi": 465, "goodHi": 473, "acceptHi": 480, "avoid": 490, "target12m": 545,   "stop": 420,  "alloc": 10000, "company": "Berkshire Hathaway B"},
}

# ── Market hours check ─────────────────────────────────────────────────────────
def is_market_hours() -> bool:
    now_et = datetime.datetime.utcnow() - datetime.timedelta(hours=4)  # rough EDT offset
    if now_et.weekday() >= 5:
        return False
    market_open  = now_et.replace(hour=9,  minute=30, second=0, microsecond=0)
    market_close = now_et.replace(hour=16, minute=0,  second=0, microsecond=0)
    return market_open <= now_et <= market_close

# ── Fetch prices ──────────────────────────────────────────────────────────────
def fetch_prices(tickers: list) -> dict:
    results = {}
    for t in tickers:
        try:
            fi = yf.Ticker(t).fast_info
            price = round(float(fi.last_price), 2)
            prev  = round(float(fi.previous_close), 2)
            results[t] = {
                "price": price,
                "prev_close": prev,
                "change_pct": round((price-prev)/prev*100, 2),
                "ts": datetime.datetime.utcnow().isoformat(),
            }
        except Exception as e:
            print(f"  ⚠️  {t}: {e}")
    return results

# ── Signal logic ──────────────────────────────────────────────────────────────
def watch_signal(ticker: str, price: float) -> str:
    w = WATCH[ticker]
    if price <= w["idealHi"]:   return "BUY_NOW"
    if price <= w["goodHi"]:    return "GOOD"
    if price <= w["acceptHi"]:  return "OK"
    if price <= w["avoid"]:     return "WAIT"
    return "AVOID"

def open_signal(ticker: str, price: float) -> str:
    o = OPEN[ticker]
    if price <= o["stop"]:      return "STOP_LOSS"
    if price >= o["target12m"]: return "AT_TARGET"
    if price >= o["entry"]:     return "PROFIT"
    return "LOSS"

# ── State management ──────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

# ── Email ─────────────────────────────────────────────────────────────────────
def send_email(subject: str, body: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = ALERT_EMAIL
    msg.attach(MIMEText(body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_APP_PASS)
        s.sendmail(GMAIL_USER, ALERT_EMAIL, msg.as_string())
    print(f"  📧 Email sent: {subject}")

def alert_html(alerts: list, prices: dict) -> tuple[str, str]:
    rows = ""
    for a in alerts:
        emoji = {"BUY_NOW":"🟢","GOOD":"🟡","OK":"🟠","WAIT":"🔴","AVOID":"⛔",
                 "AT_TARGET":"✅","STOP_LOSS":"🚨","PROFIT":"📈","LOSS":"📉"}.get(a["signal"],"•")
        p = prices.get(a["ticker"],{})
        chg = p.get("change_pct",0)
        chg_str = f"{'▲' if chg>=0 else '▼'} {abs(chg):.2f}%"
        rows += f"""
        <tr style="border-bottom:1px solid #2a2a2a">
          <td style="padding:12px 16px;font-weight:700;font-size:18px">{a["ticker"]}</td>
          <td style="padding:12px 8px;color:#888;font-size:13px">{a["company"]}</td>
          <td style="padding:12px 8px;font-family:monospace">${p.get("price","N/A"):,.2f}</td>
          <td style="padding:12px 8px;color:{"#4fffb0" if chg>=0 else "#ff6b6b"};font-family:monospace">{chg_str}</td>
          <td style="padding:12px 16px;font-size:13px">{emoji} {a["signal"].replace("_"," ")}</td>
        </tr>"""

    subject = f"Portfolio Alert — {len(alerts)} signal{'s' if len(alerts)>1 else ''} — {datetime.datetime.now().strftime('%H:%M')}"
    body = f"""
    <div style="background:#0a0d14;color:#e8eaf0;font-family:'Helvetica Neue',sans-serif;padding:32px;max-width:600px;margin:auto;border-radius:12px">
      <div style="font-size:11px;letter-spacing:.1em;color:#4fffb0;text-transform:uppercase;margin-bottom:4px">Portfolio · Fernando</div>
      <h1 style="font-size:22px;font-weight:800;margin-bottom:4px">Signal Alert</h1>
      <div style="font-size:12px;color:#6b7280;margin-bottom:24px">{datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} ET</div>
      <table style="width:100%;border-collapse:collapse;background:#111520;border-radius:10px;overflow:hidden">
        <thead><tr style="background:#1a1f30">
          <th style="padding:10px 16px;text-align:left;font-size:11px;color:#6b7280;letter-spacing:.08em">TICKER</th>
          <th style="padding:10px 8px;text-align:left;font-size:11px;color:#6b7280">COMPANY</th>
          <th style="padding:10px 8px;text-align:left;font-size:11px;color:#6b7280">PRICE</th>
          <th style="padding:10px 8px;text-align:left;font-size:11px;color:#6b7280">CHG</th>
          <th style="padding:10px 16px;text-align:left;font-size:11px;color:#6b7280">SIGNAL</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <div style="margin-top:24px;padding:16px;background:#111520;border-radius:8px;font-size:12px;color:#6b7280">
        Este é um alerta automático do seu sistema de monitoramento de portfolio.<br>
        Verifique o <a href="https://femsant0905-sudo.github.io/portfolio/" style="color:#60a5fa">dashboard</a> para análise completa.
      </div>
    </div>"""
    return subject, body

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n🔍 Monitor run — {now_str}")

    if not is_market_hours():
        print("  ⏸️  Outside market hours — skipping")
        return

    all_tickers = list(OPEN.keys()) + list(WATCH.keys())
    print(f"  Fetching {len(all_tickers)} tickers...")
    prices = fetch_prices(all_tickers)

    # Save latest prices
    PRICES_FILE.parent.mkdir(parents=True, exist_ok=True)
    PRICES_FILE.write_text(json.dumps(prices, indent=2))

    state = load_state()
    alerts = []

    # Check open positions
    for ticker, cfg in OPEN.items():
        p = prices.get(ticker, {}).get("price")
        if p is None:
            continue
        sig = open_signal(ticker, p)
        prev_sig = state.get(ticker, {}).get("signal")

        # Alert on: first time hitting target, stop loss, or transition back to profit/loss
        alert_signals = {"AT_TARGET", "STOP_LOSS"}
        if sig in alert_signals and sig != prev_sig:
            alerts.append({"ticker": ticker, "company": cfg["company"], "signal": sig, "price": p})
            print(f"  🔔 {ticker} → {sig} @ ${p:,.2f}")

        state[ticker] = {"signal": sig, "price": p, "ts": now_str}

    # Check watchlist
    for ticker, cfg in WATCH.items():
        p = prices.get(ticker, {}).get("price")
        if p is None:
            continue
        sig = watch_signal(ticker, p)
        prev_sig = state.get(ticker, {}).get("signal")

        # Alert only on meaningful transitions
        important = {"BUY_NOW", "GOOD"}
        if sig in important and sig != prev_sig:
            alerts.append({"ticker": ticker, "company": cfg["company"], "signal": sig, "price": p})
            print(f"  🔔 {ticker} → {sig} @ ${p:,.2f}")

        state[ticker] = {"signal": sig, "price": p, "ts": now_str}

    save_state(state)

    if alerts:
        print(f"  📧 Sending alert email ({len(alerts)} signals)...")
        subject, body = alert_html(alerts, prices)
        send_email(subject, body)
    else:
        print(f"  ✅ No new signals — no email sent")

    print("  Done.\n")

if __name__ == "__main__":
    main()
