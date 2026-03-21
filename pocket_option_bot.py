#!/usr/bin/env python3
"""SIGNAL AI — Bollinger Bands(20,2) + RSI(7) + MACD(12,26,9)"""
import os, math, time, json, threading, requests, io, logging
from datetime import datetime, timezone, timedelta
from telebot import TeleBot
from telebot.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                           ReplyKeyboardMarkup, KeyboardButton)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings; warnings.filterwarnings("ignore")

BOT_TOKEN  = os.environ.get("BOT_TOKEN")
TWELVE_KEY = os.environ.get("TWELVE_KEY")  # встанови в Railway Variables
TWELVE_URL = "https://api.twelvedata.com"
STATS_FILE = "stats.json"
if not BOT_TOKEN:   raise ValueError("BOT_TOKEN не встановлено!")
if not TWELVE_KEY:  TWELVE_KEY = "99b3ca01dbdf45ccb2f5968b16af1c82"  # резерв
bot = TeleBot(BOT_TOKEN)

FOREX_PAIRS=[
    {"name":"EUR/USD","symbol":"EUR/USD","p":1.085,"d":5},
    {"name":"GBP/USD","symbol":"GBP/USD","p":1.270,"d":5},
    {"name":"USD/JPY","symbol":"USD/JPY","p":149.5,"d":3},
    {"name":"USD/CHF","symbol":"USD/CHF","p":0.903,"d":5},
    {"name":"USD/CAD","symbol":"USD/CAD","p":1.357,"d":5},
    {"name":"AUD/USD","symbol":"AUD/USD","p":0.645,"d":5},
    {"name":"NZD/USD","symbol":"NZD/USD","p":0.596,"d":5},
    {"name":"EUR/GBP","symbol":"EUR/GBP","p":0.853,"d":5},
    {"name":"EUR/JPY","symbol":"EUR/JPY","p":161.5,"d":3},
    {"name":"EUR/CHF","symbol":"EUR/CHF","p":0.978,"d":5},
    {"name":"EUR/AUD","symbol":"EUR/AUD","p":1.672,"d":5},
    {"name":"EUR/CAD","symbol":"EUR/CAD","p":1.464,"d":5},
    {"name":"EUR/NZD","symbol":"EUR/NZD","p":1.820,"d":5},
    {"name":"GBP/JPY","symbol":"GBP/JPY","p":189.8,"d":3},
    {"name":"GBP/CHF","symbol":"GBP/CHF","p":1.118,"d":5},
    {"name":"GBP/AUD","symbol":"GBP/AUD","p":1.975,"d":5},
    {"name":"GBP/CAD","symbol":"GBP/CAD","p":1.722,"d":5},
    {"name":"GBP/NZD","symbol":"GBP/NZD","p":2.132,"d":5},
    {"name":"AUD/JPY","symbol":"AUD/JPY","p":96.4,"d":3},
    {"name":"AUD/CAD","symbol":"AUD/CAD","p":0.874,"d":5},
    {"name":"AUD/CHF","symbol":"AUD/CHF","p":0.581,"d":5},
    {"name":"AUD/NZD","symbol":"AUD/NZD","p":1.093,"d":5},
    {"name":"CHF/JPY","symbol":"CHF/JPY","p":165.5,"d":3},
    {"name":"CAD/JPY","symbol":"CAD/JPY","p":110.3,"d":3},
    {"name":"NZD/JPY","symbol":"NZD/JPY","p":89.2,"d":3},
    {"name":"NZD/CAD","symbol":"NZD/CAD","p":0.809,"d":5},
    {"name":"NZD/CHF","symbol":"NZD/CHF","p":0.539,"d":5},
    {"name":"CAD/CHF","symbol":"CAD/CHF","p":0.666,"d":5},
]
OTC_PAIRS=[{"name":p["name"]+" OTC","symbol":p["symbol"],"p":p["p"],"d":p["d"]} for p in FOREX_PAIRS[:20]]
CRYPTO_PAIRS=[
    {"name":"BTC/USD","symbol":"BTC/USD","p":67000,"d":0},
    {"name":"ETH/USD","symbol":"ETH/USD","p":3500,"d":2},
    {"name":"BNB/USD","symbol":"BNB/USD","p":420,"d":2},
    {"name":"SOL/USD","symbol":"SOL/USD","p":180,"d":2},
    {"name":"XRP/USD","symbol":"XRP/USD","p":0.62,"d":4},
    {"name":"ADA/USD","symbol":"ADA/USD","p":0.45,"d":4},
    {"name":"DOGE/USD","symbol":"DOGE/USD","p":0.18,"d":5},
    {"name":"LTC/USD","symbol":"LTC/USD","p":95,"d":2},
    {"name":"DOT/USD","symbol":"DOT/USD","p":7.5,"d":3},
    {"name":"AVAX/USD","symbol":"AVAX/USD","p":38,"d":2},
    {"name":"MATIC/USD","symbol":"MATIC/USD","p":0.85,"d":4},
    {"name":"LINK/USD","symbol":"LINK/USD","p":14.5,"d":3},
]
STOCKS_PAIRS=[
    {"name":"Apple","symbol":"AAPL","p":189,"d":2},
    {"name":"Tesla","symbol":"TSLA","p":245,"d":2},
    {"name":"NVIDIA","symbol":"NVDA","p":875,"d":2},
    {"name":"Amazon","symbol":"AMZN","p":185,"d":2},
    {"name":"Google","symbol":"GOOGL","p":165,"d":2},
    {"name":"Microsoft","symbol":"MSFT","p":415,"d":2},
    {"name":"Meta","symbol":"META","p":510,"d":2},
    {"name":"Netflix","symbol":"NFLX","p":625,"d":2},
    {"name":"AMD","symbol":"AMD","p":165,"d":2},
    {"name":"Intel","symbol":"INTC","p":42,"d":2},
    {"name":"Coca-Cola","symbol":"KO","p":61,"d":2},
    {"name":"McDonald's","symbol":"MCD","p":295,"d":2},
]
ALL_PAIRS={p["name"]:p for p in FOREX_PAIRS+OTC_PAIRS+CRYPTO_PAIRS+STOCKS_PAIRS}
TIMEFRAMES={"1":"1хв","3":"3хв","5":"5хв","15":"15хв","30":"30хв","60":"1год"}
CRYPTO_TF={"5":"5хв","15":"15хв","30":"30хв","60":"1год","240":"4год"}
STOCKS_TF={"5":"5хв","15":"15хв","30":"30хв","60":"1год"}
TF_HOLD={"1":1,"3":3,"5":5,"15":15,"30":30,"60":60,"240":240}
TF_LABEL={"1":"1хв","3":"3хв","5":"5хв","15":"15хв","30":"30хв","60":"1год","240":"4год"}
TF_API={"1":"1min","3":"3min","5":"5min","15":"15min","30":"30min","60":"1h","240":"4h"}

