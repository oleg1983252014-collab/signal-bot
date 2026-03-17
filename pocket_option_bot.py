#!/usr/bin/env python3
import os, math, time, requests, threading, json
from datetime import datetime, timezone, timedelta
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
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
    {"name":"MATIC/USD","symbol":"MATIC-USD","p":0.95,"d":4,"t":-1},
    {"name":"LTC/USD","symbol":"LTC-USD","p":95,"d":2,"t":1},
    {"name":"AVAX/USD","symbol":"AVAX-USD","p":38,"d":2,"t":-1},
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

ALL_PAIRS = {p["name"]: p for p in FOREX_PAIRS + OTC_PAIRS + CRYPTO_PAIRS + STOCKS_PAIRS}
TIMEFRAMES = {"1":"1 хвилина","3":"3 хвилини","5":"5 хвилин","15":"15 хвилин","30":"30 хвилин","60":"1 година"}
CRYPTO_TF  = {"5":"5 хвилин","15":"15 хвилин","30":"30 хвилин","60":"1 година","240":"4 години"}
STOCKS_TF  = {"5":"5 хвилин","15":"15 хвилин","30":"30 хвилин","60":"1 година"}

# ══════════════════════════════════════════
#  СТАТИСТИКА + МАШИННЕ НАВЧАННЯ (Рівень 2)
# ══════════════════════════════════════════
user_stats  = {}
last_signal = {}   # зберігає останній сигнал для ML
subscribers = {}   # {chat_id: {"active":True, "tf":"5", "min_conf":85, "last_sent":0}}
scan_pairs  = [p["name"] for p in FOREX_PAIRS[:8]] + [p["name"] for p in CRYPTO_PAIRS[:4]]

# Початкові ваги індикаторів (однакові для всіх)
DEFAULT_WEIGHTS = {
    "RSI": 1.0, "MACD": 1.0, "EMA Cross": 1.0,
    "Ichimoku": 1.0, "Stoch": 1.0, "BB": 1.0,
    "EMA50": 1.0, "MTF": 1.2, "Обсяг": 0.8, "Патерн": 0.9
}

def get_stats(cid):
    if cid not in user_stats:
        user_stats[cid] = {
            "total":0,"wins":0,"losses":0,"pairs":{},"streak":0,
            # ML дані
            "weights": DEFAULT_WEIGHTS.copy(),   # ваги індикаторів
            "indicator_stats": {},               # точність кожного індикатора
            "tf_stats": {},                      # точність по таймфреймах
            "history": [],                       # останні 500 угод
            "last_trained": 0,                   # коли останній раз навчались
        }
    s = user_stats[cid]
    # Якщо старий формат — оновити
    if "weights" not in s:
        s["weights"] = DEFAULT_WEIGHTS.copy()
        s["indicator_stats"] = {}
        s["tf_stats"] = {}
        s["history"] = []
        s["last_trained"] = 0
    return s

def record_trade(cid, pair, tf, votes, conf, result_win):
    """Зберігає угоду для навчання"""
    s = get_stats(cid)
    trade = {
        "pair": pair, "tf": tf, "conf": conf,
        "votes": [(v[0], v[1]) for v in votes],
        "win": result_win,
        "time": int(time.time())
    }
    s["history"].append(trade)
    if len(s["history"]) > 500:
        s["history"] = s["history"][-500:]

    # Оновити статистику по індикаторах
    for name, vote in trade["votes"]:
        if name not in s["indicator_stats"]:
            s["indicator_stats"][name] = {"correct":0,"total":0}
        is_buy_signal = vote == 1
        if (is_buy_signal and result_win) or (not is_buy_signal and not result_win):
            s["indicator_stats"][name]["correct"] += 1
        s["indicator_stats"][name]["total"] += 1

    # Оновити статистику по таймфреймах
    if tf not in s["tf_stats"]:
        s["tf_stats"][tf] = {"wins":0,"total":0}
    s["tf_stats"][tf]["total"] += 1
    if result_win: s["tf_stats"][tf]["wins"] += 1

    # Автонавчання кожні 20 угод
    if s["total"] % 20 == 0 and s["total"] >= 20:
        ml_train(cid)

def ml_train(cid):
    """Перераховує ваги індикаторів на основі статистики"""
    s = get_stats(cid)
    if s["total"] < 20:
        return
    new_weights = {}
    for name, base in DEFAULT_WEIGHTS.items():
        if name in s["indicator_stats"]:
            stat = s["indicator_stats"][name]
            if stat["total"] >= 10:
                accuracy = stat["correct"] / stat["total"]
                # Точніший індикатор отримує більшу вагу (0.5 - 2.0)
                weight = round(max(0.5, min(2.0, base * (accuracy / 0.6))), 2)
                new_weights[name] = weight
            else:
                new_weights[name] = base
        else:
            new_weights[name] = base
    s["weights"] = new_weights
    s["last_trained"] = int(time.time())

def get_weights(cid):
    """Повертає навчені ваги для конкретного користувача"""
    return get_stats(cid).get("weights", DEFAULT_WEIGHTS.copy())

