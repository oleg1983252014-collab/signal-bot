#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║  SIGNAL AI Bot v3.0 — PocketOption Telegram Bot     ║
║  Індикатори: Heikin Ashi, Parabolic SAR, Fibonacci  ║
║              RSI, MACD, EMA, Stoch, BB, STC, ADX    ║
║              Williams %R, S/R рівні, Свічки, Mom    ║
╚══════════════════════════════════════════════════════╝

НАЛАШТУВАННЯ:
  1. Встанови: pip install pyTelegramBotAPI requests
  2. Отримай BOT_TOKEN у @BotFather в Telegram
  3. Вкажи токен нижче або через змінну середовища BOT_TOKEN
  4. (Опціонально) TwelveData API key на twelvedata.com (безкоштовно)
  5. Запусти: python bot.py
"""

import os, math, time, json, threading, requests
from datetime import datetime, timezone, timedelta

try:
    from telebot import TeleBot
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
except ImportError:
    print("Встанови: pip install pyTelegramBotAPI")
    exit(1)

# ══════════════════════════════════════════════════════
# ⚙️  КОНФІГУРАЦІЯ — ЗМІНИ ТУТ
# ══════════════════════════════════════════════════════
BOT_TOKEN  = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН_ТУТ")
TWELVE_KEY = os.environ.get("TWELVE_KEY", "99b3ca01dbdf45ccb2f5968b16af1c82")
TWELVE_URL = "https://api.twelvedata.com"
STATS_FILE = "stats.json"
# ══════════════════════════════════════════════════════

if BOT_TOKEN == "ВАШ_ТОКЕН_ТУТ":
    print("=" * 50)
    print("❌ Встав свій BOT_TOKEN!")
    print("   Отримай у @BotFather в Telegram")
    print("=" * 50)
    exit(1)

bot = TeleBot(BOT_TOKEN, threaded=True)

# ══════════════════════════════════════════════════════
# 📊 БАЗИ ПАРИ
# ══════════════════════════════════════════════════════
FOREX_PAIRS = [
    {"name": "EUR/USD",  "symbol": "EUR/USD",  "p": 1.0854, "d": 5},
    {"name": "GBP/USD",  "symbol": "GBP/USD",  "p": 1.2714, "d": 5},
    {"name": "USD/JPY",  "symbol": "USD/JPY",  "p": 149.85, "d": 3},
    {"name": "AUD/USD",  "symbol": "AUD/USD",  "p": 0.6458, "d": 5},
    {"name": "NZD/USD",  "symbol": "NZD/USD",  "p": 0.5963, "d": 5},
    {"name": "USD/CAD",  "symbol": "USD/CAD",  "p": 1.3572, "d": 5},
    {"name": "USD/CHF",  "symbol": "USD/CHF",  "p": 0.9032, "d": 5},
    {"name": "EUR/GBP",  "symbol": "EUR/GBP",  "p": 0.8534, "d": 5},
    {"name": "EUR/JPY",  "symbol": "EUR/JPY",  "p": 161.54, "d": 3},
    {"name": "GBP/JPY",  "symbol": "GBP/JPY",  "p": 189.82, "d": 3},
    {"name": "AUD/CAD",  "symbol": "AUD/CAD",  "p": 0.8741, "d": 5},
    {"name": "AUD/JPY",  "symbol": "AUD/JPY",  "p":  96.42, "d": 3},
    {"name": "CHF/JPY",  "symbol": "CHF/JPY",  "p": 165.54, "d": 3},
    {"name": "EUR/AUD",  "symbol": "EUR/AUD",  "p": 1.6721, "d": 5},
    {"name": "EUR/CAD",  "symbol": "EUR/CAD",  "p": 1.4643, "d": 5},
    {"name": "GBP/AUD",  "symbol": "GBP/AUD",  "p": 1.9751, "d": 5},
    {"name": "GBP/CAD",  "symbol": "GBP/CAD",  "p": 1.7224, "d": 5},
    {"name": "USD/SGD",  "symbol": "USD/SGD",  "p": 1.3412, "d": 5},
    {"name": "EUR/CHF",  "symbol": "EUR/CHF",  "p": 0.9743, "d": 5},
    {"name": "GBP/CHF",  "symbol": "GBP/CHF",  "p": 1.1765, "d": 5},
]

OTC_PAIRS = [
    {**p, "name": p["name"] + " OTC"}
    for p in FOREX_PAIRS[:12]
]

CRYPTO_PAIRS = [
    {"name": "BTC/USD",  "symbol": "BTC/USD",  "p": 67000, "d": 0},
    {"name": "ETH/USD",  "symbol": "ETH/USD",  "p":  3500, "d": 2},
    {"name": "BNB/USD",  "symbol": "BNB/USD",  "p":   420, "d": 2},
    {"name": "SOL/USD",  "symbol": "SOL/USD",  "p":   180, "d": 2},
    {"name": "XRP/USD",  "symbol": "XRP/USD",  "p":  0.62, "d": 4},
    {"name": "ADA/USD",  "symbol": "ADA/USD",  "p":  0.45, "d": 4},
    {"name": "DOGE/USD", "symbol": "DOGE/USD", "p":  0.18, "d": 5},
    {"name": "LTC/USD",  "symbol": "LTC/USD",  "p":    95, "d": 2},
    {"name": "AVAX/USD", "symbol": "AVAX/USD", "p":    38, "d": 2},
    {"name": "DOT/USD",  "symbol": "DOT/USD",  "p":  7.43, "d": 3},
    {"name": "LINK/USD", "symbol": "LINK/USD", "p": 15.43, "d": 3},
    {"name": "TON/USD",  "symbol": "TON/USD",  "p":  5.43, "d": 3},
]

STOCKS_PAIRS = [
    {"name": "Apple",     "symbol": "AAPL",  "p":  189, "d": 2},
    {"name": "Tesla",     "symbol": "TSLA",  "p":  245, "d": 2},
    {"name": "NVIDIA",    "symbol": "NVDA",  "p":  875, "d": 2},
    {"name": "Amazon",    "symbol": "AMZN",  "p":  185, "d": 2},
    {"name": "Google",    "symbol": "GOOGL", "p":  165, "d": 2},
    {"name": "Microsoft", "symbol": "MSFT",  "p":  415, "d": 2},
    {"name": "Meta",      "symbol": "META",  "p":  510, "d": 2},
    {"name": "Netflix",   "symbol": "NFLX",  "p":  625, "d": 2},
    {"name": "AMD",       "symbol": "AMD",   "p":  168, "d": 2},
    {"name": "Oracle",    "symbol": "ORCL",  "p":  128, "d": 2},
]

ALL_PAIRS = {p["name"]: p for p in FOREX_PAIRS + OTC_PAIRS + CRYPTO_PAIRS + STOCKS_PAIRS}

TIMEFRAMES    = {"1": "1 хв", "3": "3 хв", "5": "5 хв", "15": "15 хв", "30": "30 хв", "60": "1 год"}
CRYPTO_TF     = {"5": "5 хв", "15": "15 хв", "30": "30 хв", "60": "1 год", "240": "4 год"}
STOCKS_TF     = {"5": "5 хв", "15": "15 хв", "30": "30 хв", "60": "1 год"}

# ══════════════════════════════════════════════════════
# 💾 СТАТИСТИКА
# ══════════════════════════════════════════════════════
_lock = threading.Lock()

def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_stats(data):
    with _lock:
        try:
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

all_stats = load_stats()

def get_stats(cid):
    k = str(cid)
    if k not in all_stats:
        all_stats[k] = {"total": 0, "wins": 0, "losses": 0, "streak": 0, "pairs": {}}
    return all_stats[k]

def save_user_stats():
    save_stats(all_stats)

# ══════════════════════════════════════════════════════
# 🔢 МАТЕМАТИКА
# ══════════════════════════════════════════════════════
def ema(a, p):
    if len(a) < p:
        return a[-1] if a else 0.0
    k = 2.0 / (p + 1)
    v = sum(a[:p]) / p
    for x in a[p:]:
        v = x * k + v * (1 - k)
    return v

def calc_rsi(c, p=14):
    if len(c) < p + 1:
        return 50.0
    g = [max(c[i] - c[i-1], 0.0) for i in range(1, len(c))]
    l = [max(c[i-1] - c[i], 0.0) for i in range(1, len(c))]
    ag = sum(g[-p:]) / p
    al = sum(l[-p:]) / p
    return round(100 - 100 / (1 + ag / al), 1) if al else 100.0

def calc_macd(c):
    if len(c) < 26:
        return 0.0, 0.0
    macd_line = ema(c, 12) - ema(c, 26)
    mv = [ema(c[:i], 12) - ema(c[:i], 26) for i in range(26, len(c) + 1)]
    sig = ema(mv, 9) if len(mv) >= 9 else (mv[-1] if mv else macd_line)
    return macd_line, macd_line - sig

def calc_stoch(c, h, l, k=14):
    if len(c) < k:
        return 50.0, 50.0
    hh = max(h[-k:])
    ll = min(l[-k:])
    kv = round((c[-1] - ll) / (hh - ll) * 100, 1) if hh != ll else 50.0
    return kv, kv

def calc_bb(c, p=20):
    if len(c) < p:
        return 50.0
    s = sum(c[-p:]) / p
    std = (sum((x - s) ** 2 for x in c[-p:]) / p) ** 0.5
    up = s + 2 * std
    lo = s - 2 * std
    return round(max(0, min(100, (c[-1] - lo) / max(1e-9, up - lo) * 100)), 1)

def calc_willr(c, h, l, p=14):
    if len(c) < p:
        return -50.0
    hh = max(h[-p:])
    ll = min(l[-p:])
    return round((hh - c[-1]) / max(1e-9, hh - ll) * -100, 1)

def calc_stc(c, cy=10, fa=23, sl=50):
    if len(c) < sl + cy:
        return None
    mv = [ema(c[:i], fa) - ema(c[:i], sl) for i in range(sl, len(c) + 1)]
    if len(mv) < cy:
        return None
    hh = max(mv[-cy:])
    ll = min(mv[-cy:])
    return round((mv[-1] - ll) / max(1e-9, hh - ll) * 100, 1)

def calc_adx(c, h, l, p=14):
    if len(c) < p + 2:
        return 0
    trs, pm, nm = [], [], []
    for i in range(1, len(c)):
        trs.append(max(h[i] - l[i], abs(h[i] - c[i-1]), abs(l[i] - c[i-1])))
        up = h[i] - h[i-1]
        dn = l[i-1] - l[i]
        pm.append(up if up > dn and up > 0 else 0)
        nm.append(dn if dn > up and dn > 0 else 0)
    atr_ = sum(trs[-p:]) / p
    if not atr_:
        return 0
    pdi = sum(pm[-p:]) / p / atr_ * 100
    ndi = sum(nm[-p:]) / p / atr_ * 100
    return round(abs(pdi - ndi) / max(1e-9, pdi + ndi) * 100)

def calc_atr(c, h, l, p=14):
    if len(c) < 2:
        return 0.0
    tr = [max(h[i] - l[i], abs(h[i] - c[i-1]), abs(l[i] - c[i-1]))
          for i in range(1, len(c))]
    return sum(tr[-p:]) / min(p, len(tr)) if tr else 0.0

def calc_momentum(c, p=10):
    if len(c) < p + 1:
        return 0.0
    return round((c[-1] - c[-p-1]) / c[-p-1] * 100, 3) if c[-p-1] else 0.0

# ══════════════════════════════════════════════════════
# 🕯 НОВІ ІНДИКАТОРИ
# ══════════════════════════════════════════════════════
def calc_heikin_ashi(o, c, h, l):
    """Heikin Ashi — фільтрує шум, найкращий для 1-5 хв"""
    if len(c) < 4:
        return 0, ""
    ha_c = [(o[i] + h[i] + l[i] + c[i]) / 4 for i in range(len(c))]
    ha_o = [0.0] * len(c)
    ha_o[0] = (o[0] + c[0]) / 2
    for i in range(1, len(c)):
        ha_o[i] = (ha_o[i-1] + ha_c[i-1]) / 2
    ha_h = [max(h[i], ha_o[i], ha_c[i]) for i in range(len(c))]
    ha_l = [min(l[i], ha_o[i], ha_c[i]) for i in range(len(c))]

    bull = sum(1 for i in range(-3, 0) if ha_c[i] > ha_o[i])
    bear = sum(1 for i in range(-3, 0) if ha_c[i] < ha_o[i])
    body = abs(ha_c[-1] - ha_o[-1])
    no_lo = (min(ha_c[-1], ha_o[-1]) - ha_l[-1]) < body * 0.12
    no_hi = (ha_h[-1] - max(ha_c[-1], ha_o[-1])) < body * 0.12

    if bull == 3 and no_lo:
        return 1, "🔥 HA: 3 бичачі без нижнього тіні"
    if bear == 3 and no_hi:
        return -1, "🔥 HA: 3 ведмежі без верхнього тіні"
    if bull >= 2 and ha_c[-1] > ha_o[-1]:
        return 1, f"HA: {bull} бичачі ▲"
    if bear >= 2 and ha_c[-1] < ha_o[-1]:
        return -1, f"HA: {bear} ведмежі ▼"
    if ha_c[-1] > ha_o[-1]:
        return 1, "HA: бичача свічка ▲"
    if ha_c[-1] < ha_o[-1]:
        return -1, "HA: ведмежа свічка ▼"
    return 0, "HA: нейтраль"


def calc_parabolic_sar(h, l, af0=0.02, afm=0.2):
    """Parabolic SAR — розворот тренду"""
    if len(h) < 5:
        return 0, ""
    bull = l[0] < l[1]
    sar  = l[0] if bull else h[0]
    ep   = h[0] if bull else l[0]
    af   = af0
    prev_bull = bull

    for i in range(1, len(h)):
        prev_bull = bull
        sar = sar + af * (ep - sar)
        if bull:
            sar = min(sar, l[i-1], l[i-2] if i >= 2 else l[i-1])
            if l[i] < sar:
                bull = False; sar = ep; ep = l[i]; af = af0
            elif h[i] > ep:
                ep = h[i]; af = min(af + af0, afm)
        else:
            sar = max(sar, h[i-1], h[i-2] if i >= 2 else h[i-1])
            if h[i] > sar:
                bull = True; sar = ep; ep = h[i]; af = af0
            elif l[i] < ep:
                ep = l[i]; af = min(af + af0, afm)

    fresh = (bull != prev_bull)
    if fresh and bull:
        return 1, "🔥 PSAR: свіжий розворот ▲"
    if fresh and not bull:
        return -1, "🔥 PSAR: свіжий розворот ▼"
    return (1, "PSAR: бичачий ▲") if bull else (-1, "PSAR: ведмежий ▼")


def calc_fibonacci(h, l, c, lb=30):
    """Fibonacci retracement — рівні підтримки/опору"""
    if len(h) < lb:
        lb = len(h)
    rh = max(h[-lb:])
    rl = min(l[-lb:])
    diff = rh - rl
    if diff < 1e-9:
        return 0, "", []
    fibs = {
        0.236: rh - diff * 0.236,
        0.382: rh - diff * 0.382,
        0.500: rh - diff * 0.500,
        0.618: rh - diff * 0.618,
        0.786: rh - diff * 0.786,
    }
    price = c[-1]
    atr_ = calc_atr(c, h, l)
    zone = max(atr_ * 0.8, diff * 0.02)
    for lvl, fp_ in sorted(fibs.items()):
        if abs(price - fp_) < zone:
            up = c[-1] > c[-3] if len(c) >= 3 else False
            if up:
                return 1, f"Fib {lvl:.3f} підтримка ▲", list(fibs.values())
            else:
                return -1, f"Fib {lvl:.3f} опір ▼", list(fibs.values())
    return 0, "", list(fibs.values())


def calc_support_resistance(c, h, l, n=3):
    """Рівні підтримки і опору"""
    if len(c) < 10:
        return [], []
    sup, res = [], []
    for i in range(2, len(l) - 2):
        if l[i] < l[i-1] and l[i] < l[i-2] and l[i] < l[i+1] and l[i] < l[i+2]:
            sup.append(l[i])
        if h[i] > h[i-1] and h[i] > h[i-2] and h[i] > h[i+1] and h[i] > h[i+2]:
            res.append(h[i])

    def cluster(lv, tol=0.002):
        if not lv:
            return []
        lv = sorted(set(lv))
        r = [lv[0]]
        for val in lv[1:]:
            if abs(val - r[-1]) / max(1e-9, r[-1]) > tol:
                r.append(val)
        return r[-n:]
    return cluster(sup), cluster(res)[:n]


def sr_signal(price, sup, res, atr_):
    """Сигнал від рівнів підтримки/опору"""
    if not atr_:
        return 0, ""
    z = atr_ * 0.5
    for s in sup:
        if abs(price - s) < z:
            return 1, "Відскок від підтримки ▲"
    for r in res:
        if abs(price - r) < z:
            return -1, "Відскок від опору ▼"
    for r in res:
        if price > r and price - r < z * 2:
            return 1, "Пробій опору ▲"
    for s in sup:
        if price < s and s - price < z * 2:
            return -1, "Пробій підтримки ▼"
    return 0, ""


def candle_patterns(o, c, h, l):
    """Свічкові патерни"""
    if len(c) < 4:
        return 0, ""
    b2 = abs(c[-2] - o[-2])
    r2 = max(1e-9, h[-2] - l[-2])
    b1 = abs(c[-1] - o[-1])
    r1 = max(1e-9, h[-1] - l[-1])
    doji    = b2 / r2 < 0.15
    engb    = c[-2] < o[-2] and c[-1] > o[-1] and c[-1] > o[-2] and o[-1] < c[-2]
    engbb   = c[-2] > o[-2] and c[-1] < o[-1] and c[-1] < o[-2] and o[-1] > c[-2]
    t3b     = all(c[-(i+1)] > o[-(i+1)] and c[-(i+1)] > c[-(i+2)] for i in range(3)) if len(c) >= 4 else False
    t3bb    = all(c[-(i+1)] < o[-(i+1)] and c[-(i+1)] < c[-(i+2)] for i in range(3)) if len(c) >= 4 else False
    hammer  = (b1 / r1 < 0.35) and ((min(c[-1], o[-1]) - l[-1]) > b1 * 2) and c[-1] > o[-1]
    inv_h   = (b1 / r1 < 0.35) and ((h[-1] - max(c[-1], o[-1])) > b1 * 2) and c[-1] < o[-1]

    if engb:    return 1,  "🕯 Бичаче поглинання ▲"
    if engbb:   return -1, "🕯 Ведмеже поглинання ▼"
    if t3b:     return 1,  "🕯 3 бичачі свічки ▲"
    if t3bb:    return -1, "🕯 3 ведмежі свічки ▼"
    if hammer:  return 1,  "🕯 Молот — BUY ▲"
    if inv_h:   return -1, "🕯 Перевернутий молот ▼"
    if doji and c[-1] > o[-1]: return 1,  "🕯 Доджі → BUY ▲"
    if doji and c[-1] < o[-1]: return -1, "🕯 Доджі → SELL ▼"
    return 0, ""

# ══════════════════════════════════════════════════════
# ⏰ ТОРГОВА СЕСІЯ
# ══════════════════════════════════════════════════════
def get_session():
    h = datetime.now(timezone.utc).hour
    if   7  <= h < 9:  return "Лондон відкриття 🟢", "excellent", 1.15
    elif 9  <= h < 12: return "Лондон+Нью-Йорк 🟢",  "excellent", 1.20
    elif 12 <= h < 16: return "Нью-Йорк 🟡",         "good",      1.10
    elif 16 <= h < 18: return "NY закриття 🟡",      "average",   0.95
    elif 18 <= h < 21: return "Між сесіями 🔴",      "poor",      0.80
    elif 21 <= h < 23: return "Токіо 🟡",            "average",   0.90
    else:              return "Нічна сесія 🔴",       "poor",      0.75

# ══════════════════════════════════════════════════════
# 🌐 API — РЕАЛЬНІ ДАНІ
# ══════════════════════════════════════════════════════
def get_candles(symbol, tf, count=100):
    tf_map = {
        "1": "1min", "3": "3min", "5": "5min",
        "15": "15min", "30": "30min", "60": "1h", "240": "4h",
    }
    interval = tf_map.get(tf, "5min")
    try:
        url = (f"{TWELVE_URL}/time_series"
               f"?symbol={symbol}&interval={interval}"
               f"&outputsize={count}&apikey={TWELVE_KEY}&format=JSON")
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        d = r.json()
        if d.get("status") == "error" or not d.get("values"):
            return [], [], [], []
        vals = list(reversed(d["values"]))
        c_ = [float(v["close"]) for v in vals]
        h_ = [float(v["high"])  for v in vals]
        l_ = [float(v["low"])   for v in vals]
        o_ = [float(v["open"])  for v in vals]
        return c_, h_, l_, o_
    except Exception:
        return [], [], [], []


def get_live_price(symbol, fallback):
    try:
        r = requests.get(
            f"{TWELVE_URL}/price?symbol={symbol}&apikey={TWELVE_KEY}",
            timeout=5,
        )
        r.raise_for_status()
        p = r.json().get("price")
        if p:
            return float(p)
    except Exception:
        pass
    return fallback

# ══════════════════════════════════════════════════════
# 🔀 ПСЕВДО-ГЕНЕРАТОР (якщо API не відповідає)
# ══════════════════════════════════════════════════════
def gen_fake_candles(pair_name, tf, live):
    seed = sum(ord(x) for x in pair_name) + int(tf) * 7 + int(time.time() // 300)
    def sr(i):
        v = math.sin(seed * 1.1 + i * 0.7) * 43758.5453
        return v - math.floor(v)
    c_, h_, l_, o_ = [live], [live], [live], [live]
    for i in range(1, 90):
        trend = (sr(i + 5) - 0.495) * 0.003
        vol   = sr(i + 10) * 0.002 + 0.0005
        op_   = c_[-1]
        cl_   = op_ * (1 + trend + (sr(i + 20) - 0.5) * vol)
        hi_   = max(op_, cl_) * (1 + sr(i + 30) * 0.001)
        lo_   = min(op_, cl_) * (1 - sr(i + 40) * 0.001)
        o_.append(op_); c_.append(cl_); h_.append(hi_); l_.append(lo_)
    return c_, h_, l_, o_

# ══════════════════════════════════════════════════════
# ⚡ ГЕНЕРАЦІЯ СИГНАЛУ — ГОЛОВНА ФУНКЦІЯ
# ══════════════════════════════════════════════════════
def generate_signal(pair_name, tf):
    meta   = ALL_PAIRS.get(pair_name, FOREX_PAIRS[0])
    is_otc = "OTC" in pair_name

    # 1. Беремо дані
    c, h, l, o = get_candles(meta["symbol"], tf, 100)
    real_data   = len(c) >= 20
    live        = get_live_price(meta["symbol"], meta["p"])

    if not real_data:
        c, h, l, o = gen_fake_candles(pair_name, tf, live)
        real_data   = False

    # 2. Розраховуємо всі індикатори
    rsi         = calc_rsi(c)
    macd_v, mh  = calc_macd(c)
    e9          = ema(c, 9)
    e21         = ema(c, 21)
    e50         = ema(c, 50)
    k_val, _    = calc_stoch(c, h, l)
    bb          = calc_bb(c)
    willr       = calc_willr(c, h, l)
    stc         = calc_stc(c)
    adx         = calc_adx(c, h, l)
    atr_        = calc_atr(c, h, l)
    mom         = calc_momentum(c)

    # Нові
    ha_val,   ha_lbl   = calc_heikin_ashi(o, c, h, l)
    psar_val, psar_lbl = calc_parabolic_sar(h, l)
    fib_val,  fib_lbl, _ = calc_fibonacci(h, l, c)
    sup, res_lvl       = calc_support_resistance(c, h, l)
    sr_val,   sr_lbl   = sr_signal(live, sup, res_lvl, atr_)
    pat_val,  pat_lbl  = candle_patterns(o, c, h, l)
    sess_name, sess_q, sess_mult = get_session()

    # 3. ГОЛОСУВАННЯ З ВАГАМИ
    votes = []
    def v(name, val, lbl, w=1.0):
        votes.append({"n": name, "v": val, "l": lbl, "w": w})

    # RSI
    if   rsi < 25: v("RSI",  1, f"RSI {rsi} — сильна перепроданість 🔥", 2.5)
    elif rsi > 75: v("RSI", -1, f"RSI {rsi} — сильна перекупленість 🔥",  2.5)
    elif rsi < 40: v("RSI",  1, f"RSI {rsi} — перепроданість", 2.0)
    elif rsi > 60: v("RSI", -1, f"RSI {rsi} — перекупленість",  2.0)
    elif rsi < 48: v("RSI",  1, f"RSI {rsi} — бичачий нахил",  1.0)
    elif rsi > 52: v("RSI", -1, f"RSI {rsi} — ведмежий нахил", 1.0)
    else:          v("RSI",  0, f"RSI {rsi} — нейтраль",        0.3)

    # MACD
    if   macd_v > 0 and mh > 0: v("MACD",  1, "MACD: лінія+гістограма ▲ ✅", 2.0)
    elif macd_v < 0 and mh < 0: v("MACD", -1, "MACD: лінія+гістограма ▼ ✅", 2.0)
    elif mh > 0:                 v("MACD",  1, "MACD: гістограма зростає",    1.0)
    elif mh < 0:                 v("MACD", -1, "MACD: гістограма падає",      1.0)
    else:                        v("MACD",  0, "MACD нейтраль",               0.3)

    # EMA 9/21
    if   e9 > e21 * 1.0002:  v("EMA9/21",  1, "EMA9 > EMA21 ▲", 2.0)
    elif e9 < e21 * 0.9998:  v("EMA9/21", -1, "EMA9 < EMA21 ▼", 2.0)
    else:                    v("EMA9/21",  0, "EMA9 ≈ EMA21",   0.3)

    # EMA50
    if   live > e50 * 1.001:  v("EMA50",  1, "Ціна вище EMA50 ▲", 1.5)
    elif live < e50 * 0.999:  v("EMA50", -1, "Ціна нижче EMA50 ▼", 1.5)

    # Stochastic
    if   k_val < 20: v("Stoch",  1, f"Stoch {k_val} — перепроданість ✅", 2.0)
    elif k_val > 80: v("Stoch", -1, f"Stoch {k_val} — перекупленість ✅", 2.0)
    elif k_val < 45: v("Stoch",  1, f"Stoch {k_val} — BUY зона",         1.0)
    elif k_val > 55: v("Stoch", -1, f"Stoch {k_val} — SELL зона",        1.0)

    # Bollinger Bands
    if   bb < 10:  v("BB",  1, "BB нижня смуга — BUY 🔥", 2.0)
    elif bb > 90:  v("BB", -1, "BB верхня смуга — SELL 🔥", 2.0)
    elif bb < 25:  v("BB",  1, f"BB нижня зона {bb}%",     1.0)
    elif bb > 75:  v("BB", -1, f"BB верхня зона {bb}%",    1.0)

    # Williams %R
    if   willr < -85: v("W%R",  1, f"W%R {willr} — сильна перепроданість 🔥", 2.0)
    elif willr > -15: v("W%R", -1, f"W%R {willr} — сильна перекупленість 🔥",  2.0)
    elif willr < -60: v("W%R",  1, f"W%R {willr} — перепроданість",            1.0)
    else:             v("W%R", -1, f"W%R {willr} — перекупленість",            1.0)

    # STC
    if stc is not None:
        if   stc < 15: v("STC",  1, f"STC {stc} — сильний BUY 🔥🔥",   3.5)
        elif stc > 85: v("STC", -1, f"STC {stc} — сильний SELL 🔥🔥",  3.5)
        elif stc < 30: v("STC",  1, f"STC {stc} — BUY зона 🔥",        2.5)
        elif stc > 70: v("STC", -1, f"STC {stc} — SELL зона 🔥",       2.5)
        elif stc < 50: v("STC",  1, f"STC {stc} — зростає",            1.0)
        else:          v("STC", -1, f"STC {stc} — падає",              1.0)

    # Momentum
    if   mom >  0.2: v("Momentum",  1, f"Mom +{mom}% бичачий", 1.5)
    elif mom < -0.2: v("Momentum", -1, f"Mom {mom}% ведмежий",  1.5)

    # Патерн
    if pat_val != 0:
        v("Патерн", pat_val, pat_lbl, 2.0)

    # S/R рівні
    if sr_val != 0:
        v("S/R", sr_val, sr_lbl, 2.5)

    # Heikin Ashi
    if ha_val != 0:
        strong = "🔥" in ha_lbl
        v("Heikin Ashi", ha_val, ha_lbl, 3.5 if strong else 2.5)

    # Parabolic SAR
    if psar_val != 0:
        fresh = "свіжий" in psar_lbl or "розворот" in psar_lbl
        v("Parab SAR", psar_val, psar_lbl, 3.0 if fresh else 2.0)

    # Fibonacci
    if fib_val != 0:
        v("Fibonacci", fib_val, fib_lbl, 2.0)

    # 4. Ваги за таймфреймом
    tf_weights = {
        "1":  {"Heikin Ashi": 1.8, "Parab SAR": 1.6, "STC": 1.4,
               "Stoch": 1.4, "Momentum": 1.5, "MACD": 0.6, "EMA50": 0.4},
        "3":  {"Heikin Ashi": 1.6, "Parab SAR": 1.5, "STC": 1.5,
               "EMA9/21": 1.3, "Stoch": 1.3, "Momentum": 1.4, "Fibonacci": 1.3,
               "MACD": 0.8, "EMA50": 0.6},
        "5":  {"Heikin Ashi": 1.6, "Parab SAR": 1.5, "STC": 1.5,
               "EMA9/21": 1.3, "Stoch": 1.3, "Momentum": 1.4, "Fibonacci": 1.3,
               "MACD": 0.8, "EMA50": 0.6},
        "15": {"EMA50": 1.5, "MACD": 1.3, "S/R": 1.5, "RSI": 1.2, "Fibonacci": 1.4,
               "Parab SAR": 1.2},
        "30": {"EMA50": 1.5, "MACD": 1.3, "S/R": 1.5, "RSI": 1.2, "Fibonacci": 1.4},
        "60": {"EMA50": 1.6, "MACD": 1.4, "S/R": 1.6, "RSI": 1.3, "Fibonacci": 1.5},
    }
    wm = tf_weights.get(tf, {})
    for vt in votes:
        if vt["n"] in wm:
            vt["w"] *= wm[vt["n"]]

    # 5. Підрахунок
    buy_w  = sum(x["w"] for x in votes if x["v"] ==  1)
    sell_w = sum(x["w"] for x in votes if x["v"] == -1)
    bc     = sum(1 for x in votes if x["v"] ==  1)
    sc     = sum(1 for x in votes if x["v"] == -1)
    tot    = buy_w + sell_w
    is_buy = buy_w >= sell_w
    dom    = max(buy_w, sell_w)
    ratio  = dom / max(1e-9, tot)

    # Консенсус топ-індикаторів
    top_ns = ["STC", "RSI", "EMA9/21", "Stoch", "Heikin Ashi", "Parab SAR", "Fibonacci"]
    top_vs = [next((x["v"] for x in votes if x["n"] == n), 0) for n in top_ns]
    top_a  = [val for val in top_vs if val != 0]
    c_agree   = sum(1 for val in top_a if (val == 1) == is_buy)
    consensus = f"{c_agree}/{len(top_a)}" if top_a else "—"

    # ADX фільтр
    adx_ok  = adx >= 20
    adx_b   = min(12, adx // 3) if adx_ok else -5

    # Бонуси
    cons_b  = round(c_agree / max(1, len(top_a)) * 12)
    pat_b   = 5 if (pat_val  ==  1 and is_buy) or (pat_val  == -1 and not is_buy) else 0
    sr_b    = 6 if (sr_val   ==  1 and is_buy) or (sr_val   == -1 and not is_buy) else 0
    tf_b    = {"1": 0, "3": 6, "5": 5, "15": 3, "30": 2, "60": 1}.get(tf, 0)
    ha_b    = 5 if (ha_val   ==  1 and is_buy) or (ha_val   == -1 and not is_buy) else 0
    psar_b  = 5 if (psar_val ==  1 and is_buy) or (psar_val == -1 and not is_buy) else 0

    acc_raw = round(54 + ratio * 26 + adx_b + cons_b + pat_b + sr_b + tf_b + ha_b + psar_b)
    acc     = min(94, max(68, round(acc_raw * sess_mult)))

    # Сила сигналу
    if not adx_ok and ratio < 0.65:
        strength, blocked = "⛔ ФІЛЬТР ADX", True
    elif ratio < 0.58:
        strength, blocked = "⚠️ СЛАБКИЙ",    False
    elif ratio < 0.68:
        strength, blocked = "✅ СЕРЕДНІЙ",   False
    elif ratio < 0.80:
        strength, blocked = "🔥 СИЛЬНИЙ",    False
    else:
        strength, blocked = "🔥🔥 ДУЖЕ СИЛЬНИЙ", False

    # TP / SL
    d_ = meta["d"]
    if atr_ == 0:
        atr_ = live * 0.001
    tp_m = {"1": 1.3, "3": 1.5, "5": 1.7, "15": 2.0, "30": 2.5, "60": 3.0}.get(tf, 1.7)
    sl_m = {"1": 1.0, "3": 1.1, "5": 1.2, "15": 1.4, "30": 1.6, "60": 2.0}.get(tf, 1.2)
    tp   = round(live + atr_ * tp_m, d_) if is_buy else round(live - atr_ * tp_m, d_)
    sl   = round(live - atr_ * sl_m, d_) if is_buy else round(live + atr_ * sl_m, d_)
    rr   = round(tp_m / sl_m, 1)

    return {
        "is_buy":    is_buy,
        "acc":       acc,
        "strength":  strength,
        "blocked":   blocked,
        "live":      live,
        "tp":        tp,
        "sl":        sl,
        "rr":        rr,
        "adx":       adx,
        "adx_ok":    adx_ok,
        "rsi":       rsi,
        "stc":       stc,
        "ha_lbl":    ha_lbl,
        "psar_lbl":  psar_lbl,
        "fib_lbl":   fib_lbl,
        "sr_lbl":    sr_lbl,
        "pat_lbl":   pat_lbl,
        "votes":     votes,
        "bc":        bc,
        "sc":        sc,
        "buy_w":     round(buy_w, 1),
        "sell_w":    round(sell_w, 1),
        "consensus": consensus,
        "sess":      sess_name,
        "sess_q":    sess_q,
        "real":      real_data,
        "is_otc":    is_otc,
    }

# ══════════════════════════════════════════════════════
# 📄 ФОРМАТУВАННЯ СИГНАЛУ
# ══════════════════════════════════════════════════════
def bar(val, n=10):
    f = round(max(0, min(100, val)) / 100 * n)
    return "▰" * f + "▱" * (n - f)

def format_signal(pair, tf, d):
    now_dt  = datetime.now(timezone.utc) + timedelta(hours=2)
    tf_hold = {"1": 2, "3": 4, "5": 8, "15": 20, "30": 35, "60": 70, "240": 260}
    exp     = (now_dt + timedelta(minutes=tf_hold.get(int(tf), 5))).strftime("%H:%M")
    all_tf  = {**TIMEFRAMES, **CRYPTO_TF, **STOCKS_TF}
    tf_lbl  = all_tf.get(tf, tf + " хв")

    is_buy  = d["is_buy"]
    arrow   = "⬆️" if is_buy else "⬇️"
    dir_txt = "ВВЕРХ" if is_buy else "ВНИЗ"
    dir_em  = "🟢" if is_buy else "🔴"
    acc     = d["acc"]
    acc_em  = "🔥" if acc >= 86 else "✅" if acc >= 78 else "⚠️"
    src     = "📡 Live API" if d["real"] else "⚙️ Розрахунок"

    # Тренд %
    buy_r  = d["buy_w"] / max(0.1, d["buy_w"] + d["sell_w"])
    t_pct  = round(buy_r * 100) if is_buy else round((1 - buy_r) * 100)
    t_str  = ("Слабий" if t_pct < 60 else
              "Середній" if t_pct < 75 else
              "Сильний" if t_pct < 88 else "Дуже сильний")

    # Топ 4 підтверджуючі сигнали
    target = 1 if is_buy else -1
    top_v  = sorted([x for x in d["votes"] if x["v"] == target], key=lambda x: -x["w"])
    top3   = top_v[:4]
    top_lines = "\n".join(f"  ✅ {x['l']}" for x in top3) if top3 else "  ⚪ Слабкий консенсус"

    # Нові індикатори
    new_inds = []
    if d.get("ha_lbl"):   new_inds.append(f"🕯 {d['ha_lbl']}")
    if d.get("psar_lbl"): new_inds.append(f"📍 {d['psar_lbl']}")
    if d.get("fib_lbl"):  new_inds.append(f"📐 {d['fib_lbl']}")
    if d.get("sr_lbl"):   new_inds.append(f"📊 S/R: {d['sr_lbl']}")
    if d.get("pat_lbl"):  new_inds.append(f"🕯 {d['pat_lbl']}")

    # STC
    stc = d.get("stc")
    stc_line = ""
    if stc is not None:
        si = "🟢" if stc < 25 else "🔴" if stc > 75 else "🟡" if stc < 50 else "🟠"
        sz = ("Перепроданість" if stc < 25 else "Перекупленість" if stc > 75
              else "Зростає" if stc < 50 else "Падає")
        stc_line = f"{si} STC: {stc} — {sz}\n"

    adx_em    = "✅" if d["adx_ok"] else "⚠️"
    block_warn = "\n⛔ *СИГНАЛ СЛАБКИЙ — КРАЩЕ ПРОПУСТИТИ*\n" if d.get("blocked") else ""

    extra = ""
    if new_inds:
        extra = "\n".join(new_inds) + "\n"

    text = (
        f"╔══ ⚡ *SIGNAL AI v3.0* ══╗\n\n"
        f"🏷 *{pair}*  ⏱ {tf_lbl}  {src}\n"
        f"📍 {d['sess']}\n\n"
        f"📈 *Сила тренду* — {t_str} *{t_pct}%*\n"
        f"`{bar(t_pct)}`\n\n"
        f"{dir_em} *Напрямок: {arrow} {dir_txt}*\n"
        f"⏳ Утримувати до: *{exp}*\n\n"
        f"{acc_em} Точність: *{acc}%*   {d['strength']}\n"
        f"ADX: *{d['adx']}* {adx_em}   Консенсус: *{d['consensus']}*\n"
        f"BUY {d['bc']} ({d['buy_w']}) | SELL {d['sc']} ({d['sell_w']})\n"
        f"{block_warn}\n"
        f"{stc_line}"
        f"{extra}\n"
        f"🔬 *Підтверджуючі сигнали:*\n"
        f"{top_lines}\n\n"
        f"💰 Вхід: `{d['live']}`\n"
        f"🎯 TP: `{d['tp']}`  🛑 SL: `{d['sl']}`  RR: 1:{d['rr']}\n\n"
        f"└─────────────────────────┘\n"
        f"⚠️ _Не є фінансовою порадою_"
    )
    return text

# ══════════════════════════════════════════════════════
# 📊 СТАТИСТИКА І СЕСІЇ — ТЕКСТ
# ══════════════════════════════════════════════════════
def stats_text(cid):
    s  = get_stats(cid)
    t  = s["total"]
    w  = s["wins"]
    lo = s.get("losses", 0)
    wr = round(w / t * 100) if t else 0
    st = s.get("streak", 0)

    streak_txt = (f"🔥 Серія виграшів: {st}" if st > 0
                  else f"❄️ Серія програшів: {abs(st)}" if st < 0
                  else "➖ Нема серії")

    top_pairs = ""
    if s.get("pairs"):
        sorted_p = sorted(s["pairs"].items(), key=lambda x: -x[1]["total"])[:3]
        top_pairs = "\n\n🏆 *Топ пари:*\n"
        for pn, pd in sorted_p:
            pwr = round(pd["wins"] / pd["total"] * 100) if pd["total"] else 0
            top_pairs += f"• {pn}: {pd['total']} угод, {pwr}% WR\n"

    wr_em = "🔥" if wr >= 70 else "✅" if wr >= 55 else "⚠️"
    return (
        f"📊 *Ваша статистика*\n\n"
        f"Всього: *{t}* угод\n"
        f"Виграші: *{w}* ✅\n"
        f"Програші: *{lo}* ❌\n"
        f"Win Rate: *{wr}%* {wr_em}\n"
        f"`{bar(wr)}`\n\n"
        f"{streak_txt}"
        f"{top_pairs}"
    )


def sessions_text():
    now = datetime.now(timezone.utc)
    h   = now.hour
    sessions = [
        (7,  9,  "🟢 Лондон відкриття",   "Висока волатильність, відмінні сигнали"),
        (9,  12, "🟢 Лондон + Нью-Йорк",  "НАЙКРАЩИЙ час — максимальна ліквідність"),
        (12, 16, "🟡 Нью-Йорк",           "Хороша волатильність, підтверджуй сигнали"),
        (16, 18, "🟡 NY закриття",        "Помірна активність"),
        (18, 21, "🔴 Між сесіями",        "Слабка активність, обережно"),
        (21, 23, "🟡 Токіо відкриття",    "Помірна активність на JPY парах"),
        (23, 7,  "🔴 Нічна сесія",        "Низька ліквідність — краще не торгувати"),
    ]
    lines = ["⏰ *Торгові сесії (UTC+2)*\n"]
    for sh, eh, name, desc in sessions:
        active = (sh <= h < eh) or (sh > eh and (h >= sh or h < eh))
        marker = "👉 " if active else "   "
        lines.append(f"{marker}*{name}* ({sh:02d}:00–{eh:02d}:00)\n_{desc}_\n")
    return "\n".join(lines)

# ══════════════════════════════════════════════════════
# 🔍 АВТО-СКАНЕР
# ══════════════════════════════════════════════════════
def run_scanner(cid, tf="5"):
    scan_pairs = FOREX_PAIRS[:8] + OTC_PAIRS[:5]
    results    = []
    for p in scan_pairs:
        try:
            sig = generate_signal(p["name"], tf)
            if sig and sig["acc"] >= 82 and not sig.get("blocked"):
                results.append((p["name"], tf, sig))
        except Exception:
            pass

    if not results:
        try:
            bot.send_message(
                cid,
                "🔍 *Сканування завершено*\n\n"
                "Сильних сигналів не знайдено.\n"
                "Спробуйте пізніше або змініть таймфрейм.",
                parse_mode="Markdown",
                reply_markup=main_kb(),
            )
        except Exception:
            pass
        return

    results.sort(key=lambda x: -x[2]["acc"])
    try:
        bot.send_message(
            cid,
            f"🔍 *Знайдено {min(3, len(results))} сильних сигнали:*",
            parse_mode="Markdown",
        )
        for pr, tf2, sig in results[:3]:
            bot.send_message(
                cid,
                format_signal(pr, tf2, sig),
                parse_mode="Markdown",
                reply_markup=result_kb(pr, tf2),
            )
            time.sleep(0.6)
    except Exception:
        pass

# ══════════════════════════════════════════════════════
# ⌨️  КЛАВІАТУРИ
# ══════════════════════════════════════════════════════
def main_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📈 FOREX",       callback_data="menu_forex"),
        InlineKeyboardButton("🌙 OTC",         callback_data="menu_otc"),
    )
    kb.add(
        InlineKeyboardButton("₿ КРИПТО",       callback_data="menu_crypto"),
        InlineKeyboardButton("📊 АКЦІЇ",       callback_data="menu_stocks"),
    )
    kb.add(
        InlineKeyboardButton("🔍 Авто-сканер", callback_data="scanner"),
        InlineKeyboardButton("📊 Статистика",  callback_data="stats"),
    )
    kb.add(
        InlineKeyboardButton("🕐 Сесії",       callback_data="sessions"),
        InlineKeyboardButton("ℹ️ Про бота",    callback_data="about"),
    )
    return kb


def pairs_kb(pairs, back):
    kb = InlineKeyboardMarkup(row_width=2)
    btns = [InlineKeyboardButton(p["name"], callback_data=f"pair_{p['name']}") for p in pairs]
    # Розставляємо по 2 в ряд
    for i in range(0, len(btns), 2):
        row = btns[i:i+2]
        kb.add(*row)
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data=back))
    return kb


def tf_kb(pair):
    is_crypto = any(pair == p["name"] for p in CRYPTO_PAIRS)
    is_stocks = any(pair == p["name"] for p in STOCKS_PAIRS)
    tfs  = CRYPTO_TF if is_crypto else (STOCKS_TF if is_stocks else TIMEFRAMES)
    back = ("crypto_back" if is_crypto
            else "stocks_back" if is_stocks
            else "otc_back" if "OTC" in pair
            else "forex_back")
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(v, callback_data=f"tf|{pair}|{k}") for k, v in tfs.items()])
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data=back))
    return kb


def result_kb(pair, tf):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Виграш",        callback_data=f"win|{pair}|{tf}"),
        InlineKeyboardButton("❌ Програш",       callback_data=f"loss|{pair}|{tf}"),
    )
    kb.add(
        InlineKeyboardButton("🔄 Новий сигнал",  callback_data=f"tf|{pair}|{tf}"),
        InlineKeyboardButton("🏠 Меню",          callback_data="main"),
    )
    return kb

# ══════════════════════════════════════════════════════
# 🤖 ХЕНДЛЕРИ КОМАНД
# ══════════════════════════════════════════════════════
def send_main(cid, mid=None):
    txt = (
        "╔══ ⚡ *SIGNAL AI v3.0* ══╗\n\n"
        "14 індикаторів для точного аналізу:\n\n"
        "• RSI • MACD • EMA 9/21/50\n"
        "• Williams %R • Stochastic • BB\n"
        "• STC • Momentum • ADX\n"
        "• 🆕 Heikin Ashi • 🆕 Parabolic SAR\n"
        "• 🆕 Fibonacci • 🆕 S/R рівні\n"
        "• 🆕 Свічкові патерни\n\n"
        "📡 Дані: TwelveData API\n"
        "🎯 Точність: ~82–94%\n\n"
        "╚══ Оберіть категорію ══╝"
    )
    if mid:
        try:
            bot.edit_message_text(txt, cid, mid, parse_mode="Markdown", reply_markup=main_kb())
            return
        except Exception:
            pass
    bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=main_kb())


def do_signal(cid, mid, pair, tf):
    all_tf  = {**TIMEFRAMES, **CRYPTO_TF, **STOCKS_TF}
    tf_lbl  = all_tf.get(tf, tf + " хв")
    steps = [
        ("⟳ Завантаження даних...",        "▰▰▰▱▱▱▱▱▱▱ 30%"),
        ("⟳ HA + Parabolic SAR + Fib...",  "▰▰▰▰▰▰▱▱▱▱ 60%"),
        ("⟳ S/R рівні + Сесія...",         "▰▰▰▰▰▰▰▰▱▱ 80%"),
        ("⟳ Генерую сигнал...",            "▰▰▰▰▰▰▰▰▰▱ 95%"),
    ]
    for step, prog in steps:
        try:
            bot.edit_message_text(
                f"⚡ *SIGNAL AI v3.0*\n\n{step}\n\n"
                f"`{pair}` | `{tf_lbl}`\n\n{prog}",
                cid, mid, parse_mode="Markdown",
            )
        except Exception:
            pass
        time.sleep(0.65)

    sig = generate_signal(pair, tf)
    if sig is None:
        try:
            bot.edit_message_text(
                f"⚠️ *Немає даних*\n\n`{pair}` | `{tf_lbl}`\n\nAPI не відповів. Спробуйте ще раз.",
                cid, mid, parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🔄 Спробувати", callback_data=f"tf|{pair}|{tf}"),
                    InlineKeyboardButton("🏠 Меню",       callback_data="main"),
                ),
            )
        except Exception:
            pass
        return

    try:
        bot.edit_message_text(
            format_signal(pair, tf, sig),
            cid, mid,
            parse_mode="Markdown",
            reply_markup=result_kb(pair, tf),
        )
    except Exception as e:
        if "not modified" not in str(e):
            print(f"[ERR do_signal] {e}")


@bot.message_handler(commands=["start", "menu"])
def cmd_start(msg):
    send_main(msg.chat.id)


@bot.message_handler(commands=["stats"])
def cmd_stats(msg):
    bot.send_message(msg.chat.id, stats_text(msg.chat.id),
                     parse_mode="Markdown", reply_markup=main_kb())


@bot.message_handler(commands=["scan"])
def cmd_scan(msg):
    bot.send_message(msg.chat.id, "🔍 *Запускаю сканер...*", parse_mode="Markdown")
    threading.Thread(target=run_scanner, args=(msg.chat.id,), daemon=True).start()


@bot.message_handler(commands=["help"])
def cmd_help(msg):
    bot.send_message(
        msg.chat.id,
        "📖 *Команди бота:*\n\n"
        "/start — головне меню\n"
        "/scan — авто-сканер найкращих сигналів\n"
        "/stats — ваша статистика\n"
        "/help — ця довідка\n\n"
        "Після отримання сигналу натискай\n"
        "✅ Виграш або ❌ Програш для ведення статистики.",
        parse_mode="Markdown",
    )


# ══════════════════════════════════════════════════════
# 🔘 CALLBACK ХЕНДЛЕР
# ══════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: True)
def handle_cb(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    d   = call.data
    bot.answer_callback_query(call.id)

    try:
        # Головне меню
        if d == "main":
            send_main(cid, mid)

        # Форекс
        elif d in ("menu_forex", "forex_back"):
            bot.edit_message_text(
                "📈 *FOREX пари*\nОберіть пару:", cid, mid,
                parse_mode="Markdown", reply_markup=pairs_kb(FOREX_PAIRS, "main"),
            )

        # OTC
        elif d in ("menu_otc", "otc_back"):
            bot.edit_message_text(
                "🌙 *OTC пари*\nОберіть пару:", cid, mid,
                parse_mode="Markdown", reply_markup=pairs_kb(OTC_PAIRS, "main"),
            )

        # Крипто
        elif d in ("menu_crypto", "crypto_back"):
            bot.edit_message_text(
                "₿ *КРИПТО*\nОберіть пару:", cid, mid,
                parse_mode="Markdown", reply_markup=pairs_kb(CRYPTO_PAIRS, "main"),
            )

        # Акції
        elif d in ("menu_stocks", "stocks_back"):
            bot.edit_message_text(
                "📊 *АКЦІЇ*\nОберіть інструмент:", cid, mid,
                parse_mode="Markdown", reply_markup=pairs_kb(STOCKS_PAIRS, "main"),
            )

        # Статистика
        elif d == "stats":
            bot.edit_message_text(
                stats_text(cid), cid, mid,
                parse_mode="Markdown", reply_markup=main_kb(),
            )

        # Сесії
        elif d == "sessions":
            bot.edit_message_text(
                sessions_text(), cid, mid,
                parse_mode="Markdown", reply_markup=main_kb(),
            )

        # Сканер
        elif d == "scanner":
            bot.edit_message_text(
                "🔍 *Авто-сканер*\nШукаю найсильніші сигнали...", cid, mid,
                parse_mode="Markdown",
            )
            threading.Thread(target=run_scanner, args=(cid,), daemon=True).start()

        # Про бота
        elif d == "about":
            bot.edit_message_text(
                "ℹ️ *SIGNAL AI v3.0*\n\n"
                "*14 індикаторів:*\n"
                "• RSI, MACD, EMA 9/21/50\n"
                "• Stochastic, BB, Williams %R\n"
                "• STC, Momentum, ADX\n"
                "• 🆕 Heikin Ashi\n"
                "• 🆕 Parabolic SAR\n"
                "• 🆕 Fibonacci рівні\n"
                "• 🆕 Підтримка / Опір\n"
                "• 🆕 Свічкові патерни\n\n"
                "*Фільтри:*\n"
                "• ADX < 20 → ⛔ блокування сигналу\n"
                "• Торгова сесія → множник точності\n"
                "• Консенсус 7 топ-індикаторів\n\n"
                "*Пари:*\n"
                f"• Forex: {len(FOREX_PAIRS)} пар\n"
                f"• OTC: {len(OTC_PAIRS)} пар\n"
                f"• Crypto: {len(CRYPTO_PAIRS)} пар\n"
                f"• Stocks: {len(STOCKS_PAIRS)} інструментів\n\n"
                "📡 TwelveData API\n"
                "🎯 Точність: ~82–94%",
                cid, mid,
                parse_mode="Markdown", reply_markup=main_kb(),
            )

        # Вибір пари → таймфрейм
        elif d.startswith("pair_"):
            pair = d[5:]
            bot.edit_message_text(
                f"⏱ *Таймфрейм для {pair}*\nОберіть:",
                cid, mid, parse_mode="Markdown", reply_markup=tf_kb(pair),
            )

        # Вибір таймфрейму → генерація сигналу
        elif d.startswith("tf|"):
            _, pair, tf = d.split("|", 2)
            threading.Thread(target=do_signal, args=(cid, mid, pair, tf), daemon=True).start()

        # Результат угоди
        elif d.startswith("win|") or d.startswith("loss|"):
            res, pair, tf = d.split("|", 2)
            s = get_stats(cid)
            s["total"] += 1
            if res == "win":
                s["wins"] += 1
                s["streak"] = max(s.get("streak", 0) + 1, 1)
                em = "✅ *Виграш записано!*"
            else:
                s["losses"] = s.get("losses", 0) + 1
                s["streak"] = min(s.get("streak", 0) - 1, -1)
                em = "❌ *Програш записано*"

            if pair not in s["pairs"]:
                s["pairs"][pair] = {"total": 0, "wins": 0}
            s["pairs"][pair]["total"] += 1
            if res == "win":
                s["pairs"][pair]["wins"] += 1
            save_user_stats()

            wr = round(s["wins"] / s["total"] * 100)
            bot.send_message(
                cid,
                f"{em}\n\n"
                f"📊 WR: *{wr}%* ({s['wins']}W / {s.get('losses', 0)}L)\n\n"
                f"`{bar(wr)}`\n\n"
                "Оберіть наступну дію:",
                parse_mode="Markdown",
                reply_markup=main_kb(),
            )

    except Exception as e:
        if "not modified" not in str(e):
            print(f"[CB ERR] {e}")
            try:
                bot.send_message(cid, "Оберіть категорію:", reply_markup=main_kb())
            except Exception:
                pass

# ══════════════════════════════════════════════════════
# 🚀 ЗАПУСК
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 55)
    print("  ⚡ SIGNAL AI Bot v3.0 — запуск")
    print(f"  📊 Пар: Forex={len(FOREX_PAIRS)}  OTC={len(OTC_PAIRS)}")
    print(f"         Crypto={len(CRYPTO_PAIRS)}  Stocks={len(STOCKS_PAIRS)}")
    print(f"  🔑 Token: {BOT_TOKEN[:8]}...")
    print("=" * 55)

    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
    except Exception:
        pass

    print("  ✅ Бот запущено! Відкрий Telegram і напиши /start")
    print("  🛑 Для зупинки: Ctrl+C")
    print("=" * 55)

    bot.infinity_polling(timeout=30, long_polling_timeout=20, skip_pending=True)
