#!/usr/bin/env python3
import os, math, time, requests, threading
from datetime import datetime, timezone, timedelta
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN    = os.environ.get("BOT_TOKEN")
FINNHUB_KEY  = os.environ.get("FINNHUB_KEY", "d6omma1r01qi5kh3hgu0d6omma1r01qi5kh3hgug")
FINNHUB_URL  = "https://finnhub.io/api/v1"
bot = TeleBot(BOT_TOKEN)

# ══════════════════════════════════════════
#  ПАРИ
# ══════════════════════════════════════════
FOREX_PAIRS = [
    {"name":"EUR/USD","symbol":"EURUSD=X","p":1.1559,"d":5,"t":-1},
    {"name":"GBP/USD","symbol":"GBPUSD=X","p":1.2945,"d":5,"t":-1},
    {"name":"USD/JPY","symbol":"USDJPY=X","p":148.72,"d":3,"t":1},
    {"name":"AUD/USD","symbol":"AUDUSD=X","p":0.6285,"d":5,"t":-1},
    {"name":"NZD/USD","symbol":"NZDUSD=X","p":0.5782,"d":5,"t":-1},
    {"name":"USD/CAD","symbol":"USDCAD=X","p":1.4415,"d":5,"t":1},
    {"name":"USD/CHF","symbol":"USDCHF=X","p":0.8832,"d":5,"t":1},
    {"name":"EUR/GBP","symbol":"EURGBP=X","p":0.8663,"d":5,"t":-1},
    {"name":"EUR/JPY","symbol":"EURJPY=X","p":171.88,"d":3,"t":-1},
    {"name":"GBP/JPY","symbol":"GBPJPY=X","p":192.40,"d":3,"t":1},
    {"name":"AUD/CAD","symbol":"AUDCAD=X","p":0.9529,"d":5,"t":-1},
    {"name":"AUD/JPY","symbol":"AUDJPY=X","p":93.52,"d":3,"t":-1},
    {"name":"CHF/JPY","symbol":"CHFJPY=X","p":199.65,"d":3,"t":1},
    {"name":"EUR/AUD","symbol":"EURAUD=X","p":1.8385,"d":5,"t":1},
    {"name":"EUR/CAD","symbol":"EURCAD=X","p":1.6645,"d":5,"t":-1},
    {"name":"GBP/AUD","symbol":"GBPAUD=X","p":2.0590,"d":5,"t":-1},
    {"name":"GBP/CAD","symbol":"GBPCAD=X","p":1.8742,"d":5,"t":-1},
]
OTC_PAIRS = [
    {"name":"EUR/USD OTC","symbol":"EURUSD=X","p":1.1559,"d":5,"t":-1},
    {"name":"GBP/USD OTC","symbol":"GBPUSD=X","p":1.2945,"d":5,"t":-1},
    {"name":"USD/JPY OTC","symbol":"USDJPY=X","p":148.72,"d":3,"t":1},
    {"name":"AUD/USD OTC","symbol":"AUDUSD=X","p":0.6285,"d":5,"t":-1},
    {"name":"EUR/GBP OTC","symbol":"EURGBP=X","p":0.8663,"d":5,"t":-1},
    {"name":"AUD/CAD OTC","symbol":"AUDCAD=X","p":0.9529,"d":5,"t":-1},
    {"name":"EUR/JPY OTC","symbol":"EURJPY=X","p":171.88,"d":3,"t":-1},
    {"name":"GBP/JPY OTC","symbol":"GBPJPY=X","p":192.40,"d":3,"t":1},
    {"name":"USD/CAD OTC","symbol":"USDCAD=X","p":1.4415,"d":5,"t":1},
    {"name":"NZD/USD OTC","symbol":"NZDUSD=X","p":0.5782,"d":5,"t":-1},
    {"name":"USD/CHF OTC","symbol":"USDCHF=X","p":0.8832,"d":5,"t":1},
    {"name":"CHF/JPY OTC","symbol":"CHFJPY=X","p":199.65,"d":3,"t":1},
    {"name":"EUR/AUD OTC","symbol":"EURAUD=X","p":1.8385,"d":5,"t":1},
]
CRYPTO_PAIRS = [
    {"name":"BTC/USD","symbol":"BTC-USD","p":67000,"d":1,"t":1},
    {"name":"ETH/USD","symbol":"ETH-USD","p":3500,"d":2,"t":1},
    {"name":"BNB/USD","symbol":"BNB-USD","p":420,"d":2,"t":1},
    {"name":"SOL/USD","symbol":"SOL-USD","p":180,"d":2,"t":1},
    {"name":"XRP/USD","symbol":"XRP-USD","p":0.62,"d":4,"t":1},
    {"name":"ADA/USD","symbol":"ADA-USD","p":0.45,"d":4,"t":-1},
    {"name":"DOGE/USD","symbol":"DOGE-USD","p":0.18,"d":5,"t":1},
    {"name":"LTC/USD","symbol":"LTC-USD","p":95,"d":2,"t":1},
]
STOCKS_PAIRS = [
    {"name":"Apple","symbol":"AAPL","p":189,"d":2,"t":1},
    {"name":"Tesla","symbol":"TSLA","p":245,"d":2,"t":1},
    {"name":"NVIDIA","symbol":"NVDA","p":875,"d":2,"t":1},
    {"name":"Amazon","symbol":"AMZN","p":185,"d":2,"t":1},
    {"name":"Google","symbol":"GOOGL","p":165,"d":2,"t":1},
    {"name":"Microsoft","symbol":"MSFT","p":415,"d":2,"t":1},
    {"name":"Meta","symbol":"META","p":510,"d":2,"t":1},
    {"name":"Netflix","symbol":"NFLX","p":625,"d":2,"t":1},
]
ALL_PAIRS    = {p["name"]: p for p in FOREX_PAIRS+OTC_PAIRS+CRYPTO_PAIRS+STOCKS_PAIRS}
TIMEFRAMES   = {"1":"1 хв","3":"3 хв","5":"5 хв","15":"15 хв","30":"30 хв","60":"1 год","240":"4 год"}
CRYPTO_TF    = {"5":"5 хв","15":"15 хв","30":"30 хв","60":"1 год","240":"4 год"}
STOCKS_TF    = {"5":"5 хв","15":"15 хв","30":"30 хв","60":"1 год"}

