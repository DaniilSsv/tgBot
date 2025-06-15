import pandas as pd

def sma(series, period):
    if len(series) < period: 
        return None
    return series.iloc[-period:].mean()

def rsi(series, period=14):
    if len(series) < period + 1: 
        return None
    delta = series.diff().iloc[-(period+1):].dropna()
    gains = delta[delta > 0].sum() / period
    losses = -delta[delta < 0].sum() / period
    return 100 - (100 / (1 + (gains / losses))) if losses != 0 else 100.0

def volume_spike(df, threshold=1.5):
    vol = df['Volume']
    avg_vol = vol.rolling(20).mean()
    return vol.iloc[-1] > threshold * avg_vol.iloc[-1]

def bollinger_band_signal(series, period=20):
    if len(series) < period:
        return None
    sma_val = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = sma_val + (2 * std)
    lower = sma_val - (2 * std)
    price = series.iloc[-1]
    
    if price > upper.iloc[-1]:
        return "📈 Пробой верхней границы"
    elif price < lower.iloc[-1]:
        return "📉 Пробой нижней границы"
    return "➖ Внутри границ"


def atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(window=period).mean().iloc[-1]

def macd_hist(series):
    if len(series) < 35:
        return None
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line.iloc[-1] - signal.iloc[-1]

def stochastic_oscillator(series, k_period=14, d_period=3):
    if len(series) < k_period + d_period:
        return None, None
    low_min = series.rolling(window=k_period).min()
    high_max = series.rolling(window=k_period).max()
    k = 100 * (series - low_min) / (high_max - low_min)
    d = k.rolling(window=d_period).mean()
    k_val, d_val = k.iloc[-1], d.iloc[-1]
    # Interpretation example: overbought if k_val > 80, oversold if < 20
    return k_val, d_val

def adx(df, period=14):
    import numpy as np
    high = df['High']
    low = df['Low']
    close = df['Close']
    plus_dm = high.diff()
    minus_dm = low.diff().abs()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx_val = dx.rolling(window=period).mean().iloc[-1]
    return adx_val

def ema_cross(df, short_period=9, long_period=21):
    ema_short = df['Close'].ewm(span=short_period, adjust=False).mean().iloc[-1]
    ema_long = df['Close'].ewm(span=long_period, adjust=False).mean().iloc[-1]
    if ema_short > ema_long:
        return "Bullish"
    elif ema_short < ema_long:
        return "Bearish"
    return "Neutral"

def obv(df):
    obv_val = 0
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
            obv_val += df['Volume'].iloc[i]
        elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
            obv_val -= df['Volume'].iloc[i]
    return obv_val

def vwap(df):
    vol_price = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum()
    vol = df['Volume'].cumsum()
    vwap_val = vol_price.iloc[-1] / vol.iloc[-1]
    return vwap_val
