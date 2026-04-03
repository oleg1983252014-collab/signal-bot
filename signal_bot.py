#!/usr/bin/env python3
"""
SIGNAL BOT — простий бот торгових сигналів для новачків
Forex + OTC + Крипто | Сигнали + Статистика + Авто-сканер
Railway-ready
"""

import os, math, time, json, threading, requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from datetime import datetime, timezone, timedelta
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ══════════════════════════════════════════════════════
# НАЛАШТУВАННЯ — встанови у Railway Variables
# ══════════════════════════════════════════════════════
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TWELVE_KEY = os.environ.get("TWELVE_KEY", "99b3ca01dbdf45ccb2f5968b16af1c82")

if not BOT_TOKEN:
    raise ValueError("❌ Встанови змінну BOT_TOKEN у Railway!")

bot = TeleBot(BOT_TOKEN)   # ← передається рядковий токен зі змінної

TWELVE_URL = "https://api.twelvedata.com"

# ══════════════════════════════════════════════════════
# ПАРИ
# ══════════════════════════════════════════════════════
FOREX_PAIRS = [
    {"name": "EUR/USD", "symbol": "EUR/USD", "d": 5},
    {"name": "GBP/USD", "symbol": "GBP/USD", "d": 5},
    {"name": "USD/JPY", "symbol": "USD/JPY", "d": 3},
    {"name": "AUD/USD", "symbol": "AUD/USD", "d": 5},
    {"name": "USD/CAD", "symbol": "USD/CAD", "d": 5},
    {"name": "USD/CHF", "symbol": "USD/CHF", "d": 5},
    {"name": "EUR/GBP", "symbol": "EUR/GBP", "d": 5},
    {"name": "EUR/JPY", "symbol": "EUR/JPY", "d": 3},
    {"name": "GBP/JPY", "symbol": "GBP/JPY", "d": 3},
    {"name": "NZD/USD", "symbol": "NZD/USD", "d": 5},
]

OTC_PAIRS = [
    {"name": p["name"] + " OTC", "symbol": p["symbol"], "d": p["d"]}
    for p in FOREX_PAIRS[:6]
]

CRYPTO_PAIRS = [
    {"name": "BTC/USD", "symbol": "BTC/USD", "d": 0},
    {"name": "ETH/USD", "symbol": "ETH/USD", "d": 2},
    {"name": "SOL/USD", "symbol": "SOL/USD", "d": 2},
    {"name": "BNB/USD", "symbol": "BNB/USD", "d": 2},
    {"name": "XRP/USD", "symbol": "XRP/USD", "d": 4},
]

ALL_PAIRS = {p["name"]: p for p in FOREX_PAIRS + OTC_PAIRS + CRYPTO_PAIRS}

TIMEFRAMES = {"1": "1хв", "5": "5хв", "15": "15хв", "30": "30хв", "60": "1год"}

# ══════════════════════════════════════════════════════
# ЗБЕРЕЖЕННЯ ДАНИХ
# ══════════════════════════════════════════════════════
STATS_FILE = "stats.json"
SUBS_FILE  = "subscribers.json"
_lock      = threading.Lock()
_subs_lock = threading.Lock()

def _load(path, default):
    try:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    except Exception as e:
        print(f"[WARN] load {path}: {e}")
    return default

def _save(path, data):
    with _lock:
        try:
            with open(path, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARN] save {path}: {e}")

all_stats   = _load(STATS_FILE, {})
_subscribers = set(_load(SUBS_FILE, {}).get("ids", []))

def save_stats():
    _save(STATS_FILE, all_stats)

def save_subs():
    with _subs_lock:
        try:
            with open(SUBS_FILE, "w") as f:
                json.dump({"ids": list(_subscribers)}, f)
        except Exception as e:
            print(f"[WARN] save subs: {e}")

def get_stats(cid):
    k = str(cid)
    if k not in all_stats:
        all_stats[k] = {"total": 0, "wins": 0, "losses": 0}
    return all_stats[k]

# ══════════════════════════════════════════════════════
# КЕШ СВІЧОК
# ══════════════════════════════════════════════════════
_cache = {}
_CACHE_TTL = {"1": 30, "5": 150, "15": 300, "30": 600, "60": 1200}

def get_candles(symbol, tf, count=80):
    key = f"{symbol}_{tf}"
    ttl = _CACHE_TTL.get(tf, 150)
    if key in _cache:
        ts, c, h, l, o = _cache[key]
        if time.time() - ts < ttl:
            return c, h, l, o
    if not TWELVE_KEY:
        return [], [], [], []
    tf_map = {"1": "1min", "5": "5min", "15": "15min", "30": "30min", "60": "1h"}
    interval = tf_map.get(tf, "5min")
    try:
        url = f"{TWELVE_URL}/time_series?symbol={symbol}&interval={interval}&outputsize={count}&apikey={TWELVE_KEY}&format=JSON"
        r = requests.get(url, timeout=12)
        d = r.json()
        if d.get("status") == "error" or not d.get("values"):
            print(f"[API] {symbol}/{interval}: {d.get('message','no data')}")
            return [], [], [], []
        vals = list(reversed(d["values"]))
        c = [float(v["close"]) for v in vals]
        h = [float(v["high"])  for v in vals]
        l = [float(v["low"])   for v in vals]
        o = [float(v["open"])  for v in vals]
        _cache[key] = (time.time(), c, h, l, o)
        return c, h, l, o
    except Exception as e:
        print(f"[API] get_candles {symbol}: {e}")
        return [], [], [], []

