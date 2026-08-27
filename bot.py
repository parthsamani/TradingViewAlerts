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

# AAPKA NAYA LINK AUR NAYA CLAUSE
SCREEN_LINK = "https://chartink.com/screener/copy-f-o-stocks-806"
CLAUSE = "( futures ( daily close > 110 and daily close < 750 and( cash ( daily close > 1 day ago close ) ) ) )"

old = set()

def get_ist():
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime('%d-%m %I:%M %p')

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
        print(f"Telegram: {r.status_code}")
    except Exception as e:
        print(f"Send Error: {e}")

def loop():
    global old
    print("Loop Started...")
    send(f"🚀 *Bot Live - F&O Stocks*\nTime: {get_ist()} IST")
    time.sleep(10)
    while True:
        try:
            s = requests.Session()
            s.headers.update({"User-Agent": "Mozilla/5.0"})
            
            print(f"Checking: {SCREEN_LINK}")
            resp = s.get(SCREEN_LINK, timeout=30)
            
            m = re.search(r'"csrf-token" content="([^"]+)"', resp.text)
            if not m:
                print("CSRF nahi mila")
                time.sleep(120)
                continue
                
            token = m.group(1)
            print(f"CSRF OK")
            
            r = s.post(
                "https://chartink.com/screener/process",
                data={"scan_clause": CLAUSE},
                headers={
                    "X-Csrf-Token": token,
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": SCREEN_LINK
                },
                timeout=30
            )
            
            stocks = [x['nsecode'] for x in r.json().get('data', [])]
            new = set(stocks)
            print(f"Found: {new}")
            
            if new:
                fresh = new - old if old else new
                for st in fresh:
                    msg = f"""
🟢 *F&O GREEN ALERT*

┌─────────────────────────┐
│  Stock: *{st}*          
│  Price: 110 - 750       
│  Logic: Cash Close >    
│  Yesterday Close        
│  Type: F&O              
└─────────────────────────┘

⏰ *{get_ist()} IST*
🔗 _copy-f-o-stocks-806_
"""
                    send(msg)
                    time.sleep(1)
                old = new
            else:
                print("No stocks now")
                
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(120)

@app.on_event("startup")
def on_start():
    threading.Thread(target=loop, daemon=True).start()

@app.get("/")
def home():
    return {"status": "Running F&O", "link": SCREEN_LINK, "clause": CLAUSE, "time_ist": get_ist(), "stocks": list(old)}

@app.get("/test")
def test():
    send(f"✅ *F&O Test OK*\nStock: *TCS*\nTime: {get_ist()} IST\nLink: copy-f-o-stocks-806")
    return {"sent": True}
