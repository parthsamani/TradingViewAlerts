from fastapi import FastAPI
import requests
import time
import threading
import os
import re
from datetime import datetime, timedelta

app = FastAPI()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

CLAUSE = "( futures ( latest close > 110 and latest close < 750 and latest close > latest low ( 50 ) * 1 and latest close < latest low ( 50 ) * 1.08 and latest rsi ( 14 ) < 45 ) )"

old = set()

def get_ist_time():
    # UTC to IST ( +5:30 )
    ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    return ist.strftime('%d-%m-%Y %I:%M %p')

def send(msg):
    try:
        print(f"Sending to {CHAT_ID}")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown"
        }
        r = requests.post(url, json=payload, timeout=15)
        print(f"Telegram Response: {r.status_code} - {r.text[:150]}")
    except Exception as e:
        print(f"Send Error: {e}")

def loop():
    global old
    print("Loop Started...")
    
    # Startup message with IST time
    send(f"🚀 *Bot Live Ho Gaya!*\n\nID: {CHAT_ID}\nTime: {get_ist_time()} IST\n\nAb har 2 min me scan hoga.")
    
    time.sleep(10)
    
    while True:
        try:
            print(f"[{get_ist_time()}] Chartink check kar raha hu...")
            
            s = requests.Session()
            s.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            
            resp = s.get(
                "https://chartink.com/screener/buying-range-screener-bottom-2nd-box-logic",
                timeout=30
            )
            
            print(f"Page Status: {resp.status_code}")
            
            m = re.search(r'"csrf-token" content="([^"]+)"', resp.text)
            
            if not m:
                print("CSRF nahi mila")
                time.sleep(60)
                continue
                
            token = m.group(1)
            print(f"CSRF OK: {token[:15]}...")

            r = s.post(
                "https://chartink.com/screener/process",
                data={"scan_clause": CLAUSE},
                headers={
                    "X-Csrf-Token": token,
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": "https://chartink.com/screener/buying-range-screener-bottom-2nd-box-logic"
                },
                timeout=30
            )
            
            print(f"Process Status: {r.status_code}")
            
            try:
                data = r.json()
                stocks = [x['nsecode'] for x in data.get('data', [])]
            except:
                print(f"JSON Fail: {r.text[:200]}")
                stocks = []
            
            new = set(stocks)
            print(f"Found Stocks: {new}")
            
            if new:
                fresh = new - old if old else new
                if fresh:
                    for st in fresh:
                        send(f"🟢 *BUYING RANGE*\n\nStock: *{st}*\nRange: 110-750 F&O\nLogic: 50D Low + RSI<45\n\nTime: {get_ist_time()} IST")
                        time.sleep(1)
                old = new
            else:
                print("No stocks in range")

        except Exception as e:
            print(f"Loop Error: {e}")
            
        print("2 min wait...")
        time.sleep(120)

@app.on_event("startup")
def on_start():
    threading.Thread(target=loop, daemon=True).start()

@app.get("/")
def home():
    return {
        "status": "Bot Running 24x7",
        "ist_time": get_ist_time() + " IST",
        "chat_id": str(CHAT_ID),
        "token_set": bool(BOT_TOKEN),
        "last_stocks": list(old)
    }

@app.get("/test")
def test():
    send(f"✅ *Test OK*\nTime: {get_ist_time()} IST\nBot sahi kaam kar raha hai!")
    return {"sent": True, "time_ist": get_ist_time()}
