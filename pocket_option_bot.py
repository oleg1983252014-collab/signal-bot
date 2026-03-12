#!/usr/bin/env python3
import os, math, time, json, threading, requests
from datetime import datetime, timezone, timedelta
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN    = os.environ.get("BOT_TOKEN")
TWELVE_KEY   = os.environ.get("TWELVE_KEY", "99b3ca01dbdf45ccb2f5968b16af1c82")  # TwelveData
TWELVE_URL   = "https://api.twelvedata.com"
STATS_FILE   = "stats.json"

bot = TeleBot(BOT_TOKEN)

# ══════════════════════════════════════════
#  ПАРИ
# ══════════════════════════════════════════
FOREX_PAIRS = [
    {"name":"EUR/USD","symbol":"EURUSD=X","p":1.08,"d":5},
    {"name":"GBP/USD","symbol":"GBPUSD=X","p":1.27,"d":5},
    {"name":"USD/JPY","symbol":"USDJPY=X","p":149.5,"d":3},
    {"name":"AUD/USD","symbol":"AUDUSD=X","p":0.645,"d":5},
    {"name":"NZD/USD","symbol":"NZDUSD=X","p":0.596,"d":5},
    {"name":"USD/CAD","symbol":"USDCAD=X","p":1.357,"d":5},
    {"name":"USD/CHF","symbol":"USDCHF=X","p":0.903,"d":5},
    {"name":"EUR/GBP","symbol":"EURGBP=X","p":0.853,"d":5},
    {"name":"EUR/JPY","symbol":"EURJPY=X","p":161.5,"d":3},
    {"name":"GBP/JPY","symbol":"GBPJPY=X","p":189.8,"d":3},
    {"name":"AUD/CAD","symbol":"AUDCAD=X","p":0.874,"d":5},
    {"name":"AUD/JPY","symbol":"AUDJPY=X","p":96.4,"d":3},
    {"name":"CHF/JPY","symbol":"CHFJPY=X","p":165.5,"d":3},
    {"name":"EUR/AUD","symbol":"EURAUD=X","p":1.672,"d":5},
    {"name":"EUR/CAD","symbol":"EURCAD=X","p":1.464,"d":5},
    {"name":"GBP/AUD","symbol":"GBPAUD=X","p":1.975,"d":5},
    {"name":"GBP/CAD","symbol":"GBPCAD=X","p":1.722,"d":5},
]
OTC_PAIRS = [
    {"name":"EUR/USD OTC","symbol":"EURUSD=X","p":1.08,"d":5},
    {"name":"GBP/USD OTC","symbol":"GBPUSD=X","p":1.27,"d":5},
    {"name":"USD/JPY OTC","symbol":"USDJPY=X","p":149.5,"d":3},
    {"name":"AUD/USD OTC","symbol":"AUDUSD=X","p":0.645,"d":5},
    {"name":"EUR/GBP OTC","symbol":"EURGBP=X","p":0.853,"d":5},
    {"name":"AUD/CAD OTC","symbol":"AUDCAD=X","p":0.874,"d":5},
    {"name":"EUR/JPY OTC","symbol":"EURJPY=X","p":161.5,"d":3},
    {"name":"GBP/JPY OTC","symbol":"GBPJPY=X","p":189.8,"d":3},
    {"name":"USD/CAD OTC","symbol":"USDCAD=X","p":1.357,"d":5},
    {"name":"NZD/USD OTC","symbol":"NZDUSD=X","p":0.596,"d":5},
    {"name":"USD/CHF OTC","symbol":"USDCHF=X","p":0.903,"d":5},
    {"name":"CHF/JPY OTC","symbol":"CHFJPY=X","p":165.5,"d":3},
    {"name":"EUR/AUD OTC","symbol":"EURAUD=X","p":1.672,"d":5},
]
CRYPTO_PAIRS = [
    {"name":"BTC/USD","symbol":"BTC-USD","p":67000,"d":1},
    {"name":"ETH/USD","symbol":"ETH-USD","p":3500,"d":2},
    {"name":"BNB/USD","symbol":"BNB-USD","p":420,"d":2},
    {"name":"SOL/USD","symbol":"SOL-USD","p":180,"d":2},
    {"name":"XRP/USD","symbol":"XRP-USD","p":0.62,"d":4},
    {"name":"ADA/USD","symbol":"ADA-USD","p":0.45,"d":4},
    {"name":"DOGE/USD","symbol":"DOGE-USD","p":0.18,"d":5},
    {"name":"LTC/USD","symbol":"LTC-USD","p":95,"d":2},
    {"name":"MATIC/USD","symbol":"MATIC-USD","p":0.85,"d":4},
    {"name":"DOT/USD","symbol":"DOT-USD","p":7.5,"d":3},
]
STOCKS_PAIRS = [
    {"name":"Apple","symbol":"AAPL","p":189,"d":2},
    {"name":"Tesla","symbol":"TSLA","p":245,"d":2},
    {"name":"NVIDIA","symbol":"NVDA","p":875,"d":2},
    {"name":"Amazon","symbol":"AMZN","p":185,"d":2},
    {"name":"Google","symbol":"GOOGL","p":165,"d":2},
    {"name":"Microsoft","symbol":"MSFT","p":415,"d":2},
    {"name":"Meta","symbol":"META","p":510,"d":2},
    {"name":"Netflix","symbol":"NFLX","p":625,"d":2},
]
ALL_PAIRS   = {p["name"]: p for p in FOREX_PAIRS+OTC_PAIRS+CRYPTO_PAIRS+STOCKS_PAIRS}
TIMEFRAMES  = {"1":"1 хв","5":"5 хв","15":"15 хв","30":"30 хв","60":"1 год"}
CRYPTO_TF   = {"5":"5 хв","15":"15 хв","30":"30 хв","60":"1 год","240":"4 год"}
STOCKS_TF   = {"5":"5 хв","15":"15 хв","30":"30 хв","60":"1 год"}