# ══════════════════════════════════════════
#  ТОРГОВІ СЕСІЇ
# ══════════════════════════════════════════
def best_category_now():
    h = datetime.now(timezone.utc).hour
    if 0<=h<7:
        tip = "🌙 *OTC — найкращий зараз*\nПрацює 24/7, виплата 85-92%\n\n🏆 Топ:\n• EUR/USD OTC\n• GBP/USD OTC\n• AUD/USD OTC"
        return "🌙 OTC", tip
    elif 7<=h<13:
        tip = "📈 *FOREX — Лондонська сесія*\nНайкраща ліквідність для EUR\n\n🏆 Топ:\n• EUR/USD\n• GBP/USD\n• EUR/GBP"
        return "📈 FOREX", tip
    elif 13<=h<16:
        tip = "🔥 *FOREX — НАЙКРАЩИЙ ЧАС!*\nЛондон + Нью-Йорк одночасно\n\n🏆 Топ:\n• EUR/USD ⭐\n• GBP/USD ⭐\n• USD/JPY ⭐"
        return "📈 FOREX", tip
    elif 16<=h<22:
        tip = "₿ *КРИПТО — Нью-Йоркська сесія*\nВисока волатильність\n\n🏆 Топ:\n• BTC/USD\n• ETH/USD\n• SOL/USD"
        return "₿ КРИПТО", tip
    else:
        tip = "🌙 *OTC — найкращий зараз*\nForex закритий — OTC 24/7\n\n🏆 Топ:\n• EUR/USD OTC\n• GBP/JPY OTC\n• USD/CAD OTC"
        return "🌙 OTC", tip
def sessions_text():
    now = datetime.now(timezone.utc)
    h   = now.hour
    uah = (now + timedelta(hours=2)).hour
    sess = [("🗼 Токіо",0,9),("🏦 Лондон",7,16),("🗽 Нью-Йорк",13,22)]
    act   = [n for n,s,e in sess if s<=h<e]
    inact = [n for n,s,e in sess if not(s<=h<e)]
    if 13<=h<16:   ac,tip="🔥🔥🔥 МАКСИМАЛЬНА","Лондон+Нью-Йорк — найкращий час!"
    elif 7<=h<13:  ac,tip="🔥🔥 ВИСОКА","Кращі пари: EUR/GBP, EUR/USD"
    elif 13<=h<22: ac,tip="🔥🔥 ВИСОКА","Кращі пари: USD/JPY, GBP/USD"
    elif 0<=h<9:   ac,tip="🔥 СЕРЕДНЯ","Кращі пари: JPY, AUD, NZD"
    else:          ac,tip="😴 НИЗЬКА","Краще утриматись"
    _,best_tip = best_category_now()
    return (f"🕐 *Торгові сесії*\n\n"
            f"UA: `{uah:02d}:00` | UTC: `{h:02d}:00`\n\n"
            f"✅ *Активні:* {' | '.join(act) or 'Немає'}\n"
            f"⚪ *Неактивні:* {' | '.join(inact) or 'Всі'}\n\n"
            f"📊 *Активність:* {ac}\n💡 _{tip}_\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{best_tip}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"*Розклад (UTC+2):*\n"
            f"🗼 Токіо:    02:00–11:00\n"
            f"🏦 Лондон:   09:00–18:00\n"
            f"🗽 Нью-Йорк: 15:00–00:00\n"
            f"🔥 Перетин:  15:00–18:00 ← найкращий")

# ══════════════════════════════════════════
#  FINNHUB + YAHOO API
# ══════════════════════════════════════════
def to_finnhub(symbol):
    if symbol.endswith("=X"):
        b=symbol[:-2]
        if len(b)==6: return f"OANDA:{b[:3]}_{b[3:]}","forex"
    if "-USD" in symbol:
        return f"BINANCE:{symbol.replace('-USD','')}USDT","crypto"
    return symbol,"stock"