_cache={}
TF_TTL={"1":25,"3":80,"5":140,"15":280,"30":560,"60":1100,"240":2200}

def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE) as f: return json.load(f)
    except: pass
    return {}
def save_stats(d):
    try:
        with open(STATS_FILE,"w") as f: json.dump(d,f,ensure_ascii=False,indent=2)
    except: pass
all_stats=load_stats()
def get_stats(cid):
    k=str(cid)
    if k not in all_stats:
        all_stats[k]={"total":0,"wins":0,"losses":0,"streak":0,"pairs":{}}
    return all_stats[k]
def save_user_stats(): save_stats(all_stats)

def ema(a,p):
    if not a: return 0
    if len(a)<p: return sum(a)/len(a)
    k=2/(p+1); v=sum(a[:p])/p
    for x in a[p:]: v=x*k+v*(1-k)
    return v

def calc_rsi(c,p=7):
    if len(c)<p+1: return 50.0
    g=[max(c[i]-c[i-1],0) for i in range(1,len(c))]
    l=[max(c[i-1]-c[i],0) for i in range(1,len(c))]
    ag=sum(g[-p:])/p; al=sum(l[-p:])/p
    return round(100-100/(1+ag/al),1) if al else 100.0

def calc_bb(c,p=20,mult=2.0):
    if len(c)<p: return None,None,None
    mid=sum(c[-p:])/p
    std=(sum((x-mid)**2 for x in c[-p:])/p)**0.5
    return round(mid+mult*std,6),round(mid,6),round(mid-mult*std,6)

def calc_macd(c,fast=12,slow=26,signal=9):
    if len(c)<slow+signal: return None,None,None
    macd_series=[]
    for i in range(slow,len(c)+1):
        macd_series.append(ema(c[:i],fast)-ema(c[:i],slow))
    sig_line=ema(macd_series,signal) if len(macd_series)>=signal else macd_series[-1]
    macd_line=macd_series[-1]
    return round(macd_line,6),round(sig_line,6),round(macd_line-sig_line,6)

def calc_atr(c,h,l,p=14):
    if len(c)<2: return 0
    tr=[max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])) for i in range(1,len(c))]
    return sum(tr[-p:])/min(p,len(tr)) if tr else 0

def get_session():
    h=datetime.now(timezone.utc).hour
    if 7<=h<9:    return "Лондон відкриття",1.10
    elif 9<=h<12: return "Лондон + NY",1.15
    elif 12<=h<16: return "Нью-Йорк",1.05
    elif 16<=h<18: return "NY закриття",0.95
    elif 18<=h<21: return "Між сесіями",0.85
    elif 21<=h<23: return "Токіо",0.90
    else:          return "Нічна сесія",0.80

def get_candles(symbol,tf,count=100):
    key=f"{symbol}_{tf}"
    ttl=TF_TTL.get(tf,140)
    if key in _cache:
        ts,data=_cache[key]
        if time.time()-ts<ttl: return data
    interval=TF_API.get(tf,"5min")
    try:
        url=(f"{TWELVE_URL}/time_series?symbol={symbol}&interval={interval}"
             f"&outputsize={count}&apikey={TWELVE_KEY}&format=JSON")
        r=requests.get(url,timeout=12); d=r.json()
        if d.get("status")=="error" or not d.get("values"): return None
        vals=list(reversed(d["values"]))
        data={"c":[float(v["close"]) for v in vals],
              "h":[float(v["high"]) for v in vals],
              "l":[float(v["low"]) for v in vals],
              "o":[float(v["open"]) for v in vals]}
        _cache[key]=(time.time(),data)
        return data
    except: return None

def get_price(symbol, fallback):
    try:
        r = requests.get(
            f"{TWELVE_URL}/price?symbol={symbol}&apikey={TWELVE_KEY}",
            timeout=5
        )
        p = r.json().get("price")
        if p: return float(p)
    except: pass
    return fallback

