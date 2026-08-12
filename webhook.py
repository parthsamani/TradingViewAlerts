import hashlib
import json
import logging
import os
import traceback
from flask import Flask, request, jsonify
from config import WEBHOOK_SECRET
from database import get_webhook, mark_webhook_alert, save_alert
from telegram import Bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
logger.info(f"Bot Token Loaded: {BOT_TOKEN[:10]}...") # sirf first 10 digit

def fingerprint(data, token):
    raw = json.dumps(data, sort_keys=True, default=str, separators=(",", ":")) + "|" + token
    return hashlib.sha256(raw.encode()).hexdigest()

def parse_payload():
    if request.is_json:
        data = request.get_json(silent=True)
        return data if data is not None else {}
    return dict(request.form)

@app.get("/")
def health():
    return jsonify({"status": "ok"})

def send_telegram_alert(chat_id, data):
    try:
        symbol = data.get('symbol', data.get('name', 'N/A'))
        price = data.get('price', data.get('close', 'N/A'))
        
        msg = f"🚨 *ALERT*\n\n*Symbol:* `{symbol}`\n*Price:* `{price}`"
        
        bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        logger.info(f"✅ Sent alert to {chat_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Telegram send failed: {e}")
        logger.error(traceback.format_exc())
        return False

@app.post("/webhook/<token>")
def receive(token):
    logger.info(f"📥 Webhook hit with token: {token}")
    
    if WEBHOOK_SECRET:
        supplied = request.headers.get("X-Webhook-Secret","")
        logger.info(f"Secret Check: {supplied == WEBHOOK_SECRET}")
        if supplied != WEBHOOK_SECRET:
            return jsonify({"ok":False,"error":"unauthorized"}),401

    hook = get_webhook(token)
    if not hook:
        logger.error(f"Token invalid: {token}")
        return jsonify({"ok":False,"error":"invalid webhook"}),404
    
    chat_id = hook["chat_id"]
    logger.info(f"Found chat_id: {chat_id}")

    data = parse_payload()
    logger.info(f"Data received: {data}")
    fp = fingerprint(data, token)

    if not save_alert(chat_id, token, json.dumps(data, default=str), fp):
        logger.info("Duplicate alert, skipping")
        return jsonify({"ok":True,"duplicate":True}),200

    mark_webhook_alert(token)
    send_telegram_alert(chat_id, data) # yaha send hoga
    
    return jsonify({"ok":True}),200
