from fastapi import FastAPI
import requests, time, threading, os, re

app = FastAPI()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

CLAUSE = "( futures ( latest close > 110 and latest close < 750 and latest close > latest low ( 50 ) * 1 and latest close < latest low ( 50 ) * 1.08 and latest rsi ( 14 ) < 45 ) )"
old = set()

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
    except Exception as e:
        print(f"Send Error: {e}")

def loop():
    global old
    while True:
        try:
            s = requests.Session()
            s.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            })
            # Step 1: Page se CSRF token nikalo
            resp = s.get("https://chartink.com/screener/buying-range-screener-bottom-2nd-box-logic", timeout=15)
            m = re.search(r'"csrf-token" content="([^"]+)"', resp.text)
            if not m:
                print("CSRF token nahi mila")
                time.sleep(120)
                continue
            token = m.group(1)
            print(f"CSRF Found: {token[:10]}...")

            # Step 2: Token ke saath post karo
            r = s.post("https://chartink.com/screener/process", 
                       data={"scan_clause": CLAUSE},
                       headers={
                           "X-Csrf-Token": token,
                           "X-Requested-With": "XMLHttpRequest",
                           "Referer": "https://chartink.com/screener/buying-range-screener-bottom-2nd-box-logic"
                       }, timeout=20)
            
            print(f"Chartink Status: {r.status_code}")
            stocks = [x['nsecode'] for x in r.json().get('data',[])]
            new = set(stocks)
            print(f"Found: {new}")
            
            if new:
                fresh = new - old if old else new
                for st in fresh:
                    send(f"🟢 *BUYING RANGE - Bottom 2nd Box*\n\nStock: *{st}*\nRange: 110-750 F&O\nLogic: 50D Low + RSI<45\n\nTime: {time.strftime('%d-%m %H:%M')}")
                old = new
            else:
                print("No stocks in buying zone")

        except Exception as e:
            print(f"Loop Error: {e}")
        time.sleep(120)

threading.Thread(target=loop, daemon=True).start()

@app.head("/")
def home_head():
    return {}
    
@app.get("/")
def home():
    return {"status": "Bot Running 24x7", "last_stocks": list(old), "env_set": bool(BOT_TOKEN and CHAT_ID)}

@app.get("/test")
def test():
    send("✅ Test Message: Bot sahi kaam kar raha hai!")
    return {"sent": True}
