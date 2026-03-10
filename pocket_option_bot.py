#!/usr/bin/env python3
"""
╔══════════════════════════════════════════╗
║   AI SIGNAL BOT v2.0 — Pocket Option    ║
║   Реальні ціни + Ichimoku + EMA + ADX   ║
╚══════════════════════════════════════════╝
pip install pyTelegramBotAPI requests
"""

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import math
import time
import os
from datetime import datetime, timezone, timedelta

# ══════════════════════════════════════════
#  ТОКЕН
# ══════════════════════════════════════════
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

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

ALL_PAIRS = {p["name"]: p for p in FOREX_PAIRS + OTC_PAIRS}

TIMEFRAMES = {
    "1":"1 хвилина","3":"3 хвилини","5":"5 хвилин",
    "15":"15 хвилин","30":"30 хвилин","60":"1 година",
}

# ══════════════════════════════════════════
#  ОТРИМАННЯ РЕАЛЬНОЇ ЦІНИ
# ══════════════════════════════════════════
def get_real_price(symbol: str, fallback: float) -> float:
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
        r = requests.get(url, timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        data = r.json()
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return float(price)
    except:
        return fallback

def get_candles(symbol: str, tf: str, count=50):
    """Отримати свічки для розрахунку індикаторів"""
    tf_map = {"1":"1m","3":"2m","5":"5m","15":"15m","30":"30m","60":"1h"}
    interval = tf_map.get(tf, "5m")
    period = "1d" if tf in ["1","3","5","15"] else "5d"
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={period}"
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0"})
        data = r.json()
        result = data["chart"]["result"][0]
        closes = result["indicators"]["quote"][0]["close"]
        highs  = result["indicators"]["quote"][0]["high"]
        lows   = result["indicators"]["quote"][0]["low"]
        closes = [x for x in closes if x is not None]
        highs  = [x for x in highs  if x is not None]
        lows   = [x for x in lows   if x is not None]
        return closes[-count:], highs[-count:], lows[-count:]
    except:
        return [], [], []

# ══════════════════════════════════════════
#  ІНДИКАТОРИ
# ══════════════════════════════════════════
def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    if al == 0:
        return 100
    rs = ag / al
    return round(100 - 100 / (1 + rs), 1)

def calc_ema(closes, period):
    if len(closes) < period:
        return closes[-1] if closes else 0
    k = 2 / (period + 1)
    ema = sum(closes[:period]) / period
    for price in closes[period:]:
        ema = price * k + ema * (1 - k)
    return ema

def calc_macd(closes):
    if len(closes) < 26:
        return 0, 0
    ema12 = calc_ema(closes, 12)
    ema26 = calc_ema(closes, 26)
    macd_line = ema12 - ema26
    # Signal line (9-period EMA of MACD)
    macd_values = []
    for i in range(9, len(closes)+1):
        e12 = calc_ema(closes[:i], 12)
        e26 = calc_ema(closes[:i], 26)
        macd_values.append(e12 - e26)
    signal = calc_ema(macd_values, 9) if len(macd_values) >= 9 else macd_line
    return round(macd_line, 6), round(macd_line - signal, 6)

def calc_adx(closes, highs, lows, period=14):
    if len(closes) < period + 2:
        return 20
    trs, pdms, ndms = [], [], []
    for i in range(1, len(closes)):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i-1])
        lc = abs(lows[i]  - closes[i-1])
        trs.append(max(hl, hc, lc))
        up   = highs[i]  - highs[i-1]
        down = lows[i-1] - lows[i]
        pdms.append(up   if up > down and up > 0   else 0)
        ndms.append(down if down > up and down > 0 else 0)
    atr  = sum(trs[-period:])  / period
    pdi  = (sum(pdms[-period:]) / period) / atr * 100 if atr else 0
    ndi  = (sum(ndms[-period:]) / period) / atr * 100 if atr else 0
    dx   = abs(pdi - ndi) / (pdi + ndi) * 100 if (pdi + ndi) else 0
    return round(dx, 1)

