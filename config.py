import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = {int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "").rstrip("/")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///chartink_bot.db")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is required")
if not WEBHOOK_BASE_URL:
    raise RuntimeError("WEBHOOK_BASE_URL is required")