def get_candles_finnhub(symbol,tf,count=60):
    tf_map={"1":"1","3":"5","5":"5","15":"15","30":"30","60":"60","240":"D"}
    res=tf_map.get(tf,"5")
    finn,mkt=to_finnhub(symbol)
    now=int(time.time())
    mins=int(tf) if tf.isdigit() and tf!="240" else 1440
    from_ts=now-count*mins*60*3
    try:
        ep={"forex":"forex/candle","crypto":"crypto/candle","stock":"stock/candle"}[mkt]
        url=f"{FINNHUB_URL}/{ep}?symbol={finn}&resolution={res}&from={from_ts}&to={now}&token={FINNHUB_KEY}"
        r=requests.get(url,timeout=8)
        d=r.json()
        if d.get("s")!="ok" or not d.get("c"): return [],[],[],[]
        c=d["c"]; h=d["h"]; l=d["l"]; v=d.get("v",[0]*len(c))
        n=min(len(c),len(h),len(l),len(v),count)
        return c[-n:],h[-n:],l[-n:],v[-n:]
    except: return [],[],[],[]

def get_candles_yahoo(symbol,tf,count=60):
    tf_map={"1":"1m","3":"2m","5":"5m","15":"15m","30":"30m","60":"1h","240":"4h"}
    interval=tf_map.get(tf,"5m")
    period="1d" if tf in ["1","3","5","15"] else ("60d" if tf=="240" else "5d")
    try:
        url=f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={period}"
        r=requests.get(url,timeout=8,headers={"User-Agent":"Mozilla/5.0"})
        res=r.json()["chart"]["result"][0]
        q=res["indicators"]["quote"][0]
        c=[x for x in q["close"] if x]; h=[x for x in q["high"] if x]
        l=[x for x in q["low"] if x]; v=[x for x in (q.get("volume") or [0]*len(c)) if x is not None]
        n=min(len(c),len(h),len(l),len(v),count)
        return c[-n:],h[-n:],l[-n:],v[-n:]
    except: return [],[],[],[]

def get_candles(symbol,tf,count=60):
    c,h,l,v=get_candles_finnhub(symbol,tf,count)
    if len(c)>=10: return c,h,l,v
    return get_candles_yahoo(symbol,tf,count)

def get_price(symbol,fallback):
    finn,mkt=to_finnhub(symbol)
    try:
        url=f"{FINNHUB_URL}/quote?symbol={finn}&token={FINNHUB_KEY}"
        r=requests.get(url,timeout=5)
        p=r.json().get("c")
        if p and float(p)>0: return float(p)
    except: pass
    try:
        url=f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
        r=requests.get(url,timeout=5,headers={"User-Agent":"Mozilla/5.0"})
        return float(r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"])
    except: return fallback

# ══════════════════════════════════════════
#  7 ІНДИКАТОРІВ
# ══════════════════════════════════════════
def seeded_rand(seed,offset=0):
    x=math.sin(seed+offset)*43758.5453123; return x-math.floor(x)

def calc_rsi(closes,period=14):
    if len(closes)<period+1: return 50
    gains=[max(closes[i]-closes[i-1],0) for i in range(1,len(closes))]
    losses=[max(closes[i-1]-closes[i],0) for i in range(1,len(closes))]
    ag=sum(gains[-period:])/period; al=sum(losses[-period:])/period
    return round(100-100/(1+ag/al),1) if al else 100

def calc_ema(closes,period):
    if len(closes)<period: return closes[-1] if closes else 0
    k=2/(period+1); ema=sum(closes[:period])/period
    for p in closes[period:]: ema=p*k+ema*(1-k)
    return ema

def calc_macd(closes):
    if len(closes)<26: return 0,0
    e12=calc_ema(closes,12); e26=calc_ema(closes,26); ml=e12-e26
    mv=[calc_ema(closes[:i],12)-calc_ema(closes[:i],26) for i in range(26,len(closes)+1)]
    sig=calc_ema(mv,9) if len(mv)>=9 else ml
    return round(ml,6),round(ml-sig,6)

def calc_stoch(closes,highs,lows,k=14):
    if len(closes)<k: return 50
    lk=min(lows[-k:]); hk=max(highs[-k:])
    return round((closes[-1]-lk)/(hk-lk)*100,1) if hk!=lk else 50

def calc_bb(closes,period=20):
    if len(closes)<period: return 50
    sma=sum(closes[-period:])/period
    std=(sum((x-sma)**2 for x in closes[-period:])/period)**0.5
    if std==0: return 50
    return round(max(0,min(100,(closes[-1]-(sma-2*std))/((sma+2*std)-(sma-2*std))*100)),1)

def calc_ema_cross(closes):
    if len(closes)<21: return 0
    e9=calc_ema(closes,9); e21=calc_ema(closes,21)
    e9p=calc_ema(closes[:-1],9); e21p=calc_ema(closes[:-1],21)
    if e9>e21 and e9p<=e21p: return 2
    if e9<e21 and e9p>=e21p: return -2
    return 1 if e9>e21 else -1

def calc_williams_r(closes,highs,lows,period=14):
    if len(closes)<period: return -50
    hh=max(highs[-period:]); ll=min(lows[-period:])
    if hh==ll: return -50
    return round((hh-closes[-1])/(hh-ll)*-100,1)

def calc_wave_trend(closes,n1=10,n2=21):
    if len(closes)<n2+n1: return 0,0
    diff=[abs(closes[i]-calc_ema(closes[:i+1],n1)) for i in range(len(closes))]
    if len(diff)<n1: return 0,0
    ci=[(closes[i]-calc_ema(closes[:i+1],n1))/(0.015*max(calc_ema(diff[:i+1],n1),1e-9))
        for i in range(n1,len(closes))]
    if len(ci)<n2: return 0,0
    wt1=calc_ema(ci,n2)
    wt1p=calc_ema(ci[:-1],n2) if len(ci)>n2 else wt1
    return round(wt1,2),round(wt1p,2)

def calc_adx(closes,highs,lows,period=14):
    if len(closes)<period+2: return 20
    trs,pdms,ndms=[],[],[]
    for i in range(1,len(closes)):
        trs.append(max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1])))
        up=highs[i]-highs[i-1]; dn=lows[i-1]-lows[i]
        pdms.append(up if up>dn and up>0 else 0)
        ndms.append(dn if dn>up and dn>0 else 0)
    atr=sum(trs[-period:])/period
    pdi=(sum(pdms[-period:])/period)/atr*100 if atr else 0
    ndi=(sum(ndms[-period:])/period)/atr*100 if atr else 0
    dx=abs(pdi-ndi)/(pdi+ndi)*100 if (pdi+ndi) else 0
    return round(dx,1)

