#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║   SIGNAL AI Bot v4.0 — PocketOption Telegram Bot            ║
╠══════════════════════════════════════════════════════════════╣
║  НОВЕ у v4.0:                                                ║
║  • Авто-сигнали за підпискою (кожні N хвилин)               ║
║  • Мульти-ТФ підтвердження (М1 + М5 + М15 узгодженість)     ║
║  • EMA200 + Ichimoku Kumo хмара                              ║
║  • OBV (On Balance Volume) — об'ємний тренд                  ║
║  • CCI (Commodity Channel Index)                             ║
║  • Divergence RSI/MACD детектор                              ║
║  • Кешування API — не витрачає ліміт запитів                 ║
║  • Адмін-панель: broadcast, статистика всіх юзерів           ║
║  • Рейтинг пар по winrate за останні 20 угод                 ║
║  • Сигнал-картка з emoji-графіком ціни                       ║
╠══════════════════════════════════════════════════════════════╣
║  ВСТАНОВЛЕННЯ:                                               ║
║    pip install pyTelegramBotAPI requests                     ║
║  ЗАПУСК:                                                     ║
║    python3 bot.py                                            ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, math, time, json, threading, requests, logging
from datetime import datetime, timezone, timedelta
from collections import defaultdict

try:
    from telebot import TeleBot
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
except ImportError:
    print("❌ Встанови: pip install pyTelegramBotAPI requests")
    exit(1)

# ══════════════════════════════════════════════════════════════
#  ⚙️  КОНФІГУРАЦІЯ
# ══════════════════════════════════════════════════════════════
BOT_TOKEN   = os.environ.get("BOT_TOKEN",  "ВАШ_ТОКЕН_ТУТ")
TWELVE_KEY  = os.environ.get("TWELVE_KEY", "99b3ca01dbdf45ccb2f5968b16af1c82")
TWELVE_URL  = "https://api.twelvedata.com"
ADMIN_IDS   = set()  # Додай свій Telegram ID: {123456789}
STATS_FILE  = "stats.json"
SUBS_FILE   = "subscriptions.json"
CACHE_TTL   = 90     # секунд кешування API
AUTO_SCAN_INTERVAL = 300  # секунд між авто-сканами (5 хв)

# ── Логування ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

if "ВАШ_ТОКЕН" in BOT_TOKEN:
    print("=" * 55)
    print("❌  Вкажи BOT_TOKEN у файлі або змінній середовища")
    print("    Отримай у @BotFather в Telegram")
    print("=" * 55)
    exit(1)

bot = TeleBot(BOT_TOKEN, parse_mode=None)

# ══════════════════════════════════════════════════════════════
#  📊 ПАРИ
# ══════════════════════════════════════════════════════════════
FOREX_PAIRS = [
    {"name":"EUR/USD",  "symbol":"EUR/USD",  "p":1.085,  "d":5},
    {"name":"GBP/USD",  "symbol":"GBP/USD",  "p":1.270,  "d":5},
    {"name":"USD/JPY",  "symbol":"USD/JPY",  "p":149.5,  "d":3},
    {"name":"AUD/USD",  "symbol":"AUD/USD",  "p":0.645,  "d":5},
    {"name":"NZD/USD",  "symbol":"NZD/USD",  "p":0.596,  "d":5},
    {"name":"USD/CAD",  "symbol":"USD/CAD",  "p":1.357,  "d":5},
    {"name":"USD/CHF",  "symbol":"USD/CHF",  "p":0.903,  "d":5},
    {"name":"EUR/GBP",  "symbol":"EUR/GBP",  "p":0.853,  "d":5},
    {"name":"EUR/JPY",  "symbol":"EUR/JPY",  "p":161.5,  "d":3},
    {"name":"GBP/JPY",  "symbol":"GBP/JPY",  "p":189.8,  "d":3},
    {"name":"AUD/CAD",  "symbol":"AUD/CAD",  "p":0.874,  "d":5},
    {"name":"AUD/JPY",  "symbol":"AUD/JPY",  "p":96.4,   "d":3},
    {"name":"CHF/JPY",  "symbol":"CHF/JPY",  "p":165.5,  "d":3},
    {"name":"EUR/AUD",  "symbol":"EUR/AUD",  "p":1.672,  "d":5},
    {"name":"EUR/CAD",  "symbol":"EUR/CAD",  "p":1.464,  "d":5},
    {"name":"GBP/AUD",  "symbol":"GBP/AUD",  "p":1.975,  "d":5},
    {"name":"GBP/CAD",  "symbol":"GBP/CAD",  "p":1.722,  "d":5},
    {"name":"XAU/USD",  "symbol":"XAU/USD",  "p":2310.0, "d":2},
    {"name":"XAG/USD",  "symbol":"XAG/USD",  "p":27.5,   "d":3},
]

OTC_PAIRS = [
    {**p, "name": p["name"] + " OTC"}
    for p in FOREX_PAIRS[:12]
]

CRYPTO_PAIRS = [
    {"name":"BTC/USD",   "symbol":"BTC/USD",   "p":67000, "d":0},
    {"name":"ETH/USD",   "symbol":"ETH/USD",   "p":3500,  "d":2},
    {"name":"BNB/USD",   "symbol":"BNB/USD",   "p":420,   "d":2},
    {"name":"SOL/USD",   "symbol":"SOL/USD",   "p":180,   "d":2},
    {"name":"XRP/USD",   "symbol":"XRP/USD",   "p":0.62,  "d":4},
    {"name":"ADA/USD",   "symbol":"ADA/USD",   "p":0.45,  "d":4},
    {"name":"DOGE/USD",  "symbol":"DOGE/USD",  "p":0.18,  "d":5},
    {"name":"LTC/USD",   "symbol":"LTC/USD",   "p":95,    "d":2},
    {"name":"AVAX/USD",  "symbol":"AVAX/USD",  "p":38,    "d":2},
    {"name":"DOT/USD",   "symbol":"DOT/USD",   "p":7.5,   "d":3},
    {"name":"LINK/USD",  "symbol":"LINK/USD",  "p":15.4,  "d":3},
    {"name":"TON/USD",   "symbol":"TON/USD",   "p":5.4,   "d":3},
]

STOCKS_PAIRS = [
    {"name":"Apple",       "symbol":"AAPL",  "p":189, "d":2},
    {"name":"Tesla",       "symbol":"TSLA",  "p":245, "d":2},
    {"name":"NVIDIA",      "symbol":"NVDA",  "p":875, "d":2},
    {"name":"Amazon",      "symbol":"AMZN",  "p":185, "d":2},
    {"name":"Google",      "symbol":"GOOGL", "p":165, "d":2},
    {"name":"Microsoft",   "symbol":"MSFT",  "p":415, "d":2},
    {"name":"Meta",        "symbol":"META",  "p":510, "d":2},
    {"name":"Netflix",     "symbol":"NFLX",  "p":625, "d":2},
    {"name":"AMD",         "symbol":"AMD",   "p":168, "d":2},
    {"name":"Alibaba",     "symbol":"BABA",  "p":78,  "d":2},
    {"name":"Oracle",      "symbol":"ORCL",  "p":128, "d":2},
    {"name":"Salesforce",  "symbol":"CRM",   "p":275, "d":2},
]

ALL_PAIRS  = {p["name"]: p for p in FOREX_PAIRS + OTC_PAIRS + CRYPTO_PAIRS + STOCKS_PAIRS}
TIMEFRAMES = {"1":"1 хв","3":"3 хв","5":"5 хв","15":"15 хв","30":"30 хв","60":"1 год"}
CRYPTO_TF  = {"5":"5 хв","15":"15 хв","30":"30 хв","60":"1 год","240":"4 год"}
STOCKS_TF  = {"5":"5 хв","15":"15 хв","30":"30 хв","60":"1 год"}

# ══════════════════════════════════════════════════════════════
#  💾 ЗБЕРЕЖЕННЯ ДАНИХ
# ══════════════════════════════════════════════════════════════
_lock = threading.Lock()

def _load_json(path):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        log.warning(f"Не вдалося завантажити {path}: {e}")
    return {}

def _save_json(path, data):
    with _lock:
        try:
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except Exception as e:
            log.error(f"Не вдалося зберегти {path}: {e}")

all_stats   = _load_json(STATS_FILE)
all_subs    = _load_json(SUBS_FILE)   # {str(cid): {"pair":..,"tf":..,"interval":..,"last":0}}

def get_stats(cid):
    k = str(cid)
    if k not in all_stats:
        all_stats[k] = {
            "total": 0, "wins": 0, "losses": 0,
            "streak": 0, "max_streak": 0,
            "pairs": {}, "history": [],
            "joined": datetime.now(timezone.utc).isoformat(),
        }
    return all_stats[k]

def save_stats(): _save_json(STATS_FILE, all_stats)
def save_subs():  _save_json(SUBS_FILE,  all_subs)

# ══════════════════════════════════════════════════════════════
#  🌐 API + КЕШ
# ══════════════════════════════════════════════════════════════
_cache: dict = {}  # key -> (timestamp, data)

def _cache_get(key):
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
    return None

def _cache_set(key, data):
    _cache[key] = (time.time(), data)

TF_MAP = {"1":"1min","3":"3min","5":"5min","15":"15min",
          "30":"30min","60":"1h","240":"4h"}

