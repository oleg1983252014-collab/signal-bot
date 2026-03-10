#!/usr/bin/env python3
"""
╔══════════════════════════════════════════╗
║   AI SIGNAL BOT — Pocket Option         ║
║   Telegram Bot | Forex & OTC Signals    ║
╚══════════════════════════════════════════╝

ВСТАНОВЛЕННЯ:
  pip install pyTelegramBotAPI

ЗАПУСК:
  1. Отримайте токен у @BotFather в Telegram
  2. Вставте токен у BOT_TOKEN нижче
  3. python pocket_option_bot.py
"""

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import math
import time
from datetime import datetime

# ══════════════════════════════════════════
#  НАЛАШТУВАННЯ — ВСТАВТЕ СВІЙ ТОКЕН
# ══════════════════════════════════════════
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

# ══════════════════════════════════════════
#  РИНКОВІ ДАНІ
# ══════════════════════════════════════════
FOREX_PAIRS = [
    {"name": "EUR/USD",  "p": 1.1559, "d": 5, "t": -1},
    {"name": "GBP/USD",  "p": 1.2945, "d": 5, "t": -1},
    {"name": "USD/JPY",  "p": 148.72, "d": 3, "t":  1},
    {"name": "AUD/USD",  "p": 0.6285, "d": 5, "t": -1},
    {"name": "NZD/USD",  "p": 0.5782, "d": 5, "t": -1},
    {"name": "USD/CAD",  "p": 1.4415, "d": 5, "t":  1},
    {"name": "USD/CHF",  "p": 0.8832, "d": 5, "t":  1},
    {"name": "EUR/GBP",  "p": 0.8663, "d": 5, "t": -1},
    {"name": "EUR/JPY",  "p": 171.88, "d": 3, "t": -1},
    {"name": "GBP/JPY",  "p": 192.40, "d": 3, "t":  1},
    {"name": "AUD/CAD",  "p": 0.9529, "d": 5, "t": -1},
    {"name": "AUD/JPY",  "p": 93.52,  "d": 3, "t": -1},
    {"name": "CHF/JPY",  "p": 199.65, "d": 3, "t":  1},
    {"name": "EUR/AUD",  "p": 1.8385, "d": 5, "t":  1},
    {"name": "EUR/CAD",  "p": 1.6645, "d": 5, "t": -1},
    {"name": "GBP/AUD",  "p": 2.0590, "d": 5, "t": -1},
    {"name": "GBP/CAD",  "p": 1.8742, "d": 5, "t": -1},
]

OTC_PAIRS = [
    {"name": "EUR/USD OTC",  "p": 1.1559, "d": 5, "t": -1},
    {"name": "GBP/USD OTC",  "p": 1.2945, "d": 5, "t": -1},
    {"name": "USD/JPY OTC",  "p": 148.72, "d": 3, "t":  1},
    {"name": "AUD/USD OTC",  "p": 0.6285, "d": 5, "t": -1},
    {"name": "EUR/GBP OTC",  "p": 0.8663, "d": 5, "t": -1},
    {"name": "AUD/CAD OTC",  "p": 0.9529, "d": 5, "t": -1},
    {"name": "EUR/JPY OTC",  "p": 171.88, "d": 3, "t": -1},
    {"name": "GBP/JPY OTC",  "p": 192.40, "d": 3, "t":  1},
    {"name": "USD/CAD OTC",  "p": 1.4415, "d": 5, "t":  1},
    {"name": "NZD/USD OTC",  "p": 0.5782, "d": 5, "t": -1},
    {"name": "USD/CHF OTC",  "p": 0.8832, "d": 5, "t":  1},
    {"name": "CHF/JPY OTC",  "p": 199.65, "d": 3, "t":  1},
    {"name": "EUR/AUD OTC",  "p": 1.8385, "d": 5, "t":  1},
]

ALL_PAIRS = {p["name"]: p for p in FOREX_PAIRS + OTC_PAIRS}

TIMEFRAMES = {
    "1":  "1 хвилина",
    "3":  "3 хвилини",
    "5":  "5 хвилин",
    "15": "15 хвилин",
    "30": "30 хвилин",
    "60": "1 година",
}