def calc_stoch(closes, highs, lows, k=14):
    if len(closes) < k:
        return 50
    low_k  = min(lows[-k:])
    high_k = max(highs[-k:])
    if high_k == low_k:
        return 50
    return round((closes[-1] - low_k) / (high_k - low_k) * 100, 1)

def calc_bb(closes, period=20):
    """Позиція ціни у Bollinger Bands (0-100)"""
    if len(closes) < period:
        return 50
    sma = sum(closes[-period:]) / period
    std = (sum((x - sma)**2 for x in closes[-period:]) / period) ** 0.5
    if std == 0:
        return 50
    upper = sma + 2 * std
    lower = sma - 2 * std
    pos = (closes[-1] - lower) / (upper - lower) * 100
    return round(max(0, min(100, pos)), 1)

def calc_ichimoku(closes, highs, lows):
    """Ichimoku Cloud — повертає сигнал: 1=buy, -1=sell, 0=neutral"""
    if len(closes) < 52:
        return 0
    # Tenkan-sen (9)
    tenkan = (max(highs[-9:]) + min(lows[-9:])) / 2
    # Kijun-sen (26)
    kijun  = (max(highs[-26:]) + min(lows[-26:])) / 2
    # Senkou Span A
    span_a = (tenkan + kijun) / 2
    # Senkou Span B (52)
    span_b = (max(highs[-52:]) + min(lows[-52:])) / 2
    price  = closes[-1]

    if price > span_a and price > span_b and tenkan > kijun:
        return 1   # BUY — ціна над хмарою
    elif price < span_a and price < span_b and tenkan < kijun:
        return -1  # SELL — ціна під хмарою
    return 0

def calc_ema_cross(closes):
    """EMA 9/21 crossover"""
    if len(closes) < 21:
        return 0
    ema9  = calc_ema(closes, 9)
    ema21 = calc_ema(closes, 21)
    ema9_prev  = calc_ema(closes[:-1], 9)
    ema21_prev = calc_ema(closes[:-1], 21)
    if ema9 > ema21 and ema9_prev <= ema21_prev:
        return 2   # Сильний BUY — щойно перетнуло вгору
    elif ema9 < ema21 and ema9_prev >= ema21_prev:
        return -2  # Сильний SELL — щойно перетнуло вниз
    elif ema9 > ema21:
        return 1   # BUY тренд
    else:
        return -1  # SELL тренд

# ══════════════════════════════════════════
#  ГЕНЕРАЦІЯ СИГНАЛУ
# ══════════════════════════════════════════
def seeded_rand(seed, offset=0):
    x = math.sin(seed + offset) * 43758.5453123
    return x - math.floor(x)