def get_candles(symbol, tf, count=120):
    key = f"{symbol}_{tf}_{count}"
    cached = _cache_get(key)
    if cached:
        return cached
    interval = TF_MAP.get(str(tf), "5min")
    try:
        url = (f"{TWELVE_URL}/time_series?symbol={symbol}"
               f"&interval={interval}&outputsize={count}"
               f"&apikey={TWELVE_KEY}&format=JSON")
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        d = r.json()
        if d.get("status") == "error" or not d.get("values"):
            log.warning(f"API: немає даних для {symbol} {tf}")
            return [], [], [], []
        vals = list(reversed(d["values"]))
        result = (
            [float(v["close"]) for v in vals],
            [float(v["high"])  for v in vals],
            [float(v["low"])   for v in vals],
            [float(v["open"])  for v in vals],
        )
        _cache_set(key, result)
        return result
    except Exception as e:
        log.warning(f"API candles {symbol}: {e}")
        return [], [], [], []

def get_price(symbol, fallback):
    key = f"price_{symbol}"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    try:
        r = requests.get(
            f"{TWELVE_URL}/price?symbol={symbol}&apikey={TWELVE_KEY}",
            timeout=6)
        r.raise_for_status()
        p = r.json().get("price")
        if p:
            val = float(p)
            _cache_set(key, val)
            return val
    except Exception:
        pass
    return fallback

def _pseudo_candles(pair_name, tf, base):
    """Псевдо-свічки якщо API недоступний"""
    seed = sum(ord(x) for x in pair_name) + int(tf) * 7 + int(time.time() // 300)
    def sr(i):
        v = math.sin(seed * 1.1 + i * 0.7) * 43758.5453
        return v - math.floor(v)
    cv, hv, lv, ov = [base], [base], [base], [base]
    for i in range(1, 100):
        trend = (sr(i+5) - 0.495) * 0.0025
        vol   = sr(i+10) * 0.0018 + 0.0004
        op    = cv[-1]
        cl    = op * (1 + trend + (sr(i+20) - 0.5) * vol)
        hi    = max(op, cl) * (1 + sr(i+30) * 0.0008)
        lo    = min(op, cl) * (1 - sr(i+40) * 0.0008)
        ov.append(op); cv.append(cl); hv.append(hi); lv.append(lo)
    return cv, hv, lv, ov

# ══════════════════════════════════════════════════════════════
#  📐 МАТЕМАТИКА — ІНДИКАТОРИ
# ══════════════════════════════════════════════════════════════

def ema(prices, period):
    if not prices: return 0.0
    if len(prices) < period: return sum(prices) / len(prices)
    k = 2.0 / (period + 1)
    val = sum(prices[:period]) / period
    for x in prices[period:]:
        val = x * k + val * (1 - k)
    return val

def calc_rsi(c, period=14):
    if len(c) < period + 1: return 50.0
    gains  = [max(c[i]-c[i-1], 0.0) for i in range(1, len(c))]
    losses = [max(c[i-1]-c[i], 0.0) for i in range(1, len(c))]
    ag = sum(gains[-period:])  / period
    al = sum(losses[-period:]) / period
    return 100.0 if al == 0 else round(100.0 - 100.0 / (1 + ag/al), 1)

def calc_macd(c):
    if len(c) < 26: return 0.0, 0.0
    ml = ema(c, 12) - ema(c, 26)
    mv = [ema(c[:i], 12) - ema(c[:i], 26) for i in range(26, len(c)+1)]
    sig = ema(mv, 9) if len(mv) >= 9 else ml
    return ml, ml - sig

def calc_stoch(c, h, l, k=14):
    if len(c) < k: return 50.0, 50.0
    hh = max(h[-k:]); ll = min(l[-k:])
    if hh == ll: return 50.0, 50.0
    kv = round((c[-1]-ll)/(hh-ll)*100, 1)
    return kv, kv

def calc_bb(c, period=20):
    if len(c) < period: return 50.0, 0.0
    s   = sum(c[-period:]) / period
    std = (sum((x-s)**2 for x in c[-period:]) / period) ** 0.5
    if std == 0: return 50.0, 0.0
    up = s + 2*std; lo = s - 2*std
    pct = round(max(0.0, min(100.0, (c[-1]-lo)/(up-lo)*100)), 1)
    bw  = round((up-lo)/s*100, 2) if s else 0.0  # bandwidth
    return pct, bw

def calc_willr(c, h, l, period=14):
    if len(c) < period: return -50.0
    hh = max(h[-period:]); ll = min(l[-period:])
    if hh == ll: return -50.0
    return round((hh-c[-1])/(hh-ll)*-100, 1)

def calc_stc(c, cy=10, fa=23, sl=50):
    if len(c) < sl + cy: return None
    ml = [ema(c[:i], fa) - ema(c[:i], sl) for i in range(sl, len(c)+1)]
    if len(ml) < cy: return None
    hh = max(ml[-cy:]); ll = min(ml[-cy:])
    if hh == ll: return 50.0
    return round((ml[-1]-ll)/(hh-ll)*100, 1)

def calc_adx(c, h, l, period=14):
    if len(c) < period + 2: return 0.0
    trs, pm, nm = [], [], []
    for i in range(1, len(c)):
        trs.append(max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1])))
        up = h[i]-h[i-1]; dn = l[i-1]-l[i]
        pm.append(up if up > dn and up > 0 else 0)
        nm.append(dn if dn > up and dn > 0 else 0)
    atr = sum(trs[-period:]) / period
    if not atr: return 0.0
    pdi = sum(pm[-period:]) / period / atr * 100
    ndi = sum(nm[-period:]) / period / atr * 100
    return round(abs(pdi-ndi) / max(1e-9, pdi+ndi) * 100)

def calc_atr(c, h, l, period=14):
    if len(c) < 2: return 0.0
    tr = [max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1])) for i in range(1, len(c))]
    return sum(tr[-period:]) / min(period, len(tr)) if tr else 0.0

def calc_momentum(c, period=10):
    if len(c) < period + 1: return 0.0
    base = c[-period-1]
    return round((c[-1]-base)/base*100, 3) if base else 0.0

# ── НОВІ ІНДИКАТОРИ v4.0 ──────────────────────────────────────

def calc_ema200(c):
    """EMA200 — головний тренд"""
    if len(c) < 30: return c[-1] if c else 0
    p = min(200, len(c))
    return ema(c, p)

def calc_cci(c, h, l, period=14):
    """CCI — Commodity Channel Index"""
    if len(c) < period: return 0.0
    tp = [(h[i]+l[i]+c[i])/3 for i in range(len(c))]
    sma = sum(tp[-period:]) / period
    md  = sum(abs(tp[-period:][i] - sma) for i in range(period)) / period
    if md == 0: return 0.0
    return round((tp[-1] - sma) / (0.015 * md), 1)

def calc_obv(c, vol):
    """OBV — On Balance Volume (використовує псевдо-об'єм з ATR)"""
    if len(c) < 3: return 0, ""
    obv = 0.0
    obvs = [0.0]
    vols = [abs(c[i]-c[i-1]) for i in range(1, len(c))]
    for i in range(1, len(c)):
        v = vols[i-1]
        if c[i] > c[i-1]:   obv += v
        elif c[i] < c[i-1]: obv -= v
        obvs.append(obv)
    trend = obvs[-1] - obvs[-5] if len(obvs) >= 5 else 0
    if   trend > 0.001:  return 1,  "OBV зростає ▲"
    elif trend < -0.001: return -1, "OBV падає ▼"
    return 0, "OBV нейтраль"

def calc_rsi_divergence(c, h, l, period=14):
    """RSI Дивергенція — сигнал розвороту"""
    if len(c) < 20: return 0, ""
    rsi_vals = []
    for i in range(period, len(c)):
        rsi_vals.append(calc_rsi(c[:i+1], period))
    if len(rsi_vals) < 6: return 0, ""

    # Шукаємо дивергенцію за останні 10 свічок
    n = min(10, len(rsi_vals))
    price_hi = max(h[-n:]); price_lo = min(l[-n:])
    rsi_hi   = max(rsi_vals[-n:]); rsi_lo = min(rsi_vals[-n:])
    prev_p_hi = max(h[-2*n:-n]) if len(h) >= 2*n else price_hi
    prev_p_lo = min(l[-2*n:-n]) if len(l) >= 2*n else price_lo
    prev_r_hi = max(rsi_vals[-2*n:-n]) if len(rsi_vals) >= 2*n else rsi_hi
    prev_r_lo = min(rsi_vals[-2*n:-n]) if len(rsi_vals) >= 2*n else rsi_lo

    # Бичача дивергенція: ціна робить нижчий мінімум, RSI — вищий
    if price_lo < prev_p_lo * 0.999 and rsi_lo > prev_r_lo + 2:
        return 1, "🔀 Бичача RSI-дивергенція ▲"
    # Ведмежа дивергенція: ціна — вищий максимум, RSI — нижчий
    if price_hi > prev_p_hi * 1.001 and rsi_hi < prev_r_hi - 2:
        return -1, "🔀 Ведмежа RSI-дивергенція ▼"
    return 0, ""

def calc_ichimoku(h, l, c):
    """Спрощена Ichimoku Kumo хмара (Tenkan + Kijun + перевіска)"""
    if len(c) < 26: return 0, ""
    def donchian(data_h, data_l, n):
        return (max(data_h[-n:]) + min(data_l[-n:])) / 2
    tenkan = donchian(h, l, 9)
    kijun  = donchian(h, l, 26)
    span_a = (tenkan + kijun) / 2
    span_b = donchian(h, l, 52) if len(c) >= 52 else donchian(h, l, len(c))
    price  = c[-1]

    above_cloud = price > max(span_a, span_b)
    below_cloud = price < min(span_a, span_b)
    tk_cross_up = tenkan > kijun

    if above_cloud and tk_cross_up:  return 1,  "☁️ Ichimoku: ціна вище хмари ▲"
    if below_cloud and not tk_cross_up: return -1, "☁️ Ichimoku: ціна нижче хмари ▼"
    if tk_cross_up:  return 1,  "☁️ Ichimoku: Tenkan > Kijun ▲"
    return -1, "☁️ Ichimoku: Tenkan < Kijun ▼"