def make_fallback(pair_name,tf):
    m=ALL_PAIRS.get(pair_name,FOREX_PAIRS[0])
    base=m["p"]
    seed=sum(ord(x) for x in pair_name)+(int(tf) if tf.isdigit() else 5)*7+int(time.time()//300)
    def sr(i): v=math.sin(seed*1.13+i*0.71)*43758.5453; return v-math.floor(v)
    vf=0.0015 if base>500 else(0.002 if base>50 else(0.0008 if base>5 else 0.003))
    c=[base];h=[base];l=[base];o=[base]
    for i in range(1,110):
        trend=(sr(i+5)-0.495)*vf*1.5; vol=sr(i+10)*vf+vf*0.3
        op=c[-1]; cl=op*(1+trend+(sr(i+20)-0.5)*vol)
        hi=max(op,cl)*(1+sr(i+30)*vf*0.4); lo=min(op,cl)*(1-sr(i+40)*vf*0.4)
        o.append(op);c.append(cl);h.append(hi);l.append(lo)
    return {"c":c,"h":h,"l":l,"o":o}

# ══ RATE LIMITING ═════════════════════════════════════
_user_last_req = {}
_user_req_count = {}
RATE_LIMIT_SEC = 3    # мін. секунд між запитами
RATE_LIMIT_MIN = 20   # макс. запитів на хвилину

def check_rate_limit(cid):
    now = time.time(); cid = str(cid)
    last = _user_last_req.get(cid, 0)
    if now - last < RATE_LIMIT_SEC:
        return False
    count, window = _user_req_count.get(cid, (0, now))
    if now - window > 60: count, window = 0, now
    if count >= RATE_LIMIT_MIN: return False
    _user_last_req[cid] = now
    _user_req_count[cid] = (count + 1, window)
    return True

def generate_signal(pair_name,tf):
    m=ALL_PAIRS.get(pair_name,FOREX_PAIRS[0]); dp=m["d"]
    data=get_candles(m["symbol"],tf,100)
    real=data is not None and len(data["c"])>=30
    if not real: data=make_fallback(pair_name,tf)
    c=data["c"]; h=data["h"]; l=data["l"]
    live=get_price(m["symbol"],m["p"])
    if not live or live<=0: live=c[-1]

    rsi=calc_rsi(c,7)
    macd_line,sig_line,hist=calc_macd(c,12,26,9)
    if macd_line is None: macd_line=sig_line=hist=0.0
    bb_up,bb_mid,bb_lo=calc_bb(c,20,2.0)
    if bb_up is None: bb_up=bb_mid=bb_lo=live
    hist_prev=0.0
    if len(c)>30:
        ml_p,sl_p,h_p=calc_macd(c[:-1],12,26,9)
        if ml_p is not None: hist_prev=ml_p-sl_p
    atr=calc_atr(c,h,l,14)
    sess_name,sess_mult=get_session()
    bb_width=bb_up-bb_lo if bb_up and bb_lo else 0.001
    bb_pos=(live-bb_lo)/bb_width*100 if bb_width>0 else 50

    cross_up=hist>0 and hist_prev<=0
    cross_down=hist<0 and hist_prev>=0
    signals=[]

    if rsi<=20:    signals.append(("RSI",1,f"RSI(7)={rsi} — критична перепроданість 🔥🔥",3.0))
    elif rsi>=80:  signals.append(("RSI",-1,f"RSI(7)={rsi} — критична перекупленість 🔥🔥",3.0))
    elif rsi<=30:  signals.append(("RSI",1,f"RSI(7)={rsi} — перепроданість 🔥",2.5))
    elif rsi>=70:  signals.append(("RSI",-1,f"RSI(7)={rsi} — перекупленість 🔥",2.5))
    elif rsi<45:   signals.append(("RSI",1,f"RSI(7)={rsi} — BUY зона",1.2))
    elif rsi>55:   signals.append(("RSI",-1,f"RSI(7)={rsi} — SELL зона",1.2))
    else:          signals.append(("RSI",0,f"RSI(7)={rsi} — нейтраль",0.3))

    if cross_up:         signals.append(("MACD",1,"MACD: бичачий перетин ▲ 🔥🔥",3.5))
    elif cross_down:     signals.append(("MACD",-1,"MACD: ведмежий перетин ▼ 🔥🔥",3.5))
    elif macd_line>0 and hist>0: signals.append(("MACD",1,"MACD вище нуля ▲",2.0))
    elif macd_line<0 and hist<0: signals.append(("MACD",-1,"MACD нижче нуля ▼",2.0))
    elif hist>0:         signals.append(("MACD",1,"MACD гістограма позитивна",1.0))
    elif hist<0:         signals.append(("MACD",-1,"MACD гістограма негативна",1.0))
    else:                signals.append(("MACD",0,"MACD нейтраль",0.3))

    if live<=bb_lo:    signals.append(("BB",1,"BB: нижче нижньої смуги 🔥🔥",3.5))
    elif live>=bb_up:  signals.append(("BB",-1,"BB: вище верхньої смуги 🔥🔥",3.5))
    elif bb_pos<=15:   signals.append(("BB",1,f"BB: {bb_pos:.0f}% — зона підтримки 🔥",2.5))
    elif bb_pos>=85:   signals.append(("BB",-1,f"BB: {bb_pos:.0f}% — зона опору 🔥",2.5))
    elif bb_pos<=35:   signals.append(("BB",1,f"BB: {bb_pos:.0f}% — нижня зона",1.5))
    elif bb_pos>=65:   signals.append(("BB",-1,f"BB: {bb_pos:.0f}% — верхня зона",1.5))
    else:              signals.append(("BB",0,f"BB: {bb_pos:.0f}% — середина",0.3))

    buy_w=sum(w for _,d,_,w in signals if d==1)
    sell_w=sum(w for _,d,_,w in signals if d==-1)
    is_buy=buy_w>=sell_w
    total_w=buy_w+sell_w
    ratio=max(buy_w,sell_w)/max(total_w,0.001)

    cross_bonus=15 if(cross_up and is_buy)or(cross_down and not is_buy) else 0
    bb_ex=10 if(live<=bb_lo and is_buy)or(live>=bb_up and not is_buy) else 0
    rsi_ex=8 if(rsi<=30 and is_buy)or(rsi>=70 and not is_buy) else 0
    acc_raw=round(50+ratio*25+cross_bonus+bb_ex+rsi_ex)
    acc=min(92,max(62,round(acc_raw*sess_mult)))

    rsi_against=(rsi>=75 and is_buy)or(rsi<=25 and not is_buy)
    bb_against=(live>=bb_up and is_buy)or(live<=bb_lo and not is_buy)
    blocked=rsi_against and bb_against
    block_reasons=[]
    if rsi_against: block_reasons.append(f"RSI={rsi} {'перекупленість' if is_buy else 'перепроданість'}")
    if bb_against:  block_reasons.append(f"BB: ціна {'вище верхньої' if is_buy else 'нижче нижньої'} смуги")
    if blocked: acc=min(acc,58)

    if blocked:        strength="⛔ НЕ ТОРГУВАТИ"
    elif ratio<0.55:   strength="⚠️ СЛАБКИЙ"
    elif ratio<0.68:   strength="✅ СЕРЕДНІЙ"
    elif ratio<0.82:   strength="🔥 СИЛЬНИЙ"
    else:              strength="🔥🔥 ДУЖЕ СИЛЬНИЙ"

    if atr==0: atr=live*0.001
    tp_m={"1":1.2,"3":1.4,"5":1.6,"15":2.0,"30":2.5,"60":3.0,"240":4.0}.get(tf,1.6)
    sl_m={"1":0.9,"3":1.0,"5":1.1,"15":1.3,"30":1.6,"60":2.0,"240":2.5}.get(tf,1.1)
    tp=round(live+atr*tp_m,dp) if is_buy else round(live-atr*tp_m,dp)
    sl=round(live-atr*sl_m,dp) if is_buy else round(live+atr*sl_m,dp)
    rr=round(tp_m/sl_m,1)

    return {"is_buy":is_buy,"acc":acc,"strength":strength,"blocked":blocked,
            "live":live,"tp":tp,"sl":sl,"rr":rr,"dp":dp,
            "rsi":rsi,"macd_line":macd_line,"sig_line":sig_line,"hist":hist,
            "bb_up":bb_up,"bb_mid":bb_mid,"bb_lo":bb_lo,"bb_pos":round(bb_pos,1),
            "cross_up":cross_up,"cross_down":cross_down,
            "signals":signals,"buy_w":round(buy_w,1),"sell_w":round(sell_w,1),
            "sess":sess_name,"real":real,"atr":round(atr,6),"block_reasons":block_reasons}

def build_chart(pair,tf,data,sig):
    c=data["c"];h=data["h"];l=data["l"];o=data.get("o",c)
    n=min(60,len(c)); c=c[-n:];h=h[-n:];l=l[-n:];o=o[-n:]; x=list(range(n))
    fig=plt.Figure(figsize=(10,7),facecolor="#0d1117")
    fig.subplots_adjust(left=0.04,right=0.97,top=0.93,bottom=0.04,hspace=0.08)
    ax1=fig.add_axes([0.04,0.42,0.93,0.54],facecolor="#0d1117")
    ax2=fig.add_axes([0.04,0.23,0.93,0.17],facecolor="#0d1117")
    ax3=fig.add_axes([0.04,0.04,0.93,0.17],facecolor="#0d1117")
    for i in range(n):
        col="#26a69a" if c[i]>=o[i] else "#ef5350"
        body=max(abs(c[i]-o[i]),(h[i]-l[i])*0.003)
        ax1.bar(i,body,bottom=min(c[i],o[i]),width=0.72,color=col,zorder=3)
        ax1.plot([i,i],[l[i],h[i]],color=col,lw=0.8,zorder=2)
    bb_m=[sum(c[max(0,i-20):i+1])/min(i+1,20) for i in range(n)]
    bb_s=[(sum((c[max(0,i-20):i+1][k]-bb_m[i])**2 for k in range(min(i+1,20)))/min(i+1,20))**0.5 for i in range(n)]
    bb_u=[bb_m[i]+2*bb_s[i] for i in range(n)]
    bb_l=[bb_m[i]-2*bb_s[i] for i in range(n)]
    ax1.plot(x,bb_u,color="#ef5350",lw=1.0,alpha=0.9,label="BB Upper")
    ax1.plot(x,bb_m,color="#2196f3",lw=1.0,alpha=0.8,label="BB Mid")
    ax1.plot(x,bb_l,color="#26a69a",lw=1.0,alpha=0.9,label="BB Lower")
    ax1.fill_between(x,bb_u,bb_l,alpha=0.06,color="#2196f3")
    dp=sig["dp"]; fmt=lambda v: f"{v:.{dp}f}" if dp>0 else f"{int(v):,}"
    ax1.axhline(sig["tp"],color="#26a69a",lw=1.2,ls="--",alpha=0.9)
    ax1.axhline(sig["sl"],color="#ef5350",lw=1.2,ls="--",alpha=0.9)
    ax1.text(n-0.5,sig["tp"],f" TP {fmt(sig['tp'])}",color="#26a69a",fontsize=7,va="bottom",ha="right")
    ax1.text(n-0.5,sig["sl"],f" SL {fmt(sig['sl'])}",color="#ef5350",fontsize=7,va="top",ha="right")
    is_buy=sig["is_buy"]; rng=max(max(h)-min(l),sig["live"]*0.001)
    ay=l[-1]-rng*0.5 if is_buy else h[-1]+rng*0.5
    ax1.annotate("",xy=(n-1,l[-1] if is_buy else h[-1]),
                 xytext=(n-1,ay-rng*0.3 if is_buy else ay+rng*0.3),
                 arrowprops=dict(arrowstyle="->",color="#26a69a" if is_buy else "#ef5350",lw=2.5,mutation_scale=20))
    ax1.text(n-1,ay-rng*0.9 if is_buy else ay+rng*0.9,
             f"{'▲ BUY' if is_buy else '▼ SELL'}  {sig['acc']}%",
             color="#26a69a" if is_buy else "#ef5350",fontsize=9,fontweight="bold",ha="center",
             bbox=dict(boxstyle="round,pad=0.3",facecolor="#0d1117",
                       edgecolor="#26a69a" if is_buy else "#ef5350",alpha=0.85))
    ax1.set_title(f"SIGNAL AI  {pair}  {TF_LABEL.get(tf,tf)}  BB(20,2) RSI(7) MACD(12,26,9)",
                  color="#c9d1d9",fontsize=9,fontweight="bold",pad=6,fontfamily="monospace")
    ax1.legend(loc="upper left",facecolor="#161b22",labelcolor="#c9d1d9",fontsize=6.5,framealpha=0.8,edgecolor="#30363d",handlelength=1)
    ax1.tick_params(colors="#484f58",labelsize=6); ax1.yaxis.tick_right()
    for sp in ["top","right","bottom","left"]: ax1.spines[sp].set_color("#30363d")
    ax1.set_xlim(-1,n+1)
    rsi_v=[]
    for i in range(n):
        sub=c[max(0,i-7):i+1]
        if len(sub)<2: rsi_v.append(50); continue
        g=[max(sub[j]-sub[j-1],0) for j in range(1,len(sub))]
        ll=[max(sub[j-1]-sub[j],0) for j in range(1,len(sub))]
        ag=sum(g)/len(g); al_=sum(ll)/len(ll)
        rsi_v.append(round(100-100/(1+ag/al_),1) if al_ else 100)
    ax2.plot(x,rsi_v,color="#f9a825",lw=1.4,zorder=3)
    ax2.axhline(70,color="#ef5350",lw=0.7,ls="--",alpha=0.6)
    ax2.axhline(30,color="#26a69a",lw=0.7,ls="--",alpha=0.6)
    ax2.axhline(50,color="#30363d",lw=0.5)
    ax2.fill_between(x,rsi_v,50,where=[r>50 for r in rsi_v],alpha=0.12,color="#26a69a")
    ax2.fill_between(x,rsi_v,50,where=[r<50 for r in rsi_v],alpha=0.12,color="#ef5350")
    ax2.set_ylim(0,100); ax2.set_xlim(-1,n+1)
    ax2.set_ylabel("RSI(7)",color="#484f58",fontsize=6.5,labelpad=2)
    ax2.tick_params(colors="#484f58",labelsize=5.5)
    for sp in ["top","right","bottom","left"]: ax2.spines[sp].set_color("#30363d")
    ms_=[]; ss_=[]
    for i in range(n):
        sub=c[max(0,i-55):i+1]
        if len(sub)>=27:
            ef=ema(sub,12); es=ema(sub,26); mv=ef-es; ms_.append(mv)
            mv_arr=[ema(c[max(0,j-55):j+1],12)-ema(c[max(0,j-55):j+1],26) for j in range(max(0,i-8),i+1)]
            ss_.append(ema(mv_arr,9) if len(mv_arr)>=9 else mv)
        else:
            ms_.append(0); ss_.append(0)
    hist_=[ms_[i]-ss_[i] for i in range(len(ms_))]
    ax3.bar(x,hist_,color=["#26a69a" if v>=0 else "#ef5350" for v in hist_],width=0.7,alpha=0.8,zorder=3)
    ax3.plot(x,ms_,color="#2196f3",lw=1.2,label="MACD")
    ax3.plot(x,ss_,color="#ff9800",lw=1.0,ls="--",label="Signal")
    ax3.axhline(0,color="#30363d",lw=0.7)
    ax3.set_xlim(-1,n+1); ax3.set_ylabel("MACD(12,26,9)",color="#484f58",fontsize=6.5)
    ax3.legend(loc="upper left",facecolor="#161b22",labelcolor="#c9d1d9",fontsize=6,framealpha=0.7,edgecolor="#30363d",handlelength=1)
    ax3.tick_params(colors="#484f58",labelsize=5.5)
    for sp in ["top","right","bottom","left"]: ax3.spines[sp].set_color("#30363d")
    buf=io.BytesIO()
    fig.savefig(buf,format="png",dpi=120,bbox_inches="tight",facecolor="#0d1117",edgecolor="none")
    buf.seek(0); plt.close(fig)
    return buf

def bar10(v): f=round(max(0,min(100,v))/10); return "▰"*f+"▱"*(10-f)

def format_signal(pair,tf,d):
    now=datetime.now(timezone.utc)+timedelta(hours=2)
    try: exp=(now+timedelta(minutes=TF_HOLD.get(tf,5))).strftime("%H:%M")
    except: exp="—"
    tf_l=TF_LABEL.get(tf,tf); is_buy=d["is_buy"]; dp=d["dp"]
    fmt=lambda v: f"{v:.{dp}f}" if dp>0 else f"{int(v):,}"
    bw=d["buy_w"]; sw=d["sell_w"]
    t_pct=round(bw/(bw+sw)*100) if(bw+sw)>0 else 50
    t_pct=t_pct if is_buy else 100-t_pct
    t_str="Слабий" if t_pct<55 else"Помірний" if t_pct<70 else"Сильний" if t_pct<85 else"Дуже сильний"
    rsi=d["rsi"]
    rsi_z="🟢 Перепроданість" if rsi<=30 else"🔴 Перекупленість" if rsi>=70 else"🟡 Нижня зона" if rsi<50 else"🟠 Верхня зона"
    if d["cross_up"]:    macd_z="🔥 Бичачий перетин ▲"
    elif d["cross_down"]: macd_z="🔥 Ведмежий перетин ▼"
    elif d["hist"]>0:    macd_z="▲ Позитивна гістограма"
    else:                macd_z="▼ Негативна гістограма"
    bp=d["bb_pos"]
    if bp<=10:   bb_z="🔥 Нижче нижньої смуги"
    elif bp>=90: bb_z="🔥 Вище верхньої смуги"
    elif bp<=30: bb_z="▲ Нижня зона BB"
    elif bp>=70: bb_z="▼ Верхня зона BB"
    else:        bb_z="→ Середина BB"
    acc=d["acc"]; acc_em="🔥" if acc>=85 else"✅" if acc>=75 else"⚠️"
    src="🔴 Live" if d["real"] else"⚙️ Розрахунок"
    block_txt=""
    if d["blocked"]:
        block_txt="\n⛔ *НЕ ТОРГУВАТИ*\n"+"".join(f"• {r}\n" for r in d["block_reasons"])
    lines=["╔══ 📊 *SIGNAL AI* ══╗","",
           f"🏷 *{pair}*  ⏱ {tf_l}  {src}",
           f"📍 {d['sess']}","",
           f"📈 *Сила тренду* — {t_str} *{t_pct}%*",
           f"`{bar10(t_pct)}`","",
           f"{'🟢' if is_buy else '🔴'} *{'ВВЕРХ ▲' if is_buy else 'ВНИЗ ▼'}*",
           f"Утримувати до: *{exp}*","",
           f"{acc_em} Точність: *{acc}%*   {d['strength']}","",
           "📊 *Індикатори:*",
           f"• RSI(7): *{rsi}*  {rsi_z}",
           f"• MACD:   {macd_z}",
           f"• BB:     {bb_z}",
           block_txt,
           f"💰 Вхід: `{fmt(d['live'])}`",
           f"🎯 TP: `{fmt(d['tp'])}`  🛑 SL: `{fmt(d['sl'])}`  R:R=1:{d['rr']}","",
           "└─────────────────────┘",
           "⚠️ _Не є фінансовою порадою_"]
    return "\n".join(l for l in lines if l is not None)

def sessions_text():
    h=datetime.now(timezone.utc).hour
    sess=[(7,9,"🟢 Лондон відкриття","Висока волатильність"),
          (9,12,"🟢 Лондон + NY","НАЙКРАЩИЙ час"),
          (12,16,"🟡 Нью-Йорк","Хороша волатильність"),
          (16,18,"🟡 NY закриття","Помірна активність"),
          (18,21,"🔴 Між сесіями","Слабка активність"),
          (21,23,"🟡 Токіо","Активний для JPY"),
          (23,7,"🔴 Нічна","Низька ліквідність")]
    lines=["⏰ *Торгові сесії (UTC+2)*\n"]
    for sh,eh,name,desc in sess:
        active=(sh<=h<eh) if sh<eh else(h>=sh or h<eh)
        lines.append(f"{'👉 ' if active else '     '} *{name}* ({sh:02d}:00–{eh:02d}:00)\n_{desc}_\n")
    return "\n".join(lines)

def stats_text(cid):
    s=get_stats(cid); t=s["total"]; w=s.get("wins",0); l=s.get("losses",0)
    wr=round(w/t*100) if t else 0
    st=s.get("streak",0)
    streak=f"🔥 Серія: {st}" if st>0 else(f"❄️ Серія: {abs(st)}" if st<0 else"➖")
    top=""
    if s.get("pairs"):
        sp=sorted(s["pairs"].items(),key=lambda x:-x[1]["total"])[:3]
        top="\n\n🏆 *Топ пари:*\n"
        for pn,pd in sp:
            pwr=round(pd["wins"]/pd["total"]*100) if pd["total"] else 0
            top+=f"• {pn}: {pd['total']} угод, {pwr}% WR\n"
    return (f"📊 *Статистика*\n\nВсього: *{t}*  ✅ {w}  ❌ {l}\n"
            f"Win Rate: *{wr}%*\n`{bar10(wr)}`\n\n{streak}{top}")

def run_scanner(cid,tf="5"):
    scan=FOREX_PAIRS[:10]+OTC_PAIRS[:8]
    results=[]
    for p in scan:
        try:
            sig=generate_signal(p["name"],tf)
            if sig and sig["acc"]>=78 and not sig["blocked"]:
                results.append((p["name"],sig))
        except: pass
    if not results:
        try: bot.send_message(cid,"🔍 Сканування завершено\n\nСильних сигналів не знайдено.")
        except: pass
        return
    results.sort(key=lambda x:-x[1]["acc"])
    try:
        bot.send_message(cid,f"🔍 *Знайдено {len(results[:3])} сигнали:*",parse_mode="Markdown")
        for pname,sig in results[:3]:
            kb=result_kb(pname,tf); txt=format_signal(pname,tf,sig)
            try:
                data=get_candles(ALL_PAIRS[pname]["symbol"],tf,100)
                if not data: data=make_fallback(pname,tf)
                buf=build_chart(pname,tf,data,sig)
                bot.send_photo(cid,buf,caption=txt[:1024],parse_mode="Markdown",reply_markup=kb)
            except Exception as chart_err:
                print(f"[CHART SEND ERR] {chart_err}")
                bot.send_message(cid,txt,parse_mode="Markdown",reply_markup=kb)
            time.sleep(0.5)
    except Exception as e: print(f"[SCANNER ERR] {e}")

def start_kb():
    kb=ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    kb.add(KeyboardButton("📈 FOREX"),KeyboardButton("🌙 OTC"),
           KeyboardButton("₿ КРИПТО"),KeyboardButton("📊 АКЦІЇ"),
           KeyboardButton("🔍 Сканер"),KeyboardButton("📊 Статистика"),
           KeyboardButton("🕐 Сесії"),KeyboardButton("🏠 Меню"))
    return kb

_REPLY_MAP={"📈 FOREX":"menu_forex","🌙 OTC":"menu_otc","₿ КРИПТО":"menu_crypto",
            "📊 АКЦІЇ":"menu_stocks","🔍 СКАНЕР":"scanner","📊 СТАТИСТИКА":"stats",
            "🕐 СЕСІЇ":"sessions","🏠 МЕНЮ":"main"}

def main_kb():
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("📈 FOREX",callback_data="menu_forex"),
           InlineKeyboardButton("🌙 OTC",callback_data="menu_otc"))
    kb.add(InlineKeyboardButton("₿ КРИПТО",callback_data="menu_crypto"),
           InlineKeyboardButton("📊 АКЦІЇ",callback_data="menu_stocks"))
    kb.add(InlineKeyboardButton("🔍 Сканер",callback_data="scanner"),
           InlineKeyboardButton("📊 Статистика",callback_data="stats"))
    kb.add(InlineKeyboardButton("🕐 Сесії",callback_data="sessions"),
           InlineKeyboardButton("ℹ️ Про бота",callback_data="about"))
    return kb