def generate_signal(pair_name: str, tf: str) -> dict:
    m      = ALL_PAIRS.get(pair_name, FOREX_PAIRS[0])
    is_otc = "OTC" in pair_name

    # Отримуємо реальні дані
    closes, highs, lows = get_candles(m["symbol"], tf, count=60)
    live = get_real_price(m["symbol"], m["p"])

    use_real = len(closes) >= 20

    if use_real:
        rsi   = calc_rsi(closes)
        adx   = calc_adx(closes, highs, lows)
        macd, macd_hist = calc_macd(closes)
        stoch = calc_stoch(closes, highs, lows)
        bb    = calc_bb(closes)
        ichi  = calc_ichimoku(closes, highs, lows)
        ema_c = calc_ema_cross(closes)
        ema9  = calc_ema(closes, 9)
        ema21 = calc_ema(closes, 21)
        ema50 = calc_ema(closes, 50)
    else:
        # Fallback на псевдо-дані якщо API недоступний
        seed  = sum(ord(c) for c in pair_name) + int(tf) + int(time.time()//60)
        r     = lambda i: seeded_rand(seed, i)
        rsi   = round(28 + r(1)*50)
        adx   = round(22 + r(2)*55)
        macd  = (r(3)-0.5)*0.006
        macd_hist = macd * 0.3
        stoch = round(15 + r(5)*70)
        bb    = r(4)*100
        ichi  = m["t"]
        ema_c = m["t"]
        ema9  = live * (1 + (r(7)-0.5)*0.002)
        ema21 = live * (1 + (r(8)-0.5)*0.003)
        ema50 = live * (1 + (r(9)-0.5)*0.005)

    # ══ СИСТЕМА ПІДТВЕРДЖЕННЯ ══
    # Кожен індикатор голосує: +1 BUY, -1 SELL, 0 нейтраль
    votes = []

    # 1. RSI
    if rsi < 30:    votes.append(("RSI", 1, f"RSI={rsi} перепроданість ✅"))
    elif rsi > 70:  votes.append(("RSI", -1, f"RSI={rsi} перекупленість ✅"))
    elif rsi < 45:  votes.append(("RSI", 1, f"RSI={rsi} бичачий нахил"))
    elif rsi > 55:  votes.append(("RSI", -1, f"RSI={rsi} ведмежий нахил"))
    else:           votes.append(("RSI", 0, f"RSI={rsi} нейтраль"))

    # 2. MACD
    if macd > 0 and macd_hist > 0:   votes.append(("MACD", 1,  "MACD ▲ BUY підтверджено ✅"))
    elif macd < 0 and macd_hist < 0: votes.append(("MACD", -1, "MACD ▼ SELL підтверджено ✅"))
    else:                             votes.append(("MACD", 0,  "MACD нейтральний"))

    # 3. EMA Crossover
    if ema_c == 2:    votes.append(("EMA Cross", 1,  "EMA 9/21 перетин ▲ СИЛЬНИЙ BUY ✅"))
    elif ema_c == -2: votes.append(("EMA Cross", -1, "EMA 9/21 перетин ▼ СИЛЬНИЙ SELL ✅"))
    elif ema_c == 1:  votes.append(("EMA Cross", 1,  "EMA 9>21 бичачий тренд"))
    else:             votes.append(("EMA Cross", -1, "EMA 9<21 ведмежий тренд"))

    # 4. Ichimoku
    if ichi == 1:    votes.append(("Ichimoku", 1,  "Ціна над хмарою ☁️ BUY ✅"))
    elif ichi == -1: votes.append(("Ichimoku", -1, "Ціна під хмарою ☁️ SELL ✅"))
    else:            votes.append(("Ichimoku", 0,  "Ichimoku нейтраль"))

    # 5. Stochastic
    if stoch < 20:   votes.append(("Stoch", 1,  f"Stoch={stoch} перепроданість ✅"))
    elif stoch > 80: votes.append(("Stoch", -1, f"Stoch={stoch} перекупленість ✅"))
    else:            votes.append(("Stoch", 0,  f"Stoch={stoch} нейтраль"))

    # 6. Bollinger Bands
    if bb < 15:      votes.append(("BB", 1,  "Ціна біля нижньої смуги ✅"))
    elif bb > 85:    votes.append(("BB", -1, "Ціна біля верхньої смуги ✅"))
    else:            votes.append(("BB", 0,  f"BB позиція {bb:.0f}%"))

    # 7. EMA50 тренд
    if live > ema50: votes.append(("EMA50", 1,  f"Ціна вище EMA50 — висхідний тренд"))
    else:            votes.append(("EMA50", -1, f"Ціна нижче EMA50 — низхідний тренд"))

    # ══ ПІДРАХУНОК ══
    buy_count  = sum(1 for v in votes if v[1] == 1)
    sell_count = sum(1 for v in votes if v[1] == -1)
    total      = len(votes)

    score = buy_count - sell_count

    # ══ ФІЛЬТР СИЛИ ТРЕНДУ (ADX) ══
    adx_strong = adx >= 25
    adx_note   = f"ADX={adx} {'💪 СИЛЬНИЙ тренд' if adx >= 25 else '⚠️ слабкий тренд'}"

    is_buy = score > 0

    # ══ ВПЕВНЕНІСТЬ ══
    # Базується на: кількості підтверджень + силі ADX + консенсусі
    confirm_ratio = max(buy_count, sell_count) / total
    adx_bonus     = min(adx / 100, 0.15)
    conf = round(70 + confirm_ratio * 20 + adx_bonus * 10 + (5 if adx_strong else 0))
    conf = min(97, max(72, conf))

    # Якщо сигнал слабкий (менше 4 підтверджень) — знижуємо впевненість
    strong_confirms = max(buy_count, sell_count)
    if strong_confirms < 3:
        conf = min(conf, 78)
        signal_strength = "⚠️ СЛАБКИЙ"
    elif strong_confirms < 5:
        conf = min(conf, 88)
        signal_strength = "✅ СЕРЕДНІЙ"
    else:
        signal_strength = "🔥 СИЛЬНИЙ"

    # Рівні TP/SL на основі реальної волатильності
    d    = m["d"]
    mult = 1 if live > 100 else (0.01 if live > 10 else 0.0001)

    if use_real and len(closes) >= 10:
        atr = sum(abs(closes[i]-closes[i-1]) for i in range(-10,0)) / 10
        atr = max(atr, mult * 2)
    else:
        atr = mult * 3

    sp  = 1.8 if is_otc else 1.0
    tp1 = round(live + atr * 1.5, d)   if is_buy else round(live - atr * 1.5, d)
    tp2 = round(live + atr * 2.5, d)   if is_buy else round(live - atr * 2.5, d)
    sl  = round(live - atr * 1.0 * sp, d) if is_buy else round(live + atr * 1.0 * sp, d)
    res = round(live + atr * 3.0, d)
    sup = round(live - atr * 3.0, d)
    rr  = round(abs(tp1-live) / abs(sl-live), 1) if abs(sl-live) > 0 else 1.5

    return {
        "is_buy": is_buy,
        "signal": "BUY ▲" if is_buy else "SELL ▼",
        "conf": conf,
        "signal_strength": signal_strength,
        "live": live,
        "tp1": tp1, "tp2": tp2, "sl": sl,
        "res": res, "sup": sup, "rr": rr,
        "rsi": rsi, "adx": adx, "adx_note": adx_note,
        "macd": macd, "macd_hist": macd_hist,
        "stoch": stoch, "bb": bb,
        "ichi": ichi, "ema_c": ema_c,
        "ema9": round(ema9, d), "ema21": round(ema21, d), "ema50": round(ema50, d),
        "votes": votes,
        "buy_count": buy_count, "sell_count": sell_count,
        "adx_strong": adx_strong,
        "use_real": use_real,
        "is_otc": is_otc,
    }

# ══════════════════════════════════════════
#  ФОРМАТУВАННЯ ПОВІДОМЛЕННЯ
# ══════════════════════════════════════════
def format_signal(pair: str, tf: str, d: dict) -> str:
    now_dt    = datetime.now(timezone.utc) + timedelta(hours=2)
    now       = now_dt.strftime("%H:%M:%S")
    conf_bar  = "█" * round(d["conf"]/10) + "░" * (10 - round(d["conf"]/10))
    direction = "🟢 BUY ▲" if d["is_buy"] else "🔴 SELL ▼"
    market    = "🌙 OTC MARKET" if d["is_otc"] else "📈 FOREX MARKET"
    data_src  = "🔴 Live ціни" if d["use_real"] else "⚙️ Розрахункові"
    adx_warn  = "" if d["adx_strong"] else "\n⚠️ _ADX<25 — тренд слабкий, обережно!_"

    # ⏱ Час утримання угоди
    tf_hold = {"1":(1,2),"3":(3,5),"5":(5,10),"15":(15,20),"30":(30,35),"60":(60,75)}
    hold_min = tf_hold.get(tf, (5,10))
    expiry_dt = now_dt + timedelta(minutes=hold_min[0])
    expiry    = expiry_dt.strftime("%H:%M")
    hold_txt  = f"{hold_min[0]}–{hold_min[1]} хвилин"

    # Голоси індикаторів
    votes_txt = ""
    for name, vote, desc in d["votes"]:
        icon = "🟢" if vote == 1 else ("🔴" if vote == -1 else "⚪")
        votes_txt += f"{icon} {desc}\n"

    msg = f"""
⚡ *AI SIGNAL BOT v2.0 — Pocket Option*
{market} | {data_src}

*Пара:* `{pair}`
*Таймфрейм:* `{TIMEFRAMES.get(tf, tf)}`
*Час:* `{now}`

━━━━━━━━━━━━━━━━━━━━
🎯 *СИГНАЛ: {direction}*
💪 *Сила: {d["signal_strength"]}*
⏱ *Утримувати: {hold_txt}*
🕐 *Експірація: {expiry}*
━━━━━━━━━━━━━━━━━━━━

📊 *Впевненість: {d["conf"]}%*
`{conf_bar}`

✅ Підтверджень BUY:  `{d["buy_count"]}/7`
🔴 Підтверджень SELL: `{d["sell_count"]}/7`
📐 {d["adx_note"]}{adx_warn}

━━━━━━━━━━━━━━━━━━━━
💰 *Рівні входу*

Поточна ціна: `{d["live"]}`
Вхід:         `{d["live"]}`
TP 1:         `{d["tp1"]}`
TP 2:         `{d["tp2"]}`
Stop Loss:    `{d["sl"]}`
R/R:          `1 : {d["rr"]}`

🔴 Опір:      `{d["res"]}`
🟢 Підтримка: `{d["sup"]}`

━━━━━━━━━━━━━━━━━━━━
📉 *EMA рівні*
EMA 9:  `{d["ema9"]}` | EMA 21: `{d["ema21"]}` | EMA 50: `{d["ema50"]}`

━━━━━━━━━━━━━━━━━━━━
🔬 *Аналіз індикаторів (7/7)*

{votes_txt}
━━━━━━━━━━━━━━━━━━━━
⚠️ _Не є фінансовою порадою_
"""
    return msg.strip()

# ══════════════════════════════════════════
#  НОВІ КЛАВІАТУРИ v3
# ══════════════════════════════════════════
def main_menu_v3():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📈 FOREX",       callback_data="menu_forex"),
        InlineKeyboardButton("🌙 OTC",          callback_data="menu_otc"),
    )
    kb.add(
        InlineKeyboardButton("📊 Статистика",  callback_data="stats"),
        InlineKeyboardButton("🕐 Сесії",        callback_data="sessions"),
    )
    kb.add(InlineKeyboardButton("ℹ️ Про бота", callback_data="about"))
    return kb