def get_price(symbol, fallback=0):
    try:
        r = requests.get(f"{TWELVE_URL}/price?symbol={symbol}&apikey={TWELVE_KEY}", timeout=5)
        p = r.json().get("price")
        if p:
            return float(p)
    except:
        pass
    return fallback

# ══════════════════════════════════════════════════════
# ІНДИКАТОРИ
# ══════════════════════════════════════════════════════
def ema(a, p):
    if len(a) < p: return a[-1] if a else 0
    k = 2 / (p + 1)
    v = sum(a[:p]) / p
    for x in a[p:]: v = x * k + v * (1 - k)
    return v

def calc_rsi(c, p=14):
    if len(c) < p + 1: return 50
    g = [max(c[i] - c[i-1], 0) for i in range(1, len(c))]
    l = [max(c[i-1] - c[i], 0) for i in range(1, len(c))]
    ag = sum(g[-p:]) / p
    al = sum(l[-p:]) / p
    return round(100 - 100 / (1 + ag / al), 1) if al else 100

def calc_macd(c):
    if len(c) < 26: return 0, 0
    k12 = 2/13; k26 = 2/27; k9 = 2/10
    e12 = sum(c[:12]) / 12
    e26 = sum(c[:26]) / 26
    for x in c[12:26]: e12 = x * k12 + e12 * (1 - k12)
    series = []
    for x in c[26:]:
        e12 = x * k12 + e12 * (1 - k12)
        e26 = x * k26 + e26 * (1 - k26)
        series.append(e12 - e26)
    ml = e12 - e26
    if not series: return ml, 0
    sig = sum(series[:9]) / min(9, len(series))
    for mv in series[9:]: sig = mv * k9 + sig * (1 - k9)
    return round(ml, 6), round(ml - sig, 6)

def calc_stoch(c, h, l, p=14):
    if len(c) < p: return 50
    hh = max(h[-p:]); ll = min(l[-p:])
    return round((c[-1] - ll) / (hh - ll) * 100, 1) if hh != ll else 50

def calc_bb(c, p=20):
    if len(c) < p: return 50
    s = sum(c[-p:]) / p
    std = (sum((x - s) ** 2 for x in c[-p:]) / p) ** 0.5
    up = s + 2 * std; lo = s - 2 * std
    return round(max(0, min(100, (c[-1] - lo) / max(1e-9, up - lo) * 100)), 1)

def calc_adx(c, h, l, p=14):
    if len(c) < p + 2: return 0
    trs, pm, nm = [], [], []
    for i in range(1, len(c)):
        trs.append(max(h[i] - l[i], abs(h[i] - c[i-1]), abs(l[i] - c[i-1])))
        up = h[i] - h[i-1]; dn = l[i-1] - l[i]
        pm.append(up if up > dn and up > 0 else 0)
        nm.append(dn if dn > up and dn > 0 else 0)
    atr = sum(trs[-p:]) / p
    if not atr: return 0
    pdi = sum(pm[-p:]) / p / atr * 100
    ndi = sum(nm[-p:]) / p / atr * 100
    return round(abs(pdi - ndi) / max(1e-9, pdi + ndi) * 100)

def calc_atr(c, h, l, p=14):
    if len(c) < 2: return 0
    tr = [max(h[i] - l[i], abs(h[i] - c[i-1]), abs(l[i] - c[i-1])) for i in range(1, len(c))]
    return sum(tr[-p:]) / min(p, len(tr)) if tr else 0

def calc_heikin_ashi(o, c, h, l):
    if len(c) < 3: return 0, ""
    ha_c = [(o[i] + h[i] + l[i] + c[i]) / 4 for i in range(len(c))]
    ha_o = [0] * len(c)
    ha_o[0] = (o[0] + c[0]) / 2
    for i in range(1, len(c)): ha_o[i] = (ha_o[i-1] + ha_c[i-1]) / 2
    ha_h = [max(h[i], ha_o[i], ha_c[i]) for i in range(len(c))]
    ha_l = [min(l[i], ha_o[i], ha_c[i]) for i in range(len(c))]
    bull = sum(1 for i in range(-3, 0) if ha_c[i] > ha_o[i])
    bear = sum(1 for i in range(-3, 0) if ha_c[i] < ha_o[i])
    body = abs(ha_c[-1] - ha_o[-1])
    no_lo = (min(ha_c[-1], ha_o[-1]) - ha_l[-1]) < body * 0.1
    no_hi = (ha_h[-1] - max(ha_c[-1], ha_o[-1])) < body * 0.1
    if bull == 3 and no_lo: return 1, "🔥 HA: 3 бичячі без тіні"
    if bear == 3 and no_hi: return -1, "🔥 HA: 3 ведмежі без тіні"
    if bull >= 2: return 1, f"HA: {bull} бичячі ▲"
    if bear >= 2: return -1, f"HA: {bear} ведмежі ▼"
    if ha_c[-1] > ha_o[-1]: return 1, "HA: бичяча ▲"
    if ha_c[-1] < ha_o[-1]: return -1, "HA: ведмежа ▼"
    return 0, ""

