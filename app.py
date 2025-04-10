from flask import Flask, render_template_string
import requests
from datetime import datetime
import os
import sys
import traceback

app = Flask(__name__)

tracked_tokens = ['bitcoin', 'ethereum', 'solana', 'ripple']
token_id_map = {
    'bitcoin': 'bitcoin',
    'ethereum': 'ethereum',
    'solana': 'solana',
    'ripple': 'ripple'
}
currency = 'usd'
price_history = {token: [] for token in tracked_tokens}
trend_flags = {token: {'last_trend': None, 'trend_streak': 0} for token in tracked_tokens}

html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Crypto Trend Alerts</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #0e0e0e; color: #f1f1f1; padding: 20px; }
        h1 { color: #4caf50; }
        .alert { color: red; font-weight: bold; }
        .gainer { color: #4caf50; }
        .price { margin-bottom: 10px; }
        .section { margin-top: 20px; }
    </style>
</head>
<body>
    <h1>🚀 Crypto Trend Alert System</h1>
    <div class="section">
        <h2>Top Gainers (1h Change)</h2>
        {% for gainer in gainers %}
            <div class="gainer">{{ gainer }}</div>
        {% endfor %}
    </div>
    <div class="section">
        <h2>Current Prices & Trends</h2>
        {% for line in alerts %}
            <div class="price">{{ line }}</div>
        {% endfor %}
    </div>
</body>
</html>
"""

def get_price(token):
    token_id = token_id_map[token]
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies={currency}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data[token_id][currency] if token_id in data and currency in data[token_id] else None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price for {token}: {e}", file=sys.stderr)
        return None

def get_top_gainers():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': currency,
            'order': 'percent_change_1h_desc',
            'per_page': 5,
            'page': 1
        }
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        return [
            f"{coin['symbol'].upper()}: {coin['price_change_percentage_1h_in_currency']:.2f}% (${coin['current_price']:.2f})"
            for coin in data if coin.get('price_change_percentage_1h_in_currency') is not None
        ]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching top gainers: {e}", file=sys.stderr)
        return ["Error fetching top gainers"]

def percent_change(p1, p2):
    return ((p2 - p1) / p1) * 100 if p1 != 0 else 0

@app.route("/")
def index():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alerts = []
    gainers = get_top_gainers()

    for token in tracked_tokens:
        price = get_price(token)
        if price is None:
            alerts.append(f"{token.upper()}: Error fetching price")
            continue

        history = price_history[token]
        history.append(price)
        if len(history) > 6:
            history.pop(0)

        alerts.append(f"[{timestamp}] {token.upper()}: ${price:.4f}")

        if len(history) >= 4:
            p1, p2, p3, p4 = history[-4:]
            c1, c2, c3 = percent_change(p1, p2), percent_change(p2, p3), percent_change(p3, p4)

            if c1 > 0.5 and c2 > 0.5 and c3 > 0.5:
                if trend_flags[token]['last_trend'] == 'up':
                    trend_flags[token]['trend_streak'] += 1
                else:
                    trend_flags[token]['last_trend'] = 'up'
                    trend_flags[token]['trend_streak'] = 1
                if trend_flags[token]['trend_streak'] >= 2:
                    alerts.append(f"🚨🚨 ALERT ALERT! Major Buying Signal with {token.upper()} 🚨🚨")
                else:
                    alerts.append(f"🔼 {token.upper()} rising — 3x gains (+{c1:.2f}%, +{c2:.2f}%, +{c3:.2f}%)")
            elif c1 < -0.5 and c2 < -0.5 and c3 < -0.5:
                trend_flags[token]['last_trend'] = 'down'
                trend_flags[token]['trend_streak'] = 0
                alerts.append(f"🔽 {token.upper()} dipping — 3x losses (-{abs(c1):.2f}%, -{abs(c2):.2f}%, -{abs(c3):.2f}%)")
            else:
                trend_flags[token]['last_trend'] = None
                trend_flags[token]['trend_streak'] = 0

    return render_template_string(html_template, alerts=alerts, gainers=gainers)

if __name__ == '__main__':
    try:
        port_raw = os.environ.get("PORT", "5000")
        port = int(port_raw) if port_raw.isdigit() else 5000
        print(f"Starting Flask app on port {port}...", file=sys.stderr)
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print("Flask app failed to start:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
