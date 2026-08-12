import asyncio
import logging
import threading
import json
from flask import request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_IDS, WEBHOOK_BASE_URL
from database import init_db, upsert_user, get_user, create_webhook, get_webhooks, disable_webhooks, stats
from webhook import app as flask_app

logging.basicConfig(level=logging.INFO)
log=logging.getLogger("chartink-bot")

def format_alert(data):
    if not isinstance(data,dict):
        return f"🚨 CHARTINK ALERT\n\n{data}"
    symbol = data.get("symbol") or data.get("stock") or data.get("name") or data.get("scrip") or "Unknown"
    price = data.get("price") or data.get("ltp") or data.get("close") or ""
    scan = data.get("scan_name") or data.get("scanner") or data.get("alert_name") or "Chartink"
    direction = data.get("signal") or data.get("action") or data.get("direction") or "ALERT"
    lines=[
        "🚨 <b>CHARTINK ALERT</b>",
        "",
        f"📊 <b>{direction}</b>",
        f"📈 Stock: <b>{symbol}</b>",
    ]
    if price != "":
        lines.append(f"💰 Price: <b>{price}</b>")
    lines += [f"🔎 Scanner: {scan}", "⚡ Real-Time Alert"]
    return "\n".join(lines)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u=update.effective_user
    upsert_user(update.effective_chat.id,u.username,u.first_name)
    text=(
        "👋 <b>Welcome to ParthTraderAlerts Chartink Bot</b>\\n\\n"
        "Connect your Chartink webhook and receive real-time stock alerts securely.\\n\\n"
        "Use /connect to create your personal webhook.\\n"
        "/status - View connection\\n"
        "/test - Send a test alert\\n"
        "/disconnect - Disable webhooks\\n"
        "/help - Help"
    )
    await update.message.reply_text(text,parse_mode="HTML")

async def connect(update, context):
    chat_id=update.effective_chat.id
    u=update.effective_user
    upsert_user(chat_id,u.username,u.first_name)
    token=create_webhook(chat_id)
    url=f"{WEBHOOK_BASE_URL}/webhook/{token}"
    await update.message.reply_text(
        "✅ <b>Webhook Created</b>\\n\\n"
        f"<b>Webhook URL:</b>\\n<code>{url}</code>\\n\\n"
        "Paste this URL into your Chartink webhook configuration.\\n"
        "Keep this URL private because it identifies your Telegram destination.",
        parse_mode="HTML"
    )

async def status(update, context):
    hooks=get_webhooks(update.effective_chat.id)
    if not hooks:
        await update.message.reply_text("❌ No active webhook. Use /connect.")
        return
    lines=["🔐 <b>Your Webhooks</b>",""]
    for h in hooks:
        state="🟢 Active" if h["active"] else "🔴 Disabled"
        lines.append(f"{state} — {h['name']}")
        lines.append(f"Last alert: {h['last_alert_at'] or 'Never'}")
    await update.message.reply_text("\n".join(lines),parse_mode="HTML")

async def disconnect(update, context):
    disable_webhooks(update.effective_chat.id)
    await update.message.reply_text("🔴 All your Chartink webhooks have been disabled.")

async def test(update, context):
    await update.message.reply_text(
        "🚨 <b>CHARTINK ALERT</b>\\n\\n"
        "📊 <b>TEST ALERT</b>\\n"
        "📈 Stock: <b>RELIANCE</b>\\n"
        "💰 Price: <b>1482.50</b>\\n"
        "⚡ Real-Time Alert\\n\\n"
        "This is a bot test notification.",
        parse_mode="HTML"
    )

async def help_cmd(update, context):
    await update.message.reply_text(
        "<b>Chartink Setup</b>\\n\\n"
        "1. Open Chartink and configure your scanner alert.\\n"
        "2. Use /connect here.\\n"
        "3. Copy the generated HTTPS webhook URL.\\n"
        "4. Add it to Chartink's webhook configuration.\\n"
        "5. Use /status to verify the connection.\\n"
        "6. Use /test to verify Telegram delivery.",
        parse_mode="HTML"
    )

async def admin_stats(update, context):
    if update.effective_user.id not in ADMIN_IDS:
        return
    users,hooks,alerts=stats()
    await update.message.reply_text(
        f"📊 <b>Bot Statistics</b>\\n\\n"
        f"👤 Active users: {users}\\n"
        f"🔗 Active webhooks: {hooks}\\n"
        f"🚨 Total alerts: {alerts}",
        parse_mode="HTML"
    )

import os

flask_app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
    debug=False,
    use_reloader=False
)

async def alert_dispatcher(app):
    seen=[]
    while True:
        items=flask_app.config.get("LAST_ALERTS",[])
        while items:
            chat_id,data,token=items.pop(0)
            try:
                await app.bot.send_message(chat_id=chat_id,text=format_alert(data),parse_mode="HTML")
            except Exception:
                log.exception("Telegram delivery failed")
        await asyncio.sleep(0.5)

async def post_init(application):
    application.create_task(alert_dispatcher(application))

def main():
    init_db()
    threading.Thread(target=run_flask,daemon=True).start()
    application=(Application.builder().token(BOT_TOKEN).post_init(post_init).build())
    application.add_handler(CommandHandler("start",start))
    application.add_handler(CommandHandler("connect",connect))
    application.add_handler(CommandHandler("status",status))
    application.add_handler(CommandHandler("disconnect",disconnect))
    application.add_handler(CommandHandler("test",test))
    application.add_handler(CommandHandler("help",help_cmd))
    application.add_handler(CommandHandler("stats",admin_stats))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__":
    main()
