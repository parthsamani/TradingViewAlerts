import os, asyncio, pandas as pd
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from io import BytesIO
from curl_cffi import requests as cffi_requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHANNEL_LINK = "https://t.me/ParthTraderAlertsLive"

app = Flask(__name__)
session = cffi_requests.Session(impersonate="chrome110")

# 573 UNIQUE STOCKS - NO DUPLICATE ALERT
FNO = ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","INDUSINDBK.NS","FEDERALBNK.NS","BANKBARODA.NS","BANKINDIA.NS","CANBK.NS","PNB.NS","UNIONBANK.NS","MAHABANK.NS","IDFCFIRSTB.NS","AUBANK.NS","BANDHANBNK.NS","RBLBANK.NS","INDIANB.NS","BAJFINANCE.NS","BAJAJFINSV.NS","CHOLAFIN.NS","MUTHOOTFIN.NS","MANAPPURAM.NS","M&MFIN.NS","LICHSGFIN.NS","POONAWALLA.NS","LTF.NS","ABCAPITAL.NS","MOTILALOFS.NS","JIOFIN.NS","SBICARD.NS","HDFCAMC.NS","NAM-INDIA.NS","ANGELONE.NS","BSE.NS","CDSL.NS","MCX.NS","CAMS.NS","KFINTECH.NS","SBILIFE.NS","HDFCLIFE.NS","ICICIPRULI.NS","LICI.NS","TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","LTIM.NS","TECHM.NS","MPHASIS.NS","PERSISTENT.NS","COFORGE.NS","LTTS.NS","MARUTI.NS","M&M.NS","TATAMOTORS.NS","EICHERMOT.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS","TVSMOTOR.NS","ASHOKLEY.NS","BHARATFORG.NS","MOTHERSON.NS","SONACOMS.NS","EXIDEIND.NS","ENDURANCE.NS","FORCEMOT.NS","APOLLOTYRE.NS","ITC.NS","HINDUNILVR.NS","TITAN.NS","TRENT.NS","DMART.NS","VBL.NS","DABUR.NS","MARICO.NS","TATACONSUM.NS","COLPAL.NS","BRITANNIA.NS","UNITDSPR.NS","GODREJCP.NS","ETERNAL.NS","BHARTIARTL.NS","IDEA.NS","INDUSTOWER.NS","PAYTM.NS","SUNPHARMA.NS","DIVISLAB.NS","CIPLA.NS","DRREDDY.NS","APOLLOHOSP.NS","ZYDUSLIFE.NS","LUPIN.NS","AUROPHARMA.NS","BIOCON.NS","GRANULES.NS","LAURUSLABS.NS","SYNGENE.NS","ABBOTINDIA.NS","ALKEM.NS","TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","JINDALSTEL.NS","VEDL.NS","HINDZINC.NS","HINDCOPPER.NS","NATIONALUM.NS","SAIL.NS","NMDC.NS","COALINDIA.NS","RELIANCE.NS","ONGC.NS","IOC.NS","BPCL.NS","HINDPETRO.NS","OIL.NS","GAIL.NS","PETRONET.NS","IGL.NS","GUJGASLTD.NS","TATAPOWER.NS","NTPC.NS","POWERGRID.NS","JSWENERGY.NS","ADANIGREEN.NS","ADANIPOWER.NS","ADANIENSOL.NS","SUZLON.NS","ADANIENT.NS","ADANIPORTS.NS","LT.NS","SIEMENS.NS","ABB.NS","CGPOWER.NS","BHEL.NS","POLYCAB.NS","HAVELLS.NS","CROMPTON.NS","VOLTAS.NS","DIXON.NS","THERMAX.NS","CUMMINSIND.NS","BEL.NS","HAL.NS","COCHINSHIP.NS","MAZDOCK.NS","RVNL.NS","IRFC.NS","IRCTC.NS","CONCOR.NS","NBCC.NS","NCC.NS","GMRINFRA.NS","ULTRACEMCO.NS","AMBUJACEM.NS","ACC.NS","DALBHARAT.NS","RAMCOCEM.NS","DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","LODHA.NS","TATACHEM.NS","UPL.NS","SRF.NS","DEEPAKNTR.NS","CHAMBLFERT.NS","COROMANDEL.NS","AARTIIND.NS","PIDILITIND.NS","ATUL.NS","INDIGO.NS","INDHOTEL.NS","POLICYBZR.NS","NYKAA.NS","SAGILITY.NS","ATHERENERG.NS","VMM.NS","KALYANKJIL.NS","IEX.NS","INDIAMART.NS","NAUKRI.NS","TATAELXSI.NS","TATACOMM.NS","JUBLFOOD.NS","ZEEL.NS","GODFRYPHLP.NS","SHBAJRG.NS","CPEDU.NS","RESPONIND.NS","MAJESAUT.NS","LGHL.NS","GVPIL.NS","RELIGARE.NS","JLHL.NS","ECOSMOBLTY.NS","KITEX.NS","BANSWRAS.NS","PRECOT.NS","DPWIRES.NS","ICEMAKE.NS","BNAGROCHEM.NS","TDPOWERSYS.NS","OMAXAUTO.NS","AVL.NS","SEJALLTD.NS","EVERESTIND.NS","HSCL.NS","TRITURBINE.NS","AFFORDABLE.NS","NELCAST.NS","SHAKTIPUMP.NS","MINDTECK.NS","BAJAJST.NS","IONEXCHANG.NS","BHARATWIRE.NS","CYBERTECH.NS","JSWCEMENT.NS","AWHCL.NS","SWANCORP.NS","VHLTD.NS","TEJASNET.NS","SCODATUBES.NS","DCAL.NS","VINYLINDIA.NS","TANLA.NS","OSWALPUMPS.NS","MAFATIND.NS","TAJGVK.NS","TMPV.NS","LOTUSEYE.NS","NATHBIOGEN.NS","HEMIPROP.NS","AVANTEL.NS","STANLEY.NS","GICRE.NS","WALCHANNAG.NS","LATENTVIEW.NS","RAMCOSYS.NS","NAVNETEDUL.NS","IRIS.NS","LIKHITHA.NS","SURAJEST.NS","REDTAPE.NS","REPRO.NS","GLOBALVECT.NS","DBCORP.NS","ABMKNO.NS","PTC.NS","KIRLPNU.NS","TVSELECT.NS","TIMETECHNO.NS","VLSFINANCE.NS","GREENPANEL.NS","SPARC.NS","AGIIL.NS","SURYALA.NS","MAYURUNIQ.NS","ATGL.NS","GICHSGFIN.NS","AHLUCONT.NS","HGS.NS","CHEMPLASTS.NS","HLEGLAS.NS","HITECHGEAR.NS","TENNIND.NS","EIEL.NS","ADVENZYMES.NS","BLS.NS","VSTIND.NS","GLOSTERLTD.NS","J&KBANK.NS","JWL.NS","TIPSFILMS.NS","PATANJALI.NS","HINDCOMPOS.NS","JTEKTINDIA.NS","SRGHFL.NS","GEMAROMA.NS","ARROWGREEN.NS","ASAL.NS","MAXIND.NS","BIKAJI.NS","RHIM.NS","LAOPALA.NS","NINSYS.NS","LAXMIDENTL.NS","VESUVIUS.NS","HGINFRA.NS","CAPITALSFB.NS","NUVOCO.NS","SBIFUNDS.NS","KILITCH.NS","SUBROS.NS","PNGJL.NS","POCL.NS","PPAP.NS","BELRISE.NS","RELTD.NS","SILVERTUC.NS","IVZINNIFTY.NS","AEGISVOPAK.NS","SUNTV.NS","BCONCEPTS.NS","SHREYANIND.NS","ELECON.NS","INDIANCARD.NS","FABTECH.NS","KPITTECH.NS","SIGNPOST.NS","HDFCVALUE.NS","FAZE3Q.NS","INFOBEAN.NS","TATAINVEST.NS","ASHIANA.NS","BLAL.NS","DENTA.NS","SEMAC.NS","RECLTD.NS","NIMBSPROJ.NS","WEWORK.NS","SATIN.NS","BOROSCI.NS","RCF.NS","RSWM.NS","SWSOLAR.NS","LFIC.NS","ALLTIME.NS","FINPIPE.NS","BERGEPAINT.NS","TNPL.NS","SURYAROSNI.NS","VAIBHAVGBL.NS","SYMPHONY.NS","RICOAUTO.NS","PARKHOTELS.NS","CEINSYS.NS","BATAINDIA.NS","ICICIB22.NS","ROSSARI.NS","MBEL.NS","SHARIABEES.NS","CIEINDIA.NS","ORIENTTECH.NS","SHRINGARMS.NS","KECL.NS","NV20BEES.NS","RAILTEL.NS","INDIACEM.NS","STCINDIA.NS","GPTINFRA.NS","GPTHEALTH.NS","MAHLIFE.NS","ZAGGLE.NS","SAMHI.NS","HECPROJECT.NS","HNGSNGBEES.NS","NIFTY1.NS","ARKADE.NS","RAIN.NS","MEGASTAR.NS","MASFIN.NS","SULA.NS","IIFLCAPS.NS","SRHHYPOLTD.NS","CESC.NS","BANCOINDIA.NS","APTUS.NS","CASTROLIND.NS","KNRCON.NS","INDOAMIN.NS","TRANSRAILL.NS","GODIGIT.NS","IRCON.NS","RELCHEMQ.NS","MEDIASSIST.NS","WAAREEINDO.NS","INTELLECT.NS","THOMASCOTT.NS","SOLARWORLD.NS","NDRAUTO.NS","JUSTDIAL.NS","ORIENTCEM.NS","ORIENTCER.NS","VINDHYATEL.NS","WAAREERTL.NS","EKL.NS","WENDT.NS","UNIVEST.NS","KRISHANA.NS","KAYNES.NS","GIPCL.NS","LAKSHMIEENG.NS","WELCORP.NS","NIBL.NS","APARINDS.NS","HMAAGRO.NS","KIRLOSENG.NS","MALLCOM.NS","WALPAR.NS","JYOTISTRUC.NS","RBLBANK.NS","RISHABH.NS","MUKANDLTD.NS","SMLISUZU.NS","MANGALAM.NS","SINTERCOM.NS","GRSE.NS","SAHANA.NS","SAFARI.NS","GVPTECH.NS","SARLAPOLY.NS","SHIVALIK.NS","SARVESHWAR.NS","GFLINFRA.NS","AEGISLOG.NS","MARINE.NS","ALPE2D.NS","CUPID.NS","DSSL.NS","VIKASECO.NS","BALKRISIND.NS","AARTIPHARM.NS","CIFL.NS","INDIANB.NS","NGLFINE.NS","SHK.NS","MUTHOOTMICRO.NS","BLSHIPPING.NS","BAJAJCON.NS","JAYBARMARU.NS","ADFFOODS.NS","C2C.NS","CUPIDHUB.NS","GSMFOILS.NS","BLSINFRA.NS","BHARTIHEXA.NS","BKMINDST.NS","MAITHANALL.NS","PGIL.NS","KRISHCA.NS","ZENTEC.NS","ZIMLAB.NS","SHREDIGCEM.NS","CIGNITEC.NS","CINDHOOTEX.NS","MAMATA.NS","SAVENOWS.NS","NITCO.NS","MOBIKWIK.NS","ASHOKA.NS","WAAREENER.NS","GICL.NS","GOLDIAM.NS","MANGLMCEM.NS","STYLAMIND.NS","VGUARD.NS","MATRIMONY.NS","TRU.NS","INDIGOPNTS.NS","SURYODAY.NS","PRICOLLTD.NS","EMUDHRA.NS","INDOCO.NS","BIRLACABLE.NS","AEROFLEX.NS","VETO.NS","ELEGANZ.NS","CAPLIPOINT.NS","STOVEKRAFT.NS","MRSAMOR.NS","JETFABRIC.NS","GKWLIMITED.NS","JINDALSAW.NS","VIKRAMSOLR.NS","AETHER.NS","APOLLOPIPE.NS","GALLANTT.NS","KALAMANDIR.NS","JUNIPER.NS","CLEDUCATE.NS","E2E.NS","ICICILOVOL.NS","CAMPUS.NS","FOCUS.NS","HNDFDS.NS","CFFFL.NS","GODAVARI.NS","ORIENTELEC.NS","JINDALSTEL.NS","PRIVISCL.NS","BUTTERFLY.NS","JAGRAN.NS","KOTYARK.NS","PRAKASH.NS","EMBDL.NS","VINDHYATEL.NS","INDOBEES.NS"]

