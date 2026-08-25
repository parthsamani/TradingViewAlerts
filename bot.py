from fastapi import FastAPI
import requests, time, threading

app = FastAPI()
BOT_TOKEN = "8751196373:AAH2nBmVvgAqJsNDHIOlvfxMudGUnGtwbvo"
CHAT_ID = "5980906524"
CLAUSE = "( futures ( latest close > 110 and latest close < 750 and latest close > latest low ( 50 ) * 1 and latest close < latest low ( 50 ) * 1.08 and latest rsi ( 14 ) < 45 ) )"
old = set()

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def loop():
    global old
    while True:
        try:
            s = requests.Session()
            s.get("https://chartink.com/screener/buying-range-screener-bottom-2nd-box-logic", headers={"User-Agent": "Mozilla/5.0"})
            r = s.post("https://chartink.com/screener/process", data={"scan_clause": CLAUSE}, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            stocks = [x['nsecode'] for x in r.json().get('data',[])]
            new = set(stocks)
            fresh = new - old
            if fresh and old:
                for st in fresh:
                    send(f"🟢 *BUYING RANGE ALERT - Bottom 2nd Box*\n\nStock: *{st}*\nRange: 110-750 F&O\nLogic: 50 Day Low ke paas\n\n⏰ {time.strftime('%d-%m %H:%M')}")
            if new:
                old = new
        except: pass
        time.sleep(120)

threading.Thread(target=loop, daemon=True).start()

@app.get("/")
def home(): 
    return {"status": "Bot Running 24x7", "last_scan": list(old)}