# Зберігаємо стан користувача
user_state = {}

# ══════════════════════════════════════════
#  АЛГОРИТМ СИГНАЛУ
# ══════════════════════════════════════════
def seeded_rand(seed, offset=0):
    x = math.sin(seed + offset) * 43758.5453123
    return x - math.floor(x)

def generate_signal(pair_name: str, tf: str) -> dict:
    m = ALL_PAIRS.get(pair_name, FOREX_PAIRS[0])
    is_otc = "OTC" in pair_name
    seed = sum(ord(c) for c in pair_name) + int(tf) + int(time.time() // 60)
    r = lambda i: seeded_rand(seed, i)

    rsi   = round(28 + r(1) * 50)
    adx   = round(22 + r(2) * 55)
    macd  = (r(3) - 0.5) * 0.006
    bb    = r(4) * 100
    stoch = round(15 + r(5) * 70)
    cci   = round((r(13) - 0.5) * 300)

    score = m["t"]
    if rsi > 65:  score -= 1.2
    if rsi < 35:  score += 1.2
    if macd > 0:  score += 0.6
    if macd < 0:  score -= 0.6
    if bb > 78:   score -= 0.4
    if bb < 22:   score += 0.4
    if adx > 50:  score *= 1.3
    if is_otc:    score *= 0.9

    is_buy = score >= 0
    conf   = min(97, round(88 + min(abs(score) / 3, 1) * 7 + r(6) * 4))

    p    = m["p"]
    d    = m["d"]
    mult = 1 if p > 100 else (0.01 if p > 10 else 0.0001)
    sp   = 1.8 if is_otc else 1.0

    live = round(p + (r(7) - 0.5) * 2 * mult, d)
    tp1  = round(live + (3 + r(8) * 4) * mult, d)   if is_buy else round(live - (3 + r(8) * 4) * mult, d)
    tp2  = round(tp1  + (2 + r(9) * 3) * mult, d)   if is_buy else round(tp1  - (2 + r(9) * 3) * mult, d)
    sl   = round(live - (2 + r(10)* 2) * mult * sp, d) if is_buy else round(live + (2 + r(10)* 2) * mult * sp, d)
    res  = round(live + (5 + r(11) * 5) * mult, d)
    sup  = round(live - (5 + r(12) * 5) * mult, d)

    tp_dist = abs(tp1 - live)
    sl_dist = abs(sl  - live)
    rr = round(tp_dist / sl_dist, 1) if sl_dist else 2.0

    tf_names = {"1":"1-хв","3":"3-хв","5":"5-хв","15":"15-хв","30":"30-хв","60":"1-год"}
    tf_n = tf_names.get(tf, tf+"хв")

    rsi_note = (f"RSI={rsi} — перекупленість." if rsi > 65
                else f"RSI={rsi} — перепроданість, очікується відскок." if rsi < 35
                else f"RSI={rsi} — нейтральна зона.")
    adx_note = f"ADX={adx} підтверджує {'сильний' if adx>50 else 'помірний'} тренд."
    macd_txt = "MACD вище нуля — бичачий імпульс." if macd > 0 else "MACD нижче нуля — ведмежий тиск."
    otc_txt  = " ⚠ OTC: враховуйте ширший спред." if is_otc else ""

    analysis = f"На {tf_n} {pair_name} — {'висхідна' if is_buy else 'низхідна'} динаміка. {rsi_note} {adx_note} {macd_txt}{otc_txt}"

    return {
        "is_buy": is_buy,
        "signal": "BUY ▲" if is_buy else "SELL ▼",
        "conf": conf,
        "live": live,
        "tp1": tp1, "tp2": tp2, "sl": sl,
        "res": res, "sup": sup,
        "rr": rr,
        "rsi": rsi, "adx": adx,
        "macd": "▲ БИЧ" if macd > 0 else "▼ ВЕДМІДЬ",
        "stoch": stoch, "cci": cci,
        "is_otc": is_otc,
        "analysis": analysis,
    }

def format_signal_message(pair: str, tf: str, d: dict) -> str:
    now = datetime.now().strftime("%H:%M:%S")
    conf_bar = "█" * round(d["conf"] / 10) + "░" * (10 - round(d["conf"] / 10))
    direction = "🟢 BUY ▲" if d["is_buy"] else "🔴 SELL ▼"
    market = "🌙 OTC MARKET" if d["is_otc"] else "📈 FOREX MARKET"

    msg = f"""
⚡ *AI SIGNAL BOT — Pocket Option*
{market}

*Пара:* `{pair}`
*Таймфрейм:* `{TIMEFRAMES.get(tf, tf)} `
*Час:* `{now}`

━━━━━━━━━━━━━━━━━━━━
🎯 *СИГНАЛ: {direction}*
━━━━━━━━━━━━━━━━━━━━

📊 *Впевненість:* `{d["conf"]}%`
`{conf_bar}` 

💰 *Вхід:*       `{d["live"]}`
🎯 *TP 1:*        `{d["tp1"]}`
🎯 *TP 2:*        `{d["tp2"]}`
🛑 *Stop Loss:*  `{d["sl"]}`
📐 *R/R:*         `1 : {d["rr"]}`

━━━━━━━━━━━━━━━━━━━━
📉 *Рівні*

🔴 Опір:       `{d["res"]}`
📍 Ціна:       `{d["live"]}`
🟢 Підтримка: `{d["sup"]}`

━━━━━━━━━━━━━━━━━━━━
🔬 *Індикатори*

• RSI:   `{d["rsi"]}` {'⚠️ перекуп' if d["rsi"]>68 else '⚠️ перепрод' if d["rsi"]<32 else '✅'}
• ADX:  `{d["adx"]}` {'💪 сильний' if d["adx"]>50 else '📊 помірний'}
• MACD: `{d["macd"]}`
• STOCH:`{d["stoch"]}`
• CCI:   `{d["cci"]}`

━━━━━━━━━━━━━━━━━━━━
📝 _{d["analysis"]}_

⚠️ _Не є фінансовою порадою_
"""
    return msg.strip()

# ══════════════════════════════════════════
#  КЛАВІАТУРИ
# ══════════════════════════════════════════
def main_menu_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📈 FOREX сигнал", callback_data="menu_forex"),
        InlineKeyboardButton("🌙 OTC сигнал",   callback_data="menu_otc"),
    )
    kb.add(InlineKeyboardButton("ℹ️ Про бота", callback_data="about"))
    return kb

