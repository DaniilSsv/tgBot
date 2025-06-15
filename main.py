import requests
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import io
import os
from dotenv import load_dotenv

# Load environment (Telegram bot token & chat ID)
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

previous_signals = {}

def send_telegram(message, image_bytes=None):
    """Send a message or photo to Telegram via bot."""
    url_base = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    if image_bytes:
        url = f"{url_base}/sendPhoto"
        files = {'photo': ('chart.png', image_bytes)}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': message, 'parse_mode': 'Markdown'}
        resp = requests.post(url, data=data, files=files)
    else:
        url = f"{url_base}/sendMessage"
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
        resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()

def fetch_klines(symbol, interval='1h', limit=200):
    """Fetch last N klines (OHLCV) for symbol from Binance."""
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=5)
    data = r.json()
    df = pd.DataFrame(data, columns=[
        'Open time','Open','High','Low','Close','Volume',
        'Close time','Quote asset volume','Number of trades',
        'Taker buy base asset volume','Taker buy quote asset volume','Ignore'
    ])
    # Convert types
    for col in ['Open','High','Low','Close','Volume']:
        df[col] = pd.to_numeric(df[col])
    df['Open time'] = pd.to_datetime(df['Open time'], unit='ms')
    df.set_index('Open time', inplace=True)
    return df[['Open','High','Low','Close','Volume']]

def sma(series, period):
    if len(series) < period: 
        return None
    return series.iloc[-period:].mean()

def rsi(series, period=14):
    if len(series) < period+1: 
        return None
    delta = series.diff().iloc[-(period+1):].dropna()
    gains = delta[delta > 0].sum() / period
    losses = -delta[delta < 0].sum() / period
    if losses == 0:
        return 100.0
    rs = gains / losses
    return 100 - (100 / (1 + rs))

def macd_hist(series):
    if len(series) < 35:  # need at least 26 + 9
        return None
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line.iloc[-1] - signal.iloc[-1]

def generate_signal(symbol, df):
    """Compute RSI, MACD histogram, and SMA(50,200) signals."""
    closes = df['Close']
    price = closes.iloc[-1]
    r_val = rsi(closes, 14)
    m_val = macd_hist(closes)
    sma50 = sma(closes, 50)
    sma200 = sma(closes, 200)
    if None in (r_val, m_val, sma50, sma200):
        return None, None, None
    r_sig = "🔥 Overbought" if r_val > 70 else ("🧊 Oversold" if r_val < 30 else "✅ Neutral")
    macd_sig = "🔺 Bullish" if m_val > 0 else "🔻 Bearish"
    trend_sig = "⚡ Golden Cross" if sma50 > sma200 else ("⚠ Death Cross" if sma50 < sma200 else "➖ Neutral")
    summary = f"{r_sig} | {macd_sig} | {trend_sig}"
    message = (
        f"{symbol} Analysis\n"
        f"📈 Price: {price:.2f} USDT\n"
        f"RSI (14): {r_val:.1f} — {r_sig}\n"
        f"MACD Hist: {m_val:.4f} — {macd_sig}\n"
        f"SMA50: {sma50:.2f}\n"
        f"SMA200: {sma200:.2f} — {trend_sig}"
    )
    return summary, message, (r_val, m_val, sma50, sma200)

def draw_chart(symbol, df):
    import mplfinance as mpf
    buf = io.BytesIO()

    mc = mpf.make_marketcolors(
        up='#00ff99',
        down='#ff4d4d',
        edge='inherit',
        wick={'up': '#00ff99', 'down': '#ff4d4d'},
        volume={'up': '#00ff99', 'down': '#ff4d4d'},
        ohlc='inherit'
    )

    style = mpf.make_mpf_style(
        base_mpf_style='binance',
        marketcolors=mc,
        facecolor='#000000',        # Candlestick chart background
        edgecolor='#000000',        # Border color
        figcolor='#000000',         # Entire figure background
        gridcolor='#222222',        # Subtle grid
        rc={
            'axes.labelcolor': '#CCCCCC',
            'xtick.color': '#AAAAAA',
            'ytick.color': '#AAAAAA',
            'axes.edgecolor': '#333333',
            'savefig.facecolor': '#000000',
            'savefig.edgecolor': '#000000',
        }
    )

    fig, axlist = mpf.plot(
        df,
        type='candle',
        mav=(50, 200),
        volume=True,
        title=f"{symbol} Price (USDT)",
        style=style,
        returnfig=True,
        figsize=(10, 6),
        tight_layout=True,
    )

    # Manually set black on all axes backgrounds (main and volume)
    for ax in axlist:
        ax.set_facecolor('#000000')

    fig.patch.set_facecolor('#000000')

    fig.savefig(buf, format='png', bbox_inches='tight', facecolor='#000000')
    plt.close(fig)
    buf.seek(0)
    return buf


def analyze_symbols():
    symbols = ["BTCUSDT","SOLUSDT","SUIUSDT","ENSUSDT"]
    for sym in symbols:
        try:
            df = fetch_klines(sym)
            summary, msg, _ = generate_signal(sym, df)
            if summary is None:
                print(f"⚠ Not enough data for {sym}")
                continue
            # Only send if signal changed
            if previous_signals.get(sym) != summary:
                chart = draw_chart(sym, df)
                send_telegram(msg, image_bytes=chart)
                previous_signals[sym] = summary
                print(f"🟢 Sent {sym} update: {summary}")
            else:
                print(f"⚪ {sym} no change: {summary}")
        except Exception as e:
            print(f"🔴 Error for {sym}: {e}")

if __name__ == "__main__":
    analyze_symbols()
