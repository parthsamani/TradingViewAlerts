import hashlib
import json
import logging
import os
from flask import Flask, request, jsonify
from config import WEBHOOK_SECRET
from database import get_webhook, mark_webhook_alert, save_alert
from telegram import Bot

logger = logging.getLogger(__name__)
app = Flask(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')  # Render me env variable dalna
bot = Bot(token=BOT_TOKEN)

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
    return jsonify({"status": "ok", "service": "ParthTraderAlerts Chartink Webhook"})

def send_telegram_alert(chat_id, data):
    try:
        # Chartink ka data format ke hisab se message bana
        symbol = data.get('symbol', 'N/A')
        price = data.get('price', data.get('close', 'N/A'))
        condition = data.get('condition', 'Alert Triggered')
        
        msg = f"🚨 *F&O ALERT*\n\n"
        msg += f"*Symbol:* {symbol}\n"
        msg += f"*Price:* {price}\n"
        msg += f"*Condition:* {condition}\n"
        msg += f"*Time:* {data.get('time', '')}"
        
        bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        logger.info(f"Sent alert to {chat_id}")
    except Exception as e:
        logger.error(f"Failed to send telegram message: {e}")

@app.post("/webhook/<token>")
def receive(token):
    if WEBHOOK_SECRET:
        supplied = request.headers.get("X-Webhook-Secret", "")
        if supplied != WEBHOOK_SECRET:
            return jsonify({"ok": False, "error": "unauthorized"}), 401

    hook = get_webhook(token)
    if not hook:
        return jsonify({"ok": False, "error": "invalid webhook"}), 404

    data = parse_payload()
    fp = fingerprint(data, token)

    if not save_alert(hook["chat_id"], token, json.dumps(data, default=str), fp):
        return jsonify({"ok": True, "duplicate": True}), 200

    mark_webhook_alert(token)
    
    # YAHI NAYA CODE HAI - TELEGRAM PE BHEJ DO
    send_telegram_alert(hook["chat_id"], data)
    
    app.config["LAST_ALERTS"] = getattr(app.config, "LAST_ALERTS", [])
    app.config["LAST_ALERTS"].append((hook["chat_id"], data, token))
    return jsonify({"ok": True}), 200
