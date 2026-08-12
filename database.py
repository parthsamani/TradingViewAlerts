import sqlite3
import secrets
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("chartink_bot.db")

def now():
    return datetime.now(timezone.utc).isoformat()

def connect():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            last_seen TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            name TEXT DEFAULT 'Chartink',
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            last_alert_at TEXT
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            webhook_token TEXT,
            payload TEXT,
            fingerprint TEXT UNIQUE,
            created_at TEXT NOT NULL,
            delivered INTEGER DEFAULT 0
        );
        """)

def upsert_user(chat_id, username="", first_name=""):
    t=now()
    with connect() as db:
        db.execute("""
        INSERT INTO users(chat_id,username,first_name,created_at,last_seen)
        VALUES(?,?,?,?,?)
        ON CONFLICT(chat_id) DO UPDATE SET
        username=excluded.username, first_name=excluded.first_name,
        last_seen=excluded.last_seen, active=1
        """,(chat_id,username or "",first_name or "",t,t))

def get_user(chat_id):
    with connect() as db:
        return db.execute("SELECT * FROM users WHERE chat_id=?",(chat_id,)).fetchone()

def create_webhook(chat_id, name="Chartink"):
    token=secrets.token_urlsafe(24)
    with connect() as db:
        db.execute("INSERT INTO webhooks(chat_id,token,name,created_at) VALUES(?,?,?,?)",
                   (chat_id,token,name,now()))
    return token

def get_webhooks(chat_id):
    with connect() as db:
        return db.execute("SELECT * FROM webhooks WHERE chat_id=? ORDER BY id DESC",(chat_id,)).fetchall()

def get_webhook(token):
    with connect() as db:
        return db.execute("SELECT * FROM webhooks WHERE token=? AND active=1",(token,)).fetchone()

def disable_webhooks(chat_id):
    with connect() as db:
        db.execute("UPDATE webhooks SET active=0 WHERE chat_id=?",(chat_id,))

def mark_webhook_alert(token):
    with connect() as db:
        db.execute("UPDATE webhooks SET last_alert_at=? WHERE token=?",(now(),token))

def save_alert(chat_id, token, payload, fingerprint):
    try:
        with connect() as db:
            db.execute("""INSERT INTO alerts(chat_id,webhook_token,payload,fingerprint,created_at)
                         VALUES(?,?,?,?,?)""",(chat_id,token,payload,fingerprint,now()))
        return True
    except sqlite3.IntegrityError:
        return False

def stats():
    with connect() as db:
        users=db.execute("SELECT COUNT(*) FROM users WHERE active=1").fetchone()[0]
        hooks=db.execute("SELECT COUNT(*) FROM webhooks WHERE active=1").fetchone()[0]
        alerts=db.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    return users,hooks,alerts
