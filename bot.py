import os, re, uuid, logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///notifyu.db")
PORT = int(os.getenv("PORT", 10000))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NotifyU-Clone")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
db = SQLAlchemy(app)

# --- DB Models ---
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

# --- Telegram Bot ---
application = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    with app.app_context():
        u = User.query.filter_by(chat_id=chat_id).first()
        if not u:
            u = User(chat_id=chat_id, username=user.username)
            db.session.add(u)
            db.session.commit()
    
    text = f"""🚀 **Welcome to Chartink → Telegram Alerts**

Hi {user.first_name}! Main tumhare Chartink scanners ko Telegram se connect karunga.

**Setup 2 min me:**
1. /connect - Apna unique webhook lo
2. Chartink > Create Alert > Webhook me paste karo
3. Done! Real-time alerts yahi ayenge

Commands:
/connect - Webhook setup
/status - Connection check
/myid - Tumhara Chat ID
/test - Test alert
/help - Full guide"""

    kb = [[InlineKeyboardButton("🔗 Connect Now", callback_data="connect")],
          [InlineKeyboardButton("❓ Help", callback_data="help")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def connect_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    with app.app_context():
        u = User.query.filter_by(chat_id=chat_id).first()
        webhook_url = f"{os.getenv('RENDER_EXTERNAL_URL')}/webhook/{u.webhook_token}"
        u.is_connected = True
        db.session.commit()
    
    text = f"""✅ **Webhook Ready!**

**Tumhara Unique Webhook URL:**
`{webhook_url}`

**Chartink me kaise lagaye:**
1. chartink.com > Screener > Run Scan
2. `Create Alert` > `Webhook URL` me upar wala URL paste karo
3. Alert Name: `My F&O Scanner`
4. Save

Ab koi bhi stock scan me ayega to turant Telegram pe msg ayega.

/test dabake check kar lo."""

    await update.message.reply_text(text, parse_mode="Markdown")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with app.app_context():
        u = User.query.filter_by(chat_id=update.effective_chat.id).first()
        if not u: return await update.message.reply_text("Pehle /start karo")
        status = "🟢 Connected" if u.is_connected else "🔴 Disconnected"
        last = u.last_alert_at.strftime("%d-%m %H:%M") if u.last_alert_at else "Kabhi nahi"
        await update.message.reply_text(f"Status: {status}\nWebhook: `{u.webhook_token}`\nLast Alert: {last}\nDup Protection: {u.duplicate_protection}", parse_mode="Markdown")

async def myid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your Chat ID: `{update.effective_chat.id}`\nUsername: @{update.effective_user.username}\n\nGroup me add karke /myid bhejo to Group ID milega.", parse_mode="Markdown")

async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """🚨 **TEST ALERT - Chartink Scanner**
    
📈 **Stock:** RELIANCE
💰 **Price:** ₹1,502.35
📊 **Scan:** F&O Volume Spike
⏰ **Time:** {}
🔗 **Chart:** https://chartink.com/stocks/reliance.html

⚡️ Powered by ParthTraderAlerts""".format(datetime.now().strftime("%d-%b %I:%M %p"))
    await update.message.reply_text(msg, parse_mode="Markdown")

async def disconnect_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with app.app_context():
        u = User.query.filter_by(chat_id=update.effective_chat.id).first()
        u.webhook_token = uuid.uuid4().hex[:16]
        u.is_connected = False
        db.session.commit()
    await update.message.reply_text("🔴 Disconnected. Webhook reset ho gaya. /connect se naya banao.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Help:\n1. /connect se URL lo\n2. Chartink alert me Webhook URL paste karo\n3. Message body khali chhod do\n4. /test se check karo\n\nIssue? @ParthTraderAlerts pe msg karo.", parse_mode="Markdown")

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("Duplicate Protection ON/OFF", callback_data="toggle_dup")]]
    await update.message.reply_text("Settings:", reply_markup=InlineKeyboardMarkup(kb))

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("connect", connect_cmd))
application.add_handler(CommandHandler("status", status_cmd))
application.add_handler(CommandHandler("myid", myid_cmd))
application.add_handler(CommandHandler("test", test_cmd))
application.add_handler(CommandHandler("disconnect", disconnect_cmd))
application.add_handler(CommandHandler("help", help_cmd))
application.add_handler(CommandHandler("settings", settings_cmd))

# --- Webhook Endpoint for Chartink ---
@app.route('/webhook/<token>', methods=['POST'])
def chartink_webhook(token):
    with app.app_context():
        user = User.query.filter_by(webhook_token=token).first()
        if not user:
            return jsonify({"error": "Invalid token"}), 404
        
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        # Chartink sends like: {"stocks": "RELIANCE, INFY", "scan_name": "..."}
        stocks_raw = data.get("stocks") or data.get("triggeredStocks") or str(data)[:500]
        
        # Duplicate Protection - 5 min
        if user.duplicate_protection:
            for stock in re.findall(r"[A-Z]{2,20}", stocks_raw.upper()):
                exists = AlertLog.query.filter_by(chat_id=user.chat_id, stock=stock).filter(AlertLog.created_at > datetime.utcnow() - timedelta(minutes=5)).first()
                if exists:
                    continue
                log = AlertLog(chat_id=user.chat_id, stock=stock)
                db.session.add(log)
        
        user.last_alert_at = datetime.utcnow()
        db.session.commit()

        # Clean formatted message
        msg = f"""🚨 **Chartink Alert Triggered**

📊 **Scan:** {data.get('scan_name', 'Your F&O Scanner')}
📈 **Stocks:** {stocks_raw}
⏰ **Time:** {datetime.now().strftime('%d-%b %I:%M:%S %p')}

🔗 [Open Chartink](https://chartink.com/dashboard)

💡 /settings se format change karo"""
        
        # Send via bot
        import asyncio
        async def send():
            await application.bot.send_message(chat_id=user.chat_id, text=msg, parse_mode="Markdown", disable_web_page_preview=True)
        try:
            asyncio.run(send())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(send())

        return jsonify({"status": "sent"}), 200

@app.route('/')
def home():
    return "NotifyU Clone Bot Live!"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

def run_bot():
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    run_bot()
