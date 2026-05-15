import os, uuid, hashlib, requests, json
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION (Fill these in Koyeb Environment Variables or here) ---
CONFIG = {
    "TELEGRAM_TOKEN": os.getenv("TG_TOKEN", "YOUR_BOT_TOKEN"),
    "CHAT_ID": os.getenv("TG_CHAT_ID", "YOUR_CHAT_ID"),
    "BANK_DETAILS": "IBAN: BE00 1234 5678 9012 | Holder: Said Ameeny",
    "WALLETS": {
        "USDT_TRC20": "TR7NHqfj2... (Your Wallet)",
        "BTC": "1A1zP1eP... (Your Wallet)",
        "ETH": "0x742d... (Your Wallet)",
        "BNB": "0x742d... (Your Wallet)"
    }
}

# شبیه‌سازی دفتر کل با قابلیت پیگیری (Internal Ledger)
# در محیط عملیاتی بهتر است از SQLite استفاده کنید
ledger = {}

def create_internal_hash(data_str):
    """ایجاد هش بلاک‌چین داخلی برای پیگیری تراکنش"""
    return hashlib.sha256(f"{data_str}{uuid.uuid4()}".encode()).hexdigest()

def notify_admin(msg, buttons=None):
    """ارسال اعلان هوشمند به تلگرام مدیریت"""
    url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_TOKEN']}/sendMessage"
    payload = {
        "chat_id": CONFIG["CHAT_ID"],
        "text": msg,
        "parse_mode": "HTML"
    }
    return requests.post(url, json=payload)

@app.route('/')
def home():
    return render_template('index.html', wallets=CONFIG["WALLETS"], bank=CONFIG["BANK_DETAILS"])

@app.route('/api/order', methods=['POST'])
def create_order():
    data = request.json
    tx_id = str(uuid.uuid4())[:12].upper()
    tx_hash = create_internal_hash(tx_id)
    
    order = {
        "tx_id": tx_id,
        "hash": tx_hash,
        "type": data['type'], # 'buy' or 'sell'
        "amount": data['amount'],
        "currency": data['currency'],
        "network": data['network'],
        "user_address": data['address'],
        "status": "PENDING",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    ledger[tx_id] = order
    
    # اعلان به تلگرام
    side = "خرید 🟢" if data['type'] == 'buy' else "فروش 🔴"
    msg = (
        f"📩 <b>درخواست جدید {side}</b>\n"
        f"ID: <code>{tx_id}</code>\n"
        f"مقدار: {data['amount']} {data['currency']}\n"
        f"شبکه: {data['network']}\n"
        f"آدرس مشتری: <code>{data['address']}</code>\n"
        f"------------------------\n"
        f"🔗 هش امنیتی: <code>{tx_hash[:20]}...</code>"
    )
    notify_admin(msg)
    
    return jsonify({"status": "success", "order": order})

@app.route('/api/track/<tx_id>')
def track_order(tx_id):
    order = ledger.get(tx_id.upper())
    if not order:
        return jsonify({"status": "error", "message": "تراکنش یافت نشد"}), 404
    return jsonify(order)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)