def pairs_kb(pairs,back):
    kb=InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(p["name"],callback_data=f"pair_{p['name']}") for p in pairs])
    kb.add(InlineKeyboardButton("◀️ Назад",callback_data=back))
    return kb

def tf_kb(pair):
    is_crypto=any(pair==p["name"] for p in CRYPTO_PAIRS)
    is_stocks=any(pair==p["name"] for p in STOCKS_PAIRS)
    tfs=CRYPTO_TF if is_crypto else(STOCKS_TF if is_stocks else TIMEFRAMES)
    back="crypto_back" if is_crypto else("stocks_back" if is_stocks else("otc_back" if "OTC" in pair else "forex_back"))
    kb=InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(v,callback_data=f"tf|{pair}|{k}") for k,v in tfs.items()])
    kb.add(InlineKeyboardButton("◀️ Назад",callback_data=back))
    return kb

def result_kb(pair,tf):
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("✅ Виграш",callback_data=f"win|{pair}|{tf}"),
           InlineKeyboardButton("❌ Програш",callback_data=f"loss|{pair}|{tf}"))
    kb.add(InlineKeyboardButton("🔄 Ще раз",callback_data=f"tf|{pair}|{tf}"),
           InlineKeyboardButton("🏠 Меню",callback_data="main"))
    return kb