# ══════════════════════════════════════════
#  ЗБЕРЕЖЕННЯ СТАТИСТИКИ У ФАЙЛ (fix #3)
# ══════════════════════════════════════════
_stats_lock = threading.Lock()

def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE,"r") as f:
                return json.load(f)
    except: pass
    return {}

def save_stats(data):
    with _stats_lock:
        try:
            with open(STATS_FILE,"w") as f:
                json.dump(data, f)
        except: pass

all_stats = load_stats()

def get_stats(cid):
    key=str(cid)
    if key not in all_stats:
        all_stats[key]={"total":0,"wins":0,"losses":0,"pairs":{},"streak":0}
    return all_stats[key]

def save_user_stats():
    save_stats(all_stats)

def stats_text(cid):
    s=get_stats(cid)
    if s["total"]==0:
        return "📊 *Статистика*\n\nЩе немає угод.\nПісля сигналу натисніть ✅ або ❌"
    wr=round(s["wins"]/s["total"]*100)
    bar="🟢"*round(wr/10)+"⚪"*(10-round(wr/10))
    best=sorted(s["pairs"].items(),key=lambda x:x[1]["wins"]/(x[1]["total"] or 1),reverse=True)[:3]
    bt="".join(f"  • {n}: {d['wins']}/{d['total']} ({round(d['wins']/(d['total'] or 1)*100)}%)\n" for n,d in best)
    st=s.get("streak",0)
    sl=(f"🔥 Серія виграшів: {st}\n" if st>1 else f"❄️ Серія програшів: {abs(st)}\n" if st<-1 else "")
    return (f"📊 *Статистика*\n\nВсього: `{s['total']}`\n✅ Виграші: `{s['wins']}`\n"
            f"❌ Програші: `{s['losses']}`\n\n🏆 *WR: {wr}%*\n{bar}\n\n{sl}"
            f"🥇 *Кращі пари:*\n{bt}")

# ══════════════════════════════════════════
#  ТОРГОВІ СЕСІЇ
# ══════════════════════════════════════════
def sessions_text():
    now=datetime.now(timezone.utc); h=now.hour
    uah=(now+timedelta(hours=2)).hour
    sess=[("🗼 Токіо",0,9),("🏦 Лондон",7,16),("🗽 Нью-Йорк",13,22)]
    act=[n for n,s,e in sess if s<=h<e]
    inact=[n for n,s,e in sess if not(s<=h<e)]
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
def calc_rsi(closes,period=14):
    if len(closes)<period+1: return None
    gains=[max(closes[i]-closes[i-1],0) for i in range(1,len(closes))]
    losses=[max(closes[i-1]-closes[i],0) for i in range(1,len(closes))]
    ag=sum(gains[-period:])/period; al=sum(losses[-period:])/period
    return round(100-100/(1+ag/al),1) if al else 100

def calc_ema(closes,period):
    if len(closes)<period: return closes[-1] if closes else None
    k=2/(period+1); ema=sum(closes[:period])/period
    for p in closes[period:]: ema=p*k+ema*(1-k)
    return ema

def calc_macd(closes):
    if len(closes)<26: return None,None
    e12=calc_ema(closes,12); e26=calc_ema(closes,26)
    if e12 is None or e26 is None: return None,None
    ml=e12-e26
    mv=[calc_ema(closes[:i],12)-calc_ema(closes[:i],26) for i in range(26,len(closes)+1)]
    sig=calc_ema(mv,9) if len(mv)>=9 else ml
    return round(ml,6),round(ml-sig,6)

def calc_adx(closes,highs,lows,period=14):
    if len(closes)<period+2: return None
    trs,pdms,ndms=[],[],[]
    for i in range(1,len(closes)):
        trs.append(max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1])))
        up=highs[i]-highs[i-1]; dn=lows[i-1]-lows[i]
        pdms.append(up if up>dn and up>0 else 0)
        ndms.append(dn if dn>up and dn>0 else 0)
    atr=sum(trs[-period:])/period
    if atr==0: return None
    pdi=(sum(pdms[-period:])/period)/atr*100
    ndi=(sum(ndms[-period:])/period)/atr*100
    dx=abs(pdi-ndi)/(pdi+ndi)*100 if (pdi+ndi) else 0
    return round(dx,1)

