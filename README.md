# Daily Market Report Bot

A small automated bot that fetches data for a list of stock tickers every day
and sends a formatted summary to a Telegram chat. Runs for free on GitHub
Actions — no server needed.

## How it works

1. `main.py` fetches the latest price and daily % change for each ticker in
   `TICKERS` using [yfinance](https://pypi.org/project/yfinance/) (free, no
   API key required).
2. It formats the results into a Telegram message and sends it via the
   [Telegram Bot API](https://core.telegram.org/bots/api).
3. A GitHub Actions workflow (`.github/workflows/daily_report.yml`) runs the
   script automatically every weekday morning.

## Setup

### 1. Create a Telegram bot
- Open Telegram, search for **@BotFather**, send `/newbot`, follow the
  instructions.
- BotFather gives you a **token** like `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`.
  This is your `TELEGRAM_BOT_TOKEN`.

### 2. Get your chat id
- Send any message to your new bot (e.g. "hi").
- In a browser, open:
  `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
- Look for `"chat":{"id": 123456789, ...}` in the response — that number is
  your `TELEGRAM_CHAT_ID`.
- (Alternative: message **@userinfobot**, it replies with your chat id
  directly.)

### 3. Run it locally (to test)
```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="your-token-here"
export TELEGRAM_CHAT_ID="your-chat-id-here"
python main.py
```
On Windows (PowerShell), use `$env:TELEGRAM_BOT_TOKEN="..."` instead of `export`.

### 4. Choose your tickers
Edit the `TICKERS` list at the top of `main.py`. Use Yahoo Finance ticker
symbols, e.g.:
- `AAPL` → Apple (NASDAQ)
- `NESN.SW` → Nestlé (SIX Swiss Exchange)
- `UBSG.SW` → UBS Group (SIX Swiss Exchange)
- `^GSPC` → S&P 500 index