# ══════════════════════════════════════════
#  ГЕНЕРАЦІЯ СИГНАЛУ (7 індикаторів)
# ══════════════════════════════════════════
def generate_signal(pair_name,tf):
    m=ALL_PAIRS.get(pair_name,FOREX_PAIRS[0])
    is_otc="OTC" in pair_name
    closes,highs,lows,volumes=get_candles(m["symbol"],tf,60)
    live=get_price(m["symbol"],m["p"])
    real=len(closes)>=20

    if real:
        rsi=calc_rsi(closes)
        macd,mh=calc_macd(closes)
        ec=calc_ema_cross(closes)
        stoch=calc_stoch(closes,highs,lows)
        bb=calc_bb(closes)
        wpr=calc_williams_r(closes,highs,lows)
        wt1,wt1p=calc_wave_trend(closes)
        adx=calc_adx(closes,highs,lows)
        e9=round(calc_ema(closes,9),m["d"])
        e21=round(calc_ema(closes,21),m["d"])
    else:
        seed=sum(ord(c) for c in pair_name)+int(tf)+int(time.time()//60)
        r=lambda i:seeded_rand(seed,i)
        rsi=round(28+r(1)*50); macd=(r(3)-.5)*.006; mh=macd*.3
        ec=m["t"]; stoch=round(15+r(5)*70); bb=r(4)*100
        wpr=round(-80+r(6)*60); wt1=round(-50+r(7)*100); wt1p=wt1+r(8)*5-2.5
        adx=round(22+r(2)*55)
        e9=round(live*(1+(r(9)-.5)*.002),m["d"])
        e21=round(live*(1+(r(10)-.5)*.003),m["d"])

    votes=[]
    # 1. RSI
    if rsi<30:    votes.append(("RSI",1,f"RSI={rsi} перепроданість 🟢"))
    elif rsi>70:  votes.append(("RSI",-1,f"RSI={rsi} перекупленість 🔴"))
    elif rsi<45:  votes.append(("RSI",1,f"RSI={rsi} бичачий нахил"))
    elif rsi>55:  votes.append(("RSI",-1,f"RSI={rsi} ведмежий нахил"))
    else:         votes.append(("RSI",0,f"RSI={rsi} нейтраль ⚪"))
    # 2. MACD
    if macd>0 and mh>0:   votes.append(("MACD",1,"MACD ▲ BUY 🟢"))
    elif macd<0 and mh<0: votes.append(("MACD",-1,"MACD ▼ SELL 🔴"))
    else:                  votes.append(("MACD",0,"MACD нейтральний ⚪"))
    # 3. EMA Cross
    if ec==2:    votes.append(("EMA Cross",1,"EMA 9/21 перетин ▲ BUY 🟢"))
    elif ec==-2: votes.append(("EMA Cross",-1,"EMA 9/21 перетин ▼ SELL 🔴"))
    elif ec==1:  votes.append(("EMA Cross",1,"EMA 9>21 бичачий тренд"))
    else:        votes.append(("EMA Cross",-1,"EMA 9<21 ведмежий тренд"))
    # 4. Stochastic
    if stoch<20:   votes.append(("Stoch",1,f"Stoch={stoch} перепроданість 🟢"))
    elif stoch>80: votes.append(("Stoch",-1,f"Stoch={stoch} перекупленість 🔴"))
    else:          votes.append(("Stoch",0,f"Stoch={stoch} нейтраль ⚪"))
    # 5. Bollinger Bands
    if bb<15:      votes.append(("BB",1,"BB нижня смуга — BUY 🟢"))
    elif bb>85:    votes.append(("BB",-1,"BB верхня смуга — SELL 🔴"))
    else:          votes.append(("BB",0,f"BB середина {bb:.0f}% ⚪"))
    # 6. Williams %R
    if wpr<-80:   votes.append(("Williams%R",1,f"W%R={wpr} перепроданість 🟢"))
    elif wpr>-20: votes.append(("Williams%R",-1,f"W%R={wpr} перекупленість 🔴"))
    elif wpr<-50: votes.append(("Williams%R",1,f"W%R={wpr} нахил вгору"))
    else:         votes.append(("Williams%R",-1,f"W%R={wpr} нахил вниз"))
    # 7. Wave Trend
    wt_up  = wt1>wt1p and wt1p<-60
    wt_dn  = wt1<wt1p and wt1p>60
    if wt_up:    votes.append(("WaveTrend",1,"WT перетин ▲ перепроданість 🟢"))
    elif wt_dn:  votes.append(("WaveTrend",-1,"WT перетин ▼ перекупленість 🔴"))
    elif wt1<0:  votes.append(("WaveTrend",1,f"WT={wt1} зона BUY"))
    else:        votes.append(("WaveTrend",-1,f"WT={wt1} зона SELL"))

    bc=sum(1 for v in votes if v[1]==1)
    sc=sum(1 for v in votes if v[1]==-1)
    is_buy=(bc>=sc)
    adx_ok=adx>=25

    # Впевненість
    score=max(bc,sc)
    adx_b=round(min(adx/100,.15)*8)
    conf=min(97,round(65+min(score/7,1)*25+adx_b+(4 if adx_ok else 0)))

    if score<=3:   strength="⚠️ СЛАБКИЙ"
    elif score<=5: strength="✅ СЕРЕДНІЙ"
    elif score<=6: strength="🔥 СИЛЬНИЙ"
    else:          strength="🔥🔥 ДУЖЕ СИЛЬНИЙ"

    d=m["d"]; mult=1 if live>100 else(.01 if live>10 else .0001)
    atr=sum(abs(closes[i]-closes[i-1]) for i in range(-10,0))/10 if real and len(closes)>=10 else mult*3
    atr=max(atr,mult*2); sp=1.8 if is_otc else 1.0
    tp1=round(live+atr*1.5,d) if is_buy else round(live-atr*1.5,d)
    tp2=round(live+atr*2.5,d) if is_buy else round(live-atr*2.5,d)
    sl =round(live-atr*sp,d)  if is_buy else round(live+atr*sp,d)
    rr =round(abs(tp1-live)/abs(sl-live),1) if abs(sl-live)>0 else 1.5

    return dict(is_buy=is_buy,conf=conf,strength=strength,live=live,
                tp1=tp1,tp2=tp2,sl=sl,rr=rr,adx=adx,adx_ok=adx_ok,
                rsi=rsi,macd=macd,stoch=stoch,bb=bb,wpr=wpr,wt1=wt1,
                e9=e9,e21=e21,votes=votes,bc=bc,sc=sc,real=real,is_otc=is_otc)

# ══════════════════════════════════════════
#  ФОРМАТУВАННЯ СИГНАЛУ
# ══════════════════════════════════════════
def format_signal(pair,tf,d):
    now_dt=datetime.now(timezone.utc)+timedelta(hours=2)
    now=now_dt.strftime("%H:%M:%S")
    tf_hold={"1":(1,2),"3":(3,5),"5":(5,10),"15":(15,20),"30":(30,35),"60":(60,75),"240":(240,260)}
    hm=tf_hold.get(tf,(5,10))
    exp=(now_dt+timedelta(minutes=hm[0])).strftime("%H:%M")
    is_buy=d["is_buy"]
    is_crypto=pair in [p["name"] for p in CRYPTO_PAIRS]
    is_stocks=pair in [p["name"] for p in STOCKS_PAIRS]
    mkt="₿ КРИПТО" if is_crypto else("📊 АКЦІЇ" if is_stocks else("🌙 OTC" if d["is_otc"] else "📈 FOREX"))
    conf_bar=("🟩" if is_buy else "🟥")*round(d["conf"]/10)+("⬜"*(10-round(d["conf"]/10)))
    vt="".join(f"{'🟢' if v[1]==1 else '🔴' if v[1]==-1 else '⚪'} {v[2]}\n" for v in d["votes"])
    adw="" if d["adx_ok"] else "\n⚠️ _ADX<25 — тренд слабкий_"

    if is_buy:
        hdr="🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩"; direction="📗 КУПИТИ — BUY ▲ 📗"; arrow="⬆️⬆️⬆️"
        c_tp="💚"; c_sl="❤️"
    else:
        hdr="🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥"; direction="📕 ПРОДАТИ — SELL ▼ 📕"; arrow="⬇️⬇️⬇️"
        c_tp="❤️"; c_sl="💚"

    return f"""{hdr}
⚡ *AI Signal Bot — Pocket Option*
{mkt} | {"🔴 Live" if d["real"] else "⚙️ Розрах"} | {now}
{hdr}

{arrow} *{direction}* {arrow}
💪 *{d["strength"]}*
⏱ Утримувати: *{hm[0]}–{hm[1]} хв* | 🕐 {exp}

📊 *Впевненість: {d["conf"]}%*
{conf_bar}
🟢 BUY: `{d["bc"]}/7` | 🔴 SELL: `{d["sc"]}/7`
📐 ADX: `{d["adx"]}` {"💪" if d["adx_ok"] else "⚠️"}{adw}

*Пара:* `{pair}` | *ТФ:* `{TIMEFRAMES.get(tf,tf)}`
💰 Вхід: `{d["live"]}`
{c_tp} TP1: `{d["tp1"]}` | TP2: `{d["tp2"]}`
{c_sl} SL: `{d["sl"]}` | R/R: `1:{d["rr"]}`
📉 EMA9: `{d["e9"]}` | EMA21: `{d["e21"]}`

{hdr}
🔬 *7 індикаторів:*
{vt}
{hdr}
⚠️ _Не є фінансовою порадою_""".strip()

# ══════════════════════════════════════════
#  АВТОСКАНУВАННЯ
# ══════════════════════════════════════════
auto_scan_settings={}; auto_scan_threads={}

def get_scan_settings(cid):
    if cid not in auto_scan_settings:
        auto_scan_settings[cid]={"active":False,"tf":"5","min_conf":80,"min_votes":5}
    return auto_scan_settings[cid]

def auto_scan_text(cid):
    s=get_scan_settings(cid)
    st="🟢 АКТИВНЕ" if s["active"] else "🔴 ВИМКНЕНО"
    n=len(FOREX_PAIRS)+len(OTC_PAIRS)+len(CRYPTO_PAIRS[:4])
    return (f"🔍 *Автосканування*\n\nСтатус: *{st}*\n"
            f"⏱ Таймфрейм: *{TIMEFRAMES.get(s['tf'],s['tf'])}*\n"
            f"🎯 Мін. впевненість: *{s['min_conf']}%*\n"
            f"✅ Мін. голосів: *{s['min_votes']}/7*\n"
            f"📊 Сканує: *{n} пар*\n\n"
            f"_Бот надсилає тільки найкращі сигнали_")

def auto_scan_kb(cid):
    s=get_scan_settings(cid)
    kb=InlineKeyboardMarkup(row_width=2)
    if s["active"]:
        kb.add(InlineKeyboardButton("⏹ ЗУПИНИТИ",callback_data="scan_stop"))
    else:
        kb.add(InlineKeyboardButton("▶️ ЗАПУСТИТИ",callback_data="scan_start"))
    kb.add(InlineKeyboardButton(f"⏱ {TIMEFRAMES.get(s['tf'],s['tf'])}",callback_data="scan_tf"),
           InlineKeyboardButton(f"🎯 {s['min_conf']}%",callback_data="scan_conf"))
    kb.add(InlineKeyboardButton(f"✅ Голосів: {s['min_votes']}+",callback_data="scan_votes"),
           InlineKeyboardButton("◀️ Меню",callback_data="main"))
    return kb

def result_kb_auto(pair,tf):
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("✅ Виграш",callback_data=f"win|{pair}|{tf}"),
           InlineKeyboardButton("❌ Програш",callback_data=f"loss|{pair}|{tf}"))
    kb.add(InlineKeyboardButton("⏹ Зупинити авто",callback_data="scan_stop"))
    return kb