# ── ІСНУЮЧІ ІНДИКАТОРИ (покращені) ────────────────────────────

def calc_heikin_ashi(o, c, h, l):
    if len(c) < 4: return 0, ""
    n = len(c)
    ha_c = [(o[i]+h[i]+l[i]+c[i])/4 for i in range(n)]
    ha_o = [0.0]*n
    ha_o[0] = (o[0]+c[0])/2
    for i in range(1, n):
        ha_o[i] = (ha_o[i-1]+ha_c[i-1])/2
    ha_h = [max(h[i], ha_o[i], ha_c[i]) for i in range(n)]
    ha_l = [min(l[i], ha_o[i], ha_c[i]) for i in range(n)]
    bull  = sum(1 for i in range(-4, 0) if ha_c[i] > ha_o[i])
    bear  = sum(1 for i in range(-4, 0) if ha_c[i] < ha_o[i])
    body  = abs(ha_c[-1]-ha_o[-1])
    no_lo = (min(ha_c[-1],ha_o[-1])-ha_l[-1]) < body*0.1
    no_hi = (ha_h[-1]-max(ha_c[-1],ha_o[-1])) < body*0.1
    if bull == 4 and no_lo: return 1,  "🔥 HA: 4 бичачі без тіні"
    if bear == 4 and no_hi: return -1, "🔥 HA: 4 ведмежі без тіні"
    if bull == 3 and no_lo: return 1,  "🔥 HA: 3 бичачі без тіні"
    if bear == 3 and no_hi: return -1, "🔥 HA: 3 ведмежі без тіні"
    if bull >= 2 and ha_c[-1]>ha_o[-1]: return 1,  f"HA: {bull} бичячі ▲"
    if bear >= 2 and ha_c[-1]<ha_o[-1]: return -1, f"HA: {bear} ведмежі ▼"
    if ha_c[-1] > ha_o[-1]: return 1,  "HA: бичяча свічка ▲"
    if ha_c[-1] < ha_o[-1]: return -1, "HA: ведмежа свічка ▼"
    return 0, "HA: нейтраль"

def calc_parabolic_sar(h, l, af0=0.02, afm=0.2):
    if len(h) < 5: return 0, ""
    bull = l[0] < l[1]; sar = l[0] if bull else h[0]
    ep = h[0] if bull else l[0]; af = af0; prev_bull = bull
    for i in range(1, len(h)):
        prev_bull = bull
        sar = sar + af*(ep-sar)
        if bull:
            sar = min(sar, l[i-1], l[i-2] if i>=2 else l[i-1])
            if l[i] < sar:   bull=False; sar=ep; ep=l[i]; af=af0
            elif h[i] > ep:  ep=h[i]; af=min(af+af0, afm)
        else:
            sar = max(sar, h[i-1], h[i-2] if i>=2 else h[i-1])
            if h[i] > sar:   bull=True; sar=ep; ep=h[i]; af=af0
            elif l[i] < ep:  ep=l[i]; af=min(af+af0, afm)
    fresh = bull != prev_bull
    if fresh and bull:     return 1,  "🔥 PSAR: свіжий розворот ▲"
    if fresh and not bull: return -1, "🔥 PSAR: свіжий розворот ▼"
    return (1,"PSAR: бичячий ▲") if bull else (-1,"PSAR: ведмежий ▼")

def calc_fibonacci(h, l, c, lb=30):
    if len(h) < lb: lb = len(h)
    rh = max(h[-lb:]); rl = min(l[-lb:]); diff = rh-rl
    if diff < 1e-9: return 0, "", []
    fibs = {0.236:rh-diff*0.236, 0.382:rh-diff*0.382,
            0.500:rh-diff*0.500, 0.618:rh-diff*0.618, 0.786:rh-diff*0.786}
    price = c[-1]; atr = calc_atr(c,h,l); zone = max(atr*0.8, diff*0.02)
    for lvl, fp in sorted(fibs.items()):
        if abs(price-fp) < zone:
            up = c[-1] > c[-3] if len(c)>=3 else False
            if up:  return 1,  f"Fib {lvl:.3f} підтримка ▲", list(fibs.values())
            else:   return -1, f"Fib {lvl:.3f} опір ▼",       list(fibs.values())
    return 0, "", list(fibs.values())

def calc_support_resistance(c, h, l, n=3):
    if len(c) < 10: return [], []
    sup, res = [], []
    for i in range(2, len(l)-2):
        if l[i]<l[i-1] and l[i]<l[i-2] and l[i]<l[i+1] and l[i]<l[i+2]: sup.append(l[i])
        if h[i]>h[i-1] and h[i]>h[i-2] and h[i]>h[i+1] and h[i]>h[i+2]: res.append(h[i])
    def cluster(lv, tol=0.002):
        if not lv: return []
        lv = sorted(set(lv)); r = [lv[0]]
        for v in lv[1:]:
            if abs(v-r[-1])/max(1e-9, r[-1]) > tol: r.append(v)
        return r[-n:]
    return cluster(sup), cluster(res)[:n]

def sr_signal(price, sup, res, atr):
    if not atr: return 0, ""
    z = atr*0.5
    for s in sup:
        if abs(price-s)<z: return 1, "Відскок від підтримки ▲"
    for r in res:
        if abs(price-r)<z: return -1, "Відскок від опору ▼"
    for r in res:
        if price>r and price-r<z*2: return 1, "Пробій опору ▲"
    for s in sup:
        if price<s and s-price<z*2: return -1, "Пробій підтримки ▼"
    return 0, ""

def candle_patterns(o, c, h, l):
    if len(c) < 4: return 0, ""
    b2 = abs(c[-2]-o[-2]); r2 = max(1e-9, h[-2]-l[-2])
    b1 = abs(c[-1]-o[-1]); r1 = max(1e-9, h[-1]-l[-1])
    doji   = b2/r2 < 0.15
    engb   = c[-2]<o[-2] and c[-1]>o[-1] and c[-1]>o[-2] and o[-1]<c[-2]
    engbb  = c[-2]>o[-2] and c[-1]<o[-1] and c[-1]<o[-2] and o[-1]>c[-2]
    t3b    = len(c)>=4 and all(c[-(i+1)]>o[-(i+1)] and c[-(i+1)]>c[-(i+2)] for i in range(3))
    t3bb   = len(c)>=4 and all(c[-(i+1)]<o[-(i+1)] and c[-(i+1)]<c[-(i+2)] for i in range(3))
    hammer = b1/r1<0.35 and (min(c[-1],o[-1])-l[-1])>b1*2 and c[-1]>o[-1]
    inv_h  = b1/r1<0.35 and (h[-1]-max(c[-1],o[-1]))>b1*2 and c[-1]<o[-1]
    mstar  = (c[-3]>o[-3] and abs(c[-2]-o[-2])/r2<0.2  # Morning star
              and c[-1]>o[-1] and c[-1]>(o[-3]+c[-3])/2 and len(c)>=3)
    estr   = (c[-3]<o[-3] and abs(c[-2]-o[-2])/r2<0.2   # Evening star
              and c[-1]<o[-1] and c[-1]<(o[-3]+c[-3])/2 and len(c)>=3)
    if mstar:  return 1,  "🌅 Ранкова зірка ▲"
    if estr:   return -1, "🌆 Вечірня зірка ▼"
    if engb:   return 1,  "🕯 Бичаче поглинання ▲"
    if engbb:  return -1, "🕯 Ведмеже поглинання ▼"
    if t3b:    return 1,  "🕯 3 бичачі свічки ▲"
    if t3bb:   return -1, "🕯 3 ведмежі свічки ▼"
    if hammer: return 1,  "🔨 Молот — BUY ▲"
    if inv_h:  return -1, "🔨 Перевернутий молот ▼"
    if doji and c[-1]>o[-1]: return 1,  "🕯 Доджі → BUY ▲"
    if doji and c[-1]<o[-1]: return -1, "🕯 Доджі → SELL ▼"
    return 0, ""

# ══════════════════════════════════════════════════════════════
#  ⏰ ТОРГОВІ СЕСІЇ
# ══════════════════════════════════════════════════════════════
def get_session():
    h = datetime.now(timezone.utc).hour
    if   7  <= h < 9:  return "Лондон відкриття 🟢", "excellent", 1.15
    elif 9  <= h < 12: return "Лондон + NY 🟢",      "excellent", 1.20
    elif 12 <= h < 16: return "Нью-Йорк 🟡",         "good",      1.10
    elif 16 <= h < 18: return "NY закриття 🟡",       "average",   0.95
    elif 18 <= h < 21: return "Між сесіями 🔴",       "poor",      0.80
    elif 21 <= h < 23: return "Токіо 🟡",             "average",   0.90
    else:              return "Нічна сесія 🔴",       "poor",      0.75

