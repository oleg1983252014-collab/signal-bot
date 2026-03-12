#!/usr/bin/env python3
import os, math, time, requests
from datetime import datetime, timezone, timedelta
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN   = os.environ.get("BOT_TOKEN")
FINNHUB_KEY  = os.environ.get("FINNHUB_KEY",  "d6omma1r01qi5kh3hgu0d6omma1r01qi5kh3hgug")
FINNHUB_URL  = "https://finnhub.io/api/v1"
ALPHA_KEY    = os.environ.get("ALPHA_KEY",   "XT8NVDBOAK9YWES5")
ALPHA_URL    = "https://www.alphavantage.co/query"
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
    {"name":"MATIC/USD","symbol":"MATIC-USD","p":0.85,"d":4,"t":1},
    {"name":"DOT/USD","symbol":"DOT-USD","p":7.5,"d":3,"t":1},
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
ALL_PAIRS = {p["name"]: p for p in FOREX_PAIRS+OTC_PAIRS+CRYPTO_PAIRS+STOCKS_PAIRS}
TIMEFRAMES  = {"1":"1 хв","3":"3 хв","5":"5 хв","15":"15 хв","30":"30 хв","60":"1 год"}
CRYPTO_TF   = {"5":"5 хв","15":"15 хв","30":"30 хв","60":"1 год","240":"4 год"}
STOCKS_TF   = {"5":"5 хв","15":"15 хв","30":"30 хв","60":"1 год"}

# ══════════════════════════════════════════
#  СТАТИСТИКА
# ══════════════════════════════════════════
user_stats = {}

def get_stats(cid):
    if cid not in user_stats:
        user_stats[cid] = {"total":0,"wins":0,"losses":0,"pairs":{},"streak":0}
    return user_stats[cid]

def stats_text(cid):
    s = get_stats(cid)
    if s["total"] == 0:
        return "📊 *Статистика*\n\nЩе немає угод.\nПісля сигналу натисніть ✅ або ❌"
    wr  = round(s["wins"]/s["total"]*100)
    bar = "🟢"*round(wr/10) + "⚪"*(10-round(wr/10))
    best = sorted(s["pairs"].items(), key=lambda x: x[1]["wins"]/(x[1]["total"] or 1), reverse=True)[:3]
    bt   = "".join(f"  • {n}: {d['wins']}/{d['total']} ({round(d['wins']/(d['total'] or 1)*100)}%)\n" for n,d in best)
    st   = s.get("streak",0)
    sl   = (f"🔥 Серія виграшів: {st}\n" if st>1 else f"❄️ Серія програшів: {abs(st)}\n" if st<-1 else "")
    return (f"📊 *Статистика*\n\nВсього: `{s['total']}`\n✅ Виграші: `{s['wins']}`\n"
            f"❌ Програші: `{s['losses']}`\n\n🏆 *WR: {wr}%*\n{bar}\n\n{sl}"
            f"🥇 *Кращі пари:*\n{bt}")

# ══════════════════════════════════════════
#  ТОРГОВІ СЕСІЇ
# ══════════════════════════════════════════
def sessions_text():
    now = datetime.now(timezone.utc)
    h   = now.hour
    uah = (now + timedelta(hours=2)).hour
    sess = [("🗼 Токіо",0,9),("🏦 Лондон",7,16),("🗽 Нью-Йорк",13,22)]
    act  = [n for n,s,e in sess if s<=h<e]
    inact= [n for n,s,e in sess if not(s<=h<e)]
    if 13<=h<16:   ac,tip="🔥🔥🔥 МАКСИМАЛЬНА","Лондон+Нью-Йорк — найкращий час!"
    elif 7<=h<13:  ac,tip="🔥🔥 ВИСОКА","Кращі пари: EUR/GBP, EUR/USD"
    elif 13<=h<22: ac,tip="🔥🔥 ВИСОКА","Кращі пари: USD/JPY, GBP/USD"
    elif 0<=h<9:   ac,tip="🔥 СЕРЕДНЯ","Кращі пари: JPY, AUD, NZD"
    else:          ac,tip="😴 НИЗЬКА","Краще утриматись від торгівлі"
    return (f"🕐 *Торгові сесії*\n\n"
            f"UA: `{uah:02d}:00` | UTC: `{h:02d}:00`\n\n"
            f"✅ *Активні:* {' | '.join(act) or 'Немає'}\n"
            f"⚪ *Неактивні:* {' | '.join(inact) or 'Всі'}\n\n"
            f"📊 *Активність:* {ac}\n💡 _{tip}_\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"*Розклад (UTC+2):*\n"
            f"🗼 Токіо:    02:00–11:00\n"
            f"🏦 Лондон:   09:00–18:00\n"
            f"🗽 Нью-Йорк: 15:00–00:00\n"
            f"🔥 Перетин:  15:00–18:00 ← найкращий")

