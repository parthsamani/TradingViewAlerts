from fastapi import FastAPI
import requests, time, threading, os, re

app = FastAPI()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
CLAUSE = "( futures ( latest close > 110 and latest close < 750 and latest close > latest low ( 50 ) * 1 and latest close < latest low ( 50 ) * 1.08 and latest rsi ( 14 ) < 45 ) )"
old = set()

def send(msg):
    try:
        print(f"Sending to {CHAT_ID}: {msg[:20]}")
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
        print(f"Telegram Response: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Send Error: {e}")

def loop():
    global old
    print("Loop Started...")
    # STARTUP TEST - ye message aana hi chahiye
    send(f"🚀 Bot Live Ho Gaya!\nID: {CHAT_ID}\nTime: {time.strftime('%H:%M')}")
    time.sleep(10)
    while True:
        try:
            print("Chartink check kar raha hu...")
            s = requests.Session()
            s.headers.update({"User-Agent": "Mozilla/5.0"})
            resp = s.get("https://chartink.com/screener/buying-range-screener-bottom-2nd-box-logic", timeout=30)
            print(f"Page Status: {resp.status_code}")
            m = re.search(r'"csrf-token" content="([^"]+)"', resp.text)
            if not m:
                print("CSRF nahi mila")
                time.sleep(60); continue
            token = m.group(1)
            print(f"CSRF OK: {token[:10]}")
            r = s.post("https://chartink.com/screener/process", data={"scan_clause": CLAUSE}, headers={"X-Csrf-Token": token, "X-Requested-With": "XMLHttpRequest", "Referer": "https://chartink.com/screener/buying-range-screener-bottom-2nd-box-logic"}, timeout=30)
            print(f"Process Status: {r.status_code}")
            stocks = [x['nsecode'] for x in r.json().get('data',[])]
            print(f"Found: {stocks}")
            new = set(stocks)
            if new:
                fresh = new - old if old else new
                for st in fresh:
                    send(f"🟢 *{st}* Buying Range me hai")
                old = new
        except Exception as e:
            print(f"Loop Error: {e}")
        print("2 min wait...")
        time.sleep(120)

@app.on_event("startup")
def on_start():
    threading.Thread(target=loop, daemon=True).start()

@app.get("/")
def home():
    return {"status": "Running", "chat_id": str(CHAT_ID), "token_set": bool(BOT_TOKEN), "stocks": list(old)}

@app.get("/test")
def test():
    send("✅ Test OK")
    return {"sent": True, "chat_id": CHAT_ID}
