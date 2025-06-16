from components import fetch_klines, generate_signal, send_telegram, draw_chart
import time

previous_signals = {}

def analyze_symbols():
    symbols = ["BTCUSDT", "SOLUSDT", "SUIUSDT", "ENSUSDT"]
    for sym in symbols:
        try:
            df = fetch_klines(sym)
            summary, msg, _ = generate_signal(sym, df)
            if summary is None:
                print(f"⚠ Not enough data for {sym}")
                continue
            if previous_signals.get(sym) != summary:
                chart = draw_chart(sym, df)
                send_telegram(msg, image_bytes=chart)
                previous_signals[sym] = summary
                print(f"🟢 Sent {sym} update: {summary}")
            else:
                print(f"⚪ {sym} no change")
        except Exception as e:
            print(f"🔴 Error for {sym}: {e}")

if __name__ == "__main__":
    while True:
        analyze_symbols()
        time.sleep(600)
