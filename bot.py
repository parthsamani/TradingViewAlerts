from fastapi import FastAPI
import requests, time, threading, os

app = FastAPI()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

CLAUSE = "( futures ( latest close > 110 and latest close < 750 and latest close > latest low ( 50 ) * 1 and latest close < latest low ( 50 ) * 1.08 and latest rsi ( 14 ) < 45 ) )"
old = set()

def send(msg):
    try:
        if not BOT_TOKEN or not CHAT_ID:
            print("BOT_TOKEN/CHAT_ID missing!")
            return
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
        print(f"Telegram: {r.text}")
    except Exception as e:
        print(f"Send Error: {e}")

def loop():
    global old
    while True:
        try:
            s = requests.Session()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Referer": "https://chartink.com/screener/buying-range-screener-bottom-2nd-box-logic",
                "X-Requested-With": "XMLHttpRequest"
            }
            # Pehle page visit karke cookie lena zaruri hai
            s.get("https://chartink.com/screener/buying-range-screener-bottom-2nd-box-logic", headers=headers, timeout=15)
            time.sleep(2)
            r = s.post("https://chartink.com/screener/process", data={"scan_clause": CLAUSE}, headers=headers, timeout=20)
            
            print(f"Chartink Status: {r.status_code}")
            data = r.json()
            stocks = [x['nsecode'] for x in data.get('data',[])]
            new = set(stocks)
            print(f"Found: {new}")
            
            if new:
                fresh = new - old if old else new
                for st in fresh:
                    send(f"🟢 *BUYING RANGE - Bottom 2nd Box*\n\nStock: *{st}*\nRange: 110-750 F&O\nLogic: 50D Low + RSI<45\n\nTime: {time.strftime('%d-%m %H:%M')}")
                old = new
            else:
                print("No stocks in buying zone right now")

        except Exception as e:
            print(f"Loop Error: {e}")
        time.sleep(120)

threading.Thread(target=loop, daemon=True).start()

@app.head("/")
def home_head():
    return {}

@app.get("/")
def home():
    return {"status": "Bot Running 24x7", "logic": "110-750 F&O Bottom 2nd Box", "last_stocks": list(old), "env_set": bool(BOT_TOKEN and CHAT_ID)}

@app.get("/test")
def test():
    send("✅ Test Message: Bot sahi kaam kar raha hai!")
    return {"sent": True}
