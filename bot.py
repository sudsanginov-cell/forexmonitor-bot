import telebot
from tradingview_ta import TA_Handler, Interval
import time
import threading
from datetime import datetime

# ============ ТВОИ ДАННЫЕ ============
BOT_TOKEN = "8951120742:AAF1bQEI0fubmXc4dhLK_UtEWh5-1xGN6zM"
ALLOWED_CHAT_ID = 7986217969

PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY"
]

CHECK_INTERVAL = 35
# =====================================

bot = telebot.TeleBot(BOT_TOKEN)
last_signals = {}
monitoring = True

def check_pair(symbol):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="forex",
            exchange="FX_IDC",
            interval=Interval.INTERVAL_1_MINUTE
        )
        analysis = handler.get_analysis()
        return analysis.summary["RECOMMENDATION"], analysis.summary
    except Exception as e:
        print(f"Ошибка {symbol}: {e}")
        return None, None

def monitor_loop():
    global last_signals
    while True:
        if not monitoring:
            time.sleep(5)
            continue

        for pair in PAIRS:
            rec, summary = check_pair(pair)
            if rec is None:
                continue

            if rec in ["STRONG_BUY", "STRONG_SELL"]:
                if last_signals.get(pair) != rec:
                    if rec == "STRONG_BUY":
                        text = f"🟢 <b>АКТИВНО ПОКУПАТЬ</b>\n\nПара: <b>{pair}</b>\nСигнал: STRONG_BUY\nBuy: {summary['BUY']} | Sell: {summary['SELL']}"
                    else:
                        text = f"🔴 <b>АКТИВНО ПРОДАВАТЬ</b>\n\nПара: <b>{pair}</b>\nСигнал: STRONG_SELL\nBuy: {summary['BUY']} | Sell: {summary['SELL']}"

                    try:
                        bot.send_message(ALLOWED_CHAT_ID, text, parse_mode="HTML")
                    except Exception as e:
                        print("Ошибка отправки:", e)

                    last_signals[pair] = rec
            else:
                if pair in last_signals:
                    del last_signals[pair]

        time.sleep(CHECK_INTERVAL)

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id != ALLOWED_CHAT_ID:
        bot.reply_to(message, "Доступ запрещён")
        return
    bot.reply_to(message, "✅ Бот запущен!\nМониторинг STRONG_BUY / STRONG_SELL на 1 минуте активен.\n\nКоманды:\n/status — текущий статус\n/stop — пауза\n/resume — продолжить")

@bot.message_handler(commands=['status'])
def status(message):
    if message.chat.id != ALLOWED_CHAT_ID:
        return
    text = "📊 Текущий статус (1m):\n\n"
    for pair in PAIRS:
        rec, _ = check_pair(pair)
        text += f"{pair}: {rec or 'ошибка'}\n"
    bot.reply_to(message, text)

@bot.message_handler(commands=['stop'])
def stop(message):
    global monitoring
    if message.chat.id != ALLOWED_CHAT_ID:
        return
    monitoring = False
    bot.reply_to(message, "⏸ Мониторинг на паузе")

@bot.message_handler(commands=['resume'])
def resume(message):
    global monitoring
    if message.chat.id != ALLOWED_CHAT_ID:
        return
    monitoring = True
    bot.reply_to(message, "▶️ Мониторинг возобновлён")

if __name__ == "__main__":
    print("Бот запускается...")
    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()
    bot.infinity_polling()