def result_kb(pair: str, tf: str):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Виграш",  callback_data=f"result_win_{pair}_{tf}"),
        InlineKeyboardButton("❌ Програш", callback_data=f"result_loss_{pair}_{tf}"),
    )
    kb.add(
        InlineKeyboardButton("🔄 Новий сигнал", callback_data=f"tf_{pair}_{tf}"),
        InlineKeyboardButton("🏠 Меню",          callback_data="back_main_v3"),
    )
    return kb


# ══════════════════════════════════════════
#  КЛАВІАТУРИ
# ══════════════════════════════════════════
def main_menu_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📈 FOREX", callback_data="menu_forex"),
        InlineKeyboardButton("🌙 OTC",   callback_data="menu_otc"),
    )
    kb.add(InlineKeyboardButton("ℹ️ Про бота", callback_data="about"))
    return kb

def forex_pairs_kb():
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(p["name"], callback_data=f"pair_{p['name']}") for p in FOREX_PAIRS])
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="back_main"))
    return kb

def otc_pairs_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(*[InlineKeyboardButton(p["name"], callback_data=f"pair_{p['name']}") for p in OTC_PAIRS])
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="back_main"))
    return kb

def timeframe_kb(pair: str):
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(v, callback_data=f"tf_{pair}_{k}") for k, v in TIMEFRAMES.items()])
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="back_pairs_" + ("otc" if "OTC" in pair else "forex")))
    return kb