def calc_psar(h, l, af0=0.02, afm=0.2):
    if len(h) < 5: return 0, ""
    bull = l[0] < l[1]
    sar = l[0] if bull else h[0]
    ep  = h[0] if bull else l[0]
    af  = af0
    prev_bull = bull
    for i in range(1, len(h)):
        prev_bull = bull
        sar = sar + af * (ep - sar)
        if bull:
            sar = min(sar, l[i-1], l[i-2] if i >= 2 else l[i-1])
            if l[i] < sar: bull = False; sar = ep; ep = l[i]; af = af0
            elif h[i] > ep: ep = h[i]; af = min(af + af0, afm)
        else:
            sar = max(sar, h[i-1], h[i-2] if i >= 2 else h[i-1])
            if h[i] > sar: bull = True; sar = ep; ep = h[i]; af = af0
            elif l[i] < ep: ep = l[i]; af = min(af + af0, afm)
    fresh = bull != prev_bull
    if fresh and bull:      return 1,  "🔥 PSAR: розворот ▲"
    if fresh and not bull:  return -1, "🔥 PSAR: розворот ▼"
    return (1, "PSAR: бичячий ▲") if bull else (-1, "PSAR: ведмежий ▼")

# ══════════════════════════════════════════════════════
# ГЕНЕРАЦІЯ СИГНАЛУ
# ══════════════════════════════════════════════════════
def _fallback_candles(pair_name, tf):
    """Псевдо-дані коли API недоступний"""
    seed = sum(ord(x) for x in pair_name) + (int(tf) if tf.isdigit() else 5) * 7 + int(time.time() // 300)
    def sr(i):
        v = math.sin(seed * 1.1 + i * 0.7) * 43758.5453
        return v - math.floor(v)
    base = 1.0
    cv = [base]
    hv = [base]; lv = [base]; ov = [base]
    for i in range(1, 80):
        trend = (sr(i+5) - 0.495) * 0.003
        vol   = sr(i+10) * 0.002 + 0.0005
        op = cv[-1]; cl = op * (1 + trend + (sr(i+20) - 0.5) * vol)
        hi = max(op, cl) * (1 + sr(i+30) * 0.001)
        lo = min(op, cl) * (1 - sr(i+40) * 0.001)
        ov.append(op); cv.append(cl); hv.append(hi); lv.append(lo)
    return cv, hv, lv, ov

def generate_signal(pair_name, tf):
    m = ALL_PAIRS.get(pair_name)
    if not m:
        return None
    symbol = m["symbol"]
    c, h, l, o = get_candles(symbol, tf)
    real = len(c) >= 20
    if not real:
        c, h, l, o = _fallback_candles(pair_name, tf)
    live = get_price(symbol) if TWELVE_KEY else (c[-1] if c else 1.0)

    # Індикатори
    rsi       = calc_rsi(c)
    macd, mh  = calc_macd(c)
    e9        = ema(c, 9);  e21 = ema(c, 21);  e50 = ema(c, 50)
    stoch     = calc_stoch(c, h, l)
    bb        = calc_bb(c)
    adx       = calc_adx(c, h, l)
    atr       = calc_atr(c, h, l)
    ha_v, ha_lbl   = calc_heikin_ashi(o, c, h, l)
    psar_v, psar_lbl = calc_psar(h, l)

    # Голосування
    votes = []
    def v(val, lbl, w=1.0):
        votes.append({"v": val, "l": lbl, "w": w})

    # RSI
    if   rsi < 25:  v(1,  f"RSI {rsi} — сильна перепроданість 🔥", 2.5)
    elif rsi > 75:  v(-1, f"RSI {rsi} — сильна перекупленість 🔥", 2.5)
    elif rsi < 40:  v(1,  f"RSI {rsi} — перепроданість", 2.0)
    elif rsi > 60:  v(-1, f"RSI {rsi} — перекупленість", 2.0)
    elif rsi < 48:  v(1,  f"RSI {rsi} — бичачий", 1.0)
    elif rsi > 52:  v(-1, f"RSI {rsi} — ведмежий", 1.0)

    # MACD
    if   macd > 0 and mh > 0:  v(1,  "MACD ▲ зростає", 2.0)
    elif macd < 0 and mh < 0:  v(-1, "MACD ▼ падає", 2.0)
    elif mh > 0:               v(1,  "MACD гіст ▲", 1.0)
    elif mh < 0:               v(-1, "MACD гіст ▼", 1.0)

    # EMA 9/21
    if   e9 > e21 * 1.0002:  v(1,  "EMA9 > EMA21 ▲", 2.0)
    elif e9 < e21 * 0.9998:  v(-1, "EMA9 < EMA21 ▼", 2.0)

    # EMA50
    if   live > e50 * 1.001:  v(1,  "Ціна вище EMA50", 1.5)
    elif live < e50 * 0.999:  v(-1, "Ціна нижче EMA50", 1.5)

    # Stochastic
    if   stoch < 20:  v(1,  f"Stoch {stoch} — перепроданість ✅", 2.0)
    elif stoch > 80:  v(-1, f"Stoch {stoch} — перекупленість ✅", 2.0)
    elif stoch < 45:  v(1,  f"Stoch {stoch} — BUY зона", 1.0)
    elif stoch > 55:  v(-1, f"Stoch {stoch} — SELL зона", 1.0)

    # Bollinger Bands
    if   bb < 10:  v(1,  "BB нижня смуга BUY 🔥", 2.0)
    elif bb > 90:  v(-1, "BB верхня смуга SELL 🔥", 2.0)
    elif bb < 25:  v(1,  f"BB нижня зона {bb}%", 1.0)
    elif bb > 75:  v(-1, f"BB верхня зона {bb}%", 1.0)

    # Heikin Ashi
    if ha_v != 0:
        strong = "🔥" in ha_lbl
        v(ha_v, ha_lbl, 3.5 if strong else 2.5)

    # Parabolic SAR
    if psar_v != 0:
        fresh = "розворот" in psar_lbl
        v(psar_v, psar_lbl, 3.0 if fresh else 2.0)

    # Підрахунок
    buy_w  = sum(x["w"] for x in votes if x["v"] == 1)
    sell_w = sum(x["w"] for x in votes if x["v"] == -1)
    tot    = buy_w + sell_w
    is_buy = buy_w >= sell_w
    ratio  = max(buy_w, sell_w) / max(1e-9, tot)

    # Точність
    adx_b = min(10, adx // 3) if adx >= 20 else -5
    acc = round(55 + ratio * 25 + adx_b)
    acc = min(93, max(60, acc))

    # Штраф за якість даних
    if not real:
        acc = max(55, acc - 12)
    elif "OTC" in pair_name:
        acc = max(58, acc - 8)

    # Сила сигналу
    if   not (adx >= 20) and ratio < 0.65: strength = "⛔ СЛАБКИЙ"; blocked = True
    elif ratio < 0.60:                      strength = "⚠️ Слабкий";  blocked = False
    elif ratio < 0.72:                      strength = "✅ Середній"; blocked = False
    elif ratio < 0.83:                      strength = "🔥 Сильний";  blocked = False
    else:                                   strength = "🔥🔥 Дуже сильний"; blocked = False

    # TP / SL
    d_ = m["d"]
    if atr == 0: atr = live * 0.001
    tp_m = {"1": 1.3, "5": 1.7, "15": 2.0, "30": 2.5, "60": 3.0}.get(tf, 1.7)
    sl_m = {"1": 1.0, "5": 1.2, "15": 1.4, "30": 1.6, "60": 2.0}.get(tf, 1.2)
    tp = round(live + atr * tp_m, d_) if is_buy else round(live - atr * tp_m, d_)
    sl = round(live - atr * sl_m, d_) if is_buy else round(live + atr * sl_m, d_)

    # Топ підтверджуючі
    top = sorted([x for x in votes if x["v"] == (1 if is_buy else -1)], key=lambda x: -x["w"])[:3]

    return {
        "is_buy":   is_buy,
        "acc":      acc,
        "strength": strength,
        "blocked":  blocked,
        "live":     live,
        "tp":       tp,
        "sl":       sl,
        "rr":       round(tp_m / sl_m, 1),
        "adx":      adx,
        "rsi":      rsi,
        "ha_lbl":   ha_lbl,
        "psar_lbl": psar_lbl,
        "top":      top,
        "real":     real,
        "buy_w":    round(buy_w, 1),
        "sell_w":   round(sell_w, 1),
    }

# ══════════════════════════════════════════════════════
# ФОРМАТУВАННЯ СИГНАЛУ
# ══════════════════════════════════════════════════════
def format_signal(pair, tf, d):
    tf_lbl = TIMEFRAMES.get(tf, tf + "хв")
    tf_hold = {"1": 2, "5": 8, "15": 20, "30": 35, "60": 70}
    now_dt = datetime.now(timezone.utc) + timedelta(hours=2)
    try:
        exp = (now_dt + timedelta(minutes=tf_hold.get(tf, 8))).strftime("%H:%M")
    except:
        exp = "—"

    is_buy  = d["is_buy"]
    arrow   = "⬆️" if is_buy else "⬇️"
    dir_txt = "КУПИТИ" if is_buy else "ПРОДАТИ"
    dir_em  = "🟢" if is_buy else "🔴"
    acc     = d["acc"]
    acc_em  = "🔥" if acc >= 85 else "✅" if acc >= 75 else "⚠️"

    top_lines = "\n".join(f"  ✅ {x['l']}" for x in d["top"]) if d["top"] else "  —"

    data_note = ""
    if not d["real"]:
        data_note = "\n⚠️ _Розрахункові дані (API недоступний)_"
    elif "OTC" in pair:
        data_note = "\n🟡 _OTC: синтетичні ціни_"

    # Money management
    if acc >= 85:
        mm = "💰 *MM:* 🔥 Сильний — ставка до 5% депозиту"
    elif acc >= 75:
        mm = "💰 *MM:* ✅ Середній — ставка до 3% депозиту"
    elif acc >= 68:
        mm = "💰 *MM:* ⚠️ Слабкий — ставка до 2% депозиту"
    else:
        mm = "💰 *MM:* ⛔ Пропустити угоду"

    lines = [
        "╔══ ⚡ *SIGNAL BOT* ══╗",
        "",
        f"🏷 *{pair}*  ⏱ {tf_lbl}",
        "",
        f"{dir_em} *{arrow} {dir_txt}*",
        f"Утримувати до: *{exp}*",
        "",
        f"{acc_em} Точність: *{acc}%*  {d['strength']}",
        f"ADX: *{d['adx']}*  BUY {d['buy_w']} / SELL {d['sell_w']}",
        "",
        "📊 *Підтвердження:*",
        top_lines,
        "",
        f"💰 Вхід: `{d['live']}`",
        f"🎯 TP: `{d['tp']}`   🛑 SL: `{d['sl']}`   RR 1:{d['rr']}",
        "",
        mm,
        data_note,
        "",
        "└─────────────────────┘",
        "⚠️ _Не є фінансовою порадою_",
    ]
    return "\n".join(l for l in lines if l is not None)

# ══════════════════════════════════════════════════════
# ГРАФІК
# ══════════════════════════════════════════════════════
def make_chart(pair, tf, c, h, l, o, sig):
    n = min(40, len(c))
    c = c[-n:]; h = h[-n:]; l = l[-n:]; o = o[-n:]
    x = list(range(n))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6),
        gridspec_kw={"height_ratios": [3, 1]}, facecolor="#0d1424")

    ax1.set_facecolor("#0d1424")
    for i in range(n):
        col = "#00e676" if c[i] >= o[i] else "#ff1744"
        ax1.bar(i, abs(c[i] - o[i]), bottom=min(c[i], o[i]), width=0.7, color=col, zorder=3)
        ax1.plot([i, i], [l[i], h[i]], color=col, linewidth=1, zorder=2)

    # EMA
    def ema_arr(data, p):
        if len(data) < p: return [data[0]] * len(data)
        k = 2 / (p + 1); v = sum(data[:p]) / p; res = [v]
        for x in data[p:]: v = x * k + v * (1 - k); res.append(v)
        return ([data[0]] * (p - 1) + res)[-len(data):]

    e9  = ema_arr(c, 9)
    e21 = ema_arr(c, 21)
    ax1.plot(x, e9,  color="#00bcd4", linewidth=1.3, label="EMA9")
    ax1.plot(x, e21, color="#ffca28", linewidth=1.3, label="EMA21")

    # Сигнал
    is_buy = sig["is_buy"]
    rng = max(h[-1] - l[-1], 0.0001)
    ay  = l[-1] - rng * 1.2 if is_buy else h[-1] + rng * 1.2
    ax1.annotate("", xy=(n-1, l[-1] if is_buy else h[-1]), xytext=(n-1, ay),
        arrowprops=dict(arrowstyle="->", color="#00e676" if is_buy else "#ff1744",
                        lw=2.5, mutation_scale=20))
    ax1.text(n-1, ay - rng * 0.6 if is_buy else ay + rng * 0.6,
             f"{'▲ BUY' if is_buy else '▼ SELL'}  {sig['acc']}%",
             color="#00e676" if is_buy else "#ff1744",
             fontsize=10, fontweight="bold", ha="center")

    # TP / SL
    dp = ALL_PAIRS.get(pair, {}).get("d", 5)
    ax1.axhline(sig["tp"], color="#00e676", linewidth=1, linestyle="--", alpha=0.7)
    ax1.axhline(sig["sl"], color="#ff1744", linewidth=1, linestyle="--", alpha=0.7)
    ax1.text(0, sig["tp"], f"TP {sig['tp']:.{dp}f}", color="#00e676", fontsize=8, va="bottom")
    ax1.text(0, sig["sl"], f"SL {sig['sl']:.{dp}f}", color="#ff1744", fontsize=8, va="top")

    tf_lbl = TIMEFRAMES.get(tf, tf + "хв")
    ax1.set_title(f"⚡ SIGNAL BOT  {pair} | {tf_lbl} | {sig['acc']}%",
                  color="#00bcd4", fontsize=12, fontweight="bold", pad=8)
    ax1.legend(loc="upper left", facecolor="#090e1a", labelcolor="white", fontsize=8, framealpha=0.6)
    ax1.tick_params(colors="#6a8ab0"); ax1.yaxis.tick_right()
    for spine in ax1.spines.values(): spine.set_color("#1e3050")

    # RSI panel
    ax2.set_facecolor("#0d1424")
    rsi_vals = []
    for i in range(n):
        sub = c[:i+1]
        rsi_vals.append(calc_rsi(sub) if len(sub) >= 15 else 50)
    ax2.plot(x, rsi_vals, color="#ba68c8", linewidth=1.3)
    ax2.axhline(70, color="#ff1744", linewidth=0.6, linestyle="--", alpha=0.5)
    ax2.axhline(30, color="#00e676", linewidth=0.6, linestyle="--", alpha=0.5)
    ax2.set_ylim(0, 100); ax2.set_ylabel("RSI", color="#ba68c8", fontsize=8)
    ax2.tick_params(colors="#6a8ab0")
    for spine in ax2.spines.values(): spine.set_color("#1e3050")

    plt.tight_layout(pad=0.5)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor="#0d1424", edgecolor="none")
    buf.seek(0); plt.close()
    return buf

