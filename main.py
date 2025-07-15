from flask import Flask, jsonify
import os
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('PEPEGA_BOT_TOKEN')
TELEGRAM_CHAT_ID = '-1002526387148'
TELEGRAM_TOPIC_ID = 289
CACHE_FILE = 'cache.txt'

def load_cache():
    """Load position counts from cache file"""
    cache = {}
    try:
        with open(CACHE_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split('|')
                    if len(parts) == 2:
                        symbol, count = parts
                        cache[symbol] = float(count)
    except FileNotFoundError:
        pass
    return cache

def save_cache(positions_data):
    """Save position counts to cache file"""
    with open(CACHE_FILE, 'w') as f:
        for symbol, count in positions_data.items():
            f.write(f"{symbol}|{count}\n")

def has_positions_changed(current_positions, cached_positions):
    """Check if any position counts have changed"""
    # Check for new or changed positions
    for symbol, count in current_positions.items():
        if symbol not in cached_positions or cached_positions[symbol] != count:
            return True
    
    # Check for removed positions
    for symbol in cached_positions:
        if symbol not in current_positions:
            return True
    
    return False

def send_to_telegram_topic(message, chat_id, topic_id, bot_token):
    """Send a message to a specific topic in a Telegram group"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'message_thread_id': topic_id,
        'parse_mode': 'HTML'
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
        yo = curr_price - (total_asset_value / position)
        if sign == 1:
            return yo
        if sign == -1:
            yo = ((pos_value + total_asset_value) / position)
            return yo
    
    # Load cached positions
    cached_positions = load_cache()
    current_positions = {}
    
    # Build display string and track current positions
    st = ''
    st += f'<b>💰 Account Value: ${total_asset_value:,.2f}</b>\n'
    st += f'<i>Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</i>\n'
    st += '━━━━━━━━━━━━━━━━━━━━━━\n\n'
    
    L_pos = 0
    S_pos = 0
    
    # Sort positions by value for better readability
    active_positions = []
    for pos in positions:
        position = float(pos['position'])
        if position != 0:
            active_positions.append(pos)
    
    active_positions.sort(key=lambda x: abs(float(x['position_value'])), reverse=True)
    
    for pos in active_positions:
        symbol = pos['symbol']
        entry = float(pos['avg_entry_price'])
        pos_value = float(pos['position_value'])
        imf = float(pos['initial_margin_fraction'])
        sign = int(pos['sign'])
        position = float(pos['position'])
    
        if position == 0 or entry == 0 or pos_value == 0:
            continue
        
        # Track current position count
        current_positions[symbol] = position
    
        curr_price = pos_value / position
        liq_price = calc_liq_price(curr_price, position, pos_value, total_asset_value, sign)
        
        # Calculate PnL
        pnl = (curr_price - entry) * position * sign
        pnl_percent = ((curr_price - entry) / entry) * 100 * sign
        
        # Format position type
        if sign == 1:
            pos_type = '🟢 LONG'
            L_pos += pos_value
        else:
            pos_type = '🔴 SHORT'
            L_pos -= pos_value
            S_pos += pos_value
        
        # Format PnL display
        pnl_emoji = '📈' if pnl >= 0 else '📉'
        pnl_sign = '+' if pnl >= 0 else ''
        
        st += f'<b>{pos_type} {symbol}</b>\n'
        st += f'├ Entry: ${entry:,.2f}\n'
        st += f'├ Current: ${curr_price:,.2f}\n'
        st += f'├ Count: {position:,.2f}\n'
        st += f'├ Value: ${pos_value:,.2f}\n'
        st += f'├ PnL: {pnl_emoji} {pnl_sign}${pnl:,.2f} ({pnl_sign}{pnl_percent:.2f}%)\n'
        st += f'└ Liquidation: ${liq_price:,.2f}\n\n'
    
    # Add summary section
    st += '━━━━━━━━━━━━━━━━━━━━━━\n'
    st += '<b>📊 Summary</b>\n'
    
    if S_pos == 0:
        st += '├ L/S Ratio: Long Only\n'
    else:
        st += f'├ L/S Ratio: {(L_pos / S_pos):,.2f}\n'
    
    st += f'├ Total Long: ${L_pos:,.2f}\n'
    st += f'└ Total Short: ${S_pos:,.2f}\n'
    
    # Check if positions have changed
    positions_changed = has_positions_changed(current_positions, cached_positions)
    
    # HTML version for web display
    html_st = st.replace('\n', '<br>')
    
    # Only send Telegram message if positions changed
    if positions_changed:
        send_to_telegram_topic(
            message=st,
            chat_id=TELEGRAM_CHAT_ID,
            topic_id=TELEGRAM_TOPIC_ID,
            bot_token=TELEGRAM_BOT_TOKEN
        )
        # Update cache
        save_cache(current_positions)
        html_st += '<br><br><i>✅ Telegram notification sent (positions changed)</i>'
    else:
        html_st += '<br><br><i>ℹ️ No position changes detected, Telegram notification skipped</i>'
    
    return html_st

# Initialize cache file
if not os.path.exists(CACHE_FILE):
    open(CACHE_FILE, 'w').close()

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