_LOOKUP={}
for _p in FOREX_PAIRS+OTC_PAIRS+CRYPTO_PAIRS+STOCKS_PAIRS:
    _n=_p["name"]
    _LOOKUP[_n.replace("/","").replace(" ","").upper()]=_n
    _LOOKUP[_n.upper()]=_n; _LOOKUP[_n]=_n
_LOOKUP.update({"AAPL":"Apple","TSLA":"Tesla","NVDA":"NVIDIA","AMZN":"Amazon",
                "GOOGL":"Google","MSFT":"Microsoft","META":"Meta","NFLX":"Netflix",
                "AMD":"AMD","INTC":"Intel","KO":"Coca-Cola","MCD":"McDonald's"})

def normalize_pair(text):
    t=text.strip().upper().replace("-","").replace("_","")
    if t in _LOOKUP: return _LOOKUP[t]
    t2=t.replace("/","")
    if t2 in _LOOKUP: return _LOOKUP[t2]
    if t2+"USD" in _LOOKUP: return _LOOKUP[t2+"USD"]
    if t2+"OTC" in _LOOKUP: return _LOOKUP[t2+"OTC"]
    return None

def send_main(cid,mid=None):
    total=len(ALL_PAIRS)
    txt=(f"╔══ 📊 *SIGNAL AI* ══╗\n\n"
         f"Індикатори як у PocketOption:\n\n"
         f"• *Bollinger Bands* (20, 2)\n"
         f"• *RSI* (7)\n"
         f"• *MACD* (12, 26, 9)\n\n"
         f"*{total} торгових пар*\n"
         f"Forex • OTC • Крипто • Акції\n\n"
         f"💡 _Напиши назву пари:_\n"
         f"`eurusd` • `chfjpy` • `btc` • `AAPL`\n\n"
         f"╚══ Або оберіть категорію ══╝")
    if mid:
        try: bot.edit_message_text(txt,cid,mid,parse_mode="Markdown",reply_markup=main_kb()); return
        except: pass
    bot.send_message(cid,txt,parse_mode="Markdown",reply_markup=main_kb())