# ══════════════════════════════════════════════════════
# АВТО-СКАНЕР
# ══════════════════════════════════════════════════════
def run_scanner(cid, tf="5"):
    scan = FOREX_PAIRS[:6] + OTC_PAIRS[:4] + CRYPTO_PAIRS[:3]
    results = []
    for p in scan:
        try:
            sig = generate_signal(p["name"], tf)
            if sig and sig["acc"] >= 82 and not sig.get("blocked"):
                results.append((p["name"], tf, sig))
        except Exception as e:
            print(f"[SCAN] {p['name']}: {e}")
    results.sort(key=lambda x: -x[2]["acc"])
    if not results:
        bot.send_message(cid, "🔍 Сканування завершено\n\nСильних сигналів не знайдено.\nСпробуй пізніше або інший таймфрейм.")
        return
    bot.send_message(cid, f"🔍 *Знайдено {len(results[:3])} сигнали:*", parse_mode="Markdown")
    for pair, tf2, sig in results[:3]:
        try:
            txt = format_signal(pair, tf2, sig)
            bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=result_kb(pair, tf2))
            time.sleep(0.4)
        except Exception as e:
            print(f"[SCAN SEND] {e}")

def auto_signal_loop():
    """Кожні 5 хвилин шукає сигнали ≥85% і надсилає підписникам"""
    while True:
        time.sleep(300)
        if not _subscribers:
            continue
        scan = FOREX_PAIRS[:6] + OTC_PAIRS[:3] + CRYPTO_PAIRS[:3]
        results = []
        for p in scan:
            try:
                sig = generate_signal(p["name"], "5")
                if sig and sig["acc"] >= 85 and not sig.get("blocked"):
                    results.append((p["name"], "5", sig))
            except Exception as e:
                print(f"[AUTO] {p['name']}: {e}")
        results.sort(key=lambda x: -x[2]["acc"])
        best = results[:2]
        if not best:
            continue
        for cid in list(_subscribers):
            try:
                bot.send_message(cid, "⚡ *Авто-сигнали*", parse_mode="Markdown")
                for pair, tf, sig in best:
                    bot.send_message(cid, format_signal(pair, tf, sig),
                                     parse_mode="Markdown", reply_markup=result_kb(pair, tf))
                    time.sleep(0.3)
            except Exception as e:
                print(f"[AUTO SEND] cid={cid}: {e}")