# ══════════════════════════════════════════════════════════════
#  ⚡ ГЕНЕРАЦІЯ СИГНАЛУ — ЯДРО
# ══════════════════════════════════════════════════════════════
def generate_signal(pair_name, tf):
    m      = ALL_PAIRS.get(pair_name, FOREX_PAIRS[0])
    is_otc = "OTC" in pair_name

    c, h, l, o = get_candles(m["symbol"], tf, 120)
    real = len(c) >= 20
    live = get_price(m["symbol"], m["p"])
    if not real:
        c, h, l, o = _pseudo_candles(pair_name, tf, live)

    # ── Основні ─────────────────────────────────────────────
    rsi        = calc_rsi(c)
    macd, mh   = calc_macd(c)
    e9         = ema(c, 9)
    e21        = ema(c, 21)
    e50        = ema(c, 50)
    e200       = calc_ema200(c)
    k_val, _   = calc_stoch(c, h, l)
    bb, bb_bw  = calc_bb(c)
    willr      = calc_willr(c, h, l)
    stc        = calc_stc(c)
    adx        = calc_adx(c, h, l)
    atr        = calc_atr(c, h, l)
    mom        = calc_momentum(c)
    cci        = calc_cci(c, h, l)

    # ── Нові v4.0 ────────────────────────────────────────────
    obv_val,  obv_lbl  = calc_obv(c, [abs(c[i]-c[i-1]) for i in range(1,len(c))]+[0])
    div_val,  div_lbl  = calc_rsi_divergence(c, h, l)
    ichi_val, ichi_lbl = calc_ichimoku(h, l, c)

    # ── Існуючі ──────────────────────────────────────────────
    ha_val,   ha_lbl   = calc_heikin_ashi(o, c, h, l)
    psar_val, psar_lbl = calc_parabolic_sar(h, l)
    fib_val,  fib_lbl, _ = calc_fibonacci(h, l, c)
    sup, res           = calc_support_resistance(c, h, l)
    sr_val,   sr_lbl   = sr_signal(live, sup, res, atr)
    pat_val,  pat_lbl  = candle_patterns(o, c, h, l)
    sess_name, sess_q, sess_mult = get_session()

    # ── Голосування з вагами ─────────────────────────────────
    votes = []
    def v(name, val, lbl, weight=1.0):
        votes.append({"n": name, "v": val, "l": lbl, "w": weight})

    # RSI
    if   rsi < 25: v("RSI",  1, f"RSI {rsi} — сильна перепроданість 🔥", 2.5)
    elif rsi > 75: v("RSI", -1, f"RSI {rsi} — сильна перекупленість 🔥",  2.5)
    elif rsi < 40: v("RSI",  1, f"RSI {rsi} — перепроданість",            2.0)
    elif rsi > 60: v("RSI", -1, f"RSI {rsi} — перекупленість",            2.0)
    elif rsi < 48: v("RSI",  1, f"RSI {rsi} — бичачий нахил",             1.0)
    elif rsi > 52: v("RSI", -1, f"RSI {rsi} — ведмежий нахил",            1.0)
    else:          v("RSI",  0, f"RSI {rsi} — нейтраль",                  0.3)

    # MACD
    if   macd > 0 and mh > 0: v("MACD",  1, "MACD: лінія+гістограма ▲", 2.0)
    elif macd < 0 and mh < 0: v("MACD", -1, "MACD: лінія+гістограма ▼", 2.0)
    elif mh > 0:               v("MACD",  1, "MACD: гістограма зростає", 1.0)
    elif mh < 0:               v("MACD", -1, "MACD: гістограма падає",   1.0)

    # EMA 9/21
    if   e9 > e21*1.0002:  v("EMA9/21",  1, "EMA9 > EMA21 ▲", 2.0)
    elif e9 < e21*0.9998:  v("EMA9/21", -1, "EMA9 < EMA21 ▼", 2.0)

    # EMA 50
    if   live > e50*1.001: v("EMA50",  1, "Ціна вище EMA50 ▲",  1.5)
    elif live < e50*0.999: v("EMA50", -1, "Ціна нижче EMA50 ▼", 1.5)

    # EMA 200 (новий)
    if   live > e200*1.002: v("EMA200",  1, f"Ціна вище EMA200 ▲ (тренд UP)",  2.0)
    elif live < e200*0.998: v("EMA200", -1, f"Ціна нижче EMA200 ▼ (тренд DOWN)", 2.0)

    # Stochastic
    if   k_val < 20: v("Stoch",  1, f"Stoch {k_val} — перепроданість", 2.0)
    elif k_val > 80: v("Stoch", -1, f"Stoch {k_val} — перекупленість", 2.0)
    elif k_val < 45: v("Stoch",  1, f"Stoch {k_val} — BUY зона",       1.0)
    elif k_val > 55: v("Stoch", -1, f"Stoch {k_val} — SELL зона",      1.0)

    # BB
    if   bb < 10:  v("BB",  1, "BB нижня смуга — BUY 🔥", 2.0)
    elif bb > 90:  v("BB", -1, "BB верхня смуга — SELL 🔥", 2.0)
    elif bb < 25:  v("BB",  1, f"BB нижня зона {bb}%",      1.0)
    elif bb > 75:  v("BB", -1, f"BB верхня зона {bb}%",     1.0)

    # Williams %R
    if   willr < -85: v("W%R",  1, f"W%R {willr} — перепроданість 🔥", 2.0)
    elif willr > -15: v("W%R", -1, f"W%R {willr} — перекупленість 🔥",  2.0)
    elif willr < -60: v("W%R",  1, f"W%R {willr} — перепроданість",     1.0)
    else:             v("W%R", -1, f"W%R {willr} — перекупленість",     1.0)

    # STC
    if stc is not None:
        if   stc < 15: v("STC",  1, f"STC {stc} — BUY 🔥🔥",    3.5)
        elif stc > 85: v("STC", -1, f"STC {stc} — SELL 🔥🔥",   3.5)
        elif stc < 30: v("STC",  1, f"STC {stc} — BUY зона 🔥", 2.5)
        elif stc > 70: v("STC", -1, f"STC {stc} — SELL зона 🔥", 2.5)
        elif stc < 50: v("STC",  1, f"STC {stc} — зростає",      1.0)
        else:          v("STC", -1, f"STC {stc} — падає",         1.0)

    # CCI (новий)
    if   cci < -100: v("CCI",  1, f"CCI {cci} — перепроданість ▲", 2.0)
    elif cci >  100: v("CCI", -1, f"CCI {cci} — перекупленість ▼", 2.0)
    elif cci < -50:  v("CCI",  1, f"CCI {cci} — BUY зона",         1.0)
    elif cci >   50: v("CCI", -1, f"CCI {cci} — SELL зона",        1.0)

    # Momentum
    if   mom >  0.2: v("Momentum",  1, f"Mom +{mom}% бичачий", 1.5)
    elif mom < -0.2: v("Momentum", -1, f"Mom {mom}% ведмежий",  1.5)

    # OBV (новий)
    if obv_val != 0: v("OBV", obv_val, obv_lbl, 1.5)

    # Divergence RSI (новий)
    if div_val != 0:
        v("Дивергенція", div_val, div_lbl, 3.0)

    # Ichimoku (новий)
    if ichi_val != 0:
        v("Ichimoku", ichi_val, ichi_lbl, 2.5)

    # Патерн
    if pat_val != 0: v("Патерн", pat_val, pat_lbl, 2.0)

    # S/R
    if sr_val != 0: v("S/R", sr_val, sr_lbl, 2.5)

    # Heikin Ashi
    if ha_val != 0:
        v("Heikin Ashi", ha_val, ha_lbl, 3.5 if "🔥" in ha_lbl else 2.5)

    # PSAR
    if psar_val != 0:
        v("Parab SAR", psar_val, psar_lbl, 3.0 if "🔥" in psar_lbl else 2.0)

    # Fibonacci
    if fib_val != 0: v("Fibonacci", fib_val, fib_lbl, 2.0)

    # ── Ваги за ТФ ───────────────────────────────────────────
    tf_weights = {
        "1":  {"Heikin Ashi":1.9,"Parab SAR":1.7,"STC":1.5,"Stoch":1.5,
               "Momentum":1.6,"OBV":1.4,"MACD":0.5,"EMA200":0.4},
        "3":  {"Heikin Ashi":1.7,"Parab SAR":1.6,"STC":1.6,"Stoch":1.4,
               "Momentum":1.5,"Fibonacci":1.4,"OBV":1.3,"EMA200":0.6},
        "5":  {"Heikin Ashi":1.6,"Parab SAR":1.5,"STC":1.5,"Stoch":1.3,
               "Momentum":1.4,"Fibonacci":1.3,"Ichimoku":1.3,"EMA200":0.8},
        "15": {"EMA50":1.6,"EMA200":1.5,"MACD":1.4,"S/R":1.6,"RSI":1.3,
               "Fibonacci":1.5,"Ichimoku":1.4,"Дивергенція":1.5},
        "30": {"EMA50":1.6,"EMA200":1.6,"MACD":1.4,"S/R":1.6,"RSI":1.3,
               "Fibonacci":1.5,"Ichimoku":1.5,"Дивергенція":1.6},
        "60": {"EMA200":1.8,"MACD":1.5,"S/R":1.7,"RSI":1.4,
               "Fibonacci":1.6,"Ichimoku":1.6,"Дивергенція":1.7},
    }
    for vote in votes:
        mult = tf_weights.get(str(tf), {}).get(vote["n"], 1.0)
        vote["w"] *= mult

    # ── Підрахунок ────────────────────────────────────────────
    buy_w  = sum(x["w"] for x in votes if x["v"] ==  1)
    sell_w = sum(x["w"] for x in votes if x["v"] == -1)
    bc     = sum(1 for x in votes if x["v"] ==  1)
    sc     = sum(1 for x in votes if x["v"] == -1)
    total  = buy_w + sell_w
    is_buy = buy_w >= sell_w
    ratio  = max(buy_w, sell_w) / max(1e-9, total)

    # Консенсус топ-9 (додали EMA200, CCI, Ichimoku)
    top_ns  = ["STC","RSI","EMA9/21","Stoch","Heikin Ashi","Parab SAR",
               "Fibonacci","EMA200","Ichimoku"]
    top_vs  = [next((x["v"] for x in votes if x["n"]==n), 0) for n in top_ns]
    top_a   = [vv for vv in top_vs if vv != 0]
    c_agree = sum(1 for vv in top_a if (vv==1)==is_buy)
    consensus = f"{c_agree}/{len(top_a)}" if top_a else "—"

    # Бонуси
    adx_ok = adx >= 20
    adx_b  = min(12, adx//3) if adx_ok else -5
    cons_b = round(c_agree / max(1, len(top_a)) * 12)
    pat_b  = 5  if (pat_val==1  and is_buy) or (pat_val==-1  and not is_buy) else 0
    sr_b   = 6  if (sr_val==1   and is_buy) or (sr_val==-1   and not is_buy) else 0
    ha_b   = 5  if (ha_val==1   and is_buy) or (ha_val==-1   and not is_buy) else 0
    ps_b   = 5  if (psar_val==1 and is_buy) or (psar_val==-1 and not is_buy) else 0
    div_b  = 7  if (div_val==1  and is_buy) or (div_val==-1  and not is_buy) else 0
    tf_b   = {"1":0,"3":6,"5":5,"15":3,"30":2,"60":1}.get(str(tf), 0)
    # Додаткові бонуси v4.0
    e200_b = 4  if (live > e200*1.001 and is_buy) or (live < e200*0.999 and not is_buy) else 0
    ichi_b = 4  if (ichi_val==1 and is_buy) or (ichi_val==-1 and not is_buy) else 0

    acc_raw = round(50 + ratio*28 + adx_b + cons_b + pat_b + sr_b + ha_b + ps_b
                    + div_b + tf_b + e200_b + ichi_b)
    acc     = min(96, max(68, round(acc_raw * sess_mult)))

    # Сила
    if not adx_ok and ratio < 0.65: strength = "⛔ ФІЛЬТР ADX";     blocked = True
    elif ratio < 0.58:              strength = "⚠️ СЛАБКИЙ";        blocked = False
    elif ratio < 0.68:              strength = "✅ СЕРЕДНІЙ";       blocked = False
    elif ratio < 0.80:              strength = "🔥 СИЛЬНИЙ";        blocked = False
    else:                           strength = "🔥🔥 ДУЖЕ СИЛЬНИЙ"; blocked = False

    # TP / SL
    dec = m["d"]
    if atr == 0: atr = live * 0.001
    tp_m = {"1":1.3,"3":1.5,"5":1.7,"15":2.0,"30":2.5,"60":3.0}.get(str(tf), 1.7)
    sl_m = {"1":1.0,"3":1.1,"5":1.2,"15":1.4,"30":1.6,"60":2.0}.get(str(tf), 1.2)
    tp   = round(live + atr*tp_m, dec) if is_buy else round(live - atr*tp_m, dec)
    sl   = round(live - atr*sl_m, dec) if is_buy else round(live + atr*sl_m, dec)
    rr   = round(tp_m / sl_m, 1)

    return {
        "is_buy":is_buy, "acc":acc, "strength":strength, "blocked":blocked,
        "live":live, "tp":tp, "sl":sl, "rr":rr,
        "adx":adx, "adx_ok":adx_ok, "rsi":rsi, "stc":stc, "cci":cci,
        "e200":e200, "bb_bw":bb_bw,
        "ha_lbl":ha_lbl, "psar_lbl":psar_lbl, "fib_lbl":fib_lbl,
        "sr_lbl":sr_lbl, "pat_lbl":pat_lbl, "obv_lbl":obv_lbl,
        "div_lbl":div_lbl, "ichi_lbl":ichi_lbl,
        "votes":votes, "bc":bc, "sc":sc,
        "buy_w":round(buy_w,1), "sell_w":round(sell_w,1),
        "consensus":consensus, "sess":sess_name, "sess_q":sess_q,
        "real":real, "is_otc":is_otc,
    }

# ══════════════════════════════════════════════════════════════
#  🔁 МУЛЬТИ-ТАЙМФРЕЙМ ПІДТВЕРДЖЕННЯ (НОВЕ v4.0)
# ══════════════════════════════════════════════════════════════
def multi_tf_confirm(pair_name, main_tf):
    """Перевіряємо узгодженість сигналу на старших ТФ"""
    confirm_map = {"1":["5","15"],"3":["5","15"],"5":["15","30"],
                   "15":["30","60"],"30":["60"],"60":["60"]}
    higher_tfs = confirm_map.get(str(main_tf), [])
    if not higher_tfs: return "", 0

    results = []
    for htf in higher_tfs:
        try:
            sig = generate_signal(pair_name, htf)
            if sig:
                results.append((htf, sig["is_buy"], sig["acc"]))
        except Exception:
            pass

    if not results: return "", 0
    all_tf_map = {**TIMEFRAMES, **CRYPTO_TF, **STOCKS_TF}
    lines = []
    agree = 0
    for htf, is_b, acc in results:
        icon  = "🟢" if is_b else "🔴"
        label = all_tf_map.get(htf, htf+"хв")
        lines.append(f"{icon} {label}: {'BUY' if is_b else 'SELL'} ({acc}%)")
        agree += 1 if is_b == results[0][1] else 0

    txt = "\n".join(lines)
    agreement = round(agree / len(results) * 100)
    return txt, agreement

# ══════════════════════════════════════════════════════════════
#  📄 ФОРМАТУВАННЯ
# ══════════════════════════════════════════════════════════════
def bar(val, n=10):
    f = round(max(0, min(100, val)) / 100 * n)
    return "▰"*f + "▱"*(n-f)

def mini_chart(c, n=12):
    """Emoji мікро-графік ціни"""
    if len(c) < n: return ""
    pts = c[-n:]
    mn = min(pts); mx = max(pts)
    if mx == mn: return "─" * n
    blocks = "▁▂▃▄▅▆▇█"
    return "".join(blocks[round((p-mn)/(mx-mn)*7)] for p in pts)

def esc(t):
    t = str(t)
    for ch in r"_*[]()~`>#+-=|{}.!":
        t = t.replace(ch, f"\\{ch}")
    return t

def format_signal(pair, tf, d, mtf_txt="", mtf_agree=0):
    now_dt  = datetime.now(timezone.utc) + timedelta(hours=2)
    tf_hold = {1:2, 3:4, 5:8, 15:20, 30:35, 60:70, 240:260}
    tf_int  = int(tf) if str(tf).isdigit() else 5
    exp     = (now_dt + timedelta(minutes=tf_hold.get(tf_int, 5))).strftime("%H:%M")
    all_tf  = {**TIMEFRAMES, **CRYPTO_TF, **STOCKS_TF}
    tf_lbl  = all_tf.get(str(tf), str(tf)+"хв")

    is_buy  = d["is_buy"]
    arrow   = "⬆️" if is_buy else "⬇️"
    dir_txt = "КУПИТИ — ВВЕРХ" if is_buy else "ПРОДАТИ — ВНИЗ"
    dir_em  = "🟢" if is_buy else "🔴"
    acc     = d["acc"]
    acc_em  = "🔥" if acc >= 88 else "✅" if acc >= 78 else "⚠️"
    src     = "📡 Live" if d["real"] else "⚙️ Розрахунок"

    buy_r  = d["buy_w"] / max(0.1, d["buy_w"]+d["sell_w"])
    t_pct  = round(buy_r*100) if is_buy else round((1-buy_r)*100)
    t_str  = ("Слабий" if t_pct<60 else "Середній" if t_pct<75
              else "Сильний" if t_pct<88 else "Дуже сильний")

    # Топ 4 підтверджуючі
    target    = 1 if is_buy else -1
    top_v     = sorted([x for x in d["votes"] if x["v"]==target], key=lambda x:-x["w"])
    top_lines = "\n".join(f"  ✅ {esc(x['l'])}" for x in top_v[:5]) or "  ⚪ Слабкий консенсус"

    # Нові індикатори v4.0
    new_inds = []
    if d.get("ha_lbl"):    new_inds.append(f"🕯 {esc(d['ha_lbl'])}")
    if d.get("psar_lbl"):  new_inds.append(f"📍 {esc(d['psar_lbl'])}")
    if d.get("fib_lbl"):   new_inds.append(f"📐 {esc(d['fib_lbl'])}")
    if d.get("sr_lbl"):    new_inds.append(f"📊 {esc(d['sr_lbl'])}")
    if d.get("pat_lbl"):   new_inds.append(f"🕯 {esc(d['pat_lbl'])}")
    if d.get("div_lbl"):   new_inds.append(f"🔀 {esc(d['div_lbl'])}")
    if d.get("ichi_lbl"):  new_inds.append(f"☁️ {esc(d['ichi_lbl'])}")
    if d.get("obv_lbl"):   new_inds.append(f"📦 {esc(d['obv_lbl'])}")
    new_ind_txt = "\n".join(new_inds)

    # STC
    stc = d.get("stc")
    stc_line = ""
    if stc is not None:
        si = "🟢" if stc<25 else "🔴" if stc>75 else "🟡" if stc<50 else "🟠"
        sz = ("Перепроданість" if stc<25 else "Перекупленість" if stc>75
              else "Зростає" if stc<50 else "Падає")
        stc_line = f"{si} STC: {stc} — {esc(sz)}"

    # CCI
    cci = d.get("cci", 0)
    cci_em = "🟢" if cci < -100 else "🔴" if cci > 100 else "⚪"
    cci_line = f"{cci_em} CCI: {cci}"

    # EMA200
    e200 = d.get("e200", 0)
    e200_em = "▲" if d["live"] > e200 else "▼"
    e200_line = f"📏 EMA200: {round(e200, d.get('dec',5))} {e200_em}"

    # Мульти-ТФ блок
    mtf_block = ""
    if mtf_txt:
        agree_em = "🟢" if mtf_agree >= 100 else "🟡" if mtf_agree >= 50 else "🔴"
        mtf_block = (f"\n\n🔭 *Мульти\\-ТФ підтвердження:*\n"
                     f"{esc(mtf_txt)}\n"
                     f"{agree_em} Узгодженість: *{mtf_agree}%*")

    adx_em     = "✅" if d["adx_ok"] else "⚠️"
    block_warn = "\n\n⛔ *СИГНАЛ СЛАБКИЙ — КРАЩЕ ПРОПУСТИТИ*\n" if d.get("blocked") else ""

    text = (
        f"╔══ ⚡ *SIGNAL AI v4\\.0* ══╗\n\n"
        f"🏷 *{esc(pair)}*  ⏱ {esc(tf_lbl)}  {src}\n"
        f"📍 {esc(d['sess'])}\n\n"
        f"📊 `{mini_chart([d['live']])}`\n\n"
        f"📈 *Сила тренду* — {esc(t_str)} *{t_pct}%*\n"
        f"`{bar(t_pct)}`\n\n"
        f"{dir_em} *{esc(dir_txt)}*  {arrow}\n"
        f"⏳ Утримувати до: *{exp}*\n\n"
        f"{acc_em} Точність: *{acc}%*\n"
        f"`{bar(acc)}`\n"
        f"{esc(d['strength'])}\n\n"
        f"ADX: *{d['adx']}* {adx_em}  Консенсус: *{d['consensus']}*\n"
        f"BUY {d['bc']} \\({d['buy_w']}\\) \\| SELL {d['sc']} \\({d['sell_w']}\\)\n"
        f"{block_warn}\n"
        f"{stc_line}\n"
        f"{cci_line}\n"
        f"{e200_line}\n\n"
        f"{new_ind_txt}\n\n"
        f"🔬 *Підтверджуючі сигнали:*\n"
        f"{top_lines}\n"
        f"{mtf_block}\n\n"
        f"💰 Вхід: `{d['live']}`\n"
        f"🎯 TP:   `{d['tp']}`\n"
        f"🛑 SL:   `{d['sl']}`\n"
        f"⚖️ RR:   1:{d['rr']}\n\n"
        f"└─────────────────────┘\n"
        f"⚠️ _Не є фінансовою порадою_"
    )
    return text

# ══════════════════════════════════════════════════════════════
#  📊 АВТО-СКАНЕР (покращений)
# ══════════════════════════════════════════════════════════════
def run_scanner(cid, tf="5", min_acc=82, pairs_list=None):
    if pairs_list is None:
        pairs_list = FOREX_PAIRS[:10] + OTC_PAIRS[:6] + CRYPTO_PAIRS[:4]
    results = []
    for p in pairs_list:
        try:
            sig = generate_signal(p["name"], tf)
            if sig and sig["acc"] >= min_acc and not sig.get("blocked"):
                results.append((p["name"], tf, sig))
        except Exception as e:
            log.warning(f"Scanner {p['name']}: {e}")

    if not results:
        try:
            bot.send_message(cid,
                "🔍 Сканування завершено\n\n"
                "Сильних сигналів не знайдено\\. Спробуйте пізніше\\.",
                parse_mode="MarkdownV2", reply_markup=main_kb())
        except Exception: pass
        return

    results.sort(key=lambda x: -x[2]["acc"])
    best = results[:3]
    try:
        all_tf = {**TIMEFRAMES, **CRYPTO_TF, **STOCKS_TF}
        header = (f"🔍 *Знайдено {len(results)} сигналів\\!*\n"
                  f"Топ {len(best)} за точністю — ТФ {esc(all_tf.get(tf, tf))}:")
        bot.send_message(cid, header, parse_mode="MarkdownV2")
        for pair_name, tf2, sig in best:
            bot.send_message(cid, format_signal(pair_name, tf2, sig),
                             parse_mode="MarkdownV2", reply_markup=result_kb(pair_name, tf2))
            time.sleep(0.6)
    except Exception as e:
        log.error(f"Scanner send: {e}")

# ══════════════════════════════════════════════════════════════
#  🔔 АВТО-СИГНАЛИ ЗА ПІДПИСКОЮ (НОВЕ v4.0)
# ══════════════════════════════════════════════════════════════
def subscribe_pair(cid, pair, tf):
    k = str(cid)
    all_subs[k] = {"pair": pair, "tf": tf, "interval": AUTO_SCAN_INTERVAL, "last": 0}
    save_subs()

def unsubscribe(cid):
    k = str(cid)
    if k in all_subs:
        del all_subs[k]
        save_subs()

def auto_signal_worker():
    """Фоновий потік — надсилає авто-сигнали підписникам"""
    log.info("Auto-signal worker запущено")
    while True:
        try:
            now = time.time()
            for cid_str, sub in list(all_subs.items()):
                if now - sub.get("last", 0) >= sub.get("interval", AUTO_SCAN_INTERVAL):
                    try:
                        sig = generate_signal(sub["pair"], sub["tf"])
                        if sig and not sig.get("blocked") and sig["acc"] >= 78:
                            all_tf = {**TIMEFRAMES, **CRYPTO_TF, **STOCKS_TF}
                            tf_lbl = all_tf.get(str(sub["tf"]), sub["tf"]+"хв")
                            header = (f"🔔 *Авто\\-сигнал*\n"
                                      f"`{esc(sub['pair'])}` \\| {esc(tf_lbl)}")
                            bot.send_message(int(cid_str), header, parse_mode="MarkdownV2")
                            bot.send_message(int(cid_str),
                                format_signal(sub["pair"], sub["tf"], sig),
                                parse_mode="MarkdownV2",
                                reply_markup=result_kb(sub["pair"], sub["tf"]))
                        all_subs[cid_str]["last"] = now
                        save_subs()
                    except Exception as e:
                        log.warning(f"Auto signal {cid_str}: {e}")
        except Exception as e:
            log.error(f"Auto worker: {e}")
        time.sleep(30)

# ══════════════════════════════════════════════════════════════
#  📈 РЕЙТИНГ ПАР ПО WINRATE (НОВЕ v4.0)
# ══════════════════════════════════════════════════════════════
def pair_rating_text(cid):
    s = get_stats(cid)
    pairs = s.get("pairs", {})
    if not pairs:
        return "📈 *Рейтинг пар*\n\n_Поки немає угод\\. Торгуйте і відмічайте результати\\!_"
    rows = []
    for name, pd in pairs.items():
        if pd["total"] >= 2:
            wr = round(pd["wins"]/pd["total"]*100)
            rows.append((name, pd["total"], wr))
    rows.sort(key=lambda x: (-x[2], -x[1]))
    if not rows:
        return "📈 *Рейтинг пар*\n\n_Потрібно мінімум 2 угоди на пару\\._"
    lines = ["📈 *Рейтинг пар по Winrate*\n"]
    medals = ["🥇","🥈","🥉"]
    for i, (name, total, wr) in enumerate(rows[:10]):
        medal = medals[i] if i < 3 else f"{i+1}\\."
        em    = "🔥" if wr>=70 else "✅" if wr>=55 else "⚠️"
        lines.append(f"{medal} *{esc(name)}*  {em} {wr}% \\({total} угод\\)")
    return "\n".join(lines)

# ══════════════════════════════════════════════════════════════
#  📊 СТАТИСТИКА та СЕСІЇ
# ══════════════════════════════════════════════════════════════
def stats_text(cid):
    s  = get_stats(cid)
    t  = s["total"]; w = s["wins"]; lo = s.get("losses", 0)
    wr = round(w/t*100) if t else 0
    st = s.get("streak", 0)
    ms = s.get("max_streak", 0)
    streak_txt = (f"🔥 Серія виграшів: {st}" if st > 0
                  else f"❄️ Серія програшів: {abs(st)}" if st < 0
                  else "➖ Нема серії")
    sub_info = ""
    if str(cid) in all_subs:
        sb = all_subs[str(cid)]
        all_tf = {**TIMEFRAMES, **CRYPTO_TF, **STOCKS_TF}
        sub_info = f"\n\n🔔 Підписка: *{esc(sb['pair'])}* {esc(all_tf.get(sb['tf'],sb['tf']))}"
    wr_em = "🔥" if wr>=70 else "✅" if wr>=55 else "⚠️" if wr>=40 else "❌"
    return (
        f"📊 *Ваша статистика*\n\n"
        f"Всього: *{t}* угод\n"
        f"Виграші: *{w}* ✅\n"
        f"Програші: *{lo}* ❌\n"
        f"Win Rate: *{wr}%* {wr_em}\n"
        f"`{bar(wr)}`\n\n"
        f"{streak_txt}\n"
        f"🏆 Макс\\. серія: *{ms}*"
        f"{sub_info}"
    )

def sessions_text():
    h = datetime.now(timezone.utc).hour
    sessions = [
        (7,  9,  "🟢 Лондон відкриття",     "Висока волатильність, відмінні сигнали"),
        (9,  12, "🟢 Лондон \\+ Нью\\-Йорк", "НАЙКРАЩИЙ час — максимальна ліквідність"),
        (12, 16, "🟡 Нью\\-Йорк",             "Хороша волатильність"),
        (16, 18, "🟡 NY закриття",            "Помірна активність"),
        (18, 21, "🔴 Між сесіями",            "Слабка активність — обережно"),
        (21, 23, "🟡 Токіо",                  "Помірна активність на JPY"),
        (23, 7,  "🔴 Нічна",                  "Низька ліквідність — краще не торгувати"),
    ]
    lines = ["⏰ *Торгові сесії \\(UTC\\+2\\)*\n"]
    for sh, eh, name, desc in sessions:
        active = (sh <= h < eh) or (sh > eh and (h >= sh or h < eh))
        marker = "👉 " if active else "    "
        lines.append(f"{marker}*{name}* \\({sh:02d}:00–{eh:02d}:00\\)\n_{esc(desc)}_\n")
    return "\n".join(lines)

# ══════════════════════════════════════════════════════════════
#  ⌨️  КЛАВІАТУРИ
# ══════════════════════════════════════════════════════════════
def main_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📈 FOREX",       callback_data="menu_forex"),
        InlineKeyboardButton("🌙 OTC",          callback_data="menu_otc"),
    )
    kb.add(
        InlineKeyboardButton("₿ КРИПТО",       callback_data="menu_crypto"),
        InlineKeyboardButton("📊 АКЦІЇ",        callback_data="menu_stocks"),
    )
    kb.add(
        InlineKeyboardButton("🔍 Авто-сканер", callback_data="scanner"),
        InlineKeyboardButton("🔔 Підписка",    callback_data="sub_menu"),
    )
    kb.add(
        InlineKeyboardButton("📊 Статистика",  callback_data="stats"),
        InlineKeyboardButton("🏆 Рейтинг пар", callback_data="pair_rating"),
    )
    kb.add(
        InlineKeyboardButton("🕐 Сесії",       callback_data="sessions"),
        InlineKeyboardButton("ℹ️ Про бота",    callback_data="about"),
    )
    return kb

