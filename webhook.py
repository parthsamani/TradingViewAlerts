import hashlib
import json
import logging
from flask import Flask, request, jsonify
from config import WEBHOOK_SECRET
from database import get_webhook, mark_webhook_alert, save_alert

logger=logging.getLogger(__name__)
app=Flask(__name__)

def fingerprint(data, token):
    raw=json.dumps(data,sort_keys=True,default=str,separators=(",",":"))+"|"+token
    return hashlib.sha256(raw.encode()).hexdigest()

def parse_payload():
    if request.is_json:
        data=request.get_json(silent=True)
        return data if data is not None else {}
    return dict(request.form)

@app.get("/")
def health():
    return jsonify({"status":"ok","service":"ParthTraderAlerts Chartink Webhook"})


@app.post("/webhook/<token>")
def receive(token):
    if WEBHOOK_SECRET:
        supplied=request.headers.get("X-Webhook-Secret","")
        if supplied != WEBHOOK_SECRET:
            return jsonify({"ok":False,"error":"unauthorized"}),401

    hook=get_webhook(token)
    if not hook:
        return jsonify({"ok":False,"error":"invalid webhook"}),404

    data=parse_payload()
    fp=fingerprint(data,token)

    if not save_alert(hook["chat_id"],token,json.dumps(data,default=str),fp):
        return jsonify({"ok":True,"duplicate":True}),200

    mark_webhook_alert(token)
    app.config["LAST_ALERTS"] = getattr(app.config,"LAST_ALERTS",[])
    app.config["LAST_ALERTS"].append((hook["chat_id"],data,token))
    return jsonify({"ok":True}),200
