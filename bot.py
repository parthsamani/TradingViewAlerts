from fastapi import FastAPI
import requests
import time
import threading
import os
import re

app = FastAPI()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

CLAUSE = "( futures ( latest close > 110 and latest close < 750 and latest close > latest low ( 50 ) * 1 and latest close < latest low ( 50 ) * 1.08 and latest rsi ( 14 ) < 45 ) )"

old = set()

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown"
        }
        r = requests.post(url, json=payload, timeout=15)
        print(f"Telegram Send: {r.status_code}")
        return r
    except Exception as e:
        print(f"Send Error: {e}")

def loop():
    global old
    print("Loop Started...")
    time.sleep(10)
    while True:
        try:
            s = requests.Session()
            s.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            })

            resp = s.get(
                "https://chartink.com/screener/buying-range-screener-bottom-2nd-box-logic",
                timeout=20
            )

            m = re.search(r'"csrf-token" content="([^"]+)"', resp.text)

            if not m:
                print("CSRF nahi mila, retry in 2 min")
                time.sleep(120)
                continue

            token = m.group(1)
            print(f"CSRF Found: {token[:10]}...")

            r = s.post(
                "https://chartink.com/screener/process",
                data={"scan_clause": CLAUSE},
                headers={
                    "X-Csrf-Token": token,
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": "https://chartink.com/screener/buying-range-screener-bottom-2nd-box-logic"
                },
                timeout=20
            )

            data = r.json()
            stocks = [x['nsecode'] for x in data.get('data', [])]
            new = set(stocks)

            print(f"Found Stocks: {new}")

            if new:
                fresh = new - old if old else new
                for st in fresh:
                    send(f"🟢 *{st}* Buying Range me hai\nTime: {time.strftime('%H:%M')}")
                    time.sleep(1)
                old = new
            else:
                print("No stocks right now")

        except Exception as e:
            print(f"Loop Error: {e}")

        time.sleep(120)

@app.on_event("startup")
def on_start():
    threading.Thread(target=loop, daemon=True).start()

@app.get("/")
def home():
    return {
        "status": "Bot Running 24x7",
        "last_stocks": list(old),
        "chat_id": CHAT_ID
    }

@app.get("/test")
def test():
    send("✅ Test OK - Bot kaam kar raha hai!")
    return {"sent": True}
