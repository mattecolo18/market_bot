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

### 5. Deploy for free with GitHub Actions
1. Push this folder to a new GitHub repository.
2. In the repo: **Settings → Secrets and variables → Actions → New repository secret**
   - Add `TELEGRAM_BOT_TOKEN`
   - Add `TELEGRAM_CHAT_ID`
3. That's it — the workflow in `.github/workflows/daily_report.yml` will run
   automatically on the schedule. You can also trigger it manually from the
   **Actions** tab (`Run workflow`) to test it without waiting.

## Ideas to extend it (good for making the project more "complete")
- Add more asset classes: FX rates, crypto, bond yields (yfinance supports
  most of these).
- Add a simple technical indicator (e.g. 50-day moving average, RSI) next to
  each price.
- Pull top financial headlines (e.g. via an RSS feed) and include 2-3 in the
  message.
- Store daily data in a CSV/SQLite file (committed back to the repo) to build
  your own historical dataset over time — this alone could become a second
  project (data analysis on data you collected yourself).
- Turn it into a two-way bot: reply to `/price AAPL` on demand using
  `python-telegram-bot` instead of a one-way daily push.