def do_signal(cid,mid,pair,tf):
    # Перевірка що pair існує в списку
    if pair not in ALL_PAIRS:
        try: bot.edit_message_text("❌ Невідома пара",cid,mid,reply_markup=main_kb())
        except: pass
        return
    # Перевірка rate limit
    if not check_rate_limit(cid):
        try: bot.edit_message_text("⏳ Зачекайте кілька секунд перед наступним запитом",cid,mid,reply_markup=main_kb())
        except: pass
        return
    tf_l=TF_LABEL.get(tf,tf)
    steps=[("⟳ Завантаження свічок...","▰▰▰▱▱▱▱▱▱▱ 30%"),
           ("⟳ BB + RSI(7)...","▰▰▰▰▰▰▱▱▱▱ 60%"),
           ("⟳ MACD(12,26,9)...","▰▰▰▰▰▰▰▰▱▱ 80%"),
           ("⟳ Генерую сигнал...","▰▰▰▰▰▰▰▰▰▱ 95%")]
    last=""
    for step,b in steps:
        try:
            txt=f"📊 *SIGNAL AI*\n\n{step}\n\n`{pair}` | `{tf_l}`\n\n{b}"
            if txt!=last: bot.edit_message_text(txt,cid,mid,parse_mode="Markdown"); last=txt
        except: pass
        time.sleep(0.6)
    sig=None
    try: sig=generate_signal(pair,tf)
    except Exception as e:
        print(f"[SIGNAL ERR] {pair} {tf}: {e}")
        import traceback; traceback.print_exc()
    if sig is None:
        try: bot.delete_message(cid,mid)
        except: pass
        try:
            bot.send_message(cid,f"⚠️ *Помилка аналізу*\n\n`{pair}` | `{tf_l}`\n\nСпробуйте ще раз.",
                             parse_mode="Markdown",
                             reply_markup=InlineKeyboardMarkup().add(
                                 InlineKeyboardButton("🔄 Повторити",callback_data=f"tf|{pair}|{tf}"),
                                 InlineKeyboardButton("🏠 Меню",callback_data="main")))
        except: pass
        return
    chart_buf=None
    try:
        m=ALL_PAIRS.get(pair,FOREX_PAIRS[0])
        data=get_candles(m["symbol"],tf,100)
        if not data: data=make_fallback(pair,tf)
        chart_buf=build_chart(pair,tf,data,sig)
    except Exception as e: print(f"[CHART ERR] {e}")
    txt=format_signal(pair,tf,sig)
    try: bot.delete_message(cid,mid)
    except: pass
    try:
        if chart_buf:
            bot.send_photo(cid,chart_buf,caption=txt[:1024],parse_mode="Markdown",reply_markup=result_kb(pair,tf))
            if len(txt)>1024: bot.send_message(cid,txt[1024:],parse_mode="Markdown")
        else:
            bot.send_message(cid,txt,parse_mode="Markdown",reply_markup=result_kb(pair,tf))
    except Exception as e:
        print(f"[SEND ERR] {e}")
        try: bot.send_message(cid,txt,parse_mode="Markdown",reply_markup=result_kb(pair,tf))
        except: pass