# ══════════════════════════════════════════════════════
# КЛАВІАТУРИ
# ══════════════════════════════════════════════════════
def main_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📈 Forex",   callback_data="cat_forex"),
        InlineKeyboardButton("🌙 OTC",     callback_data="cat_otc"),
    )
    kb.add(
        InlineKeyboardButton("₿ Крипто",  callback_data="cat_crypto"),
        InlineKeyboardButton("🔍 Сканер", callback_data="scanner"),
    )
    kb.add(
        InlineKeyboardButton("📊 Статистика",    callback_data="stats"),
        InlineKeyboardButton("🔔 Авто-сигнали", callback_data="auto"),
    )
    kb.add(InlineKeyboardButton("ℹ️ Як користуватись", callback_data="help"))
    return kb

def pairs_kb(pairs, back):
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(p["name"], callback_data=f"pair_{p['name']}") for p in pairs])
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data=back))
    return kb

def tf_kb(pair):
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(v, callback_data=f"tf|{pair}|{k}") for k, v in TIMEFRAMES.items()])
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="main"))
    return kb

def result_kb(pair, tf):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Виграш",  callback_data=f"win|{pair}|{tf}"),
        InlineKeyboardButton("❌ Програш", callback_data=f"loss|{pair}|{tf}"),
    )
    kb.add(
        InlineKeyboardButton("🔄 Ще раз",  callback_data=f"tf|{pair}|{tf}"),
        InlineKeyboardButton("🏠 Меню",    callback_data="main"),
    )
    return kb

