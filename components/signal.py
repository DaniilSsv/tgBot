from .indicators import (
    sma, rsi, macd_hist, bollinger_band_signal,
    volume_spike, atr, stochastic_oscillator, adx, ema_cross, obv, vwap
)

def generate_signal(symbol, df):
    closes = df['Close']
    price = closes.iloc[-1]

    # Calculate indicators
    # Trend and momentum indicators
    r_val = rsi(closes)
    m_val = macd_hist(closes)
    sma50 = sma(closes, 50)
    sma200 = sma(closes, 200)
    ema_signal = ema_cross(df)
    adx_val = adx(df)
    k_val, d_val = stochastic_oscillator(closes)

    # Volatility and volume indicators
    bb_signal = bollinger_band_signal(closes)
    v_spike = volume_spike(df)
    atr_val = atr(df)
    obv_val = obv(df)
    vwap_val = vwap(df)

    # Check for missing data
    if None in (r_val, m_val, sma50, sma200, bb_signal, atr_val, k_val, d_val, adx_val, ema_signal, obv_val, vwap_val):
        return None, None, None

    # Signals (in Russian)
    r_sig = (
        "🔥 Перекупленность" if r_val > 70 else
        "🧊 Перепроданность" if r_val < 30 else
        "✅ Нейтрально"
    )
    stoch_sig = (
        "🔥 Перекупленность" if k_val > 80 else
        "🧊 Перепроданность" if k_val < 20 else
        "✅ Нейтрально"
    )
    macd_sig = "🔺 Бычий сигнал (MACD)" if m_val > 0 else "🔻 Медвежий сигнал (MACD)"
    ema_sig = (
        "🔺 Бычий сигнал (EMA)" if ema_signal == "Bullish" else
        "🔻 Медвежий сигнал (EMA)" if ema_signal == "Bearish" else
        "➖ Нейтрально"
    )
    trend_sig = (
        "💪 Сильный тренд (ADX)" if adx_val > 25 else
        "⚠ Слабый тренд (ADX)" if adx_val < 20 else
        "➖ Нет тренда"
    )
    sma_sig = (
        "⚡ Золотое пересечение (SMA)" if sma50 > sma200 else
        "⚠ Мёртвое пересечение (SMA)" if sma50 < sma200 else
        "➖ Нейтральный тренд"
    )
    vol_spike_sig = "🚀 Всплеск объёма" if v_spike else "➖ Обычный объём"
    obv_sig = (
        "📈 Подтверждает тренд (OBV)" if obv_val > 0 else
        "📉 Расхождение (OBV)" if obv_val < 0 else
        "➖ Нейтрально"
    )
    vwap_sig = "📊 Цена выше VWAP" if price > vwap_val else "📉 Цена ниже VWAP"
    atr_sig = f"{atr_val:.4f}"

    summary = (
        f"{r_sig} | {stoch_sig} | {macd_sig} | {ema_sig} | {sma_sig} | "
        f"{trend_sig} | {bb_signal} | {vol_spike_sig} | {obv_sig} | {vwap_sig}"
    )

    message = (
        f"📊 *Анализ {symbol}*\n\n"
        f"📈 Текущая цена: *{price:.2f}* USDT\n\n"

        f"--- *Индикаторы тренда и момента* ---\n"
        f"• 💡 RSI (14): {r_val:.1f} — {r_sig}\n"
        f"• 💡 Стохастик: K={k_val:.1f}, D={d_val:.1f} — {stoch_sig}\n"
        f"• 📉 MACD гистограмма: {m_val:.4f} — {macd_sig}\n"
        f"• ⚡ EMA Cross: {ema_sig}\n"
        f"• 📏 SMA50: {sma50:.2f}\n"
        f"• 📐 SMA200: {sma200:.2f} — {sma_sig}\n"
        f"• 💪 ADX (сила тренда): {adx_val:.1f} — {trend_sig}\n\n"

        f"--- *Волатильность и объём* ---\n"
        f"• 🎯 Полосы Боллинджера: {bb_signal}\n"
        f"• 🌪️ ATR (волатильность): {atr_sig}\n"
        f"• 🔊 Объём: {vol_spike_sig}\n"
        f"• 📈 OBV: {obv_sig}\n"
        f"• 📊 VWAP: {vwap_sig}"
    )

    return summary, message, (r_val, m_val, sma50, sma200, k_val, d_val, adx_val, obv_val, vwap_val)