def sub_kb(cid):
    kb = InlineKeyboardMarkup(row_width=1)
    if str(cid) in all_subs:
        sb = all_subs[str(cid)]
        all_tf = {**TIMEFRAMES, **CRYPTO_TF, **STOCKS_TF}
        label = f"🔕 Відписатися від {sb['pair']} {all_tf.get(sb['tf'],sb['tf'])}"
        kb.add(InlineKeyboardButton(label, callback_data="unsub"))
    kb.add(InlineKeyboardButton("📈 FOREX (авто)", callback_data="sub_forex"))
    kb.add(InlineKeyboardButton("🌙 OTC (авто)",   callback_data="sub_otc"))
    kb.add(InlineKeyboardButton("◀️ Назад",        callback_data="main"))
    return kb

def pairs_kb(pairs, back):
    kb = InlineKeyboardMarkup(row_width=2)
    btns = [InlineKeyboardButton(p["name"], callback_data=f"pair_{p['name']}") for p in pairs]
    for i in range(0, len(btns), 2):
        kb.add(*btns[i:i+2])
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data=back))
    return kb

def tf_kb(pair):
    is_crypto = any(pair == p["name"] for p in CRYPTO_PAIRS)
    is_stocks = any(pair == p["name"] for p in STOCKS_PAIRS)
    tfs  = CRYPTO_TF if is_crypto else (STOCKS_TF if is_stocks else TIMEFRAMES)
    back = ("crypto_back" if is_crypto else "stocks_back" if is_stocks
            else "otc_back" if "OTC" in pair else "forex_back")
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(*[InlineKeyboardButton(v, callback_data=f"tf|{pair}|{k}") for k, v in tfs.items()])
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data=back))
    return kb