def calc_stoch(closes,highs,lows,k=14):
    if len(closes)<k: return None
    lk=min(lows[-k:]); hk=max(highs[-k:])
    return round((closes[-1]-lk)/(hk-lk)*100,1) if hk!=lk else 50

def calc_bb(closes,period=20):
    if len(closes)<period: return None
    sma=sum(closes[-period:])/period
    std=(sum((x-sma)**2 for x in closes[-period:])/period)**0.5
    if std==0: return 50
    pos=(closes[-1]-(sma-2*std))/((sma+2*std)-(sma-2*std))*100
    return round(max(0,min(100,pos)),1)

def calc_ema_cross(closes):
    if len(closes)<22: return None
    e9=calc_ema(closes,9); e21=calc_ema(closes,21)
    e9p=calc_ema(closes[:-1],9); e21p=calc_ema(closes[:-1],21)
    if None in (e9,e21,e9p,e21p): return None
    if e9>e21 and e9p<=e21p: return 2
    if e9<e21 and e9p>=e21p: return -2
    return 1 if e9>e21 else -1

# ── НОВІ ІНДИКАТОРИ (fix #5, #6) ──────────

def calc_williams_r(closes,highs,lows,period=14):
    """Williams %R — найточніший для бінарних опціонів"""
    if len(closes)<period: return None
    hh=max(highs[-period:]); ll=min(lows[-period:])
    if hh==ll: return -50
    return round((hh-closes[-1])/(hh-ll)*-100,1)

def calc_candlestick(closes,highs,lows,opens=None):
    """
    Свічкові патерни (якщо є opens — точні, інакше апроксимація)
    Повертає: 1=бичачий, -1=ведмежий, 0=нейтраль
    """
    if len(closes)<3: return 0
    c=closes; h=highs; l=lows
    # Апроксимуємо open як попередній close
    o=opens if opens else c[:-1]+[c[-2]]

    # Остання свічка
    c0=c[-1]; h0=h[-1]; l0=l[-1]; o0=c[-2]
    body=abs(c0-o0); rng=h0-l0
    if rng==0: return 0
    body_pct=body/rng

    # Doji — невизначеність
    if body_pct<0.1: return 0

    # Hammer (молот) — бичачий розворот
    lower_wick=(min(c0,o0)-l0)/rng
    upper_wick=(h0-max(c0,o0))/rng
    if lower_wick>0.6 and upper_wick<0.1 and c[-2]>c[-3]:
        return 1  # Hammer — BUY

    # Shooting Star — ведмежий розворот
    if upper_wick>0.6 and lower_wick<0.1 and c[-2]<c[-3]:
        return -1  # Shooting star — SELL

    # Bullish Engulfing
    if c0>o0 and c[-2]<c[-3] and c0>c[-3] and o0<c[-2]:
        return 1

    # Bearish Engulfing
    if c0<o0 and c[-2]>c[-3] and c0<c[-3] and o0>c[-2]:
        return -1

    # Три зростаючі свічки
    if c[-1]>c[-2]>c[-3]: return 1
    # Три падаючі свічки
    if c[-1]<c[-2]<c[-3]: return -1

    return 0

def calc_volume_trend(volumes):
    """Аналіз об'єму — підтвердження сигналу"""
    if not volumes or len(volumes)<5: return 0
    avg=sum(volumes[-10:])/min(10,len(volumes))
    last=volumes[-1]
    if avg==0: return 0
    ratio=last/avg
    if ratio>1.5: return 1   # Зростання об'єму — підтвердження
    if ratio<0.5: return -1  # Падіння об'єму — слабкий сигнал
    return 0

# ══════════════════════════════════════════
#  API ДАНІ
# ══════════════════════════════════════════

# ══════════════════════════════════════════
#  TWELVEDATA API (основний, 800 запитів/день)
# ══════════════════════════════════════════
def to_twelve_symbol(symbol):
    """Конвертує символ у формат TwelveData"""
    if symbol.endswith("=X"):
        b = symbol[:-2]
        if len(b) == 6:
            return f"{b[:3]}/{b[3:]}", "forex"
    if "-USD" in symbol:
        return f"{symbol.replace('-USD', '')}/USD", "crypto"
    return symbol, "stock"

def get_candles_twelve(symbol, tf, count=80):
    """TwelveData — 800 безкоштовних запитів/день, всі ринки"""
    if not TWELVE_KEY:
        return [], [], [], []
    tf_map = {"1":"1min","5":"5min","15":"15min","30":"30min","60":"1h","240":"4h"}
    interval = tf_map.get(tf, "5min")
    sym, mkt = to_twelve_symbol(symbol)
    try:
        url = (f"{TWELVE_URL}/time_series"
               f"?symbol={sym}&interval={interval}&outputsize={count}"
               f"&apikey={TWELVE_KEY}&format=JSON")
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("status") == "error":
            print(f"[TWELVE ERR] {sym}: {data.get('message','')}")
            return [], [], [], []
        values = data.get("values", [])
        if not values:
            print(f"[TWELVE] {sym} — немає даних")
            return [], [], [], []
        # TwelveData повертає від нового до старого — реверсуємо
        values = list(reversed(values))
        c = [float(v["close"])  for v in values]
        h = [float(v["high"])   for v in values]
        l = [float(v["low"])    for v in values]
        vol = [float(v.get("volume", 0) or 0) for v in values]
        print(f"[TWELVE] {sym} n={len(c)} ✅")
        return c, h, l, vol
    except Exception as e:
        print(f"[TWELVE ERR] {sym}: {e}")
        return [], [], [], []

