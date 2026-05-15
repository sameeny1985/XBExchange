import os, uuid, hashlib, requests, json
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION (Reading from Koyeb Env) ---
# متغیرها رو دقیقاً از همون نام‌هایی که در عکس فرستادی می‌خونه
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

CONFIG = {
    "BANK_DETAILS": "IBAN: BE00 1234 5678 9012 | Holder: Said Ameeny",
    "WALLETS": {
        "USDT_TRC20": "TR7NHqfj2... (Your Wallet)",
        "BTC": "1A1zP1eP... (Your Wallet)",
        "ETH": "0x742d... (Your Wallet)",
        "BNB": "0x742d... (Your Wallet)"
    }
}

# شبیه‌سازی دفتر کل (Internal Ledger)
ledger = {}

def create_internal_hash(data_str):
    """ایجاد هش اختصاصی برای امنیت تراکنش"""
    return hashlib.sha256(f"{data_str}{uuid.uuid4()}".encode()).hexdigest()

def notify_admin(msg):
    """تابع اصلی ارسال اعلان به تلگرام"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ ERROR: TG_TOKEN or TG_CHAT_ID not found in Environment Variables!")
        return None
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"❌ Telegram Connection Error: {e}")
        return None

@app.route('/')
def home():
    """نمایش صفحه اصلی صرافی"""
    return render_template('index.html', wallets=CONFIG["WALLETS"], bank=CONFIG["BANK_DETAILS"])

@app.route('/api/order', methods=['POST'])
def create_order():
    """دریافت فرم از سایت و ارسال به تلگرام"""
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400
            
        tx_id = str(uuid.uuid4())[:12].upper()
        tx_hash = create_internal_hash(tx_id)
        
        order = {
            "tx_id": tx_id,
            "hash": tx_hash,
            "type": data.get('type', 'buy'),
            "amount": data.get('amount', '0'),
            "currency": data.get('currency', 'USDT'),
            "network": data.get('network', 'TRC20'),
            "user_address": data.get('address', 'N/A'),
            "status": "PENDING",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        ledger[tx_id] = order
        
        # ساخت متن پیام برای ادمین
        side_icon = "🟢" if data.get('type') == 'buy' else "🔴"
        side_text = "خرید" if data.get('type') == 'buy' else "فروش"
        
        msg = (
            f"📩 <b>درخواست جدید {side_text} {side_icon}</b>\n\n"
            f"🆔 کد پیگیری: <code>{tx_id}</code>\n"
            f"💰 مقدار: <b>{order['amount']} {order['currency']}</b>\n"
            f"🌐 شبکه: {order['network']}\n"
            f"📍 آدرس مشتری: <code>{order['user_address']}</code>\n"
            f"------------------------\n"
            f"🔗 هش امنیتی: <code>{tx_hash[:20]}...</code>"
        )
        
        # شلیک پیام به تلگرام
        notify_admin(msg)
        
        return jsonify({"status": "success", "order": order})
    
    except Exception as e:
        print(f"❌ Server Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/track/<tx_id>')
def track_order(tx_id):
    """پیگیری وضعیت تراکنش"""
    order = ledger.get(tx_id.upper())
    if not order:
        return jsonify({"status": "error", "message": "Transaction not found"}), 404
    return jsonify(order)

if __name__ == '__main__':
    # تنظیم پورت برای Koyeb
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