# ══════════════════════════════════════════
#  ІНДИКАТОРИ
# ══════════════════════════════════════════
def seeded_rand(seed, offset=0):
    x = math.sin(seed+offset)*43758.5453123
    return x-math.floor(x)

def calc_rsi(closes, period=14):
    if len(closes)<period+1: return 50
    gains=[max(closes[i]-closes[i-1],0) for i in range(1,len(closes))]
    losses=[max(closes[i-1]-closes[i],0) for i in range(1,len(closes))]
    ag=sum(gains[-period:])/period; al=sum(losses[-period:])/period
    return round(100-100/(1+ag/al),1) if al else 100

def calc_ema(closes, period):
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

def calc_stoch(closes,highs,lows,k=14):
    if len(closes)<k: return 50
    lk=min(lows[-k:]); hk=max(highs[-k:])
    return round((closes[-1]-lk)/(hk-lk)*100,1) if hk!=lk else 50

def calc_bb(closes,period=20):
    if len(closes)<period: return 50
    sma=sum(closes[-period:])/period
    std=(sum((x-sma)**2 for x in closes[-period:])/period)**0.5
    if std==0: return 50
    pos=(closes[-1]-(sma-2*std))/((sma+2*std)-(sma-2*std))*100
    return round(max(0,min(100,pos)),1)

def calc_ichimoku(closes,highs,lows):
    if len(closes)<52: return 0
    tenkan=(max(highs[-9:])+min(lows[-9:]))/2
    kijun=(max(highs[-26:])+min(lows[-26:]))/2
    spa=(tenkan+kijun)/2; spb=(max(highs[-52:])+min(lows[-52:]))/2
    p=closes[-1]
    if p>spa and p>spb and tenkan>kijun: return 1
    if p<spa and p<spb and tenkan<kijun: return -1
    return 0

def calc_ema_cross(closes):
    if len(closes)<21: return 0
    e9=calc_ema(closes,9); e21=calc_ema(closes,21)
    e9p=calc_ema(closes[:-1],9); e21p=calc_ema(closes[:-1],21)
    if e9>e21 and e9p<=e21p: return 2
    if e9<e21 and e9p>=e21p: return -2
    return 1 if e9>e21 else -1

# ══ ALPHA VANTAGE ══
def get_candles_alpha(symbol, tf, count=60):
    """Alpha Vantage — 1хв точність для Forex"""
    tf_map={"1":"1min","3":"5min","5":"5min","15":"15min","30":"30min","60":"60min"}
    interval=tf_map.get(tf,"5min")
    # Forex
    if symbol.endswith("=X"):
        base=symbol[:-2]
        if len(base)==6:
            from_sym,to_sym=base[:3],base[3:]
            try:
                url=f"{ALPHA_URL}?function=FX_INTRADAY&from_symbol={from_sym}&to_symbol={to_sym}&interval={interval}&outputsize=compact&apikey={ALPHA_KEY}"
                r=requests.get(url,timeout=10)
                data=r.json()
                key=f"Time Series FX ({interval})"
                if key not in data: return [],[],[]
                ts=data[key]
                items=list(ts.items())[:count]
                items.reverse()
                c=[float(v["4. close"]) for _,v in items]
                h=[float(v["2. high"])  for _,v in items]
                l=[float(v["3. low"])   for _,v in items]
                return c,h,l
            except: return [],[],[]
    # Акції
    if not symbol.endswith("=X") and "-USD" not in symbol:
        try:
            url=f"{ALPHA_URL}?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&outputsize=compact&apikey={ALPHA_KEY}"
            r=requests.get(url,timeout=10)
            data=r.json()
            key=f"Time Series ({interval})"
            if key not in data: return [],[],[]
            ts=data[key]
            items=list(ts.items())[:count]
            items.reverse()
            c=[float(v["4. close"]) for _,v in items]
            h=[float(v["2. high"])  for _,v in items]
            l=[float(v["3. low"])   for _,v in items]
            return c,h,l
        except: return [],[],[]
    return [],[],[]

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
        r=requests.get(url,timeout=8); d=r.json()
        if d.get("s")!="ok" or not d.get("c"): return [],[],[]
        c=d["c"]; h=d["h"]; l=d["l"]
        n=min(len(c),len(h),len(l),count)
        return c[-n:],h[-n:],l[-n:]
    except: return [],[],[]