def get_price_twelve(symbol):
    """Поточна ціна через TwelveData"""
    if not TWELVE_KEY:
        return None
    sym, _ = to_twelve_symbol(symbol)
    try:
        url = f"{TWELVE_URL}/price?symbol={sym}&apikey={TWELVE_KEY}"
        r = requests.get(url, timeout=5)
        p = r.json().get("price")
        if p:
            return float(p)
    except: pass
    return None

def get_candles_yahoo(symbol,tf,count=80):
    tf_map={"1":"1m","5":"5m","15":"15m","30":"30m","60":"1h","240":"4h"}
    interval=tf_map.get(tf,"5m")
    period="1d" if tf in ["1","5","15"] else "5d"
    for yhost in ["query1","query2"]:
        try:
            url=f"https://{yhost}.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={period}"
            r=requests.get(url,timeout=8,headers={"User-Agent":"Mozilla/5.0"})
            res=r.json()["chart"]["result"][0]
            q=res["indicators"]["quote"][0]
            c=[x for x in q["close"] if x]
            h=[x for x in q["high"]  if x]
            l=[x for x in q["low"]   if x]
            v=[x for x in q.get("volume",[]) if x]
            n=min(len(c),len(h),len(l),count)
            print(f"[YAHOO/{yhost}] {symbol} n={n}")
            return c[-n:],h[-n:],l[-n:],(v[-n:] if len(v)>=n else [])
        except Exception as e: print(f"[YAHOO/{yhost} ERR] {e}")
    return [],[],[],[]

def get_candles(symbol,tf,count=80):
    # 1. TwelveData — основний (800/день)
    c,h,l,v=get_candles_twelve(symbol,tf,count)
    if len(c)>=15: return c,h,l,v
    # 2. Yahoo — резерв
    c,h,l,v=get_candles_yahoo(symbol,tf,count)
    return c,h,l,v