def ml_status_text(cid):
    """Текст про статус ML навчання"""
    s = get_stats(cid)
    total = s["total"]
    if total < 20:
        need = 20 - total
        return f"🤖 *ML навчання:* очікує {need} угод для старту"
    weights = s.get("weights", DEFAULT_WEIGHTS)
    trained = s.get("last_trained", 0)
    trained_str = datetime.fromtimestamp(trained, tz=timezone.utc).strftime("%d.%m %H:%M") if trained else "ще не"
    # Топ індикатори
    ind_stats = s.get("indicator_stats", {})
    top = sorted(
        [(n, d["correct"]/d["total"]*100) for n,d in ind_stats.items() if d["total"]>=5],
        key=lambda x: x[1], reverse=True
    )[:3]
    top_txt = "\n".join(f"  🏆 {n}: {round(acc)}%" for n,acc in top) if top else "  Ще мало даних"
    # Найкращий ТФ
    tf_stats = s.get("tf_stats", {})
    best_tf = max(tf_stats.items(), key=lambda x: x[1]["wins"]/(x[1]["total"] or 1)) if tf_stats else None
    tf_txt = f"  ⏱ {best_tf[0]}хв: {round(best_tf[1]['wins']/(best_tf[1]['total'] or 1)*100)}%" if best_tf else "  Ще мало даних"
    # Ваги що найбільше змінились
    changed = [(n, w) for n,w in weights.items() if abs(w - DEFAULT_WEIGHTS.get(n,1.0)) > 0.1]
    changed_txt = "\n".join(f"  {'📈' if w>1 else '📉'} {n}: {w}x" for n,w in changed[:3]) if changed else "  Ваги ще не змінились"
    return (
        f"🤖 *ML Навчання — Рівень 2*\n\n"
        f"📊 Угод для навчання: `{total}`\n"
        f"🕐 Останнє навчання: `{trained_str}`\n"
        f"🔄 Наступне: через `{20 - (total % 20)}` угод\n\n"
        f"🏆 *Найточніші індикатори:*\n{top_txt}\n\n"
        f"⏱ *Найкращий таймфрейм:*\n{tf_txt}\n\n"
        f"⚖️ *Адаптовані ваги:*\n{changed_txt}\n\n"
        f"_Бот вчиться на вашій статистиці автоматично_"
    )

def stats_text(cid):
    s = get_stats(cid)
    if s["total"] == 0:
        return "📊 *Статистика*\n\nЩе немає угод.\nПісля сигналу натискайте ✅ або ❌"
    wr  = round(s["wins"]/s["total"]*100)
    bar = "🟢"*round(wr/10) + "⚪"*(10-round(wr/10))
    best = sorted(s["pairs"].items(), key=lambda x: x[1]["wins"]/(x[1]["total"] or 1), reverse=True)[:3]
    bt   = "".join(f"  • {n}: {d['wins']}/{d['total']} ({round(d['wins']/(d['total'] or 1)*100)}%)\n" for n,d in best)
    st   = s.get("streak",0)
    sl   = (f"🔥 Серія виграшів: {st}\n" if st>1 else f"❄️ Серія програшів: {abs(st)}\n" if st<-1 else "")
    ml   = ml_status_text(cid)
    return (f"📊 *Статистика*\n\nВсього: `{s['total']}`\n✅ Виграші: `{s['wins']}`\n"
            f"❌ Програші: `{s['losses']}`\n\n🏆 *WR: {wr}%*\n{bar}\n\n{sl}"
            f"🥇 *Кращі пари:*\n{bt}\n\n━━━━━━━━━━━━━━━━━━━━\n{ml}")

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
            f"🔥 Перетин:  15:00–18:00 ← найкращий час")

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

def get_candles(symbol,tf,count=60):
    tf_map={"1":"1m","3":"2m","5":"5m","15":"15m","30":"30m","60":"1h","240":"4h"}
    interval=tf_map.get(tf,"5m")
    period="1d" if tf in ["1","3","5","15"] else ("60d" if tf=="240" else "5d")
    try:
        url=f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={period}"
        r=requests.get(url,timeout=8,headers={"User-Agent":"Mozilla/5.0"})
        res=r.json()["chart"]["result"][0]
        q=res["indicators"]["quote"][0]
        c=[x for x in q["close"] if x]
        h=[x for x in q["high"]  if x]
        l=[x for x in q["low"]   if x]
        v=[x for x in (q.get("volume") or [0]*len(c)) if x is not None]
        n=min(len(c),len(h),len(l),len(v),count)
        return c[-n:],h[-n:],l[-n:],v[-n:]
    except: return [],[],[],[]