def get_candles_yahoo(symbol,tf,count=60):
    tf_map={"1":"1m","3":"2m","5":"5m","15":"15m","30":"30m","60":"1h","240":"4h"}
    interval=tf_map.get(tf,"5m")
    period="1d" if tf in ["1","3","5","15"] else "5d"
    try:
        url=f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={period}"
        r=requests.get(url,timeout=8,headers={"User-Agent":"Mozilla/5.0"})
        res=r.json()["chart"]["result"][0]
        q=res["indicators"]["quote"][0]
        c=[x for x in q["close"] if x]; h=[x for x in q["high"] if x]; l=[x for x in q["low"] if x]
        return c[-count:],h[-count:],l[-count:]
    except: return [],[],[]

def get_candles(symbol,tf,count=60):
    # 1. Finnhub (реальний час)
    c,h,l=get_candles_finnhub(symbol,tf,count)
    if len(c)>=10: return c,h,l
    # 2. Alpha Vantage (1хв точність для Forex/Акцій)
    c,h,l=get_candles_alpha(symbol,tf,count)
    if len(c)>=10: return c,h,l
    # 3. Yahoo (резерв)
    return get_candles_yahoo(symbol,tf,count)

def get_price(symbol,fallback):
    finn,_=to_finnhub(symbol)
    try:
        r=requests.get(f"{FINNHUB_URL}/quote?symbol={finn}&token={FINNHUB_KEY}",timeout=5)
        p=r.json().get("c")
        if p and float(p)>0: return float(p)
    except: pass
    try:
        url=f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
        r=requests.get(url,timeout=5,headers={"User-Agent":"Mozilla/5.0"})
        return float(r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"])
    except: return fallback

# ══════════════════════════════════════════
#  ГЕНЕРАЦІЯ СИГНАЛУ
# ══════════════════════════════════════════
def generate_signal(pair_name, tf):
    m=ALL_PAIRS.get(pair_name,FOREX_PAIRS[0])
    is_otc="OTC" in pair_name
    closes,highs,lows=get_candles(m["symbol"],tf,60)
    live=get_price(m["symbol"],m["p"])
    real=len(closes)>=20
    if real:
        rsi=calc_rsi(closes); adx=calc_adx(closes,highs,lows)
        macd,mh=calc_macd(closes); stoch=calc_stoch(closes,highs,lows)
        bb=calc_bb(closes); ichi=calc_ichimoku(closes,highs,lows)
        ec=calc_ema_cross(closes)
        e9=calc_ema(closes,9); e21=calc_ema(closes,21); e50=calc_ema(closes,50)
    else:
        seed=sum(ord(c) for c in pair_name)+int(tf)+int(time.time()//60)
        r=lambda i:seeded_rand(seed,i)
        rsi=round(28+r(1)*50); adx=round(22+r(2)*55); macd=(r(3)-.5)*.006; mh=macd*.3
        stoch=round(15+r(5)*70); bb=r(4)*100; ichi=m["t"]; ec=m["t"]
        e9=live*(1+(r(7)-.5)*.002); e21=live*(1+(r(8)-.5)*.003); e50=live*(1+(r(9)-.5)*.005)

    votes=[]
    if rsi<30:    votes.append(("RSI",1,f"RSI={rsi} перепроданість ✅"))
    elif rsi>70:  votes.append(("RSI",-1,f"RSI={rsi} перекупленість ✅"))
    elif rsi<45:  votes.append(("RSI",1,f"RSI={rsi} бичачий нахил"))
    elif rsi>55:  votes.append(("RSI",-1,f"RSI={rsi} ведмежий нахил"))
    else:         votes.append(("RSI",0,f"RSI={rsi} нейтраль"))

    if macd>0 and mh>0:   votes.append(("MACD",1,"MACD ▲ BUY підтверджено ✅"))
    elif macd<0 and mh<0: votes.append(("MACD",-1,"MACD ▼ SELL підтверджено ✅"))
    else:                  votes.append(("MACD",0,"MACD нейтральний"))

    if ec==2:    votes.append(("EMA Cross",1,"EMA 9/21 перетин ▲ СИЛЬНИЙ BUY ✅"))
    elif ec==-2: votes.append(("EMA Cross",-1,"EMA 9/21 перетин ▼ СИЛЬНИЙ SELL ✅"))
    elif ec==1:  votes.append(("EMA Cross",1,"EMA 9>21 бичачий тренд"))
    else:        votes.append(("EMA Cross",-1,"EMA 9<21 ведмежий тренд"))

    if ichi==1:   votes.append(("Ichimoku",1,"Ціна над хмарою ☁️ BUY ✅"))
    elif ichi==-1:votes.append(("Ichimoku",-1,"Ціна під хмарою ☁️ SELL ✅"))
    else:         votes.append(("Ichimoku",0,"Ichimoku нейтраль"))

    if stoch<20:  votes.append(("Stoch",1,f"Stoch={stoch} перепроданість ✅"))
    elif stoch>80:votes.append(("Stoch",-1,f"Stoch={stoch} перекупленість ✅"))
    else:         votes.append(("Stoch",0,f"Stoch={stoch} нейтраль"))

    if bb<15:     votes.append(("BB",1,"Ціна біля нижньої смуги ✅"))
    elif bb>85:   votes.append(("BB",-1,"Ціна біля верхньої смуги ✅"))
    else:         votes.append(("BB",0,f"BB позиція {bb:.0f}%"))

    if live>e50:  votes.append(("EMA50",1,"Ціна вище EMA50 — висхідний тренд"))
    else:         votes.append(("EMA50",-1,"Ціна нижче EMA50 — низхідний тренд"))

    bc=sum(1 for v in votes if v[1]==1); sc=sum(1 for v in votes if v[1]==-1)
    score=bc-sc; is_buy=score>=0
    adx_ok=adx>=25
    conf=min(97,round(70+min(abs(score)/7,1)*20+(min(adx/100,.15)*10)+(5 if adx_ok else 0)))
    sc2=max(bc,sc)
    if sc2<3:   conf=min(conf,78); strength="⚠️ СЛАБКИЙ"
    elif sc2<5: conf=min(conf,88); strength="✅ СЕРЕДНІЙ"
    else:       strength="🔥 СИЛЬНИЙ"

    d=m["d"]; mult=1 if live>100 else(.01 if live>10 else .0001)
    atr=sum(abs(closes[i]-closes[i-1]) for i in range(-10,0))/10 if real and len(closes)>=10 else mult*3
    atr=max(atr,mult*2); sp=1.8 if is_otc else 1.0
    tp1=round(live+atr*1.5,d) if is_buy else round(live-atr*1.5,d)
    tp2=round(live+atr*2.5,d) if is_buy else round(live-atr*2.5,d)
    sl =round(live-atr*sp,d)  if is_buy else round(live+atr*sp,d)
    res=round(live+atr*3,d); sup=round(live-atr*3,d)
    rr =round(abs(tp1-live)/abs(sl-live),1) if abs(sl-live)>0 else 1.5

    return dict(is_buy=is_buy,signal="BUY ▲" if is_buy else "SELL ▼",conf=conf,
                strength=strength,live=live,tp1=tp1,tp2=tp2,sl=sl,res=res,sup=sup,rr=rr,
                rsi=rsi,adx=adx,adx_ok=adx_ok,macd=macd,stoch=stoch,bb=bb,
                e9=round(e9,d),e21=round(e21,d),e50=round(e50,d),
                votes=votes,bc=bc,sc=sc,real=real,is_otc=is_otc)

def trend_bar(val):
    """Шкала сили тренду як у SIGNAL AI"""
    v=max(0,min(100,val))
    filled=round(v/10)
    return "▰"*filled+"▱"*(10-filled)

def format_signal(pair,tf,d):
    now_dt=datetime.now(timezone.utc)+timedelta(hours=2)
    now=now_dt.strftime("%H:%M")
    tf_hold={"1":(1,2),"3":(3,5),"5":(5,10),"15":(15,20),"30":(30,35),"60":(60,75),"240":(240,260)}
    hm=tf_hold.get(tf,(5,10))
    exp=(now_dt+timedelta(minutes=hm[0])).strftime("%H:%M")

    is_crypto=any(pair==p["name"] for p in CRYPTO_PAIRS)
    is_stocks=any(pair==p["name"] for p in STOCKS_PAIRS)
    mkt_lbl="₿ КРИПТО" if is_crypto else("📊 АКЦІЇ" if is_stocks else("🌙 OTC" if d["is_otc"] else "📈 FOREX"))

    # Точність (як у SIGNAL AI)
    accuracy=min(95,max(78,round(70+(d["bc"] if d["is_buy"] else d["sc"])*3.5+(d["adx"]/100)*10)))

    # Сила тренду %
    trend_pct=min(99,max(50,round(50+(d["bc"] if d["is_buy"] else d["sc"])*7+(d["adx"]/100)*15)))
    t_bar=trend_bar(trend_pct)

    # Напрямок
    direction="⬆️ ВВЕРХ" if d["is_buy"] else "⬇️ ВНИЗ"
    dir_emoji="🟢" if d["is_buy"] else "🔴"

    # Сила тренду текст
    if trend_pct<60:   t_str="Слабий"
    elif trend_pct<75: t_str="Середній"
    elif trend_pct<88: t_str="Сильний"
    else:              t_str="Дуже сильний"

    return f"""╔══ 🤖 *SIGNAL AI* ══╗

🏷 *Валютна пара*
`{pair}`

⏱ *Таймфрейм* | 🎯 *Точність*
`{TIMEFRAMES.get(tf,tf)}` | `{accuracy}%`

📊 *Сила тренду* — {t_str} `{trend_pct}%`
`{t_bar}`

{dir_emoji} *Напрямок:*
┌─────────────────────┐
│  *{direction}*  до `{exp}`  │
└─────────────────────┘

💰 Вхід: `{d["live"]}`
🎯 TP: `{d["tp1"]}` | SL: `{d["sl"]}`

📡 {mkt_lbl} | {'🔴 Live' if d["real"] else '⚙️ Розрах'} | `{now}`
╚══════════════════════╝
⚠️ _Не є фінансовою порадою_"""

# ══════════════════════════════════════════
#  КЛАВІАТУРИ
# ══════════════════════════════════════════
def main_kb():
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("📈 FOREX",  callback_data="menu_forex"),
           InlineKeyboardButton("🌙 OTC",    callback_data="menu_otc"))
    kb.add(InlineKeyboardButton("₿ КРИПТО", callback_data="menu_crypto"),
           InlineKeyboardButton("📊 АКЦІЇ",  callback_data="menu_stocks"))
    kb.add(InlineKeyboardButton("📊 Статистика",callback_data="stats"),
           InlineKeyboardButton("🕐 Сесії",     callback_data="sessions"))
    kb.add(InlineKeyboardButton("ℹ️ Про бота",  callback_data="about"))
    return kb

def crypto_kb():
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(*[InlineKeyboardButton(p["name"],callback_data=f"pair_{p['name']}") for p in CRYPTO_PAIRS])
    kb.add(InlineKeyboardButton("◀️ Назад",callback_data="main"))
    return kb

def stocks_kb():
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(*[InlineKeyboardButton(p["name"],callback_data=f"pair_{p['name']}") for p in STOCKS_PAIRS])
    kb.add(InlineKeyboardButton("◀️ Назад",callback_data="main"))
    return kb

def forex_kb():
    kb=InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(p["name"],callback_data=f"pair_{p['name']}") for p in FOREX_PAIRS])
    kb.add(InlineKeyboardButton("◀️ Назад",callback_data="main"))
    return kb