CHANNEL_FIXED_CFG = {"min_price": 110, "max_price": 750, "rsi_max": 45, "low_per": 8}
CHANNEL_AUTO_ENABLED = True
user_settings = {}
trade_log = {}
user_tracking = {}
alerted_today = {}
last_alert_time = {}
alerted_today_channel = {}
last_alert_time_channel = {}
COOLDOWN_MIN = 120

def get_ist():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)
def get_settings(chat_id):
    return user_settings.get(chat_id, CHANNEL_FIXED_CFG.copy())
def track_user(update: Update):
    try:
        user=update.effective_user; chat=update.effective_chat; uid=user.id
        now_str=get_ist().strftime('%d-%m-%Y %I:%M:%S %p')
        if uid not in user_tracking:
            user_tracking[uid]={"user_id":uid,"name":user.full_name,"username":f"@{user.username}" if user.username else "No username","chat_type":chat.type,"chat_id":chat.id,"first_seen":now_str,"last_seen":now_str,"count":1}
        else:
            user_tracking[uid]["last_seen"]=now_str; user_tracking[uid]["count"]+=1
    except: pass

def fetch_yahoo_data(symbol, range_str, interval):
    try:
        url=f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params={"range":range_str,"interval":interval,"includePrePost":"false"}
        r=session.get(url, params=params, timeout=15)
        data=r.json(); result=data['chart']['result'][0]; timestamps=result['timestamp']; ohlc=result['indicators']['quote'][0]
        df=pd.DataFrame({'Open':ohlc['open'],'Close':ohlc['close'],'High':ohlc['high'],'Low':ohlc['low'],'Volume':ohlc['volume']}, index=pd.to_datetime(timestamps, unit='s'))
        df.dropna(inplace=True); return df
    except: return pd.DataFrame()