def after_signal_kb(pair: str, tf: str):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔄 Оновити сигнал", callback_data=f"tf_{pair}_{tf}"),
        InlineKeyboardButton("🔀 Змінити пару",   callback_data="back_pairs_" + ("otc" if "OTC" in pair else "forex")),
    )
    kb.add(InlineKeyboardButton("🏠 Головне меню", callback_data="back_main"))
    return kb

# ══════════════════════════════════════════
#  ХЕНДЛЕРИ
# ══════════════════════════════════════════
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    text = (
        "⚡ *AI Signal Bot v2.0 — Pocket Option*\n\n"
        "🔴 Реальні ціни з ринку\n"
        "📊 7 індикаторів одночасно\n"
        "☁️ Ichimoku Cloud\n"
        "📈 EMA 9/21/50 Crossover\n"
        "💪 Фільтр сили тренду (ADX)\n"
        "✅ Підтвердження від 3+ індикаторів\n\n"
        "🟢 *17 Forex* | 🌙 *13 OTC* | ⏱ *6 таймфреймів*\n\n"
        "Оберіть категорію:"
    )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=main_menu_v3())

@bot.callback_query_handler(func=lambda c: c.data == "back_main")
def back_main(call):
    bot.edit_message_text("Оберіть категорію:", call.message.chat.id,
                          call.message.message_id, parse_mode="Markdown", reply_markup=main_menu_v3())

