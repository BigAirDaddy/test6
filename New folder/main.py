import time
import pandas as pd
import oandapyV20
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments
import requests

# OANDA API key
api_key = "a29f449ec75cb7790f8af739ddd1d328-62a6426f2d2bf8e38d68a8d1f759e2d0"

# Initialize the OANDA API client
api = API(environment="practice", access_token=api_key)  # Use "live" for real trading

# Define your OANDA account ID
account_id = "101-001-27146548-004"

# Define trading parameters
symbol = 'EUR_USD'  # Forex currency pair
short_period = 10  # Short-term moving average period
long_period = 30   # Long-term moving average period
order_size = 400  # Trade size in the base currency

# Function to get historical OHLCV data
def fetch_ohlcv(symbol, timeframe, count):
    params = {
        "count": count,
        "granularity": timeframe
    }
    request = instruments.InstrumentsCandles(instrument=symbol, params=params)
    response = api.request(request)
    ohlcv_data = response.get("candles")
    df = pd.DataFrame(ohlcv_data)
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time')
    return df

# Function to calculate moving averages
def calculate_moving_averages(df, short_period, long_period):
    df['SMA_Short'] = df['mid'].apply(lambda x: float(x['c'])).rolling(window=short_period).mean()
    df['SMA_Long'] = df['mid'].apply(lambda x: float(x['c'])).rolling(window=long_period).mean()
    return df

# Function to execute a trade
def execute_market_order(symbol, side, quantity):
    endpoint = f"/v3/accounts/{account_id}/orders"
    url = f"https://api-fxpractice.oanda.com{endpoint}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "order": {
            "type": "MARKET",
            "instrument": symbol,
            "units": quantity if side == 'buy' else -quantity,
            "timeInForce": "FOK",
            "positionFill": "DEFAULT"
        }
    }

    response = requests.post(url, headers=headers, json=data)
    return response

# Main trading loop
while True:
    # Fetch historical data
    print("Fetching historical data...")
    ohlcv_data = fetch_ohlcv(symbol, 'H1', count=long_period)

    # Calculate moving averages
    ohlcv_data = calculate_moving_averages(ohlcv_data, short_period, long_period)

    # Check for crossover
    if ohlcv_data['SMA_Short'].iloc[-1] > ohlcv_data['SMA_Long'].iloc[-1]:
        # Buy when the short-term MA crosses above the long-term MA
        print("Crossover detected. Buying...")
        execute_market_order(symbol, 'buy', order_size)
    elif ohlcv_data['SMA_Short'].iloc[-1] < ohlcv_data['SMA_Long'].iloc[-1]:
        # Sell when the short-term MA crosses below the long-term MA
        print("Crossover detected. Selling...")
        execute_market_order(symbol, 'sell', order_size)

    print("Sleeping for 1 hour before checking again...")
    time.sleep(900)  # Sleep for 1 hour
