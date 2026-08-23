import os, asyncio, yfinance as yf
from datetime import datetime
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
app = Flask(__name__)

FNO = ["RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","TCS.NS","INFY.NS","LT.NS","ITC.NS","BHARTIARTL.NS","BAJFINANCE.NS","MARUTI.NS","M&M.NS","TATAMOTORS.NS","SUNPHARMA.NS","HCLTECH.NS","WIPRO.NS","ADANIENT.NS","ADANIPOWER.NS","ADANIPORTS.NS","TATAPOWER.NS","TATASTEEL.NS","JSWSTEEL.NS","ZOMATO.NS","JIOFIN.NS","HYUNDAI.NS"]

# User Settings DB (simple memory, restart pe default)
user_settings = {}
# default: open near prev 0.6%, movement 1.0%
def get_settings(chat_id):
    return user_settings.get(chat_id, {"near": 0.6, "move": 1.0})

application = Application.builder().token(BOT_TOKEN).build()

def get_fno_alerts(chat_id):
    cfg = get_settings(chat_id)
    alerts = []
    for sym in FNO:
        try:
            df_daily = yf.download(sym, period="5d", interval="1d", progress=False, auto_adjust=True)
            df_intra = yf.download(sym, period="1d", interval="5m", progress=False, auto_adjust=True)
            if len(df_daily) < 2 or len(df_intra) < 2: continue
            prev_close = float(df_daily['Close'].iloc[-2])
            today_open = float(df_daily['Open'].iloc[-1])
            curr_price = float(df_intra['Close'].iloc[-1])

            open_near_prev = abs(today_open - prev_close) / prev_close * 100 <= cfg["near"]
            if not open_near_prev: continue

            move_pct = (curr_price - today_open) / today_open * 100
            if abs(move_pct) >= cfg["move"]:
                side = "🟢 UP" if move_pct > 0 else "🔴 DOWN"
                alerts.append(f"{side} **{sym.replace('.NS','')}** {curr_price:.1f} ({move_pct:+.2f}%)\nPrev {prev_close:.1f} → Open {today_open:.1f}")
        except: continue
    return alerts

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 PDC Bot\n/scan - scan\n/auto - auto 5min\n/settings - % change\n/stop - stop")

async def scan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Scanning...")
    alerts = get_fno_alerts(update.effective_chat.id)
    if not alerts:
        cfg = get_settings(update.effective_chat.id)
        await update.message.reply_text(f"⏰ {datetime.now().strftime('%I:%M %p')} - Koi alert nahi.\nFilter: Open near {cfg['near']}% & Move {cfg['move']}%")
    else:
        await update.message.reply_text(f"🚨 **Alerts {datetime.now().strftime('%I:%M')}**\n\n" + "\n\n".join(alerts[:20]), parse_mode="Markdown")

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = get_settings(update.effective_chat.id)
    kb = [
        [InlineKeyboardButton(f"Near Prev: {cfg['near']}%", callback_data="noop"),
         InlineKeyboardButton(f"Move: {cfg['move']}%", callback_data="noop")],
        [InlineKeyboardButton("Near 0.3%", callback_data="near_0.3"), InlineKeyboardButton("Near 0.6%", callback_data="near_0.6"), InlineKeyboardButton("Near 1%", callback_data="near_1.0")],
        [InlineKeyboardButton("Move 0.5%", callback_data="move_0.5"), InlineKeyboardButton("Move 1%", callback_data="move_1.0"), InlineKeyboardButton("Move 1.5%", callback_data="move_1.5")],
    ]
    await update.message.reply_text(f"⚙️ **Settings**\n\n1. **Near Prev:** Kal ke close ke kitne % paas open hua ho\n2. **Move:** Open se kitna % bhaaga ho\n\nCurrent: Near={cfg['near']}% Move={cfg['move']}%", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def button_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    cfg = get_settings(chat_id)
    if query.data.startswith("near_"):
        cfg["near"] = float(query.data.split("_")[1])
    if query.data.startswith("move_"):
        cfg["move"] = float(query.data.split("_")[1])
    user_settings[chat_id] = cfg
    await query.edit_message_text(f"✅ Saved!\nNear: {cfg['near']}% | Move: {cfg['move']}%\n\nAb /scan karo.", reply_markup=query.message.reply_markup)

auto_users = set()
async def auto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auto_users.add(update.effective_chat.id)
    await update.message.reply_text("✅ Auto ON (9:15-11:30 har 5 min)")
async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auto_users.discard(update.effective_chat.id)
    await update.message.reply_text("🔴 Auto OFF")
async def myid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"ID: {update.effective_chat.id}")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("scan", scan_cmd))
application.add_handler(CommandHandler("fno", scan_cmd))
application.add_handler(CommandHandler("auto", auto_cmd))
application.add_handler(CommandHandler("stop", stop_cmd))
application.add_handler(CommandHandler("myid", myid_cmd))
application.add_handler(CommandHandler("settings", settings_cmd))
application.add_handler(CallbackQueryHandler(button_cb))

@app.route('/')
def home(): return "Bot Live with Settings"

async def auto_loop():
    while True:
        await asyncio.sleep(300)
        now = datetime.now()
        if not (9 <= now.hour <= 12): continue
        if not auto_users: continue
        for uid in list(auto_users):
            alerts = get_fno_alerts(uid)
            if alerts:
                msg = f"🚨 **Auto {now.strftime('%I:%M %p')}**\n\n" + "\n\n".join(alerts[:10])
                try: await application.bot.send_message(chat_id=uid, text=msg, parse_mode="Markdown")
                except: pass

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.create_task(auto_loop())
    application.run_polling(drop_pending_updates=True)