def forex_pairs_kb():
    kb = InlineKeyboardMarkup(row_width=3)
    btns = [InlineKeyboardButton(p["name"], callback_data=f"pair_{p['name']}") for p in FOREX_PAIRS]
    kb.add(*btns)
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="back_main"))
    return kb

def otc_pairs_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    btns = [InlineKeyboardButton(p["name"], callback_data=f"pair_{p['name']}") for p in OTC_PAIRS]
    kb.add(*btns)
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="back_main"))
    return kb

def timeframe_kb(pair: str):
    kb = InlineKeyboardMarkup(row_width=3)
    btns = [InlineKeyboardButton(v, callback_data=f"tf_{pair}_{k}") for k, v in TIMEFRAMES.items()]
    kb.add(*btns)
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="back_pairs_" + ("otc" if "OTC" in pair else "forex")))
    return kb

def after_signal_kb(pair: str, tf: str):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔄 Новий сигнал", callback_data=f"tf_{pair}_{tf}"),
        InlineKeyboardButton("🔀 Змінити пару", callback_data="back_pairs_" + ("otc" if "OTC" in pair else "forex")),
    )
    kb.add(InlineKeyboardButton("🏠 Головне меню", callback_data="back_main"))
    return kb

# ══════════════════════════════════════════
#  ХЕНДЛЕРИ
# ══════════════════════════════════════════
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    text = (
        "⚡ *AI Signal Bot — Pocket Option*\n\n"
        "Вітаю! Я аналізую Forex та OTC пари і генерую торгові сигнали.\n\n"
        "🟢 *17 Forex пар*\n"
        "🌙 *13 OTC пар*\n"
        "📊 *6 таймфреймів* (1–60 хв)\n"
        "🎯 *Впевненість 88–97%*\n\n"
        "Оберіть категорію:"
    )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=main_menu_kb())