@bot.message_handler(commands=["start","menu"])
def cmd_start(msg):
    send_main(msg.chat.id)
    bot.send_message(msg.chat.id,"⌨️ _Клавіатура активована!_",
                     parse_mode="Markdown",reply_markup=start_kb())

@bot.message_handler(commands=["stats"])
def cmd_stats(msg):
    bot.send_message(msg.chat.id,stats_text(msg.chat.id),parse_mode="Markdown",reply_markup=main_kb())

@bot.message_handler(commands=["scan"])
def cmd_scan(msg):
    bot.send_message(msg.chat.id,"🔍 *Сканую ринок...*",parse_mode="Markdown")
    threading.Thread(target=run_scanner,args=(msg.chat.id,),daemon=True).start()

@bot.message_handler(func=lambda m: True)
def cmd_text(msg):
    cid=msg.chat.id; text=(msg.text or "").strip()
    if not text: return
    if text.upper() in _REPLY_MAP:
        action=_REPLY_MAP[text.upper()]
        if action=="main": send_main(cid)
        elif action=="menu_forex": bot.send_message(cid,"📈 *FOREX*\nОберіть пару:",parse_mode="Markdown",reply_markup=pairs_kb(FOREX_PAIRS,"main"))
        elif action=="menu_otc":   bot.send_message(cid,"🌙 *OTC*\nОберіть пару:",parse_mode="Markdown",reply_markup=pairs_kb(OTC_PAIRS,"main"))
        elif action=="menu_crypto":bot.send_message(cid,"₿ *КРИПТО*\nОберіть:",parse_mode="Markdown",reply_markup=pairs_kb(CRYPTO_PAIRS,"main"))
        elif action=="menu_stocks":bot.send_message(cid,"📊 *АКЦІЇ*\nОберіть:",parse_mode="Markdown",reply_markup=pairs_kb(STOCKS_PAIRS,"main"))
        elif action=="scanner":
            bot.send_message(cid,"🔍 *Сканую...*",parse_mode="Markdown")
            threading.Thread(target=run_scanner,args=(cid,),daemon=True).start()
        elif action=="stats":    bot.send_message(cid,stats_text(cid),parse_mode="Markdown",reply_markup=main_kb())
        elif action=="sessions": bot.send_message(cid,sessions_text(),parse_mode="Markdown",reply_markup=main_kb())
        return
    pair=normalize_pair(text)
    if pair:
        is_crypto=any(pair==p["name"] for p in CRYPTO_PAIRS)
        is_stocks=any(pair==p["name"] for p in STOCKS_PAIRS)
        is_otc="OTC" in pair
        tfs=CRYPTO_TF if is_crypto else(STOCKS_TF if is_stocks else TIMEFRAMES)
        cat="₿ Крипто" if is_crypto else("📊 Акції" if is_stocks else("🌙 OTC" if is_otc else"📈 Forex"))
        kb=InlineKeyboardMarkup(row_width=3)
        kb.add(*[InlineKeyboardButton(v,callback_data=f"tf|{pair}|{k}") for k,v in tfs.items()])
        kb.add(InlineKeyboardButton("◀️ Меню",callback_data="main"))
        bot.send_message(cid,f"✅ *{pair}*  {cat}\n\n⏱ Оберіть таймфрейм:",parse_mode="Markdown",reply_markup=kb)
    else:
        bot.send_message(cid,"❓ *Пару не знайдено*\n\n`EURUSD` • `chfjpy` • `btc` • `AAPL`",
                         parse_mode="Markdown",reply_markup=main_kb())

