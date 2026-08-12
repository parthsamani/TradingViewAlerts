# ParthTraderAlerts Chartink Telegram Bot

Chartink webhook -> secure webhook endpoint -> Telegram Bot.

## 1. Create Telegram bot
Create a bot using BotFather and copy the token.

## 2. Deploy
Deploy this repository to Render as a Web Service.

Build:
pip install -r requirements.txt

Start:
python bot.py

## 3. Environment variables
BOT_TOKEN = Telegram bot token
ADMIN_IDS = comma-separated Telegram numeric user IDs
WEBHOOK_BASE_URL = your public HTTPS Render URL
WEBHOOK_SECRET = optional extra secret

Do not commit real secrets.

## 4. User setup
Open the bot and send:
/start
/connect

The bot creates a unique HTTPS webhook URL. Add that URL to your Chartink alert webhook configuration.

## 5. Test
Use:
/test
/status

Then trigger a Chartink scanner alert.

## Notes
- SQLite is included for simple single-instance deployments.
- For production scaling across multiple instances, replace SQLite with PostgreSQL and use a proper queue such as Redis.
- Never expose BOT_TOKEN or WEBHOOK_SECRET publicly.
- The webhook URL itself should be treated as sensitive because it maps alerts to a Telegram chat.
