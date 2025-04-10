import requests
import time


# CONFIG SECTION
tracked_tokens = {
    'solana': {
        'symbol': 'SOL',
        'low_alert': 176,
        'high_alert': 185
    },
    'ripple': {
        'symbol': 'XRP',
        'low_alert': 0.56,
        'high_alert': 0.62
    }
}

currency = 'usd'
check_interval = 60  # seconds

# FUNCTION: Get price from CoinGecko
def get_price(token_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies={currency}"
    response = requests.get(url)
    data = response.json()
    return data[token_id][currency]

# FUNCTION: Send alert notification
def send_alert(title, message):
    notification.notify(
        title=title,
        message=message,
        timeout=5
    )

# MAIN LOOP
while True:
    try:
        for token_id, info in tracked_tokens.items():
            price = get_price(token_id)
            symbol = info['symbol']
            print(f"{symbol}: ${price}")

            if price <= info['low_alert']:
                send_alert(f"{symbol} ALERT: Price Drop", f"{symbol} is down to ${price}")
            elif price >= info['high_alert']:
                send_alert(f"{symbol} ALERT: Price Spike", f"{symbol} is up to ${price}")

        print("-" * 30)

    except Exception as e:
        print("Error:", e)

    time.sleep(check_interval)
