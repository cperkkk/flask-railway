from flask import Flask, jsonify
import os
import requests
import json

app = Flask(__name__)

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('PEPEGA_BOT_TOKEN')
TELEGRAM_CHAT_ID = '-1002526387148'  # e.g., -1001234567890
TELEGRAM_TOPIC_ID = 289  # e.g., 123

def send_to_telegram_topic(message, chat_id, topic_id, bot_token):
    """Send a message to a specific topic in a Telegram group"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'message_thread_id': topic_id,  # This specifies the topic
        'parse_mode': 'HTML'  # Since you're using HTML formatting
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending to Telegram: {e}")
        return None

@app.route('/')
def index():
    x = requests.get('https://mainnet.zklighter.elliot.ai/api/v1/account?by=index&value=24').content
    
    data = x
    j = json.loads(data)
    account = j['accounts'][0]
    positions = account['positions']
    total_asset_value = float(account['total_asset_value'])
    
    def calc_leverage(imf):
        return 1 / (float(imf) / 100)
    
    def calc_liq_price(curr_price, position, pos_value, total_asset_value, sign):
        # my bad, 1 for long, -1 for short
        yo = curr_price - (total_asset_value / position)
        if sign == 1:
            return yo
        if sign == -1:
            yo = ((pos_value + total_asset_value) / position)
            return yo
    
    st = ''
    st += (f'ACC VALUE {total_asset_value:,.2f}')
    st += '\n<br>'
    L_pos = 0
    S_pos = 0
    
    for pos in positions:
        symbol = pos['symbol']
        entry = float(pos['avg_entry_price'])
        pos_value = float(pos['position_value'])
        imf = float(pos['initial_margin_fraction'])
        sign = int(pos['sign'])
        position = float(pos['position'])
    
        if position == float(0) or entry == 0 or pos_value == 0:
            continue  # skip empty positions
    
        curr_price = pos_value / position
        liq_price = calc_liq_price(curr_price, position, pos_value, total_asset_value, sign)
        LS = '+L'
        L_pos += pos_value
        if sign == -1:
            LS = '-S'
            L_pos -= pos_value
            S_pos += pos_value
        st += (f"{LS} {symbol} => ENTRY {entry:,.2f}, COUNT {position:,.2f}, CURR_PRICE {curr_price:,.2f}, VALUE {pos_value:,.2f}, LIQUIDATION {liq_price:,.2f}")
        st += '\n<br>'
    
    st += (f'L/S ratio = {(L_pos / S_pos):,.2f}')
    st += '\n<br>'
    
    # Prepare message for Telegram (remove HTML breaks)
    telegram_message = st.replace('<br>', '')
    
    # Send to Telegram topic
    send_to_telegram_topic(
        message=telegram_message,
        chat_id=TELEGRAM_CHAT_ID,
        topic_id=TELEGRAM_TOPIC_ID,
        bot_token=TELEGRAM_BOT_TOKEN
    )
    
    return st

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