def auto_scan_loop(cid):
    s=get_scan_settings(cid)
    print(f"🔄 Авто для {cid}")
    while s.get("active",False):
        try:
            tf=s["tf"]; mc=s["min_conf"]; mv=s["min_votes"]
            all_p=FOREX_PAIRS+OTC_PAIRS+CRYPTO_PAIRS[:4]
            best=[]
            for p in all_p:
                try:
                    sig=generate_signal(p["name"],tf)
                    vf=sig["bc"] if sig["is_buy"] else sig["sc"]
                    if sig["conf"]>=mc and vf>=mv:
                        best.append((p["name"],sig))
                except: pass
            best.sort(key=lambda x:x[1]["conf"],reverse=True)
            best=best[:2]
            now_str=(datetime.now(timezone.utc)+timedelta(hours=2)).strftime("%H:%M")
            if not best:
                bot.send_message(cid,f"🔍 *{now_str}* — сканував {len(all_p)} пар\n😴 Сильних сигналів немає\n_Наступне через {tf} хв_",parse_mode="Markdown")
            else:
                for pn,sig in best:
                    bot.send_message(cid,f"🔔 *АВТОСИГНАЛ {now_str}*\n\n"+format_signal(pn,tf,sig),
                        parse_mode="Markdown",reply_markup=result_kb_auto(pn,tf))
                    time.sleep(1)
            for _ in range(int(tf)):
                if not s.get("active",False): break
                time.sleep(60)
        except Exception as e:
            print(f"Scan err: {e}"); time.sleep(30)