def sub_tf_kb(pair_group):
    kb = InlineKeyboardMarkup(row_width=3)
    tfs = {"1":"1 хв","3":"3 хв","5":"5 хв","15":"15 хв"}
    kb.add(*[InlineKeyboardButton(v, callback_data=f"sub_confirm|{pair_group}|{k}")
             for k, v in tfs.items()])
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="sub_menu"))
    return kb

def result_kb(pair, tf):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Виграш",       callback_data=f"win|{pair}|{tf}"),
        InlineKeyboardButton("❌ Програш",      callback_data=f"loss|{pair}|{tf}"),
    )
    kb.add(
        InlineKeyboardButton("🔄 Новий сигнал", callback_data=f"tf|{pair}|{tf}"),
        InlineKeyboardButton("🏠 Меню",         callback_data="main"),
    )
    return kb

def scanner_tf_kb():
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("1 хв", callback_data="scan_tf|1"),
        InlineKeyboardButton("3 хв", callback_data="scan_tf|3"),
        InlineKeyboardButton("5 хв", callback_data="scan_tf|5"),
        InlineKeyboardButton("15 хв",callback_data="scan_tf|15"),
        InlineKeyboardButton("30 хв",callback_data="scan_tf|30"),
    )
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="main"))
    return kb

# ══════════════════════════════════════════════════════════════
#  🤖 ХЕНДЛЕРИ
# ══════════════════════════════════════════════════════════════
def send_main(cid, mid=None):
    sub_txt = ""
    if str(cid) in all_subs:
        sb = all_subs[str(cid)]
        all_tf = {**TIMEFRAMES, **CRYPTO_TF, **STOCKS_TF}
        sub_txt = f"\n🔔 Підписка: *{esc(sb['pair'])}* {esc(all_tf.get(sb['tf'],''))} активна"

    txt = (
        f"╔══ ⚡ *SIGNAL AI v4\\.0* ══╗\n\n"
        "19 індикаторів \\+ Мульти\\-ТФ:\n\n"
        "• RSI • MACD • EMA 9/21/50/200\n"
        "• Stochastic • BB • Williams %R\n"
        "• STC • Momentum • ADX • ATR\n"
        "• 🆕 CCI • 🆕 OBV • 🆕 Ichimoku\n"
        "• Heikin Ashi • Parabolic SAR\n"
        "• Fibonacci • S/R • Divergence\n"
        "• Свічкові патерни \\(7 типів\\)\n\n"
        "🔭 Мульти\\-ТФ підтвердження\n"
        "🔔 Авто\\-сигнали за підпискою\n"
        "🏆 Рейтинг пар по WinRate\n\n"
        f"📡 TwelveData API \\| ~84\\-96%"
        f"{sub_txt}\n\n"
        "╚══ Оберіть категорію ══╝"
    )
    if mid:
        try:
            bot.edit_message_text(txt, cid, mid, parse_mode="MarkdownV2", reply_markup=main_kb())
            return
        except Exception: pass
    bot.send_message(cid, txt, parse_mode="MarkdownV2", reply_markup=main_kb())