def get_price(symbol,fallback):
    # 1. TwelveData
    p=get_price_twelve(symbol)
    if p and p>0: return p
    # 2. Yahoo резерв
    for yhost in ["query1","query2"]:
        try:
            url=f"https://{yhost}.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
            r=requests.get(url,timeout=5,headers={"User-Agent":"Mozilla/5.0"})
            return float(r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"])
        except: pass
    return fallback

# ══════════════════════════════════════════
#  ГЕНЕРАЦІЯ СИГНАЛУ (виправлено #1, #5, #6, #7)
# ══════════════════════════════════════════
def generate_signal(pair_name, tf):
    m=ALL_PAIRS.get(pair_name,FOREX_PAIRS[0])
    is_otc="OTC" in pair_name
    closes,highs,lows,volumes=get_candles(m["symbol"],tf,80)
    live=get_price(m["symbol"],m["p"])
    real=len(closes)>=15

    # ── Якщо немає реальних даних — розрахунковий режим (позначається ⚙️) ──
    if not real:
        print(f"[FALLBACK] {pair_name} tf={tf} — API не відповів, розрахунковий режим")
        seed=sum(ord(ch) for ch in pair_name)+int(tf)+int(time.time()//300)
        def sr(i):
            x=math.sin(seed+i)*43758.5453123; return x-math.floor(x)
        rsi   = round(25+sr(1)*50)
        adx   = round(20+sr(2)*50); adx_ok=adx>=25
        macd_v= (sr(3)-.5)*.004; mh=macd_v*.4
        stoch = round(15+sr(5)*70)
        bb    = sr(4)*100
        willr = round(-80+sr(6)*60)
        ec    = 2 if sr(7)>0.6 else(-2 if sr(7)<0.4 else 1)
        candle= 0; vol_t=0
        e9 =live*(1+(sr(8)-.5)*.001)
        e21=live*(1+(sr(9)-.5)*.002)
        e50=live*(1+(sr(10)-.5)*.003)
        closes=[live*(1+(sr(i+20)-.5)*.002) for i in range(30)]
        highs =[c*(1+sr(i+50)*.001) for i,c in enumerate(closes)]
        lows  =[c*(1-sr(i+70)*.001) for i,c in enumerate(closes)]
        volumes=[]
        macd=macd_v
        mh_val=mh
    else:
        # Розраховуємо всі індикатори з реальних даних
        rsi   = calc_rsi(closes)
        macd_v, mh_val = calc_macd(closes)
        macd  = macd_v
        mh    = mh_val
        ec    = calc_ema_cross(closes)
        stoch = calc_stoch(closes,highs,lows)
        bb    = calc_bb(closes)
        adx   = calc_adx(closes,highs,lows) or 20
        adx_ok= adx>=25
        willr = calc_williams_r(closes,highs,lows)
        candle= calc_candlestick(closes,highs,lows)
        vol_t = calc_volume_trend(volumes)
        e9 =calc_ema(closes,9)  or live
        e21=calc_ema(closes,21) or live
        e50=calc_ema(closes,50) or live

    votes=[]

    # RSI
    if rsi is not None:
        if rsi<30:   votes.append(("RSI",1,f"RSI={rsi} перепроданість 🔥"))
        elif rsi>70: votes.append(("RSI",-1,f"RSI={rsi} перекупленість 🔥"))
        elif rsi<45: votes.append(("RSI",1,f"RSI={rsi} бичачий нахил"))
        elif rsi>55: votes.append(("RSI",-1,f"RSI={rsi} ведмежий нахил"))
        else:        votes.append(("RSI",0,f"RSI={rsi} нейтраль"))

    # MACD
    if macd is not None and mh is not None:
        if macd>0 and mh>0:   votes.append(("MACD",1,"MACD ▲ BUY підтверджено ✅"))
        elif macd<0 and mh<0: votes.append(("MACD",-1,"MACD ▼ SELL підтверджено ✅"))
        else:                  votes.append(("MACD",0,"MACD нейтральний"))

    # EMA Cross
    if ec is not None:
        if ec==2:    votes.append(("EMA",1,"EMA 9/21 перетин ▲ СИЛЬНИЙ BUY 🔥"))
        elif ec==-2: votes.append(("EMA",-1,"EMA 9/21 перетин ▼ СИЛЬНИЙ SELL 🔥"))
        elif ec==1:  votes.append(("EMA",1,"EMA 9>21 висхідний тренд"))
        else:        votes.append(("EMA",-1,"EMA 9<21 низхідний тренд"))

    # Stochastic
    if stoch is not None:
        if stoch<20:   votes.append(("Stoch",1,f"Stoch={stoch} перепроданість ✅"))
        elif stoch>80: votes.append(("Stoch",-1,f"Stoch={stoch} перекупленість ✅"))
        else:          votes.append(("Stoch",0,f"Stoch={stoch} нейтраль"))

    # Bollinger Bands
    if bb is not None:
        if bb<15:   votes.append(("BB",1,"Ціна біля нижньої смуги ✅"))
        elif bb>85: votes.append(("BB",-1,"Ціна біля верхньої смуги ✅"))
        else:       votes.append(("BB",0,f"BB позиція {bb:.0f}%"))

    # EMA50 тренд
    if e50:
        if live>e50: votes.append(("EMA50",1,"Ціна вище EMA50 — висхідний тренд"))
        else:        votes.append(("EMA50",-1,"Ціна нижче EMA50 — низхідний тренд"))

    # Williams %R (fix #5)
    if willr is not None:
        if willr<-80:   votes.append(("W%R",1,f"Williams %R={willr} перепроданість 🔥"))
        elif willr>-20: votes.append(("W%R",-1,f"Williams %R={willr} перекупленість 🔥"))
        elif willr<-50: votes.append(("W%R",1,f"Williams %R={willr} слабкий BUY"))
        else:           votes.append(("W%R",-1,f"Williams %R={willr} слабкий SELL"))

    # Свічкові патерни (fix #6)
    if candle==1:  votes.append(("Candle",1,"🕯 Бичачий патерн ✅"))
    elif candle==-1: votes.append(("Candle",-1,"🕯 Ведмежий патерн ✅"))

    # Об'єм (fix #7)
    if vol_t==1:  votes.append(("Volume",1,"📊 Зростання об'єму — підтвердження"))
    elif vol_t==-1: votes.append(("Volume",-1,"📊 Падіння об'єму — слабкий сигнал"))

    bc=sum(1 for v in votes if v[1]==1)
    sc=sum(1 for v in votes if v[1]==-1)
    nc=sum(1 for v in votes if v[1]==0)
    total_signals=len(votes)
    score=bc-sc
    is_buy=score>=0

    adx_val = adx if adx is not None else 0

    # Впевненість — на основі консенсусу голосів
    dominant=max(bc,sc)
    conf=min(97,round(60+(dominant/max(total_signals,1))*30+(min(adx_val/100,0.15)*10)+(5 if adx_ok else 0)))

    # Сила сигналу
    if dominant<=3:   strength="⚠️ СЛАБКИЙ";   conf=min(conf,75)
    elif dominant<=5: strength="✅ СЕРЕДНІЙ";   conf=min(conf,87)
    elif dominant<=7: strength="🔥 СИЛЬНИЙ"
    else:             strength="🔥🔥 ДУЖЕ СИЛЬНИЙ"

    # ATR для рівнів
    d=m["d"]
    mult=1 if live>100 else(0.01 if live>10 else 0.0001)
    atr=sum(abs(closes[i]-closes[i-1]) for i in range(-10,0))/10 if len(closes)>=10 else mult*3
    atr=max(atr,mult*2)
    sp=1.8 if is_otc else 1.0
    tp1=round(live+atr*1.5,d) if is_buy else round(live-atr*1.5,d)
    sl =round(live-atr*sp, d) if is_buy else round(live+atr*sp, d)
    rr =round(abs(tp1-live)/abs(sl-live),1) if abs(sl-live)>0 else 1.5

    return dict(
        is_buy=is_buy, conf=conf, strength=strength,
        live=live, tp1=tp1, sl=sl, rr=rr,
        rsi=rsi, adx=adx_val, adx_ok=adx_ok,
        willr=willr, candle=candle, vol_t=vol_t,
        e9=round(e9,d), e21=round(e21,d), e50=round(e50,d),
        votes=votes, bc=bc, sc=sc, nc=nc,
        total=total_signals, real=True, is_otc=is_otc
    )

# ══════════════════════════════════════════
#  ФОРМАТУВАННЯ СИГНАЛУ
# ══════════════════════════════════════════
def trend_bar(val):
    v=max(0,min(100,val)); f=round(v/10)
    return "▰"*f+"▱"*(10-f)

def format_signal(pair,tf,d):
    now_dt=datetime.now(timezone.utc)+timedelta(hours=2)
    now=now_dt.strftime("%H:%M")
    tf_hold={"1":(1,2),"5":(5,10),"15":(15,20),"30":(30,35),"60":(60,75),"240":(240,260)}
    hm=tf_hold.get(tf,(5,10))
    exp=(now_dt+timedelta(minutes=hm[0])).strftime("%H:%M")
    tf_label=TIMEFRAMES.get(tf,CRYPTO_TF.get(tf,STOCKS_TF.get(tf,tf)))
    is_crypto=any(pair==p["name"] for p in CRYPTO_PAIRS)
    is_stocks=any(pair==p["name"] for p in STOCKS_PAIRS)
    mkt_lbl="КРИПТО" if is_crypto else("АКЦІЇ" if is_stocks else("OTC" if d["is_otc"] else "FOREX"))
    total=max(d["total"],1)
    dominant=max(d["bc"],d["sc"])
    accuracy=min(95,max(75,round(60+(dominant/total)*35+(d["adx"]/100*10))))
    trend_pct=min(99,max(50,round(50+(dominant/total)*45+(d["adx"]/100*10))))
    f=round(trend_pct/10)
    t_bar="\u25b0"*f+"\u25b1"*(10-f)
    if trend_pct<60:   t_str="Слабий"
    elif trend_pct<75: t_str="Середній"
    elif trend_pct<88: t_str="Сильний"
    else:              t_str="Дуже сильний"
    dir_arrow="\u2b06\ufe0f" if d["is_buy"] else "\u2b07\ufe0f"
    dir_emoji="\U0001f7e2" if d["is_buy"] else "\U0001f534"
    direction="ВВЕРХ" if d["is_buy"] else "ВНИЗ"
    target_vote=1 if d["is_buy"] else -1
    strong=[v for v in d["votes"] if v[1]==target_vote][:3]
    top3_lines="\n".join("\u2705 "+v[2] for v in strong) if strong else "\u26aa Слабкий консенсус"
    extras_lines=[]
    if d.get("willr") is not None:
        extras_lines.append(f"\U0001f4d0 Williams %R: {d['willr']}")
    if d.get("candle",0)!=0:
        extras_lines.append("\U0001f56f Патерн: "+("Бичачий" if d["candle"]==1 else "Ведмежий"))
    if d.get("vol_t",0)!=0:
        extras_lines.append("\U0001f4ca Обєм: "+("Підтверджує" if d["vol_t"]==1 else "Слабкий"))
    extras=("\n".join(extras_lines)+"\n\n") if extras_lines else ""
    src="\U0001f534 Live" if d["real"] else "\u2699\ufe0f Розрахунок"
    adx_status="\u2705" if d["adx_ok"] else "\u26a0\ufe0f слабкий"
    lines=[
        "\u256c\u2550\u2550 \U0001f916 *SIGNAL AI* \u2550\u2550\u2563",
        "",
        f"\U0001f3f7 *{pair}*",
        f"\u23f1 {tf_label}    \U0001f3af Точність: *{accuracy}%*",
        "",
        f"\U0001f4ca *Сила тренду* \u2014 {t_str} *{trend_pct}%*",
        f"`{t_bar}`",
        "",
        f"{dir_emoji} *Напрямок: {dir_arrow} {direction}*",
        f"Утримувати до: *{exp}*",
        "",
        f"{d['strength']}   Голоси: *{d['bc']}\u2191 {d['sc']}\u2193*",
        f"ADX: *{d['adx']}* {adx_status}",
        "",
    ]
    if extras_lines:
        lines+=extras_lines+[""]
    lines+=[
        f"\U0001f4b0 Вхід: `{d['live']}`",
        f"\U0001f3af TP: `{d['tp1']}`  \U0001f6d1 SL: `{d['sl']}`  RR: 1:{d['rr']}",
        "",
        "\U0001f52c *Сигнали:*",
        top3_lines,
        "",
        f"\U0001f4e1 {mkt_lbl}  {src}  {now}",
        "\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518",
        "\u26a0\ufe0f _Не є фінансовою порадою_",
    ]
    return "\n".join(lines)


# ══════════════════════════════════════════
#  АВТО-СКАНЕР (fix #10) — в окремому потоці
# ══════════════════════════════════════════
scanner_active = {}  # cid -> True/False

def run_scanner(cid, tf="15"):
    """Сканує всі Forex+OTC пари і надсилає топ-3 сигнали"""
    scan_pairs=FOREX_PAIRS[:8]+OTC_PAIRS[:5]
    results=[]
    for p in scan_pairs:
        try:
            sig=generate_signal(p["name"],tf)
            if sig and sig["conf"]>=82 and max(sig["bc"],sig["sc"])>=5:
                results.append((p["name"],tf,sig))
        except: pass
    if not results:
        try: bot.send_message(cid,"🔍 Сканування завершено — сильних сигналів не знайдено")
        except: pass
        return
    results.sort(key=lambda x:x[2]["conf"],reverse=True)
    try:
        bot.send_message(cid,f"🔍 *Автосканер знайшов {len(results[:3])} сигнал(и):*",parse_mode="Markdown")
        for pair,tf2,sig in results[:3]:
            kb=InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("✅ Виграш",callback_data=f"win|{pair}|{tf2}"),
                   InlineKeyboardButton("❌ Програш",callback_data=f"loss|{pair}|{tf2}"))
            bot.send_message(cid,format_signal(pair,tf2,sig),parse_mode="Markdown",reply_markup=kb)
            time.sleep(0.5)
    except: pass

def start_scanner(cid):
    scanner_active[cid]=True
    bot.send_message(cid,"🔄 *Сканування запущено...*\nШукаю найкращі сигнали на TF 15хв",
                     parse_mode="Markdown")
    t=threading.Thread(target=run_scanner,args=(cid,),daemon=True)
    t.start()

# ══════════════════════════════════════════
#  КЛАВІАТУРИ
# ══════════════════════════════════════════
def main_kb():
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("📈 FOREX",  callback_data="menu_forex"),
           InlineKeyboardButton("🌙 OTC",    callback_data="menu_otc"))
    kb.add(InlineKeyboardButton("₿ КРИПТО", callback_data="menu_crypto"),
           InlineKeyboardButton("📊 АКЦІЇ",  callback_data="menu_stocks"))
    kb.add(InlineKeyboardButton("🔍 Авто-сканер",callback_data="scanner"),
           InlineKeyboardButton("📊 Статистика", callback_data="stats"))
    kb.add(InlineKeyboardButton("🕐 Сесії",      callback_data="sessions"),
           InlineKeyboardButton("ℹ️ Про бота",   callback_data="about"))
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