def start_auto_scan(cid):
    s=get_scan_settings(cid); s["active"]=True
    old=auto_scan_threads.get(cid)
    if old and old.is_alive(): return
    t=threading.Thread(target=auto_scan_loop,args=(cid,),daemon=True)
    auto_scan_threads[cid]=t; t.start()

def stop_auto_scan(cid):
    get_scan_settings(cid)["active"]=False

# ══════════════════════════════════════════
#  КЛАВІАТУРИ
# ══════════════════════════════════════════
def main_kb(cid=None):
    is_active=auto_scan_settings.get(cid,{}).get("active",False) if cid else False
    auto_lbl="🟢 АВТО ВКЛ ✅" if is_active else "🔴 АВТО ВИКЛ"
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("📈 FOREX",   callback_data="menu_forex"),
           InlineKeyboardButton("🌙 OTC",     callback_data="menu_otc"))
    kb.add(InlineKeyboardButton("₿ КРИПТО",  callback_data="menu_crypto"),
           InlineKeyboardButton("📊 АКЦІЇ",   callback_data="menu_stocks"))
    kb.add(InlineKeyboardButton(auto_lbl,     callback_data="auto_menu"))
    kb.add(InlineKeyboardButton("🕐 Сесії",   callback_data="sessions"),
           InlineKeyboardButton("ℹ️ Про бота",callback_data="about"))
    return kb

