from flask import Flask, jsonify
import os

app = Flask(__name__)


@app.route('/')
def index():
    import requests

    x = requests.get('https://mainnet.zklighter.elliot.ai/api/v1/account?by=index&value=24').content
    import json
    
  
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
    return st



if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