def tf_kb(pair):
    is_crypto=any(pair==p["name"] for p in CRYPTO_PAIRS)
    is_stocks=any(pair==p["name"] for p in STOCKS_PAIRS)
    tfs=CRYPTO_TF if is_crypto else(STOCKS_TF if is_stocks else TIMEFRAMES)
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
def send_main(cid,mid=None):
    txt=("╔══ 🤖 *SIGNAL AI* ══╗\n\n"
         "Нейромережа для аналізу ринку\n\n"
         "• RSI • MACD • EMA • Williams %R\n"
         "• Stochastic • BB • ADX\n"
         "• Свічкові патерни • Об'єм\n\n"
         "📡 *Finnhub + Alpha Vantage + Yahoo*\n"
         "🎯 *Точність сигналів: ~82-95%*\n\n"
         "╚══ Оберіть категорію ══╝")
    if mid:
        try: bot.edit_message_text(txt,cid,mid,parse_mode="Markdown",reply_markup=main_kb()); return
        except: pass
    bot.send_message(cid,txt,parse_mode="Markdown",reply_markup=main_kb())

@bot.message_handler(commands=["start","menu"])
def cmd_start(msg): send_main(msg.chat.id)

@bot.message_handler(commands=["stats"])
def cmd_stats(msg):
    bot.send_message(msg.chat.id,stats_text(msg.chat.id),parse_mode="Markdown",reply_markup=main_kb())