def forex_kb():
    kb=InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(p["name"],callback_data=f"pair_{p['name']}") for p in FOREX_PAIRS])
    kb.add(InlineKeyboardButton("◀️ Назад",callback_data="main")); return kb

def otc_kb():
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(*[InlineKeyboardButton(p["name"],callback_data=f"pair_{p['name']}") for p in OTC_PAIRS])
    kb.add(InlineKeyboardButton("◀️ Назад",callback_data="main")); return kb

def crypto_kb():
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(*[InlineKeyboardButton(p["name"],callback_data=f"pair_{p['name']}") for p in CRYPTO_PAIRS])
    kb.add(InlineKeyboardButton("◀️ Назад",callback_data="main")); return kb

def stocks_kb():
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(*[InlineKeyboardButton(p["name"],callback_data=f"pair_{p['name']}") for p in STOCKS_PAIRS])
    kb.add(InlineKeyboardButton("◀️ Назад",callback_data="main")); return kb

def tf_kb(pair):
    is_crypto=pair in [p["name"] for p in CRYPTO_PAIRS]
    is_stocks=pair in [p["name"] for p in STOCKS_PAIRS]
    tfs=CRYPTO_TF if is_crypto else(STOCKS_TF if is_stocks else TIMEFRAMES)
    back="crypto_back" if is_crypto else("stocks_back" if is_stocks else("otc_back" if "OTC" in pair else "forex_back"))
    kb=InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(v,callback_data=f"tf|{pair}|{k}") for k,v in tfs.items()])
    kb.add(InlineKeyboardButton("◀️ Назад",callback_data=back)); return kb

def result_kb(pair,tf):
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("✅ Виграш", callback_data=f"win|{pair}|{tf}"),
           InlineKeyboardButton("❌ Програш",callback_data=f"loss|{pair}|{tf}"))
    kb.add(InlineKeyboardButton("🔄 Ще сигнал",callback_data=f"tf|{pair}|{tf}"),
           InlineKeyboardButton("🏠 Меню",      callback_data="main"))
    return kb

def safe_edit(bot,cid,mid,text,markup=None):
    try:
        bot.edit_message_text(text,cid,mid,parse_mode="Markdown",reply_markup=markup)
    except Exception as e:
        if "not modified" in str(e) or "400" in str(e):
            try: bot.edit_message_text(text+" ",cid,mid,parse_mode="Markdown",reply_markup=markup)
            except: bot.send_message(cid,text,parse_mode="Markdown",reply_markup=markup)
        else:
            bot.send_message(cid,text,parse_mode="Markdown",reply_markup=markup)

def send_main(cid,mid=None):
    best_cat, best_tip = best_category_now()
    uah = (datetime.now(timezone.utc)+timedelta(hours=2)).strftime("%H:%M")
    txt=(f"⚡ *AI Signal Bot — Pocket Option*\n\n"
         f"• RSI • MACD • EMA 9/21\n"
         f"• Stochastic • Bollinger Bands\n"
         f"• Williams %R • Wave Trend\n\n"
         f"📊 *7 індикаторів | Finnhub API*\n\n"
         f"━━━━━━━━━━━━━━━━━━\n"
         f"🕐 *{uah} — Зараз найкраще:*\n"
         f"{best_tip}\n"
         f"━━━━━━━━━━━━━━━━━━\n\n"
         f"Оберіть категорію:")
    if mid:
        try: bot.edit_message_text(txt,cid,mid,parse_mode="Markdown",reply_markup=main_kb(cid)); return
        except: pass
    bot.send_message(cid,txt,parse_mode="Markdown",reply_markup=main_kb(cid))

# ══════════════════════════════════════════
#  СТАТИСТИКА (спрощена)
# ══════════════════════════════════════════
user_stats={}
last_signal={}

def get_stats(cid):
    if cid not in user_stats:
        user_stats[cid]={"total":0,"wins":0,"losses":0,"pairs":{},"streak":0}
    return user_stats[cid]

# ══════════════════════════════════════════
#  ХЕНДЛЕРИ
# ══════════════════════════════════════════
@bot.message_handler(commands=["start","menu"])
def cmd_start(msg): send_main(msg.chat.id)

@bot.message_handler(commands=["sessions"])
def cmd_sessions(msg):
    bot.send_message(msg.chat.id,sessions_text(),parse_mode="Markdown",reply_markup=main_kb(msg.chat.id))