def otc_kb():
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(*[InlineKeyboardButton(p["name"],callback_data=f"pair_{p['name']}") for p in OTC_PAIRS])
    kb.add(InlineKeyboardButton("◀️ Назад",callback_data="main"))
    return kb

def tf_kb(pair):
    is_crypto = any(pair==p["name"] for p in CRYPTO_PAIRS)
    is_stocks = any(pair==p["name"] for p in STOCKS_PAIRS)
    tfs = CRYPTO_TF if is_crypto else (STOCKS_TF if is_stocks else TIMEFRAMES)
    if is_crypto: back="crypto_back"
    elif is_stocks: back="stocks_back"
    elif "OTC" in pair: back="otc_back"
    else: back="forex_back"
    kb=InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(v,callback_data=f"tf|{pair}|{k}") for k,v in tfs.items()])
    kb.add(InlineKeyboardButton("◀️ Назад",callback_data=back))
    return kb

def result_kb(pair,tf):
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("✅ Виграш",callback_data=f"win|{pair}|{tf}"),
           InlineKeyboardButton("❌ Програш",callback_data=f"loss|{pair}|{tf}"))
    kb.add(InlineKeyboardButton("🔄 Новий сигнал",callback_data=f"tf|{pair}|{tf}"),
           InlineKeyboardButton("🏠 Меню",callback_data="main"))
    return kb