def compute_rsi(close_series, period=14):
    try:
        delta=close_series.diff(); gain=(delta.where(delta>0,0)).rolling(window=period).mean(); loss=(-delta.where(delta<0,0)).rolling(window=period).mean(); rs=gain/loss; rsi=100-(100/(1+rs)); return rsi
    except: return pd.Series([50]*len(close_series))

application = Application.builder().token(BOT_TOKEN).build()

async def is_joined_channel(user_id):
    if not CHANNEL_ID: return True
    try:
        member=await application.bot.get_chat_member(chat_id=int(CHANNEL_ID), user_id=user_id)
        return member.status in ['member','administrator','creator','owner']
    except: return True

def get_fno_alerts(chat_id=None, cfg_override=None, save_log=True, debug=False, is_channel=False):
    cfg=cfg_override if cfg_override else CHANNEL_FIXED_CFG if is_channel else get_settings(chat_id) if chat_id else CHANNEL_FIXED_CFG
    alerts=[]; debug_logs=[]; today_str=get_ist().strftime('%Y-%m-%d')
    for sym in FNO:
        try:
            df_daily=fetch_yahoo_data(sym,"3mo","1d")
            if df_daily.empty or len(df_daily)<52: continue
            curr_price=float(df_daily['Close'].iloc[-1])
            if curr_price<cfg["min_price"] or curr_price>cfg["max_price"]: continue
            rsi_val=float(compute_rsi(df_daily['Close'],14).iloc[-1])
            if rsi_val>cfg["rsi_max"]: continue
            low_50=float(df_daily['Low'].tail(50).min())
            if curr_price>low_50*(1+cfg["low_per"]/100): continue
            sma50=df_daily['Close'].rolling(50).mean()
            if pd.isna(sma50.iloc[-1]) or pd.isna(sma50.iloc[-20]): continue
            if sma50.iloc[-1]<sma50.iloc[-20]: continue
            symbol=sym.replace('.NS','')
            if is_channel:
                if alerted_today_channel.get(symbol)==today_str: continue
                if symbol in last_alert_time_channel and (get_ist()-last_alert_time_channel[symbol]).seconds/60<COOLDOWN_MIN: continue
            else:
                if chat_id:
                    if chat_id not in alerted_today: alerted_today[chat_id]={}
                    if chat_id not in last_alert_time: last_alert_time[chat_id]={}
                    if alerted_today[chat_id].get(symbol)==today_str: continue
                    if symbol in last_alert_time[chat_id] and (get_ist()-last_alert_time[chat_id][symbol]).seconds/60<COOLDOWN_MIN: continue
            per_from_low=((curr_price-low_50)/low_50*100) if low_50>0 else 0
            text=f"🔵 **BUYING RANGE - BOTTOM 2ND BOX**\n**{symbol}** | ₹{curr_price:.2f}\nRSI: {rsi_val:.1f} | 50D Low: ₹{low_50:.2f} ({per_from_low:.1f}% up)\nTime: {get_ist().strftime('%d-%m %I:%M %p IST')}"
            alerts.append(text)
            if is_channel:
                alerted_today_channel[symbol]=today_str; last_alert_time_channel[symbol]=get_ist()
            elif chat_id:
                alerted_today[chat_id][symbol]=today_str; last_alert_time[chat_id][symbol]=get_ist()
                trade_log.setdefault(chat_id,[]).append({"time":get_ist().strftime('%Y-%m-%d %H:%M'),"symbol":symbol,"close":curr_price,"rsi":round(rsi_val,1),"50D_Low":round(low_50,2)})
        except: continue
    return alerts, debug_logs

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update)
    if not await is_joined_channel(update.effective_user.id):
        await update.message.reply_text(f"⛔ **Channel Join Karo**\n👉 {CHANNEL_LINK}", parse_mode="Markdown"); return
    await update.message.reply_text(f"🚀 **Buying Range Bot - 573 Stocks**\nIST: {get_ist().strftime('%I:%M %p')}\n\nLogic: Close {CHANNEL_FIXED_CFG['min_price']}-{CHANNEL_FIXED_CFG['max_price']}, RSI<{CHANNEL_FIXED_CFG['rsi_max']}, Low {CHANNEL_FIXED_CFG['low_per']}%\nTotal: {len(FNO)} Unique\n\n/scan /debug /settings /auto /stop /export")