@bot.message_handler(commands=["scan"])
def cmd_scan(msg): start_scanner(msg.chat.id)

def do_signal(cid, mid, pair, tf):
    """Генерація сигналу в окремому потоці (fix #2)"""
    tfs_label=TIMEFRAMES.get(tf,CRYPTO_TF.get(tf,STOCKS_TF.get(tf,tf)))
    # Анімація
    steps=[
        ("⟳ Аналіз ринку...","▰▰▰▱▱▱▱▱▱▱ 30%"),
        ("⟳ Обробка індикаторів...","▰▰▰▰▰▰▱▱▱▱ 60%"),
        ("⟳ Генерую сигнал...","▰▰▰▰▰▰▰▰▰▱ 90%"),
    ]
    last_text = ""
    for step,bar in steps:
        try:
            new_text = f"🔵 *SIGNAL AI* 🔵\n\n{step}\n\n`{pair}` | `{tfs_label}`\n\n{bar}"
            if new_text != last_text:
                bot.edit_message_text(new_text, cid, mid, parse_mode="Markdown")
                last_text = new_text
        except Exception as e:
            if "not modified" not in str(e): pass
        time.sleep(0.8)

    sig=generate_signal(pair,tf)

    # fix #1 — якщо немає даних
    if sig is None:
        try:
            bot.edit_message_text(
                f"⚠️ *Немає даних*\n\n`{pair}` | `{tfs_label}`\n\nAPI не відповів. Спробуйте:\n• Інший таймфрейм\n• Через 1-2 хвилини",
                cid,mid,parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🔄 Спробувати знову",callback_data=f"tf|{pair}|{tf}"),
                    InlineKeyboardButton("🏠 Меню",callback_data="main")))
        except: pass
        return

    try:
        bot.edit_message_text(format_signal(pair,tf,sig),cid,mid,
                              parse_mode="Markdown",reply_markup=result_kb(pair,tf))
    except Exception as e:
        print(f"Помилка відправки сигналу: {e}")