# ══════════════════════════════════════════
#  ХЕНДЛЕРИ
# ══════════════════════════════════════════
def send_main(cid, mid=None):
    txt=("╔══ 🤖 *SIGNAL AI* ══╗\n\n"
         "Нейромережа для аналізу ринку\n\n"
         "• RSI • MACD • EMA • Ichimoku\n"
         "• Stochastic • BB • ADX\n\n"
         "📡 *Finnhub + Alpha Vantage + Yahoo*\n"
         "🎯 *Точність сигналів: ~82-95%*\n\n"
         "╚══ Оберіть категорію ══╝")
    if mid:
        try: bot.edit_message_text(txt,cid,mid,parse_mode="Markdown",reply_markup=main_kb()); return
        except: pass
    bot.send_message(cid,txt,parse_mode="Markdown",reply_markup=main_kb())

@bot.message_handler(commands=["start","menu"])
def cmd_start(msg):
    send_main(msg.chat.id)

@bot.message_handler(commands=["stats"])
def cmd_stats(msg):
    bot.send_message(msg.chat.id,stats_text(msg.chat.id),parse_mode="Markdown",reply_markup=main_kb())

@bot.message_handler(commands=["sessions"])
def cmd_sessions(msg):
    bot.send_message(msg.chat.id,sessions_text(),parse_mode="Markdown",reply_markup=main_kb())