# ══════════════════════════════════════════════════════
# ХЕНДЛЕРИ
# ══════════════════════════════════════════════════════
def send_main(cid, mid=None):
    txt = (
        "╔══ ⚡ *SIGNAL BOT* ══╗\n\n"
        "Торгові сигнали для:\n"
        "📈 Forex  🌙 OTC  ₿ Крипто\n\n"
        "8 індикаторів:\n"
        "RSI • MACD • EMA 9/21/50\n"
        "Stochastic • BB • ADX\n"
        "Heikin Ashi • Parabolic SAR\n\n"
        "╚══ Оберіть категорію ══╝"
    )
    if mid:
        try:
            bot.edit_message_text(txt, cid, mid, parse_mode="Markdown", reply_markup=main_kb())
            return
        except:
            pass
    bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=main_kb())

def do_signal(cid, mid, pair, tf):
    if pair not in ALL_PAIRS:
        try: bot.edit_message_text("❌ Невідома пара", cid, mid, reply_markup=main_kb())
        except: pass
        return
    tf_lbl = TIMEFRAMES.get(tf, tf + "хв")
    try:
        bot.edit_message_text(f"⟳ Аналізую *{pair}* {tf_lbl}...", cid, mid, parse_mode="Markdown")
    except:
        pass
    sig = None
    try:
        sig = generate_signal(pair, tf)
    except Exception as e:
        print(f"[SIGNAL] {pair}/{tf}: {e}")
    if not sig:
        try:
            bot.edit_message_text("⚠️ Не вдалося отримати сигнал. Спробуй ще раз.",
                                  cid, mid, reply_markup=main_kb())
        except:
            pass
        return

    txt = format_signal(pair, tf, sig)

    # Графік
    chart_buf = None
    try:
        m = ALL_PAIRS[pair]
        c2, h2, l2, o2 = get_candles(m["symbol"], tf)
        if len(c2) >= 20:
            chart_buf = make_chart(pair, tf, c2, h2, l2, o2, sig)
    except Exception as e:
        print(f"[CHART] {e}")

    try:
        bot.delete_message(cid, mid)
    except:
        pass

    try:
        if chart_buf:
            cap = txt if len(txt) <= 1024 else txt[:1020] + "..."
            bot.send_photo(cid, chart_buf, caption=cap,
                           parse_mode="Markdown", reply_markup=result_kb(pair, tf))
            if len(txt) > 1024:
                bot.send_message(cid, txt, parse_mode="Markdown")
        else:
            bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=result_kb(pair, tf))
    except Exception as e:
        print(f"[SEND] {e}")
        try:
            bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=result_kb(pair, tf))
        except:
            pass