def get_price(symbol,fallback):
    try:
        url=f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
        r=requests.get(url,timeout=5,headers={"User-Agent":"Mozilla/5.0"})
        return float(r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"])
    except: return fallback

# ══════════════════════════════════════════
#  НОВІ ІНДИКАТОРИ
# ══════════════════════════════════════════
def calc_support_resistance(highs, lows, closes, n=20):
    """Знаходить сильні рівні підтримки та опору"""
    if len(closes) < n: return [],[]
    window=5
    resistance_levels=[]
    support_levels=[]
    for i in range(window, len(highs)-window):
        if highs[i]==max(highs[i-window:i+window+1]):
            resistance_levels.append(highs[i])
        if lows[i]==min(lows[i-window:i+window+1]):
            support_levels.append(lows[i])
    # Кластеризуємо близькі рівні
    def cluster(levels, tol=0.002):
        if not levels: return []
        levels=sorted(set(levels))
        clusters=[[levels[0]]]
        for lv in levels[1:]:
            if (lv-clusters[-1][-1])/clusters[-1][-1]<tol:
                clusters[-1].append(lv)
            else:
                clusters.append([lv])
        return [sum(c)/len(c) for c in clusters]
    return cluster(resistance_levels), cluster(support_levels)

def calc_volume_signal(volumes):
    """Аналіз обсягу торгів"""
    if len(volumes)<10: return 0,"Обсяг н/д"
    avg_vol=sum(volumes[-10:])/10
    curr_vol=volumes[-1]
    ratio=curr_vol/avg_vol if avg_vol>0 else 1
    if ratio>1.5:   return 1, f"Обсяг +{round((ratio-1)*100)}% ✅ сильний сигнал"
    elif ratio>1.1: return 0.5, f"Обсяг +{round((ratio-1)*100)}% нормальний"
    else:           return -0.5, f"Обсяг низький ⚠️"

def calc_candle_patterns(closes, highs, lows):
    """Патерни свічок"""
    if len(closes)<3: return 0,""
    o1,h1,l1,c1 = closes[-3],highs[-3],lows[-3],closes[-3]
    o2,h2,l2,c2 = closes[-2],highs[-2],lows[-2],closes[-2]
    o3,h3,l3,c3 = closes[-1],highs[-1],lows[-1],closes[-1]
    body2=abs(c2-o2); body3=abs(c3-o3)
    range2=h2-l2 if h2!=l2 else 0.0001

    patterns=[]

    # Doji
    if body3<range2*0.1:
        patterns.append((0,"🕯 Doji — невизначеність"))

    # Hammer (молоток) — бичачий розворот
    lower_wick=o3-l3 if c3>o3 else c3-l3
    upper_wick=h3-c3 if c3>o3 else h3-o3
    if lower_wick>body3*2 and upper_wick<body3*0.5 and body3>0:
        patterns.append((1,"🔨 Hammer — бичачий розворот ✅"))

    # Shooting Star — ведмежий розворот
    if upper_wick>body3*2 and lower_wick<body3*0.5 and body3>0:
        patterns.append((-1,"⭐ Shooting Star — ведмежий розворот ✅"))

    # Bullish Engulfing
    if c2<o2 and c3>o3 and c3>o2 and o3<c2:
        patterns.append((1,"🟢 Bullish Engulfing ✅"))

    # Bearish Engulfing
    if c2>o2 and c3<o3 and c3<o2 and o3>c2:
        patterns.append((-1,"🔴 Bearish Engulfing ✅"))

    # Three White Soldiers
    if c1>o1 and c2>o2 and c3>o3 and c3>c2>c1:
        patterns.append((1,"💪 Three White Soldiers ✅"))

    # Three Black Crows
    if c1<o1 and c2<o2 and c3<o3 and c3<c2<c1:
        patterns.append((-1,"🐦 Three Black Crows ✅"))

    if not patterns: return 0,"Патернів не виявлено"
    score=sum(p[0] for p in patterns)
    desc=" | ".join(p[1] for p in patterns)
    return score, desc

def calc_mtf(symbol, tf):
    """Мультитаймфреймний аналіз — старший ТФ"""
    tf_up={"1":"5","3":"15","5":"15","15":"60","30":"60","60":"240","240":"240"}
    higher_tf=tf_up.get(tf,tf)
    if higher_tf==tf: return 0,"MTF: н/д"
    c,h,l,v=get_candles(symbol,higher_tf,30)
    if len(c)<20: return 0,"MTF: недостатньо даних"
    # Простий тренд на старшому ТФ
    ema9 =calc_ema(c,9)
    ema21=calc_ema(c,21)
    rsi  =calc_rsi(c)
    tf_names={"5":"5хв","15":"15хв","60":"1год","240":"4год"}
    tf_name=tf_names.get(higher_tf,higher_tf+"хв")
    if ema9>ema21 and rsi>50:
        return 1, f"MTF {tf_name}: бичачий тренд ✅"
    elif ema9<ema21 and rsi<50:
        return -1, f"MTF {tf_name}: ведмежий тренд ✅"
    return 0, f"MTF {tf_name}: нейтраль"

def nearest_sr(price, resistances, supports, decimals):
    """Знаходить найближчі рівні S/R та відстань до них"""
    near_res = min(resistances, key=lambda x: abs(x-price)) if resistances else None
    near_sup = min(supports,    key=lambda x: abs(x-price)) if supports    else None
    sr_warn=""
    if near_res and abs(near_res-price)/price<0.003:
        sr_warn=f"⚠️ Ціна біля сильного ОПОРУ ({round(near_res,decimals)})"
    elif near_sup and abs(near_sup-price)/price<0.003:
        sr_warn=f"⚠️ Ціна біля сильної ПІДТРИМКИ ({round(near_sup,decimals)})"
    return (round(near_res,decimals) if near_res else None,
            round(near_sup,decimals) if near_sup else None,
            sr_warn)

# ══════════════════════════════════════════
#  ГЕНЕРАЦІЯ СИГНАЛУ v3 (MTF + S/R + Patterns + Volume)
# ══════════════════════════════════════════
def generate_signal(pair_name, tf, cid=None):
    m=ALL_PAIRS.get(pair_name,FOREX_PAIRS[0])
    is_otc="OTC" in pair_name
    closes,highs,lows,volumes=get_candles(m["symbol"],tf,60)
    live=get_price(m["symbol"],m["p"])
    real=len(closes)>=20

    if real:
        rsi=calc_rsi(closes); adx=calc_adx(closes,highs,lows)
        macd,mh=calc_macd(closes); stoch=calc_stoch(closes,highs,lows)
        bb=calc_bb(closes); ichi=calc_ichimoku(closes,highs,lows)
        ec=calc_ema_cross(closes)
        e9=calc_ema(closes,9); e21=calc_ema(closes,21); e50=calc_ema(closes,50)
        # Нові
        resistances,supports=calc_support_resistance(highs,lows,closes)
        vol_score,vol_desc=calc_volume_signal(volumes)
        pat_score,pat_desc=calc_candle_patterns(closes,highs,lows)
        mtf_score,mtf_desc=calc_mtf(m["symbol"],tf)
        nr,ns,sr_warn=nearest_sr(live,resistances,supports,m["d"])
    else:
        seed=sum(ord(c) for c in pair_name)+int(tf)+int(time.time()//60)
        r=lambda i:seeded_rand(seed,i)
        rsi=round(28+r(1)*50); adx=round(22+r(2)*55); macd=(r(3)-.5)*.006; mh=macd*.3
        stoch=round(15+r(5)*70); bb=r(4)*100; ichi=m["t"]; ec=m["t"]
        e9=live*(1+(r(7)-.5)*.002); e21=live*(1+(r(8)-.5)*.003); e50=live*(1+(r(9)-.5)*.005)
        resistances=[]; supports=[]; vol_score=0; vol_desc="Обсяг н/д"
        pat_score=0; pat_desc="Патернів не виявлено"; mtf_score=m["t"]; mtf_desc="MTF розрахунковий"
        nr=None; ns=None; sr_warn=""

    votes=[]
    # 1. RSI
    if rsi<30:    votes.append(("RSI",1,f"RSI={rsi} перепроданість ✅"))
    elif rsi>70:  votes.append(("RSI",-1,f"RSI={rsi} перекупленість ✅"))
    elif rsi<45:  votes.append(("RSI",1,f"RSI={rsi} бичачий нахил"))
    elif rsi>55:  votes.append(("RSI",-1,f"RSI={rsi} ведмежий нахил"))
    else:         votes.append(("RSI",0,f"RSI={rsi} нейтраль"))
    # 2. MACD
    if macd>0 and mh>0:   votes.append(("MACD",1,"MACD ▲ BUY ✅"))
    elif macd<0 and mh<0: votes.append(("MACD",-1,"MACD ▼ SELL ✅"))
    else:                  votes.append(("MACD",0,"MACD нейтральний"))
    # 3. EMA Cross
    if ec==2:    votes.append(("EMA Cross",1,"EMA 9/21 ▲ СИЛЬНИЙ BUY ✅"))
    elif ec==-2: votes.append(("EMA Cross",-1,"EMA 9/21 ▼ СИЛЬНИЙ SELL ✅"))
    elif ec==1:  votes.append(("EMA Cross",1,"EMA 9>21 бичачий тренд"))
    else:        votes.append(("EMA Cross",-1,"EMA 9<21 ведмежий тренд"))
    # 4. Ichimoku
    if ichi==1:    votes.append(("Ichimoku",1,"Ціна над хмарою ☁️ BUY ✅"))
    elif ichi==-1: votes.append(("Ichimoku",-1,"Ціна під хмарою ☁️ SELL ✅"))
    else:          votes.append(("Ichimoku",0,"Ichimoku нейтраль"))
    # 5. Stochastic
    if stoch<20:   votes.append(("Stoch",1,f"Stoch={stoch} перепроданість ✅"))
    elif stoch>80: votes.append(("Stoch",-1,f"Stoch={stoch} перекупленість ✅"))
    else:          votes.append(("Stoch",0,f"Stoch={stoch} нейтраль"))
    # 6. Bollinger Bands
    if bb<15:      votes.append(("BB",1,"Ціна біля нижньої смуги ✅"))
    elif bb>85:    votes.append(("BB",-1,"Ціна біля верхньої смуги ✅"))
    else:          votes.append(("BB",0,f"BB позиція {bb:.0f}%"))
    # 7. EMA50
    if live>e50:   votes.append(("EMA50",1,"Ціна вище EMA50 — висхідний тренд"))
    else:          votes.append(("EMA50",-1,"Ціна нижче EMA50 — низхідний тренд"))
    # 8. MTF
    if mtf_score==1:    votes.append(("MTF",1,mtf_desc))
    elif mtf_score==-1: votes.append(("MTF",-1,mtf_desc))
    else:               votes.append(("MTF",0,mtf_desc))
    # 9. Обсяг
    if vol_score>=1:     votes.append(("Обсяг",1,vol_desc))
    elif vol_score<=-0.5:votes.append(("Обсяг",-1,vol_desc))
    else:                votes.append(("Обсяг",0,vol_desc))
    # 10. Патерни
    if pat_score>0:   votes.append(("Патерн",1,pat_desc))
    elif pat_score<0: votes.append(("Патерн",-1,pat_desc))
    else:             votes.append(("Патерн",0,pat_desc))

    # ══ ML ВАГИ — застосовуємо навчені ваги ══
    weights = get_weights(cid) if cid else DEFAULT_WEIGHTS
    weighted_score = sum(v[1] * weights.get(v[0], 1.0) for v in votes)
    bc=sum(1 for v in votes if v[1]==1)
    sc=sum(1 for v in votes if v[1]==-1)
    # Зважений score замість простого підрахунку
    score = weighted_score; is_buy = score >= 0
    tv=len(votes)

    # ══ ЖОРСТКІ ФІЛЬТРИ ══
    adx_ok   = adx>=30              # Підвищено з 25 до 30
    mtf_ok   = (mtf_score==1 and is_buy) or (mtf_score==-1 and not is_buy)
    pat_ok   = (pat_score>0 and is_buy) or (pat_score<0 and not is_buy)
    sr_block = bool(sr_warn)        # Ціна біля S/R — блокуємо

    # Бонуси
    mtf_bonus = 6 if mtf_ok else -4          # MTF не збігається — штраф
    pat_bonus = 4 if pat_ok else 0
    adx_bonus = round(min(adx/100,.15)*10)

    conf=min(97,round(66+min(abs(score)/tv,1)*24+adx_bonus+(5 if adx_ok else 0)+mtf_bonus+pat_bonus))

    sc2=max(bc,sc)

    # ══ РІВНІ СИЛИ (жорсткіші пороги) ══
    if sc2<5 or not adx_ok:
        conf=min(conf,72); strength="⛔ ПРОПУСТІТЬ"
        skip=True
    elif sc2<7 or not mtf_ok:
        conf=min(conf,83); strength="⚠️ СЛАБКИЙ — обережно"
        skip=False
    elif sc2<9:
        conf=min(conf,91); strength="✅ СЕРЕДНІЙ"
        skip=False
    else:
        strength="🔥 СИЛЬНИЙ — входити!"; skip=False

    # S/R блокує сигнал
    if sr_block:
        conf=max(55,conf-10)
        if skip==False and sc2<8: strength="⚠️ S/R блокує — ризик"

    d=m["d"]; mult=1 if live>100 else(.01 if live>10 else .0001)
    atr=sum(abs(closes[i]-closes[i-1]) for i in range(-10,0))/10 if real and len(closes)>=10 else mult*3
    atr=max(atr,mult*2); sp=1.8 if is_otc else 1.0
    tp1=round(live+atr*1.5,d) if is_buy else round(live-atr*1.5,d)
    tp2=round(live+atr*2.5,d) if is_buy else round(live-atr*2.5,d)
    sl =round(live-atr*sp,d)  if is_buy else round(live+atr*sp,d)
    rr =round(abs(tp1-live)/abs(sl-live),1) if abs(sl-live)>0 else 1.5
    if is_buy and nr: tp1=round(min(tp1,nr*0.999),d)
    if not is_buy and ns: tp1=round(max(tp1,ns*1.001),d)

    return dict(is_buy=is_buy,signal="BUY ▲" if is_buy else "SELL ▼",conf=conf,
                strength=strength,skip=skip,live=live,tp1=tp1,tp2=tp2,sl=sl,rr=rr,
                rsi=rsi,adx=adx,adx_ok=adx_ok,macd=macd,stoch=stoch,bb=bb,
                e9=round(e9,d),e21=round(e21,d),e50=round(e50,d),
                votes=votes,bc=bc,sc=sc,real=real,is_otc=is_otc,
                nr=nr,ns=ns,sr_warn=sr_warn,pat_desc=pat_desc,
                mtf_desc=mtf_desc,vol_desc=vol_desc,
                total_votes=tv,mtf_ok=mtf_ok,pat_ok=pat_ok,
                votes_raw=votes,weighted_score=round(weighted_score,2))

def format_signal(pair,tf,d):
    now_dt=datetime.now(timezone.utc)+timedelta(hours=2)
    now=now_dt.strftime("%H:%M:%S")
    tf_hold={"1":(1,2),"3":(3,5),"5":(5,10),"15":(15,20),"30":(30,35),"60":(60,75),"240":(240,260)}
    hm=tf_hold.get(tf,(5,10))
    exp=(now_dt+timedelta(minutes=hm[0])).strftime("%H:%M")
    is_buy=d["is_buy"]
    is_crypto = pair in [p["name"] for p in CRYPTO_PAIRS]
    is_stocks = pair in [p["name"] for p in STOCKS_PAIRS]
    mkt = "₿ КРИПТО" if is_crypto else ("📊 АКЦІЇ" if is_stocks else ("🌙 OTC" if d["is_otc"] else "📈 FOREX"))
    tv  = d.get("total_votes", 7)
    sr_line = f"\n{d['sr_warn']}" if d.get("sr_warn") else ""
    nr_line = f"🔴 Опір:      `{d['nr']}`\n" if d.get("nr") else ""
    ns_line = f"🟢 Підтримка: `{d['ns']}`\n" if d.get("ns") else ""
    adw = "" if d["adx_ok"] else "\n⚠️ _ADX<25 — тренд слабкий!_"
    vt  = "".join(f"{'🟢' if v[1]==1 else '🔴' if v[1]==-1 else '⚪'} {v[2]}\n" for v in d["votes"])

    # ══ КОЛЬОРОВЕ ОФОРМЛЕННЯ ══
    skip = d.get("skip", False)
    mtf_ok = d.get("mtf_ok", True)
    pat_ok = d.get("pat_ok", False)

    if skip:
        # Сигнал слабкий — показуємо попередження
        return f"""⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔
⚡ *AI SIGNAL BOT v3 — Pocket Option*
{mkt} | {"🔴 Live" if d["real"] else "⚙️ Розрах"} | {now}
⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔

🚫 *СИГНАЛ ЗАБЛОКОВАНО*
💪 {d["strength"]}

❌ Причини блокування:
{"✅" if d["adx_ok"] else "❌"} ADX={d["adx"]} {"≥30 ✅" if d["adx_ok"] else "<30 — тренд слабкий"}
{"✅" if mtf_ok else "❌"} MTF {"збігається" if mtf_ok else "не збігається зі старшим ТФ"}
📊 Підтверджень: {d["bc"] if is_buy else d["sc"]}/{tv} (потрібно 5+)

⏭ _Очікуйте сильнішого сигналу_
⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔
⚠️ _Не є фінансовою порадою_""".strip()

    if is_buy:
        header   = "🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩"
        direction= "📗 КУПИТИ — BUY ▲ 📗"
        border   = "🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢"
        conf_bar = "🟩"*round(d["conf"]/10)+"⬜"*(10-round(d["conf"]/10))
        arrow    = "⬆️⬆️⬆️"
        color_tp = "💚"; color_sl="❤️"
    else:
        header   = "🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥"
        direction= "📕 ПРОДАТИ — SELL ▼ 📕"
        border   = "🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴"
        conf_bar = "🟥"*round(d["conf"]/10)+"⬜"*(10-round(d["conf"]/10))
        arrow    = "⬇️⬇️⬇️"
        color_tp = "❤️"; color_sl="💚"

    # Статус фільтрів
    filters = (
        f"{'✅' if d['adx_ok'] else '⚠️'} ADX={d['adx']} {'≥30' if d['adx_ok'] else '<30'} | "
        f"{'✅' if mtf_ok else '⚠️'} MTF | "
        f"{'✅' if pat_ok else '⚪'} Патерн"
    )

    return f"""{header}
⚡ *AI SIGNAL BOT v3 — Pocket Option*
{mkt} | {"🔴 Live" if d["real"] else "⚙️ Розрах"} | {now}
{header}

{arrow} *{direction}* {arrow}
💪 Сила: *{d["strength"]}*
⏱ Утримувати: *{hm[0]}–{hm[1]} хв* | 🕐 Експірація: *{exp}*

{border}
📊 *Впевненість: {d["conf"]}%*
{conf_bar}
✅ BUY: `{d["bc"]}/{tv}` | 🔴 SELL: `{d["sc"]}/{tv}`
📐 {filters}{adw}{sr_line}
{border}

*Пара:* `{pair}` | *ТФ:* `{TIMEFRAMES.get(tf,tf)}`
💰 Вхід: `{d["live"]}`
{color_tp} TP1: `{d["tp1"]}` | TP2: `{d["tp2"]}`
{color_sl} SL:  `{d["sl"]}` | R/R: `1:{d["rr"]}`
{nr_line}{ns_line}
📉 EMA9:`{d["e9"]}` EMA21:`{d["e21"]}` EMA50:`{d["e50"]}`

{border}
🔬 *{tv} індикаторів:*
{vt}
{header}
⚠️ _Не є фінансовою порадою_""".strip()

# ══════════════════════════════════════════
#  КЛАВІАТУРИ
# ══════════════════════════════════════════
def main_kb(cid=None):
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("📈 FOREX",callback_data="menu_forex"),
           InlineKeyboardButton("🌙 OTC",callback_data="menu_otc"))
    kb.add(InlineKeyboardButton("₿ КРИПТО",callback_data="menu_crypto"),
           InlineKeyboardButton("📊 АКЦІЇ",callback_data="menu_stocks"))
    kb.add(InlineKeyboardButton("📊 Статистика",callback_data="stats"),
           InlineKeyboardButton("🕐 Сесії",callback_data="sessions"))
    kb.add(InlineKeyboardButton("🤖 ML Навчання",callback_data="ml_status"),
           InlineKeyboardButton("ℹ️ Про бота",callback_data="about"))
    # Авто кнопка — показує статус
    is_active = subscribers.get(cid,{}).get("active",False) if cid else False
    auto_label = "🟢 АВТО: ВКЛ" if is_active else "🔴 АВТО: ВИКЛ"
    kb.add(InlineKeyboardButton(auto_label, callback_data="auto_menu"))
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
    kb=InlineKeyboardMarkup(row_width=3)
    is_crypto = pair in [p["name"] for p in CRYPTO_PAIRS]
    is_stocks = pair in [p["name"] for p in STOCKS_PAIRS]
    tfs = CRYPTO_TF if is_crypto else (STOCKS_TF if is_stocks else TIMEFRAMES)
    back = "crypto_back" if is_crypto else ("stocks_back" if is_stocks else ("otc_back" if "OTC" in pair else "forex_back"))
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
    txt="⚡ *AI Signal Bot — Pocket Option*\n\nОберіть категорію:"
    if mid:
        try: bot.edit_message_text(txt,cid,mid,parse_mode="Markdown",reply_markup=main_kb(cid)); return
        except: pass
    bot.send_message(cid,txt,parse_mode="Markdown",reply_markup=main_kb(cid))

@bot.message_handler(commands=["start","menu"])
def cmd_start(msg):
    send_main(msg.chat.id)

@bot.message_handler(commands=["stats"])
def cmd_stats(msg):
    bot.send_message(msg.chat.id,stats_text(msg.chat.id),parse_mode="Markdown",reply_markup=main_kb())

@bot.message_handler(commands=["sessions"])
def cmd_sessions(msg):
    bot.send_message(msg.chat.id,sessions_text(),parse_mode="Markdown",reply_markup=main_kb())

def safe_edit(bot, cid, mid, text, markup=None):
    try:
        bot.edit_message_text(text, cid, mid, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        if "not modified" in str(e) or "400" in str(e):
            try:
                bot.edit_message_text(text+" ", cid, mid, parse_mode="Markdown", reply_markup=markup)
            except:
                bot.send_message(cid, text, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(cid, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    cid=call.message.chat.id; mid=call.message.message_id; d=call.data
    bot.answer_callback_query(call.id)
    try:
        if d=="main":
            send_main(cid,mid)
        elif d in ("menu_forex","forex_back"):
            safe_edit(bot,cid,mid,"📈 *FOREX пари*\nОберіть пару:",forex_kb())
        elif d in ("menu_otc","otc_back"):
            safe_edit(bot,cid,mid,"🌙 *OTC пари*\nОберіть пару:",otc_kb())
        elif d in ("menu_crypto","crypto_back"):
            safe_edit(bot,cid,mid,"₿ *Криптовалюти*\nОберіть пару:",crypto_kb())
        elif d in ("menu_stocks","stocks_back"):
            safe_edit(bot,cid,mid,"📊 *Акції*\nОберіть актив:",stocks_kb())
        elif d=="stats":
            safe_edit(bot,cid,mid,stats_text(cid),main_kb())
        elif d=="sessions":
            safe_edit(bot,cid,mid,sessions_text(),main_kb())
        elif d=="ml_status":
            safe_edit(bot,cid,mid,ml_status_text(cid),main_kb(cid))

        elif d=="auto_menu":
            if cid not in subscribers:
                subscribers[cid]={"active":False,"tf":"5","min_conf":85,"last_sent":0}
            safe_edit(bot,cid,mid,auto_menu_text(cid),sub_settings_kb(cid))

        elif d=="auto_start":
            if cid not in subscribers:
                subscribers[cid]={"active":False,"tf":"5","min_conf":85,"last_sent":0}
            subscribers[cid]["active"]=True
            subscribers[cid]["last_sent"]=0
            tf=subscribers[cid].get("tf","5")
            conf=subscribers[cid].get("min_conf",85)
            bot.send_message(cid,
                f"✅ *Автосканування запущено!*\n\n"
                f"⏱ Таймфрейм: *{tf} хв*\n"
                f"🎯 Мін. впевненість: *{conf}%*\n"
                f"📡 Сканую *{len(scan_pairs)}* пар\n\n"
                f"_Перший сигнал надійде через ~{tf} хв_\n"
                f"_Тільки сигнали {conf}%+ впевненості_",
                parse_mode="Markdown",reply_markup=sub_settings_kb(cid))

        elif d=="auto_stop":
            if cid in subscribers:
                subscribers[cid]["active"]=False
            bot.send_message(cid,
                "⏹ *Автосканування зупинено*\n\n"
                "Натисніть ▶️ Запустити щоб увімкнути знову",
                parse_mode="Markdown",reply_markup=main_kb(cid))

        elif d=="auto_tf":
            # Перемикаємо таймфрейм по колу
            tfs=["5","15","30","60"]
            if cid not in subscribers:
                subscribers[cid]={"active":False,"tf":"5","min_conf":85,"last_sent":0}
            cur=subscribers[cid].get("tf","5")
            idx=(tfs.index(cur)+1)%len(tfs) if cur in tfs else 0
            subscribers[cid]["tf"]=tfs[idx]
            safe_edit(bot,cid,mid,auto_menu_text(cid),sub_settings_kb(cid))

        elif d=="auto_conf":
            # Перемикаємо мін. впевненість
            confs=[75,80,85,90,95]
            if cid not in subscribers:
                subscribers[cid]={"active":False,"tf":"5","min_conf":85,"last_sent":0}
            cur=subscribers[cid].get("min_conf",85)
            idx=(confs.index(cur)+1)%len(confs) if cur in confs else 2
            subscribers[cid]["min_conf"]=confs[idx]
            safe_edit(bot,cid,mid,auto_menu_text(cid),sub_settings_kb(cid))

        elif d=="about":
            txt=("ℹ️ *AI Signal Bot v3*\n\n"
                 "• RSI, MACD, EMA 9/21/50\n• Ichimoku Cloud\n• ADX фільтр\n"
                 "• Stochastic, Bollinger Bands\n• MTF аналіз\n• Патерни свічок\n"
                 "• Рівні підтримки/опору\n• Обсяг торгів\n\n"
                 "📡 Yahoo Finance API | UTC+2")
            safe_edit(bot,cid,mid,txt,main_kb())
        elif d.startswith("pair_"):
            pair=d[5:]
            safe_edit(bot,cid,mid,f"⏱ *Таймфрейм для {pair}*\nОберіть:",tf_kb(pair))
        elif d.startswith("tf|"):
            _,pair,tf=d.split("|",2)
            bot.edit_message_text(f"⏳ Аналізую *{pair}*...",cid,mid,parse_mode="Markdown")
            sig=generate_signal(pair,tf,cid=cid)
            # Зберігаємо останній сигнал для ML
            if cid not in last_signal: last_signal[cid]={}
            last_signal[cid]={"pair":pair,"tf":tf,"votes":sig.get("votes_raw",sig["votes"]),"conf":sig["conf"]}
            bot.edit_message_text(format_signal(pair,tf,sig),cid,mid,
                                   parse_mode="Markdown",reply_markup=result_kb(pair,tf))
        elif d.startswith("win|") or d.startswith("loss|"):
            res,pair,tf=d.split("|",2)
            s=get_stats(cid); s["total"]+=1
            is_win = res=="win"
            if is_win:
                s["wins"]+=1; s["streak"]=max(s.get("streak",0)+1,1); emoji="✅ Виграш записано!"
            else:
                s["losses"]+=1; s["streak"]=min(s.get("streak",0)-1,-1); emoji="❌ Програш записано"
            if pair not in s["pairs"]: s["pairs"][pair]={"total":0,"wins":0}
            s["pairs"][pair]["total"]+=1
            if is_win: s["pairs"][pair]["wins"]+=1
            # ML — записати угоду
            ls = last_signal.get(cid,{})
            if ls.get("pair")==pair:
                record_trade(cid, pair, tf, ls.get("votes",[]), ls.get("conf",70), is_win)
            wr=round(s["wins"]/s["total"]*100)
            # Перевірити чи відбулось навчання
            ml_note=""
            if s["total"]>0 and s["total"]%20==0:
                ml_note="\n\n🤖 _ML навчання оновлено! Ваги індикаторів перераховано._"
            bot.send_message(cid,f"{emoji}\n\n📊 WR: *{wr}%* ({s['wins']}W/{s['losses']}L){ml_note}\n\nОберіть дію:",
                             parse_mode="Markdown",reply_markup=main_kb())
    except Exception as e:
        print(f"Помилка: {e}")
        bot.send_message(cid,"Оберіть категорію:",reply_markup=main_kb())

# ══════════════════════════════════════════
#  АВТОСКАНУВАННЯ
# ══════════════════════════════════════════

auto_scan_settings = {}
auto_scan_threads  = {}

def get_scan_settings(cid):
    if cid not in auto_scan_settings:
        auto_scan_settings[cid] = {
            "active": False, "interval": 5,
            "min_conf": 85,  "tf": "5", "min_votes": 7,
        }
    return auto_scan_settings[cid]

def scan_all_pairs(cid, settings):
    tf = settings["tf"]
    min_conf = settings["min_conf"]
    min_votes = settings["min_votes"]
    best = []
    for pair_data in FOREX_PAIRS + OTC_PAIRS:
        try:
            sig = generate_signal(pair_data["name"], tf, cid=cid)
            votes_for = sig["bc"] if sig["is_buy"] else sig["sc"]
            if (sig["conf"] >= min_conf and
                votes_for >= min_votes and
                not sig.get("skip", False) and
                sig.get("adx_ok", False)):
                best.append((pair_data["name"], sig))
        except Exception as e:
            print(f"Scan error {pair_data['name']}: {e}")
    best.sort(key=lambda x: x[1]["conf"], reverse=True)
    return best[:3]

def auto_scan_loop(cid):
    settings = get_scan_settings(cid)
    print(f"🔄 Автосканування запущено для {cid}")
    while settings.get("active", False):
        try:
            interval_sec = settings["interval"] * 60
            tf = settings["tf"]
            tf_name = TIMEFRAMES.get(tf, tf)
            now_str = (datetime.now(timezone.utc)+timedelta(hours=2)).strftime("%H:%M")
            bot.send_message(cid,
                f"🔍 _Сканую {len(FOREX_PAIRS)+len(OTC_PAIRS)} пар на {tf_name}..._",
                parse_mode="Markdown")
            results = scan_all_pairs(cid, settings)
            if not results:
                bot.send_message(cid,
                    f"😴 *{now_str}* — сильних сигналів немає\n"
                    f"_Наступне через {settings['interval']} хв_",
                    parse_mode="Markdown")
            else:
                bot.send_message(cid,
                    f"🎯 *{now_str} — знайдено {len(results)} сигналів!*",
                    parse_mode="Markdown")
                for pair_name, sig in results:
                    if cid not in last_signal:
                        last_signal[cid] = {}
                    last_signal[cid] = {
                        "pair": pair_name, "tf": tf,
                        "votes": sig.get("votes_raw", sig["votes"]),
                        "conf": sig["conf"]
                    }
                    bot.send_message(cid, format_signal(pair_name, tf, sig),
                                     parse_mode="Markdown", reply_markup=result_kb(pair_name, tf))
                    time.sleep(1)
            for _ in range(interval_sec // 60):
                if not settings.get("active", False):
                    break
                time.sleep(60)
        except Exception as e:
            print(f"AutoScan error: {e}")
            time.sleep(30)
    print(f"Автосканування зупинено для {cid}")

def start_auto_scan(cid):
    settings = get_scan_settings(cid)
    settings["active"] = True
    old = auto_scan_threads.get(cid)
    if old and old.is_alive():
        pass
    t = threading.Thread(target=auto_scan_loop, args=(cid,), daemon=True)
    auto_scan_threads[cid] = t
    t.start()

def stop_auto_scan(cid):
    settings = get_scan_settings(cid)
    settings["active"] = False

def auto_scan_menu_kb(cid):
    s = get_scan_settings(cid)
    tf_name = TIMEFRAMES.get(s["tf"], s["tf"])
    kb = InlineKeyboardMarkup(row_width=2)
    if s["active"]:
        kb.add(InlineKeyboardButton("⏹ ЗУПИНИТИ", callback_data="scan_stop"))
    else:
        kb.add(InlineKeyboardButton("▶️ ЗАПУСТИТИ", callback_data="scan_start"))
    kb.add(
        InlineKeyboardButton(f"⏱ ТФ: {tf_name}", callback_data="scan_tf"),
        InlineKeyboardButton(f"🔁 {s['interval']} хв", callback_data="scan_interval"),
    )
    kb.add(
        InlineKeyboardButton(f"🎯 Мін {s['min_conf']}%", callback_data="scan_conf"),
        InlineKeyboardButton(f"✅ Мін {s['min_votes']}/10", callback_data="scan_votes"),
    )
    kb.add(InlineKeyboardButton("◀️ Меню", callback_data="main"))
    return kb

def auto_scan_text(cid):
    s = get_scan_settings(cid)
    status = "🟢 АКТИВНЕ" if s["active"] else "🔴 ВИМКНЕНО"
    tf_name = TIMEFRAMES.get(s["tf"], s["tf"])
    pairs_count = len(FOREX_PAIRS) + len(OTC_PAIRS)
    return (
        f"🔍 *Автосканування*\n\n"
        f"Статус: *{status}*\n"
        f"⏱ Таймфрейм: *{tf_name}*\n"
        f"🔁 Інтервал: *кожні {s['interval']} хв*\n"
        f"🎯 Мін. впевненість: *{s['min_conf']}%*\n"
        f"✅ Мін. підтверджень: *{s['min_votes']}/10*\n\n"
        f"📊 Сканує: *{pairs_count} пар*\n\n"
        f"_Бот надсилає тільки найкращі сигнали автоматично_"
    )

# ══════════════════════════════════════════
#  ЗАПУСК
# ══════════════════════════════════════════
if __name__=="__main__":
    import threading
    print("✅ AI Signal Bot v3 + Автосканування запущено!")
    # Запустити автосканування в окремому потоці
    scan_thread = threading.Thread(target=auto_scan_loop, daemon=True)
    scan_thread.start()
    bot.infinity_polling()