async def scan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update)
    await update.message.reply_text(f"🔍 Scanning {len(FNO)} stocks...")
    alerts,_=get_fno_alerts(chat_id=update.effective_chat.id, is_channel=False)
    if not alerts: await update.message.reply_text(f"No stock now. {get_ist().strftime('%I:%M %p')}")
    else:
        for a in alerts[:15]: await update.message.reply_text(a, parse_mode="Markdown"); await asyncio.sleep(0.3)

async def debug_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update); await update.message.reply_text("🔍 Debug..."); alerts,logs=get_fno_alerts(chat_id=update.effective_chat.id, debug=True); await update.message.reply_text(f"Alerts: {len(alerts)}");
    for a in alerts[:3]: await update.message.reply_text(a, parse_mode="Markdown")

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update); cfg=get_settings(update.effective_chat.id)
    kb=[[InlineKeyboardButton(f"Min {cfg['min_price']}",callback_data="noop")],[InlineKeyboardButton("Min 50",callback_data="min_50"),InlineKeyboardButton("Min 110",callback_data="min_110")],[InlineKeyboardButton("RSI 35",callback_data="rsi_35"),InlineKeyboardButton("RSI 45",callback_data="rsi_45")],[InlineKeyboardButton("Low 5%",callback_data="low_5"),InlineKeyboardButton("Low 8%",callback_data="low_8")]]
    await update.message.reply_text(f"⚙️ Min={cfg['min_price']} Max={cfg['max_price']} RSI<{cfg['rsi_max']} Low={cfg['low_per']}%", reply_markup=InlineKeyboardMarkup(kb))