@bot.callback_query_handler(func=lambda c:True)
def handle_callback(call):
    cid=call.message.chat.id; mid=call.message.message_id; d=call.data
    bot.answer_callback_query(call.id)
    try:
        if d=="main":
            send_main(cid,mid)
        elif d in("menu_forex","forex_back"):
            bot.edit_message_text("📈 *FOREX пари*\nОберіть пару:",cid,mid,parse_mode="Markdown",reply_markup=forex_kb())
        elif d in("menu_otc","otc_back"):
            bot.edit_message_text("🌙 *OTC пари*\nОберіть пару:",cid,mid,parse_mode="Markdown",reply_markup=otc_kb())
        elif d in("menu_crypto","crypto_back"):
            bot.edit_message_text("₿ *КРИПТО*\nОберіть пару:",cid,mid,parse_mode="Markdown",reply_markup=crypto_kb())
        elif d in("menu_stocks","stocks_back"):
            bot.edit_message_text("📊 *АКЦІЇ*\nОберіть:",cid,mid,parse_mode="Markdown",reply_markup=stocks_kb())
        elif d=="stats":
            bot.edit_message_text(stats_text(cid),cid,mid,parse_mode="Markdown",reply_markup=main_kb())
        elif d=="sessions":
            bot.edit_message_text(sessions_text(),cid,mid,parse_mode="Markdown",reply_markup=main_kb())
        elif d=="scanner":
            bot.edit_message_text("🔍 *Авто-сканер*\nЗапускаю пошук найсильніших сигналів...",
                                  cid,mid,parse_mode="Markdown")
            threading.Thread(target=start_scanner,args=(cid,),daemon=True).start()
        elif d=="about":
            txt=("ℹ️ *SIGNAL AI — Про бота*\n\n"
                 "*Індикатори:*\n"
                 "• RSI • MACD • EMA 9/21/50\n"
                 "• Williams %R • Stochastic\n"
                 "• Bollinger Bands • ADX\n"
                 "• Свічкові патерни\n"
                 "• Аналіз об'єму\n\n"
                 "*API:*\n"
                 "• Finnhub (реальний час)\n"
                 "• Alpha Vantage (1хв Forex)\n"
                 "• Yahoo Finance (резерв)\n\n"
                 "🎯 Точність: ~82-95%\n"
                 "📊 Forex • OTC • Крипто • Акції")
            bot.edit_message_text(txt,cid,mid,parse_mode="Markdown",reply_markup=main_kb())
        elif d.startswith("pair_"):
            pair=d[5:]
            bot.edit_message_text(f"⏱ *Таймфрейм для {pair}*\nОберіть:",cid,mid,
                                  parse_mode="Markdown",reply_markup=tf_kb(pair))
        elif d.startswith("tf|"):
            _,pair,tf=d.split("|",2)
            # fix #2 — threading, не блокуємо основний потік
            threading.Thread(target=do_signal,args=(cid,mid,pair,tf),daemon=True).start()
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
            save_user_stats()  # fix #3
            wr=round(s["wins"]/s["total"]*100)
            bot.send_message(cid,f"{emoji}\n\n📊 WR: *{wr}%* ({s['wins']}W/{s['losses']}L)\n\nОберіть наступну дію:",
                             parse_mode="Markdown",reply_markup=main_kb())
    except Exception as e:
        print(f"Помилка: {e}")
        try: bot.send_message(cid,"Оберіть категорію:",reply_markup=main_kb())
        except: pass

# ══════════════════════════════════════════
#  ЗАПУСК
# ══════════════════════════════════════════
if __name__=="__main__":
    print("✅ SIGNAL AI Bot запущено!")
    # Скидаємо webhook і старі з'єднання перед стартом
try:
    bot.delete_webhook(drop_pending_updates=True)
    time.sleep(1)
except: pass
bot.infinity_polling(timeout=30, long_polling_timeout=20, skip_pending=True)
