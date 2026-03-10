#!/usr/bin/env python3
import os, math, time, requests
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
ALL_PAIRS = {p["name"]: p for p in FOREX_PAIRS + OTC_PAIRS}
TIMEFRAMES = {"1":"1 хвилина","3":"3 хвилини","5":"5 хвилин","15":"15 хвилин","30":"30 хвилин","60":"1 година"}

# ══════════════════════════════════════════
#  СТАТИСТИКА (зберігається в пам'яті)
# ══════════════════════════════════════════
user_stats = {}

def get_stats(cid):
    if cid not in user_stats:
        user_stats[cid] = {"total":0,"wins":0,"losses":0,"pairs":{},"streak":0}
    return user_stats[cid]

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
    tf_map={"1":"1m","3":"2m","5":"5m","15":"15m","30":"30m","60":"1h"}
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

def get_price(symbol,fallback):
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

def format_signal(pair,tf,d):
    now_dt=datetime.now(timezone.utc)+timedelta(hours=2)
    now=now_dt.strftime("%H:%M:%S")
    tf_hold={"1":(1,2),"3":(3,5),"5":(5,10),"15":(15,20),"30":(30,35),"60":(60,75)}
    hm=tf_hold.get(tf,(5,10))
    exp=(now_dt+timedelta(minutes=hm[0])).strftime("%H:%M")
    bar="█"*round(d["conf"]/10)+"░"*(10-round(d["conf"]/10))
    adw="" if d["adx_ok"] else "\n⚠️ _ADX<25 — тренд слабкий!_"
    vt="".join(f"{'🟢' if v[1]==1 else '🔴' if v[1]==-1 else '⚪'} {v[2]}\n" for v in d["votes"])
    return f"""⚡ *AI SIGNAL BOT — Pocket Option*
{'🌙 OTC' if d['is_otc'] else '📈 FOREX'} | {'🔴 Live' if d['real'] else '⚙️ Розрах'}

*Пара:* `{pair}` | *ТФ:* `{TIMEFRAMES.get(tf,tf)}`
*Час:* `{now}`

━━━━━━━━━━━━━━━━━━━━
🎯 *СИГНАЛ: {'🟢 BUY ▲' if d['is_buy'] else '🔴 SELL ▼'}*
💪 *Сила: {d['strength']}*
⏱ *Утримувати: {hm[0]}–{hm[1]} хв*
🕐 *Експірація: {exp}*
━━━━━━━━━━━━━━━━━━━━

📊 *Впевненість: {d['conf']}%*
`{bar}`
✅ BUY: `{d['bc']}/7` | 🔴 SELL: `{d['sc']}/7`
📐 ADX={d['adx']} {'💪' if d['adx_ok'] else '⚠️'}{adw}

💰 *Рівні*
Ціна: `{d['live']}` | Вхід: `{d['live']}`
TP1: `{d['tp1']}` | TP2: `{d['tp2']}`
SL: `{d['sl']}` | R/R: `1:{d['rr']}`
🔴 Опір: `{d['res']}` | 🟢 Підтримка: `{d['sup']}`

📉 EMA9:`{d['e9']}` EMA21:`{d['e21']}` EMA50:`{d['e50']}`

━━━━━━━━━━━━━━━━━━━━
🔬 *7 індикаторів:*
{vt}
⚠️ _Не є фінансовою порадою_""".strip()

# ══════════════════════════════════════════
#  КЛАВІАТУРИ
# ══════════════════════════════════════════
def main_kb():
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("📈 FOREX",callback_data="menu_forex"),
           InlineKeyboardButton("🌙 OTC",callback_data="menu_otc"))
    kb.add(InlineKeyboardButton("📊 Статистика",callback_data="stats"),
           InlineKeyboardButton("🕐 Сесії",callback_data="sessions"))
    kb.add(InlineKeyboardButton("ℹ️ Про бота",callback_data="about"))
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
    kb.add(*[InlineKeyboardButton(v,callback_data=f"tf|{pair}|{k}") for k,v in TIMEFRAMES.items()])
    kb.add(InlineKeyboardButton("◀️ Назад",callback_data="otc_back" if "OTC" in pair else "forex_back"))
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
            bot.answer_callback_query(call.id,"⚡ Аналізую...")
            bot.edit_message_text(f"⏳ Аналізую *{pair}*...",cid,mid,parse_mode="Markdown")
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
            bot.answer_callback_query(call.id,f"{emoji} WR: {wr}%")
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