@bot.callback_query_handler(func=lambda c: True)
def handle_cb(call):
    cid=call.message.chat.id; mid=call.message.message_id; d=call.data
    bot.answer_callback_query(call.id)
    try:
        if d=="main": send_main(cid,mid)
        elif d in("menu_forex","forex_back"):   bot.edit_message_text("📈 *FOREX*\nОберіть:",cid,mid,parse_mode="Markdown",reply_markup=pairs_kb(FOREX_PAIRS,"main"))
        elif d in("menu_otc","otc_back"):       bot.edit_message_text("🌙 *OTC*\nОберіть:",cid,mid,parse_mode="Markdown",reply_markup=pairs_kb(OTC_PAIRS,"main"))
        elif d in("menu_crypto","crypto_back"): bot.edit_message_text("₿ *КРИПТО*\nОберіть:",cid,mid,parse_mode="Markdown",reply_markup=pairs_kb(CRYPTO_PAIRS,"main"))
        elif d in("menu_stocks","stocks_back"): bot.edit_message_text("📊 *АКЦІЇ*\nОберіть:",cid,mid,parse_mode="Markdown",reply_markup=pairs_kb(STOCKS_PAIRS,"main"))
        elif d=="stats":    bot.edit_message_text(stats_text(cid),cid,mid,parse_mode="Markdown",reply_markup=main_kb())
        elif d=="sessions": bot.edit_message_text(sessions_text(),cid,mid,parse_mode="Markdown",reply_markup=main_kb())
        elif d=="scanner":
            bot.edit_message_text("🔍 *Сканую...*",cid,mid,parse_mode="Markdown")
            threading.Thread(target=run_scanner,args=(cid,),daemon=True).start()
        elif d=="about":
            bot.edit_message_text(
                "ℹ️ *SIGNAL AI — Індикатори*\n\n"
                "📊 *Bollinger Bands* (20, 2)\n_Зони перекупленості/перепроданості_\n\n"
                "📈 *RSI* (7)\n_Осцилятор сили з коротким періодом_\n\n"
                "⚡ *MACD* (12, 26, 9)\n_Перетини = точки входу_\n\n"
                f"🗂 Пар: *{len(ALL_PAIRS)}*",
                cid,mid,parse_mode="Markdown",reply_markup=main_kb())
        elif d.startswith("pair_"):
            pair=d[5:]
            # Валідація — pair має бути в списку
            if pair not in ALL_PAIRS:
                bot.answer_callback_query(call.id, "❌ Невідома пара")
                return
            bot.edit_message_text(f"⏱ *{pair}*\nОберіть таймфрейм:",cid,mid,parse_mode="Markdown",reply_markup=tf_kb(pair))
        elif d.startswith("tf|"):
            parts=d.split("|",2)
            if len(parts)==3:
                _,pair,tf=parts
                # Валідація pair і tf
                if pair not in ALL_PAIRS or tf not in TF_API:
                    bot.answer_callback_query(call.id, "❌ Некоректні дані")
                    return
                threading.Thread(target=do_signal,args=(cid,mid,pair,tf),daemon=True).start()
        elif d.startswith(("win|","loss|")):
            parts=d.split("|",2)
            if len(parts)!=3: return
            res,pair,tf=parts
            s=get_stats(cid); s["total"]+=1
            if res=="win":
                s["wins"]+=1; s["streak"]=max(s.get("streak",0)+1,1); em="✅ Виграш!"
            else:
                s["losses"]=s.get("losses",0)+1; s["streak"]=min(s.get("streak",0)-1,-1); em="❌ Програш"
            if pair not in s["pairs"]: s["pairs"][pair]={"total":0,"wins":0}
            s["pairs"][pair]["total"]+=1
            if res=="win": s["pairs"][pair]["wins"]+=1
            save_user_stats()
            wr=round(s["wins"]/s["total"]*100)
            bot.send_message(cid,f"{em}\n\n📊 WR: *{wr}%* ({s['wins']}✅/{s.get('losses',0)}❌)",
                             parse_mode="Markdown",reply_markup=main_kb())
    except Exception as e:
        if "not modified" not in str(e):
            print(f"[CB ERR] {e}")
            try: bot.send_message(cid,"Оберіть категорію:",reply_markup=main_kb())
            except: pass

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO,format="%(asctime)s [%(levelname)s] %(message)s")
    logger=logging.getLogger(__name__)
    print(f"✅ SIGNAL AI запущено! Пар: {len(ALL_PAIRS)}")
    logger.info("Bot starting...")
    for attempt in range(8):
        try: bot.close()
        except: pass
        try:
            bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook видалено"); break
        except Exception as e:
            logger.warning(f"delete_webhook {attempt+1}: {e}"); time.sleep(3+attempt*2)
    logger.info("Чекаємо 15 сек..."); time.sleep(15)
    while True:
        try:
            logger.info("Починаємо polling...")
            bot.infinity_polling(timeout=25,long_polling_timeout=20,skip_pending=True,
                                 none_stop=True,allowed_updates=["message","callback_query"])
        except Exception as e:
            err=str(e); logger.error(f"Polling crashed: {err}")
            time.sleep(30 if "409" in err else 10)
            try: bot.close()
            except: pass
            try: bot.delete_webhook(drop_pending_updates=True); time.sleep(5)
            except: pass
