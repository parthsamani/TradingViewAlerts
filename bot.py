import os, re, uuid, logging, asyncio
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///notifyu.db")
PORT = int(os.getenv("PORT", 10000))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NotifyU-Clone")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(100))
    webhook_token = db.Column(db.String(64), unique=True, default=lambda: uuid.uuid4().hex[:16])
    is_connected = db.Column(db.Boolean, default=False)
    last_alert_at = db.Column(db.DateTime)
    duplicate_protection = db.Column(db.Boolean, default=True)

class AlertLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.BigInteger)
    stock = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

application = Application.builder().token(BOT_TOKEN).build()

# ... (tumhare saare handlers yaha same rakho - start, connect, status, myid, test, disconnect, help, settings) ...

# --- Webhook ---
@app.route('/webhook/<token>', methods=['POST'])
def chartink_webhook(token):
    with app.app_context():
        user = User.query.filter_by(webhook_token=token).first()
        if not user:
            return jsonify({"error": "Invalid token"}), 404
        data = request.get_json(silent=True) or {}
        stocks_raw = str(data.get("stocks") or data)[:500]
        user.last_alert_at = datetime.utcnow()
        db.session.commit()
        # send message
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.create_task(application.bot.send_message(chat_id=user.chat_id, text=f"🚨 Chartink Alert:\n{stocks_raw}"))
        return jsonify({"status": "sent"}), 200

@app.route('/')
def home():
    return "NotifyU Clone Bot Live!"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    # FIX for Python 3.14
    try:
        asyncio.set_event_loop(asyncio.new_event_loop())
    except:
        pass
    logger.info("Starting Polling...")
    application.run_polling(drop_pending_updates=True)