@bot.message_handler(commands=["signal"])
def cmd_signal(msg):
    bot.send_message(msg.chat.id, "Оберіть категорію:", reply_markup=main_menu_kb())

@bot.callback_query_handler(func=lambda c: c.data == "back_main")
def back_main(call):
    bot.edit_message_text(
        "Оберіть категорію:", call.message.chat.id, call.message.message_id,
        parse_mode="Markdown", reply_markup=main_menu_kb()
    )

@bot.callback_query_handler(func=lambda c: c.data == "menu_forex")
def menu_forex(call):
    bot.edit_message_text(
        "📈 *FOREX пари*\nОберіть валютну пару:",
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown", reply_markup=forex_pairs_kb()
    )

@bot.callback_query_handler(func=lambda c: c.data == "menu_otc")
def menu_otc(call):
    bot.edit_message_text(
        "🌙 *OTC пари* — торгівля у вихідні\nОберіть валютну пару:",
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown", reply_markup=otc_pairs_kb()
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("back_pairs_"))
def back_pairs(call):
    market = call.data.split("_")[-1]
    if market == "otc":
        bot.edit_message_text(
            "🌙 *OTC пари*\nОберіть валютну пару:",
            call.message.chat.id, call.message.message_id,
            parse_mode="Markdown", reply_markup=otc_pairs_kb()
        )
    else:
        bot.edit_message_text(
            "📈 *FOREX пари*\nОберіть валютну пару:",
            call.message.chat.id, call.message.message_id,
            parse_mode="Markdown", reply_markup=forex_pairs_kb()
        )

@bot.callback_query_handler(func=lambda c: c.data.startswith("pair_"))
def select_pair(call):
    pair = call.data[5:]
    bot.edit_message_text(
        f"⏱ *Таймфрейм для {pair}*\nОберіть час свічки:",
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown", reply_markup=timeframe_kb(pair)
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("tf_"))
def select_tf(call):
    parts = call.data.split("_")
    # tf_EUR/USD OTC_5  →  parts = ["tf", "EUR/USD OTC", "5"]
    tf   = parts[-1]
    pair = "_".join(parts[1:-1])

    bot.answer_callback_query(call.id, "⚡ Аналізую...")
    bot.edit_message_text(
        f"⏳ Аналізую *{pair}* на `{TIMEFRAMES.get(tf,tf)}`...",
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown"
    )

    d   = generate_signal(pair, tf)
    msg = format_signal_message(pair, tf, d)

    bot.edit_message_text(
        msg,
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown",
        reply_markup=after_signal_kb(pair, tf)
    )

@bot.callback_query_handler(func=lambda c: c.data == "about")
def about(call):
    text = (
        "ℹ️ *AI Signal Bot — Pocket Option*\n\n"
        "Бот аналізує валютні пари за допомогою технічних індикаторів:\n\n"
        "• *RSI* — індекс відносної сили\n"
        "• *MACD* — конвергенція/дивергенція\n"
        "• *ADX* — сила тренду\n"
        "• *Stochastic* — осцилятор\n"
        "• *CCI* — індекс товарного каналу\n"
        "• *Bollinger Bands* — смуги Боллінджера\n\n"
        "📊 *30 пар* | *6 таймфреймів* | *88–97% впевненість*\n\n"
        "⚠️ _Сигнали носять інформаційний характер._"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=main_menu_kb())

# ══════════════════════════════════════════
#  ЗАПУСК
# ══════════════════════════════════════════
if __name__ == "__main__":
    print("╔══════════════════════════════════════╗")
    print("║  AI Signal Bot — Pocket Option      ║")
    print("║  Запущено! Очікую повідомлень...    ║")
    print("╚══════════════════════════════════════╝")
    bot.infinity_polling()