async def button_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); cfg=get_settings(q.message.chat_id); d=q.data
    if d.startswith("min_"): cfg["min_price"]=float(d.split("_")[1])
    if d.startswith("rsi_"): cfg["rsi_max"]=float(d.split("_")[1])
    if d.startswith("low_"): cfg["low_per"]=float(d.split("_")[1])
    user_settings[q.message.chat_id]=cfg
    await q.edit_message_text(f"✅ Saved {cfg}\n/scan karo", reply_markup=q.message.reply_markup)

async def export_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logs=trade_log.get(update.effective_chat.id,[])
    if not logs: await update.message.reply_text("Koi log nahi"); return
    df=pd.DataFrame(logs); output=BytesIO(); df.to_excel(output,index=False); output.seek(0)
    await update.message.reply_document(document=output, filename=f"BuyingRange_{get_ist().strftime('%d-%b')}.xlsx")

auto_users=set()
async def auto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auto_users.add(update.effective_chat.id); await update.message.reply_text(f"✅ Auto ON {len(FNO)} stocks")
async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auto_users.discard(update.effective_chat.id); await update.message.reply_text("🔴 Auto OFF")
async def channel_on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHANNEL_AUTO_ENABLED; CHANNEL_AUTO_ENABLED=True; await update.message.reply_text(f"✅ Channel Auto ON {len(FNO)}")
async def channel_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHANNEL_AUTO_ENABLED; CHANNEL_AUTO_ENABLED=False; await update.message.reply_text("🔴 Channel Auto OFF")
async def set_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHANNEL_FIXED_CFG
    try:
        args=context.args; CHANNEL_FIXED_CFG={"min_price":float(args[0]),"max_price":float(args[1]),"rsi_max":float(args[2]),"low_per":float(args[3])}
        await update.message.reply_text(f"✅ Updated {CHANNEL_FIXED_CFG}")
    except Exception as e: await update.message.reply_text(f"Usage: /setchannel 110 750 45 8")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("scan", scan_cmd))