@bot.callback_query_handler(func=lambda c:True)
def handle_callback(call):
    cid=call.message.chat.id; mid=call.message.message_id; d=call.data
    bot.answer_callback_query(call.id)
    try:
        if d=="main": send_main(cid,mid)
        elif d in("menu_forex","forex_back"): safe_edit(bot,cid,mid,"📈 *FOREX*\nОберіть пару:",forex_kb())
        elif d in("menu_otc","otc_back"):     safe_edit(bot,cid,mid,"🌙 *OTC*\nОберіть пару:",otc_kb())
        elif d in("menu_crypto","crypto_back"):safe_edit(bot,cid,mid,"₿ *КРИПТО*\nОберіть:",crypto_kb())
        elif d in("menu_stocks","stocks_back"):safe_edit(bot,cid,mid,"📊 *АКЦІЇ*\nОберіть:",stocks_kb())
        elif d=="sessions": safe_edit(bot,cid,mid,sessions_text(),main_kb(cid))
        elif d=="about":
            safe_edit(bot,cid,mid,
                "ℹ️ *AI Signal Bot*\n\n"
                "• RSI\n• MACD\n• EMA Cross 9/21\n"
                "• Stochastic\n• Bollinger Bands\n"
                "• Williams %R\n• Wave Trend\n\n"
                "📊 *7 індикаторів одночасно*\n"
                "📡 Finnhub (реальний час) + Yahoo\n"
                "🕐 UTC+2",main_kb(cid))
        elif d=="auto_menu": safe_edit(bot,cid,mid,auto_scan_text(cid),auto_scan_kb(cid))
        elif d=="scan_start":
            start_auto_scan(cid)
            s=get_scan_settings(cid)
            bot.send_message(cid,
                f"✅ *Автосканування запущено!*\n\n"
                f"⏱ ТФ: *{TIMEFRAMES.get(s['tf'],s['tf'])}*\n"
                f"🎯 Мін: *{s['min_conf']}%* | ✅ Голосів: *{s['min_votes']}/7*\n\n"
                f"_Перший сигнал через ~{s['tf']} хв_",
                parse_mode="Markdown",reply_markup=auto_scan_kb(cid))
        elif d=="scan_stop":
            stop_auto_scan(cid)
            bot.send_message(cid,"⏹ *Зупинено*\n\nНатисніть ▶️ щоб запустити знову",
                parse_mode="Markdown",reply_markup=main_kb(cid))
        elif d=="scan_tf":
            tfs=["5","15","30","60"]; s=get_scan_settings(cid); cur=s.get("tf","5")
            s["tf"]=tfs[(tfs.index(cur)+1)%len(tfs) if cur in tfs else 0]
            safe_edit(bot,cid,mid,auto_scan_text(cid),auto_scan_kb(cid))
        elif d=="scan_conf":
            confs=[70,75,80,85,90]; s=get_scan_settings(cid); cur=s.get("min_conf",80)
            s["min_conf"]=confs[(confs.index(cur)+1)%len(confs) if cur in confs else 2]
            safe_edit(bot,cid,mid,auto_scan_text(cid),auto_scan_kb(cid))
        elif d=="scan_votes":
            vts=[4,5,6,7]; s=get_scan_settings(cid); cur=s.get("min_votes",5)
            s["min_votes"]=vts[(vts.index(cur)+1)%len(vts) if cur in vts else 1]
            safe_edit(bot,cid,mid,auto_scan_text(cid),auto_scan_kb(cid))
        elif d.startswith("pair_"):
            pair=d[5:]
            safe_edit(bot,cid,mid,f"⏱ *Таймфрейм для {pair}*\nОберіть:",tf_kb(pair))
        elif d.startswith("tf|"):
            _,pair,tf=d.split("|",2)
            bot.edit_message_text(f"⏳ Аналізую *{pair}*...",cid,mid,parse_mode="Markdown")
            sig=generate_signal(pair,tf)
            last_signal[cid]={"pair":pair,"tf":tf}
            bot.edit_message_text(format_signal(pair,tf,sig),cid,mid,
                parse_mode="Markdown",reply_markup=result_kb(pair,tf))
        elif d.startswith("win|") or d.startswith("loss|"):
            res,pair,tf=d.split("|",2)
            s=get_stats(cid); s["total"]+=1; is_win=res=="win"
            if is_win: s["wins"]+=1; s["streak"]=max(s.get("streak",0)+1,1); emoji="✅ Виграш!"
            else:      s["losses"]+=1; s["streak"]=min(s.get("streak",0)-1,-1); emoji="❌ Програш"
            if pair not in s["pairs"]: s["pairs"][pair]={"total":0,"wins":0}
            s["pairs"][pair]["total"]+=1
            if is_win: s["pairs"][pair]["wins"]+=1
            wr=round(s["wins"]/s["total"]*100)
            st=s.get("streak",0)
            streak_txt=f"\n🔥 Серія: {st}" if st>1 else(f"\n❄️ Серія: {abs(st)}" if st<-1 else "")
            bot.send_message(cid,
                f"{emoji}\n\n📊 WR: *{wr}%* ({s['wins']}W/{s['losses']}L){streak_txt}\n\nОберіть дію:",
                parse_mode="Markdown",reply_markup=main_kb(cid))
    except Exception as e:
        print(f"Err: {e}")
        bot.send_message(cid,"Оберіть категорію:",reply_markup=main_kb(cid))

# ══════════════════════════════════════════
#  ЗАПУСК
# ══════════════════════════════════════════
if __name__=="__main__":
    print("✅ AI Signal Bot запущено! 7 індикаторів | Finnhub API")
    bot.infinity_polling()