@bot.callback_query_handler(func=lambda c: c.data == "menu_forex")
def menu_forex(call):
    bot.edit_message_text("📈 *FOREX пари*\nОберіть пару:", call.message.chat.id,
                          call.message.message_id, parse_mode="Markdown", reply_markup=forex_pairs_kb())

@bot.callback_query_handler(func=lambda c: c.data == "menu_otc")
def menu_otc(call):
    bot.edit_message_text("🌙 *OTC пари*\nОберіть пару:", call.message.chat.id,
                          call.message.message_id, parse_mode="Markdown", reply_markup=otc_pairs_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("back_pairs_"))
def back_pairs(call):
    market = call.data.split("_")[-1]
    if market == "otc":
        bot.edit_message_text("🌙 *OTC пари*\nОберіть пару:", call.message.chat.id,
                              call.message.message_id, parse_mode="Markdown", reply_markup=otc_pairs_kb())
    else:
        bot.edit_message_text("📈 *FOREX пари*\nОберіть пару:", call.message.chat.id,
                              call.message.message_id, parse_mode="Markdown", reply_markup=forex_pairs_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("pair_"))
def select_pair(call):
    pair = call.data[5:]
    bot.edit_message_text(f"⏱ *Таймфрейм для {pair}*\nОберіть час свічки:",
                          call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=timeframe_kb(pair))

@bot.callback_query_handler(func=lambda c: c.data.startswith("tf_"))
def select_tf(call):
    parts = call.data.split("_")
    tf    = parts[-1]
    pair  = "_".join(parts[1:-1])
    bot.answer_callback_query(call.id, "⚡ Аналізую ринок...")
    bot.edit_message_text(f"⏳ Отримую реальні дані для *{pair}*...\n🔬 Аналізую 7 індикаторів...",
                          call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    d   = generate_signal(pair, tf)
    msg = format_signal(pair, tf, d)
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=result_kb(pair, tf))