@bot.message_handler(commands=["start", "menu"])
def cmd_start(msg):
    send_main(msg.chat.id)

@bot.message_handler(commands=["stats"])
def cmd_stats(msg):
    cid = msg.chat.id
    s = get_stats(cid)
    t = s["total"]; w = s["wins"]; l = s.get("losses", 0)
    wr = round(w / t * 100) if t else 0
    filled = round(wr / 10)
    bar = "▰" * filled + "▱" * (10 - filled)
    bot.send_message(
        cid,
        f"📊 *Твоя статистика*\n\n"
        f"Всього угод: *{t}*\n"
        f"Виграші: *{w}* ✅\n"
        f"Програші: *{l}* ❌\n"
        f"Win Rate: *{wr}%*\n"
        f"`{bar}`",
        parse_mode="Markdown", reply_markup=main_kb()
    )

@bot.message_handler(commands=["scan"])
def cmd_scan(msg):
    bot.send_message(msg.chat.id, "🔍 *Сканую ринок...*", parse_mode="Markdown")
    threading.Thread(target=run_scanner, args=(msg.chat.id,), daemon=True).start()

@bot.message_handler(commands=["auto"])
def cmd_auto(msg):
    cid = msg.chat.id
    if cid in _subscribers:
        _subscribers.discard(cid)
        save_subs()
        bot.send_message(cid, "🔕 *Авто-сигнали вимкнено*\n\n/auto — увімкнути знову",
                         parse_mode="Markdown")
    else:
        _subscribers.add(cid)
        save_subs()
        bot.send_message(
            cid,
            "🔔 *Авто-сигнали увімкнено!*\n\n"
            "Найсильніші сигнали (≥85%) надходитимуть кожні 5 хвилин.\n\n"
            "/auto — вимкнути",
            parse_mode="Markdown"
        )

