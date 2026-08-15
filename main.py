"""
Daily Market Report Bot
------------------------
Fetches data for a list of stock tickers and sends a formatted
summary to a Telegram chat. Designed to run once a day (locally
via cron/Task Scheduler, or in the cloud via GitHub Actions).

Setup:
1. pip install -r requirements.txt
2. Create a Telegram bot via @BotFather -> get TELEGRAM_BOT_TOKEN
3. Get your chat id (see README.md) -> TELEGRAM_CHAT_ID
4. Set both as environment variables (or GitHub Actions secrets)
5. Edit the TICKERS list below with the companies you want to track
"""

import os
import sys
from datetime import datetime

import requests
import yfinance as yf

# ---------------------------------------------------------------
# CONFIGURATION — edit this list with the tickers you want to track.
# Use Yahoo Finance ticker format, e.g.:
#   "AAPL"      -> Apple (NASDAQ)
#   "NESN.SW"   -> Nestlé (SIX Swiss Exchange)
#   "UBSG.SW"   -> UBS Group (SIX Swiss Exchange)
#   "^GSPC"     -> S&P 500 index
# ---------------------------------------------------------------
TICKERS = ["AAPL", "MSFT", "NESN.SW", "UBSG.SW", "^GSPC"]

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def fetch_data(ticker: str):
    """Fetch the latest price and daily % change for one ticker."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist.empty or len(hist) < 2:
            return None

        last_close = hist["Close"].iloc[-1]
        prev_close = hist["Close"].iloc[-2]
        change_pct = (last_close - prev_close) / prev_close * 100

        info = stock.info
        name = info.get("shortName", ticker)
        currency = info.get("currency", "")

        return {
            "ticker": ticker,
            "name": name,
            "price": last_close,
            "change_pct": change_pct,
            "currency": currency,
        }
    except Exception as exc:  # keep the report alive even if one ticker fails
        print(f"[WARN] Could not fetch data for {ticker}: {exc}", file=sys.stderr)
        return None


def build_message() -> str:
    today = datetime.now().strftime("%d %B %Y")
    lines = [f"*Daily Market Report — {today}*", ""]

    for ticker in TICKERS:
        data = fetch_data(ticker)
        if data is None:
            lines.append(f"⚠️ {ticker}: data unavailable")
            continue

        arrow = "🟢" if data["change_pct"] >= 0 else "🔴"
        lines.append(
            f"{arrow} *{data['name']}* ({data['ticker']}): "
            f"{data['price']:.2f} {data['currency']} "
            f"({data['change_pct']:+.2f}%)"
        )

    lines.append("")
    lines.append("_Data via Yahoo Finance. Not investment advice._")
    return "\n".join(lines)


def send_telegram_message(text: str) -> dict:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    response = requests.post(url, data=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(
            "ERROR: TELEGRAM_BOT_TOKEN and/or TELEGRAM_CHAT_ID environment "
            "variables are not set. See README.md for setup instructions.",
            file=sys.stderr,
        )
        sys.exit(1)

    message = build_message()
    print(message)  # useful for debugging / GitHub Actions logs
    send_telegram_message(message)


if __name__ == "__main__":
    main()