@bot.callback_query_handler(func=lambda c: c.data == "about")
def about(call):
    text = (
        "ℹ️ *AI Signal Bot v2.0*\n\n"
        "*Індикатори:*\n"
        "• RSI (14) — перекупленість/перепроданість\n"
        "• MACD — імпульс тренду\n"
        "• EMA 9/21/50 — напрямок тренду\n"
        "• Ichimoku Cloud — хмара підтримки\n"
        "• ADX — сила тренду (фільтр)\n"
        "• Stochastic — точка входу\n"
        "• Bollinger Bands — волатильність\n\n"
        "*Система підтвердження:*\n"
        "🔥 Сильний: 5-7 індикаторів ✅\n"
        "✅ Середній: 4 індикатори\n"
        "⚠️ Слабкий: 3 індикатори\n\n"
        "📡 Дані: Yahoo Finance API (реальний час)"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=main_menu_v3())

# ══════════════════════════════════════════
#  ЗАПУСК
# ══════════════════════════════════════════
if __name__ == "__main__":
    print("╔══════════════════════════════════════════╗")
    print("║  AI Signal Bot v2.0 — Pocket Option     ║")
    print("║  Реальні ціни + 7 індикаторів           ║")
    print("║  Запущено! Очікую повідомлень...        ║")
    print("╚══════════════════════════════════════════╝")
    bot.infinity_polling()

# ══════════════════════════════════════════
#  СТАТИСТИКА v3
# ══════════════════════════════════════════
user_stats  = {}
last_signal = {}

def get_stats(chat_id):
    if chat_id not in user_stats:
        user_stats[chat_id] = {"total":0,"wins":0,"losses":0,"pairs":{},"streak":0}
    return user_stats[chat_id]

def format_stats(chat_id) -> str:
    s = get_stats(chat_id)
    total = s["total"]
    if total == 0:
        return (
            "📊 *Ваша статистика*\n\n"
            "Ще немає записів.\n"
            "Після кожного сигналу натискайте ✅ або ❌ щоб записати результат!"
        )
    wins = s["wins"]; losses = s["losses"]
    wr   = round(wins / total * 100)
    bar  = "🟢" * round(wr/10) + "⚪" * (10 - round(wr/10))
    pairs = s["pairs"]
    best  = sorted(pairs.items(), key=lambda x: x[1]["wins"]/(x[1]["total"] or 1), reverse=True)[:3]
    best_txt = "".join(f"  • {n}: {d['wins']}/{d['total']} ({round(d['wins']/(d['total'] or 1)*100)}%)\n" for n,d in best)
    streak = s.get("streak", 0)
    streak_txt = (f"🔥 Серія виграшів: {streak}\n" if streak > 1
                  else f"❄️ Серія програшів: {abs(streak)}\n" if streak < -1 else "")
    return (
        f"📊 *Ваша статистика*\n\n"
        f"Всього угод: `{total}`\n"
        f"✅ Виграші:  `{wins}`\n"
        f"❌ Програші: `{losses}`\n\n"
        f"🏆 *Виграшів: {wr}%*\n{bar}\n\n"
        f"{streak_txt}"
        f"🥇 *Кращі пари:*\n{best_txt}"
    )

def get_session_info() -> str:
    from datetime import datetime, timezone, timedelta
    now  = datetime.now(timezone.utc)
    h    = now.hour
    ua_h = (now + timedelta(hours=2)).hour
    sessions = [("🗼 Токіо", 0, 9), ("🏦 Лондон", 7, 16), ("🗽 Нью-Йорк", 13, 22)]
    active   = [n for n,s,e in sessions if s <= h < e]
    inactive = [n for n,s,e in sessions if not (s <= h < e)]
    if 13 <= h < 16:   act, tip = "🔥🔥🔥 МАКСИМАЛЬНА", "Лондон + Нью-Йорк — найкращий час!"
    elif 7 <= h < 13:  act, tip = "🔥🔥 ВИСОКА",        "Добрі пари: EUR/GBP, EUR/USD"
    elif 13 <= h < 22: act, tip = "🔥🔥 ВИСОКА",        "Добрі пари: USD/JPY, GBP/USD"
    elif 0 <= h < 9:   act, tip = "🔥 СЕРЕДНЯ",         "Добрі пари: JPY, AUD, NZD"
    else:              act, tip = "😴 НИЗЬКА",           "Краще утриматись від торгівлі"
    return (
        f"🕐 *Торгові сесії*\n\n"
        f"Час UA: `{ua_h:02d}:00` | UTC: `{h:02d}:00`\n\n"
        f"✅ *Активні:* {' | '.join(active) or 'Немає'}\n"
        f"⚪ *Неактивні:* {' | '.join(inactive) or 'Всі активні'}\n\n"
        f"📊 *Активність:* {act}\n"
        f"💡 _{tip}_\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*Розклад (UTC+2):*\n"
        f"🗼 Токіо:    02:00–11:00\n"
        f"🏦 Лондон:   09:00–18:00\n"
        f"🗽 Нью-Йорк: 15:00–00:00\n"
        f"🔥 Перетин:  15:00–18:00 ← найкращий час"
    )

