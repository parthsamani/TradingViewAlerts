from fastapi import FastAPI
import requests, time, threading, os

app = FastAPI()

# Render me Environment Variables me add karna hai
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Tumhara Final Bottom 2nd Box Clause
CLAUSE = "( futures ( latest close > 110 and latest close < 750 and latest close > latest low ( 50 ) * 1 and latest close < latest low ( 50 ) * 1.08 and latest rsi ( 14 ) < 45 ) )"
old = set()

def send(msg):
    try:
        if not BOT_TOKEN or not CHAT_ID:
            return
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def loop():
    global old
    while True:
        try:
            s = requests.Session()
            s.get("https://chartink.com/screener/buying-range-screener-bottom-2nd-box-logic", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            r = s.post("https://chartink.com/screener/process", data={"scan_clause": CLAUSE}, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            stocks = [x['nsecode'] for x in r.json().get('data',[])]
            new = set(stocks)
            fresh = new - old
            if fresh and old:
                for st in fresh:
                    send(f"🟢 *BUYING RANGE - Bottom 2nd Box*\n\nStock: *{st}*\nRange: 110-750 F&O\nLogic: 50D Low + RSI<45\n\nTime: {time.strftime('%d-%m %H:%M')}")
            if new:
                old = new
        except:
            pass
        time.sleep(120)

threading.Thread(target=loop, daemon=True).start()

@app.get("/")
def home():
    return {"status": "Bot Running 24x7", "logic": "110-750 F&O Bottom 2nd Box", "last_stocks": list(old)}