application.add_handler(CommandHandler("debug", debug_cmd))
application.add_handler(CommandHandler("fno", scan_cmd))
application.add_handler(CommandHandler("settings", settings_cmd))
application.add_handler(CommandHandler("export", export_cmd))
application.add_handler(CommandHandler("auto", auto_cmd))
application.add_handler(CommandHandler("stop", stop_cmd))
application.add_handler(CommandHandler("channelon", channel_on_cmd))
application.add_handler(CommandHandler("channeloff", channel_off_cmd))
application.add_handler(CommandHandler("setchannel", set_channel_cmd))
application.add_handler(CallbackQueryHandler(button_cb))

@app.route('/')
def home(): return f"Bot Live {len(FNO)} {get_ist().strftime('%H:%M IST')}"
@app.route('/reset')
def reset_locks(): alerted_today.clear(); last_alert_time.clear(); alerted_today_channel.clear(); last_alert_time_channel.clear(); return "Reset done"

async def auto_loop():
    while True:
        await asyncio.sleep(1800); now=get_ist()
        if not (9<=now.hour<=15) or now.weekday()>=5 or not CHANNEL_AUTO_ENABLED: continue
        channel_alerts,_=get_fno_alerts(is_channel=True)
        if channel_alerts and CHANNEL_ID:
            for a in channel_alerts[:10]:
                try: await application.bot.send_message(chat_id=int(CHANNEL_ID), text=a, parse_mode="Markdown")
                except: pass

if __name__=="__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().create_task(auto_loop())
    application.run_polling(drop_pending_updates=True)