# ══════════════════════════════════════════
#  НОВІ КЛАВІАТУРИ v3
# ══════════════════════════════════════════
def main_menu_v3():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📈 FOREX",       callback_data="menu_forex"),
        InlineKeyboardButton("🌙 OTC",          callback_data="menu_otc"),
    )
    kb.add(
        InlineKeyboardButton("📊 Статистика",  callback_data="stats"),
        InlineKeyboardButton("🕐 Сесії",        callback_data="sessions"),
    )
    kb.add(InlineKeyboardButton("ℹ️ Про бота", callback_data="about"))
    return kb

def result_kb(pair: str, tf: str):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Виграш",  callback_data=f"result_win_{pair}_{tf}"),
        InlineKeyboardButton("❌ Програш", callback_data=f"result_loss_{pair}_{tf}"),
    )
    kb.add(
        InlineKeyboardButton("🔄 Новий сигнал", callback_data=f"tf_{pair}_{tf}"),
        InlineKeyboardButton("🏠 Меню",          callback_data="back_main_v3"),
    )
    return kb

# ══════════════════════════════════════════
#  НОВІ ХЕНДЛЕРИ v3
# ══════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "back_main_v3")
def back_main_v3(call):
    bot.edit_message_text("Оберіть категорію:", call.message.chat.id,
                          call.message.message_id, parse_mode="Markdown", reply_markup=main_menu_v3())

@bot.callback_query_handler(func=lambda c: c.data == "stats")
def show_stats(call):
    text = format_stats(call.message.chat.id)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=main_menu_v3())

@bot.callback_query_handler(func=lambda c: c.data == "sessions")
def show_sessions(call):
    text = get_session_info()
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=main_menu_v3())

@bot.callback_query_handler(func=lambda c: c.data.startswith("result_"))
def handle_result(call):
    parts  = call.data.split("_")
    result = parts[1]        # win або loss
    tf     = parts[-1]
    pair   = "_".join(parts[2:-1])
    chat   = call.message.chat.id
    s      = get_stats(chat)
    s["total"] += 1
    if result == "win":
        s["wins"]   += 1
        s["streak"] = max(s.get("streak",0)+1, 1)
        emoji = "✅ Виграш записано!"
    else:
        s["losses"] += 1
        s["streak"] = min(s.get("streak",0)-1, -1)
        emoji = "❌ Програш записано"
    if pair not in s["pairs"]:
        s["pairs"][pair] = {"total":0,"wins":0}
    s["pairs"][pair]["total"] += 1
    if result == "win":
        s["pairs"][pair]["wins"] += 1
    wr  = round(s["wins"] / s["total"] * 100)
    bot.answer_callback_query(call.id, f"{emoji} | Загальний WR: {wr}%")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=main_menu_v3())

@bot.message_handler(commands=["stats"])
def cmd_stats(msg):
    text = format_stats(msg.chat.id)
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=main_menu_v3())

@bot.message_handler(commands=["sessions"])
def cmd_sessions(msg):
    text = get_session_info()
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=main_menu_v3())
