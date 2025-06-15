import requests
import matplotlib.pyplot as plt
from datetime import datetime
import io
import os
from dotenv import load_dotenv

# === Telegram настройки ===
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

previous_signals = {}

def send_telegram(message, image_bytes=None):
    if image_bytes:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        files = {'photo': ('chart.png', image_bytes)}
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'caption': message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, data=data, files=files)
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, data=data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Telegram API returned an error: {e}\nResponse content: {response.text}")
    return response.json()


def fetch_klines(symbol, limit=200):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": "1h", "limit": limit}
    r = requests.get(url, params=params)
    data = r.json()
    if not isinstance(data, list) or len(data) < limit:
        raise ValueError(f"Invalid or insufficient data for {symbol}")
    closes = [float(c[4]) for c in data]
    times = [datetime.fromtimestamp(c[0]/1000) for c in data]
    print(f"Fetched {len(closes)} prices for {symbol}")
    return closes, times

def sma(prices, length):
    if len(prices) < length:
        return None
    return sum(prices[-length:]) / length

def rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, period + 1):
        diff = prices[-i] - prices[-i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def ema(prices, period):
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    ema_val = prices[-period]
    for price in prices[-period + 1:]:
        ema_val = price * k + ema_val * (1 - k)
    return ema_val

def macd(prices):
    ema12 = ema(prices, 12)
    ema26 = ema(prices, 26)
    if ema12 is None or ema26 is None:
        return None
    return ema12 - ema26

def macd_hist(prices):
    if len(prices) < 35:
        return None  # Need at least 26 for EMA and 9 for signal

    macd_line = []
    for i in range(26, len(prices)):
        slice_prices = prices[:i+1]
        macd_val = macd(slice_prices)
        if macd_val is not None:
            macd_line.append(macd_val)

    if len(macd_line) < 9:
        return None

    signal_line = ema(macd_line[-9:], 9)
    current_macd = macd(prices)
    return current_macd - signal_line if signal_line is not None else None


def generate_signal(symbol, prices):
    price = prices[-1]
    rsi_val = rsi(prices)
    macd_h = macd_hist(prices)
    sma50 = sma(prices, 50)
    sma200 = sma(prices, 200)
    print(f"{symbol} indicators: RSI={rsi_val}, MACD_H={macd_h}, SMA50={sma50}, SMA200={sma200}")

    if None in (rsi_val, macd_h, sma50, sma200):
        return None, None, None

    rsi_sig = "🔥 Перекуплен" if rsi_val > 70 else "🧊 Перепродан" if rsi_val < 30 else "✅ Нейтрально"
    macd_sig = "🔺 Бычий" if macd_h > 0 else "🔻 Медвежий"
    trend_sig = "⚡ Golden Cross" if sma50 > sma200 else "⚠ Death Cross" if sma50 < sma200 else "➖ Нейтрально"

    signal_summary = f"{rsi_sig} | {macd_sig} | {trend_sig}"
    message = (
        f"{symbol} анализ\n"
        f"📈 Цена: {price:.2f} USDT\n"
        f"RSI: {rsi_val:.2f} — {rsi_sig}\n"
        f"MACD Hist: {macd_h:.2f} — {macd_sig}\n"
        f"SMA50: {sma50:.2f}, SMA200: {sma200:.2f} — {trend_sig}"
    )
    return signal_summary, message, (rsi_val, macd_h, sma50, sma200)

def draw_chart(symbol, times, prices, sma50, sma200, rsi_val, macd_h):
    plt.figure(figsize=(10, 6))

    # --- Price and SMA plot ---
    plt.subplot(2, 1, 1)
    plt.plot(times, prices, label="Цена", color='blue')
    if sma50 and sma200:
        sma50_line = [sma(prices[:i+1], 50) if i >= 49 else None for i in range(len(prices))]
        sma200_line = [sma(prices[:i+1], 200) if i >= 199 else None for i in range(len(prices))]
        plt.plot(times, sma50_line, label="SMA 50", color='orange')
        plt.plot(times, sma200_line, label="SMA 200", color='red')
    plt.title(f"{symbol} Цена + SMA")
    plt.legend()
    plt.grid(True)

    # --- RSI Plot ---
    plt.subplot(2, 2, 3)
    plt.axhline(70, color='red', linestyle='--')
    plt.axhline(30, color='green', linestyle='--')
    rsi_values = []
    rsi_times = []
    for i in range(len(prices[-50:])):
        global_index = len(prices) - 50 + i
        if global_index >= 14:
            rsi_val = rsi(prices[:global_index+1])
            rsi_values.append(rsi_val)
            rsi_times.append(times[global_index])
    plt.plot(rsi_times, rsi_values, label='RSI', color='purple')
    plt.title("RSI")
    plt.grid(True)

    # --- MACD Histogram Plot ---
    plt.subplot(2, 2, 4)
    macd_vals = []
    macd_times = []
    for i in range(len(prices[-50:])):
        global_index = len(prices) - 50 + i
        if global_index >= 26:
            macd_val = macd(prices[:global_index+1])
            macd_vals.append(macd_val)
            macd_times.append(times[global_index])
        else:
            macd_vals.append(None)
            macd_times.append(times[global_index])

    signal_vals = [ema(macd_vals[:i+1], 9) if i >= 8 and macd_vals[i] is not None else None for i in range(len(macd_vals))]

    macd_hist_vals = []
    valid_times = []
    for i in range(len(macd_vals)):
        m = macd_vals[i]
        s = signal_vals[i]
        t = macd_times[i]
        if m is not None and s is not None:
            macd_hist_vals.append(m - s)
            valid_times.append(t)
        else:
            macd_hist_vals.append(0)
            valid_times.append(t)

    plt.bar(valid_times, macd_hist_vals, color='gray', label='MACD Hist')
    plt.title("MACD Histogram")
    plt.grid(True)

    # --- Finalize ---
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def analyze_symbols():
    global previous_signals
    symbols = ["BTCUSDT", "SOLUSDT", "SUIUSDT", "ENSUSDT"]
    for symbol in symbols:
        try:
            prices, times = fetch_klines(symbol)
            signal, message, indicators = generate_signal(symbol, prices)
            if signal is None or indicators is None or any(val is None for val in indicators):
                print(f"⚠ Недостаточно данных: {symbol}")
                continue
            if previous_signals.get(symbol) != signal:
                image = draw_chart(symbol, times, prices, *indicators)
                send_telegram(message, image_bytes=image)
                previous_signals[symbol] = signal
                print(f"🟢 Обновление {symbol}")
            else:
                print(f"⚪ Без изменений: {symbol}")
        except Exception as e:
            print(f"🔴 Ошибка анализа {symbol}: {e}")

if __name__ == "__main__": 
    analyze_symbols()