@bot.callback_query_handler(func=lambda c: True)
def handle_cb(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    d   = call.data
    bot.answer_callback_query(call.id)
    try:
        if d == "main":
            send_main(cid, mid)

        elif d == "cat_forex":
            bot.edit_message_text("📈 *Forex пари*\nОберіть пару:",
                                  cid, mid, parse_mode="Markdown",
                                  reply_markup=pairs_kb(FOREX_PAIRS, "main"))
        elif d == "cat_otc":
            bot.edit_message_text("🌙 *OTC пари*\nОберіть пару:",
                                  cid, mid, parse_mode="Markdown",
                                  reply_markup=pairs_kb(OTC_PAIRS, "main"))
        elif d == "cat_crypto":
            bot.edit_message_text("₿ *Крипто*\nОберіть пару:",
                                  cid, mid, parse_mode="Markdown",
                                  reply_markup=pairs_kb(CRYPTO_PAIRS, "main"))

        elif d == "scanner":
            bot.edit_message_text("🔍 Шукаю найсильніші сигнали...", cid, mid)
            threading.Thread(target=run_scanner, args=(cid,), daemon=True).start()

        elif d == "stats":
            s = get_stats(cid)
            t = s["total"]; w = s["wins"]; l = s.get("losses", 0)
            wr = round(w / t * 100) if t else 0
            filled = round(wr / 10)
            bar = "▰" * filled + "▱" * (10 - filled)
            bot.edit_message_text(
                f"📊 *Твоя статистика*\n\n"
                f"Всього угод: *{t}*\n"
                f"Виграші: *{w}* ✅\n"
                f"Програші: *{l}* ❌\n"
                f"Win Rate: *{wr}%*\n"
                f"`{bar}`",
                cid, mid, parse_mode="Markdown", reply_markup=main_kb()
            )

        elif d == "auto":
            if cid in _subscribers:
                _subscribers.discard(cid)
                save_subs()
                bot.edit_message_text("🔕 *Авто-сигнали вимкнено*",
                                      cid, mid, parse_mode="Markdown", reply_markup=main_kb())
            else:
                _subscribers.add(cid)
                save_subs()
                bot.edit_message_text(
                    "🔔 *Авто-сигнали увімкнено!*\n\nСигнали ≥85% кожні 5 хвилин.",
                    cid, mid, parse_mode="Markdown", reply_markup=main_kb()
                )

        elif d == "help":
            bot.edit_message_text(
                "ℹ️ *Як користуватись:*\n\n"
                "1️⃣ Обери категорію: Forex / OTC / Крипто\n"
                "2️⃣ Обери пару (наприклад EUR/USD)\n"
                "3️⃣ Обери таймфрейм (5хв рекомендовано)\n"
                "4️⃣ Отримай сигнал з графіком\n"
                "5️⃣ Запиши результат ✅/❌\n\n"
                "🔍 *Сканер* — автоматично знаходить найсильніші сигнали\n\n"
                "🔔 *Авто-сигнали* — отримуй сигнали ≥85% кожні 5 хвилин\n\n"
                "📊 *Статистика* — відстежуй свій Win Rate\n\n"
                "⚠️ _Торгуй тільки при точності ≥75%_\n"
                "_Ніколи не ризикуй більше 3-5% депозиту_",
                cid, mid, parse_mode="Markdown", reply_markup=main_kb()
            )

        elif d.startswith("pair_"):
            pair = d[5:]
            if pair not in ALL_PAIRS:
                bot.answer_callback_query(call.id, "❌ Невідома пара")
                return
            bot.edit_message_text(
                f"⏱ *{pair}*\nОберіть таймфрейм:",
                cid, mid, parse_mode="Markdown", reply_markup=tf_kb(pair)
            )

        elif d.startswith("tf|"):
            parts = d.split("|", 2)
            if len(parts) == 3:
                _, pair, tf = parts
                if pair in ALL_PAIRS and tf in TIMEFRAMES:
                    threading.Thread(target=do_signal, args=(cid, mid, pair, tf), daemon=True).start()

        elif d.startswith(("win|", "loss|")):
            parts = d.split("|", 2)
            if len(parts) != 3: return
            res, pair, tf = parts
            s = get_stats(cid)
            s["total"] += 1
            if res == "win":
                s["wins"] += 1
                em = "✅ Виграш записано!"
            else:
                s["losses"] = s.get("losses", 0) + 1
                em = "❌ Програш записано"
            save_stats()
            wr = round(s["wins"] / s["total"] * 100)
            bot.send_message(
                cid,
                f"{em}\n📊 Win Rate: *{wr}%* ({s['wins']}W / {s.get('losses',0)}L)",
                parse_mode="Markdown", reply_markup=main_kb()
            )

    except Exception as e:
        if "not modified" not in str(e):
            print(f"[CB] {e}")
        try:
            bot.send_message(cid, "Оберіть дію:", reply_markup=main_kb())
        except:
            pass

@bot.message_handler(func=lambda m: True)
def cmd_text(msg):
    send_main(msg.chat.id)

# ══════════════════════════════════════════════════════
# ЗАПУСК
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger(__name__)

    print("✅ SIGNAL BOT запущено!")
    logger.info("Запуск авто-сигналів...")
    threading.Thread(target=auto_signal_loop, daemon=True).start()

    # Очищення старих сесій
    for attempt in range(5):
        try:
            bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook видалено")
            break
        except Exception as e:
            logger.warning(f"delete_webhook спроба {attempt+1}: {e}")
            time.sleep(4 + attempt * 2)

    logger.info("Чекаємо 10 сек перед стартом...")
    time.sleep(10)

    # Polling з автоперезапуском
    while True:
        try:
            logger.info("Polling запущено...")
            bot.infinity_polling(
                timeout=20,
                long_polling_timeout=15,
                skip_pending=True,
                none_stop=True,
                allowed_updates=["message", "callback_query"]
            )
        except Exception as e:
            err = str(e)
            logger.error(f"Polling crash: {err}")
            if "409" in err:
                logger.warning("409 Conflict — чекаємо 60 сек...")
                time.sleep(60)
            else:
                time.sleep(10)
            try: bot.close()
            except: pass
            try: bot.delete_webhook(drop_pending_updates=True)
            except: pass
            time.sleep(3)