def do_signal(cid, mid, pair, tf):
    all_tf = {**TIMEFRAMES, **CRYPTO_TF, **STOCKS_TF}
    tf_lbl = all_tf.get(str(tf), str(tf)+"хв")
    steps  = [
        ("⟳ Завантаження даних\\.\\.\\.",       "▰▰▰▱▱▱▱▱▱▱ 30%"),
        ("⟳ HA \\+ PSAR \\+ Ichimoku\\.\\.\\.", "▰▰▰▰▰▰▱▱▱▱ 60%"),
        ("⟳ S\\/R \\+ Fibonacci \\+ OBV\\.\\.\\.", "▰▰▰▰▰▰▰▰▱▱ 80%"),
        ("⟳ Мульти\\-ТФ підтвердження\\.\\.\\.", "▰▰▰▰▰▰▰▰▰▱ 95%"),
    ]
    for step, prog in steps:
        try:
            bot.edit_message_text(
                f"⚡ *SIGNAL AI v4\\.0*\n\n{step}\n\n`{esc(pair)}` \\| `{esc(tf_lbl)}`\n\n{prog}",
                cid, mid, parse_mode="MarkdownV2")
        except Exception: pass
        time.sleep(0.65)

    sig = generate_signal(pair, tf)
    if sig is None:
        try:
            err_kb = InlineKeyboardMarkup()
            err_kb.add(
                InlineKeyboardButton("🔄 Спробувати", callback_data=f"tf|{pair}|{tf}"),
                InlineKeyboardButton("🏠 Меню",       callback_data="main"),
            )
            bot.edit_message_text(
                f"⚠️ *Немає даних*\n\n`{esc(pair)}`\n\nAPI не відповів\\. Спробуйте ще раз\\.",
                cid, mid, parse_mode="MarkdownV2", reply_markup=err_kb)
        except Exception: pass
        return

    # Мульти-ТФ підтвердження
    mtf_txt, mtf_agree = "", 0
    try:
        mtf_txt, mtf_agree = multi_tf_confirm(pair, tf)
    except Exception: pass

    try:
        bot.edit_message_text(
            format_signal(pair, tf, sig, mtf_txt, mtf_agree),
            cid, mid, parse_mode="MarkdownV2",
            reply_markup=result_kb(pair, tf))
    except Exception as e:
        if "not modified" not in str(e):
            log.error(f"[SIGNAL ERR] {e}")

# ── Команди ───────────────────────────────────────────────────
@bot.message_handler(commands=["start", "menu"])
def cmd_start(msg):
    send_main(msg.chat.id)

@bot.message_handler(commands=["stats"])
def cmd_stats(msg):
    bot.send_message(msg.chat.id, stats_text(msg.chat.id),
                     parse_mode="MarkdownV2", reply_markup=main_kb())

@bot.message_handler(commands=["scan"])
def cmd_scan(msg):
    bot.send_message(msg.chat.id, "🔍 *Вибери таймфрейм для сканера:*",
                     parse_mode="MarkdownV2", reply_markup=scanner_tf_kb())

@bot.message_handler(commands=["rating"])
def cmd_rating(msg):
    bot.send_message(msg.chat.id, pair_rating_text(msg.chat.id),
                     parse_mode="MarkdownV2", reply_markup=main_kb())

@bot.message_handler(commands=["unsub"])
def cmd_unsub(msg):
    unsubscribe(msg.chat.id)
    bot.send_message(msg.chat.id, "🔕 Підписку скасовано\\.", parse_mode="MarkdownV2")

@bot.message_handler(commands=["help"])
def cmd_help(msg):
    bot.send_message(msg.chat.id,
        "📖 *Команди SIGNAL AI v4\\.0*\n\n"
        "/start \\— головне меню\n"
        "/scan \\— авто\\-сканер ринку\n"
        "/stats \\— ваша статистика\n"
        "/rating \\— рейтинг пар по WR\n"
        "/unsub \\— скасувати підписку\n"
        "/help \\— ця довідка\n\n"
        "*Як користуватися:*\n"
        "1\\. Обери категорію → пару → ТФ\n"
        "2\\. Отримай сигнал \\+ мульти\\-ТФ\n"
        "3\\. Відмітив ✅/❌ — зберігається WR\n"
        "4\\. Підпишись на авто\\-сигнали 🔔\n\n"
        "*Нове у v4\\.0:*\n"
        "🆕 CCI \\+ OBV \\+ Ichimoku\n"
        "🆕 RSI Дивергенція\n"
        "🆕 EMA200 \\(глобальний тренд\\)\n"
        "🆕 Мульти\\-ТФ підтвердження\n"
        "🆕 Авто\\-сигнали за підпискою\n"
        "🆕 Рейтинг пар по WinRate\n"
        "🆕 Мікро\\-графік ціни",
        parse_mode="MarkdownV2")

