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

# Used to compute each ticker's relative 1-month performance
BENCHMARK_TICKER = "^GSPC"
# Daily % move (absolute value) that triggers an alert flag on a ticker
ALERT_THRESHOLD_PCT = 3.0

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def compute_sma(close_series, window):
    """Simple moving average over the last `window` trading days."""
    if len(close_series) < window:
        return None
    return close_series.tail(window).mean()


def compute_rsi(close_series, period=14):
    """Relative Strength Index (simple average version, not Wilder-smoothed)."""
    if len(close_series) < period + 1:
        return None
    delta = close_series.diff().dropna()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.tail(period).mean()
    avg_loss = loss.tail(period).mean()
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def one_month_return(close_series):
    """Approx. 1-month return using ~21 trading days."""
    if len(close_series) < 22:
        return None
    return (close_series.iloc[-1] / close_series.iloc[-22] - 1) * 100


def fetch_data(ticker: str):
    """Fetch price, moving averages, RSI and 1-month return for one ticker."""
    try:
        stock = yf.Ticker(ticker)
        # 1 year of history gives us enough data for the 200-day SMA
        hist = stock.history(period="1y")
        if hist.empty or len(hist) < 2:
            return None

        close = hist["Close"]
        last_close = close.iloc[-1]
        prev_close = close.iloc[-2]
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
            "sma50": compute_sma(close, 50),
            "sma200": compute_sma(close, 200),
            "rsi14": compute_rsi(close, 14),
            "return_1m": one_month_return(close),
        }
    except Exception as exc:  # keep the report alive even if one ticker fails
        print(f"[WARN] Could not fetch data for {ticker}: {exc}", file=sys.stderr)
        return None


def build_message() -> str:
    today = datetime.now().strftime("%d %B %Y")
    lines = [f"*Daily Market Report — {today}*", ""]

    # Fetch the benchmark once, used for relative performance on every ticker
    benchmark_data = fetch_data(BENCHMARK_TICKER)
    benchmark_return_1m = benchmark_data["return_1m"] if benchmark_data else None

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

        # Alert flag — only shown when the daily move is unusually large
        if abs(data["change_pct"]) >= ALERT_THRESHOLD_PCT:
            direction = "surged" if data["change_pct"] > 0 else "dropped"
            lines.append(
                f"   🚨 ALERT: {data['ticker']} {direction} "
                f"{data['change_pct']:+.2f}% today (threshold: ±{ALERT_THRESHOLD_PCT:.0f}%)"
            )
        

        # Technical indicators line (only shown if we have enough history)
        sma_parts = []
        if data["sma50"] is not None:
            sma_parts.append(f"SMA50: {data['sma50']:.2f}")
        if data["sma200"] is not None:
            sma_parts.append(f"SMA200: {data['sma200']:.2f}")
        if data["rsi14"] is not None:
            sma_parts.append(f"RSI14: {data['rsi14']:.1f}")
        if sma_parts:
            lines.append("   " + " | ".join(sma_parts))

        # 1-month return vs benchmark
        if data["return_1m"] is not None:
            rel_str = ""
            if benchmark_return_1m is not None and data["ticker"] != BENCHMARK_TICKER:
                relative = data["return_1m"] - benchmark_return_1m
                rel_str = f" (vs S&P500: {relative:+.2f} pp)"
            lines.append(f"   1M: {data['return_1m']:+.2f}%{rel_str}")

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
