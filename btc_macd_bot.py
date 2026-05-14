import requests
import numpy as np
import pandas as pd
import os
from datetime import datetime

SMS_API_KEY = os.getenv('IPPANEL_API_KEY')
YOUR_NUMBER = os.getenv('PHONE_NUMBER')

def get_btc_4h_data():
    try:
        url = "https://api.nobitex.ir/v3/trades/btc-rls"
        params = {"type": "sell", "limit": 100}
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            prices = []
            trades = data.get('trades', [])
            for trade in trades:
                price = float(trade.get('price', 0))
                if price > 0:
                    prices.append(price)
            prices.reverse()
            if len(prices) >= 34:
                return prices
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def calculate_macd(prices, fast=12, slow=26, signal=9):
    prices_series = pd.Series(prices)
    ema_fast = prices_series.ewm(span=fast, adjust=False).mean()
    ema_slow = prices_series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

def check_cross(macd_line, signal_line):
    if len(macd_line) < 2:
        return None
    if macd_line.iloc[-2] <= signal_line.iloc[-2] and macd_line.iloc[-1] > signal_line.iloc[-1]:
        return "BUY"
    elif macd_line.iloc[-2] >= signal_line.iloc[-2] and macd_line.iloc[-1] < signal_line.iloc[-1]:
        return "SELL"
    return None

def send_sms(message):
    if not SMS_API_KEY or not YOUR_NUMBER:
        print("API Key or phone number missing")
        return False
    url = "https://api.ippanel.com/v1/messages"
    headers = {"Authorization": f"AccessKey {SMS_API_KEY}", "Content-Type": "application/json"}
    data = {"sender": "+983000505", "recipient": YOUR_NUMBER, "message": message}
    try:
        r = requests.post(url, json=data, headers=headers, timeout=20)
        return r.status_code == 200
    except Exception as e:
        print(f"SMS error: {e}")
        return False

def main():
    print(f"{datetime.now()} - Checking Bitcoin MACD...")
    prices = get_btc_4h_data()
    if not prices:
        print("No data")
        return
    macd, signal = calculate_macd(prices)
    cross = check_cross(macd, signal)
    if cross:
        msg = f"BTC 4H MACD CROSS: {cross} at {datetime.now()}"
        print(msg)
        send_sms(msg)
    else:
        print("No cross")

if __name__ == "__main__":
    main()