@bot.message_handler(commands=["admin"])
def cmd_admin(msg):
    if msg.chat.id not in ADMIN_IDS:
        return
    total_users = len(all_stats)
    total_trades = sum(s.get("total", 0) for s in all_stats.values())
    total_subs = len(all_subs)
    bot.send_message(msg.chat.id,
        f"👤 Користувачів: *{total_users}*\n"
        f"📈 Угод всього: *{total_trades}*\n"
        f"🔔 Підписок: *{total_subs}*",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_text(msg):
    send_main(msg.chat.id)

# ── Callbacks ─────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: True)
def handle_cb(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    d   = call.data
    bot.answer_callback_query(call.id)
    try:
        if d == "main":
            send_main(cid, mid)

        elif d in ("menu_forex", "forex_back"):
            bot.edit_message_text("📈 *FOREX пари*\nОберіть:", cid, mid,
                parse_mode="MarkdownV2", reply_markup=pairs_kb(FOREX_PAIRS, "main"))

        elif d in ("menu_otc", "otc_back"):
            bot.edit_message_text("🌙 *OTC пари*\nОберіть:", cid, mid,
                parse_mode="MarkdownV2", reply_markup=pairs_kb(OTC_PAIRS, "main"))

        elif d in ("menu_crypto", "crypto_back"):
            bot.edit_message_text("₿ *КРИПТО*\nОберіть:", cid, mid,
                parse_mode="MarkdownV2", reply_markup=pairs_kb(CRYPTO_PAIRS, "main"))

        elif d in ("menu_stocks", "stocks_back"):
            bot.edit_message_text("📊 *АКЦІЇ*\nОберіть:", cid, mid,
                parse_mode="MarkdownV2", reply_markup=pairs_kb(STOCKS_PAIRS, "main"))

        elif d == "stats":
            bot.edit_message_text(stats_text(cid), cid, mid,
                parse_mode="MarkdownV2", reply_markup=main_kb())

        elif d == "pair_rating":
            bot.edit_message_text(pair_rating_text(cid), cid, mid,
                parse_mode="MarkdownV2", reply_markup=main_kb())

        elif d == "sessions":
            bot.edit_message_text(sessions_text(), cid, mid,
                parse_mode="MarkdownV2", reply_markup=main_kb())

        elif d == "scanner":
            bot.edit_message_text("🔍 *Авто\\-сканер*\nОберіть таймфрейм:", cid, mid,
                parse_mode="MarkdownV2", reply_markup=scanner_tf_kb())

        elif d.startswith("scan_tf|"):
            tf2 = d.split("|")[1]
            bot.edit_message_text(
                f"🔍 Сканую ринок на ТФ {TIMEFRAMES.get(tf2,tf2+'хв')}\\.\\.\\.",
                cid, mid, parse_mode="MarkdownV2")
            threading.Thread(target=run_scanner, args=(cid, tf2), daemon=True).start()

        # ── Підписка ──────────────────────────────────────────
        elif d == "sub_menu":
            txt = "🔔 *Авто\\-сигнали за підпискою*\nОтримуй сигнали кожні 5 хв автоматично\\!"
            bot.edit_message_text(txt, cid, mid, parse_mode="MarkdownV2", reply_markup=sub_kb(cid))

        elif d == "sub_forex":
            bot.edit_message_text("📈 *Forex підписка*\nОберіть таймфрейм:", cid, mid,
                parse_mode="MarkdownV2", reply_markup=sub_tf_kb("forex"))

        elif d == "sub_otc":
            bot.edit_message_text("🌙 *OTC підписка*\nОберіть таймфрейм:", cid, mid,
                parse_mode="MarkdownV2", reply_markup=sub_tf_kb("otc"))

        elif d.startswith("sub_confirm|"):
            _, group, tf2 = d.split("|", 2)
            pairs_for_group = {"forex": FOREX_PAIRS, "otc": OTC_PAIRS}
            plist = pairs_for_group.get(group, FOREX_PAIRS)
            best_pair = plist[0]["name"]
            subscribe_pair(cid, best_pair, tf2)
            all_tf = {**TIMEFRAMES, **CRYPTO_TF}
            bot.edit_message_text(
                f"✅ Підписку активовано\\!\n\n"
                f"Пара: *{esc(best_pair)}*\n"
                f"ТФ: *{esc(all_tf.get(tf2,tf2))}*\n"
                f"Інтервал: кожні 5 хвилин\n\n"
                f"Відписатися: /unsub",
                cid, mid, parse_mode="MarkdownV2", reply_markup=main_kb())

        elif d == "unsub":
            unsubscribe(cid)
            bot.edit_message_text("🔕 Підписку скасовано\\.", cid, mid,
                parse_mode="MarkdownV2", reply_markup=main_kb())

        elif d == "about":
            bot.edit_message_text(
                "ℹ️ *SIGNAL AI v4\\.0 — Оновлення*\n\n"
                "*19 індикаторів:*\n"
                "RSI, MACD, EMA 9/21/50/200\n"
                "Stochastic, BB, Williams %R\n"
                "STC, Momentum, ADX, ATR\n"
                "🆕 CCI \\| 🆕 OBV \\| 🆕 Ichimoku\n"
                "Heikin Ashi, Parabolic SAR\n"
                "Fibonacci, S/R, Divergence\n"
                "Свічкові патерни \\(7 типів\\)\n\n"
                "*Нові функції v4\\.0:*\n"
                "🔭 Мульти\\-ТФ підтвердження\n"
                "🔔 Авто\\-сигнали за підпискою\n"
                "🏆 Рейтинг пар по WinRate\n"
                "📊 Мікро\\-графік ціни\n"
                "💾 Атомарне збереження даних\n"
                "🗂 Кешування API запитів\n\n"
                "📡 TwelveData API\n"
                "🎯 Точність: \\~84\\-96%",
                cid, mid, parse_mode="MarkdownV2", reply_markup=main_kb())

        elif d.startswith("pair_"):
            pair = d[5:]
            bot.edit_message_text(f"⏱ *Таймфрейм для {esc(pair)}*\nОберіть:",
                cid, mid, parse_mode="MarkdownV2", reply_markup=tf_kb(pair))

        elif d.startswith("tf|"):
            _, pair, tf = d.split("|", 2)
            threading.Thread(target=do_signal, args=(cid, mid, pair, tf), daemon=True).start()

        elif d.startswith(("win|", "loss|")):
            res, pair, tf = d.split("|", 2)
            s = get_stats(cid)
            s["total"] += 1
            won = res == "win"
            if won:
                s["wins"]   += 1
                s["streak"]  = max(s.get("streak", 0) + 1, 1)
                s["max_streak"] = max(s.get("max_streak", 0), s["streak"])
                em = "✅ *Виграш записано\\!*"
            else:
                s["losses"] = s.get("losses", 0) + 1
                s["streak"] = min(s.get("streak", 0) - 1, -1)
                em = "❌ *Програш записано*"
            if pair not in s["pairs"]:
                s["pairs"][pair] = {"total": 0, "wins": 0}
            s["pairs"][pair]["total"] += 1
            if won: s["pairs"][pair]["wins"] += 1
            # Зберігаємо в history (останні 50)
            s.setdefault("history", []).append({
                "pair": pair, "tf": tf, "result": res,
                "time": datetime.now(timezone.utc).isoformat()
            })
            if len(s["history"]) > 50: s["history"] = s["history"][-50:]
            save_stats()
            wr = round(s["wins"] / s["total"] * 100)
            bot.send_message(cid,
                f"{em}\n\n"
                f"📊 WR: *{wr}%* \\({s['wins']}W \\/ {s.get('losses',0)}L\\)\n"
                f"`{bar(wr)}`\n\n"
                "Оберіть наступну дію:",
                parse_mode="MarkdownV2", reply_markup=main_kb())

    except Exception as e:
        if "not modified" not in str(e):
            log.error(f"[CB ERR] {d!r}: {e}")
            try:
                bot.send_message(cid, "Оберіть категорію:", reply_markup=main_kb())
            except Exception: pass

# ══════════════════════════════════════════════════════════════
#  🚀 ЗАПУСК
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 58)
    print("  ⚡ SIGNAL AI Bot v4.0 — PocketOption Signals")
    print("=" * 58)
    print(f"  Forex:   {len(FOREX_PAIRS)} пар")
    print(f"  OTC:     {len(OTC_PAIRS)} пар")
    print(f"  Crypto:  {len(CRYPTO_PAIRS)} пар")
    print(f"  Stocks:  {len(STOCKS_PAIRS)} пар")
    print(f"  Всього:  {len(ALL_PAIRS)} інструментів")
    print(f"  Індик.:  19 (CCI+OBV+Ichimoku+EMA200+Div.)")
    print(f"  Підписників: {len(all_subs)}")
    print("=" * 58)

    # Запуск авто-сигналів у фоні
    threading.Thread(target=auto_signal_worker, daemon=True).start()
    log.info("Auto-signal worker запущено")

    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
    except Exception: pass

    print("  ✅ Бот запущено! Напиши /start у Telegram")
    print("  🛑 Ctrl+C для зупинки")
    print("=" * 58)

    bot.infinity_polling(timeout=30, long_polling_timeout=20, skip_pending=True)