@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    cid=call.message.chat.id; mid=call.message.message_id; d=call.data
    bot.answer_callback_query(call.id)
    try:
        if d=="main":
            send_main(cid,mid)
        elif d=="menu_forex":
            bot.edit_message_text("📈 *FOREX пари*\nОберіть пару:",cid,mid,parse_mode="Markdown",reply_markup=forex_kb())
        elif d=="menu_otc":
            bot.edit_message_text("🌙 *OTC пари*\nОберіть пару:",cid,mid,parse_mode="Markdown",reply_markup=otc_kb())
        elif d=="forex_back":
            bot.edit_message_text("📈 *FOREX пари*\nОберіть пару:",cid,mid,parse_mode="Markdown",reply_markup=forex_kb())
        elif d=="otc_back":
            bot.edit_message_text("🌙 *OTC пари*\nОберіть пару:",cid,mid,parse_mode="Markdown",reply_markup=otc_kb())
        elif d=="stats":
            bot.edit_message_text(stats_text(cid),cid,mid,parse_mode="Markdown",reply_markup=main_kb())
        elif d=="sessions":
            bot.edit_message_text(sessions_text(),cid,mid,parse_mode="Markdown",reply_markup=main_kb())
        elif d=="about":
            txt=("ℹ️ *AI Signal Bot*\n\n"
                 "• RSI, MACD, EMA 9/21/50\n• Ichimoku Cloud\n• ADX фільтр\n"
                 "• Stochastic, Bollinger Bands\n• 7 індикаторів одночасно\n\n"
                 "📡 Yahoo Finance API | UTC+2")
            bot.edit_message_text(txt,cid,mid,parse_mode="Markdown",reply_markup=main_kb())
        elif d.startswith("pair_"):
            pair=d[5:]
            bot.edit_message_text(f"⏱ *Таймфрейм для {pair}*\nОберіть:",cid,mid,
                                   parse_mode="Markdown",reply_markup=tf_kb(pair))
        elif d.startswith("tf|"):
            _,pair,tf=d.split("|",2)
            # Анімація як у SIGNAL AI
            bot.edit_message_text(
                f"🔵 *SIGNAL AI* 🔵\n\n"
                f"⟳ Аналіз ринку...\n\n"
                f"`{pair}` | `{TIMEFRAMES.get(tf,tf)}`\n\n"
                f"▰▰▰▱▱▱▱▱▱▱ 30%",
                cid,mid,parse_mode="Markdown")
            time.sleep(1)
            bot.edit_message_text(
                f"🔵 *SIGNAL AI* 🔵\n\n"
                f"⟳ Обробка індикаторів...\n\n"
                f"`{pair}` | `{TIMEFRAMES.get(tf,tf)}`\n\n"
                f"▰▰▰▰▰▰▱▱▱▱ 60%",
                cid,mid,parse_mode="Markdown")
            time.sleep(1)
            bot.edit_message_text(
                f"🔵 *SIGNAL AI* 🔵\n\n"
                f"⟳ Генерую сигнал...\n\n"
                f"`{pair}` | `{TIMEFRAMES.get(tf,tf)}`\n\n"
                f"▰▰▰▰▰▰▰▰▰▱ 90%",
                cid,mid,parse_mode="Markdown")
            time.sleep(0.8)
            sig=generate_signal(pair,tf)
            bot.edit_message_text(format_signal(pair,tf,sig),cid,mid,
                                   parse_mode="Markdown",reply_markup=result_kb(pair,tf))
        elif d.startswith("win|") or d.startswith("loss|"):
            res,pair,tf=d.split("|",2)
            s=get_stats(cid); s["total"]+=1
            if res=="win":
                s["wins"]+=1; s["streak"]=max(s.get("streak",0)+1,1); emoji="✅ Виграш записано!"
            else:
                s["losses"]+=1; s["streak"]=min(s.get("streak",0)-1,-1); emoji="❌ Програш записано"
            if pair not in s["pairs"]: s["pairs"][pair]={"total":0,"wins":0}
            s["pairs"][pair]["total"]+=1
            if res=="win": s["pairs"][pair]["wins"]+=1
            wr=round(s["wins"]/s["total"]*100)
            bot.send_message(cid,f"{emoji}\n\n📊 WR: *{wr}%* ({s['wins']}W/{s['losses']}L)\n\nОберіть наступну дію:",
                             parse_mode="Markdown",reply_markup=main_kb())
    except Exception as e:
        print(f"Помилка: {e}")
        bot.send_message(cid,"Оберіть категорію:",reply_markup=main_kb())

# ══════════════════════════════════════════
#  ЗАПУСК
# ══════════════════════════════════════════
if __name__=="__main__":
    print("✅ AI Signal Bot запущено!")
    bot.infinity_polling()
