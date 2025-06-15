import requests
import pandas as pd

def fetch_klines(symbol, interval='1h', limit=200):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=5)
    data = r.json()
    df = pd.DataFrame(data, columns=[
        'Open time','Open','High','Low','Close','Volume',
        'Close time','Quote asset volume','Number of trades',
        'Taker buy base asset volume','Taker buy quote asset volume','Ignore'
    ])
    for col in ['Open','High','Low','Close','Volume']:
        df[col] = pd.to_numeric(df[col])
    df['Open time'] = pd.to_datetime(df['Open time'], unit='ms')
    df.set_index('Open time', inplace=True)
    return df[['Open','High','Low','Close','Volume']]
