import os, uuid, hashlib, requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# دریافت تنظیمات (دقیقاً با نام‌هایی که در عکس کویب گذاشتی)
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

def notify_admin(msg):
    """تابع ارسال پیام با قابلیت چاپ خطا در لاگ"""
    if not TG_TOKEN or not TG_CHAT_ID:
        print(f"❌ خطای تنظیمات: TOKEN={TG_TOKEN}, ID={TG_CHAT_ID}")
        return False
    
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        res = r.json()
        if not res.get("ok"):
            print(f"❌ تلگرام ارور داد: {res.get('description')}")
        else:
            print("✅ پیام با موفقیت به تلگرام ارسال شد.")
        return res.get("ok")
    except Exception as e:
        print(f"❌ خطای شبکه تلگرام: {e}")
        return False

# --- تست خودکار هنگام اجرا ---
# به محض اینکه کویب برنامه رو بالا بیاره، این پیام باید بیاد
with app.app_context():
    print("🚀 در حال ارسال پیام تست به تلگرام...")
    notify_admin("<b>✅ سیستم صرافی با موفقیت در Koyeb بالا آمد!</b>")

@app.route('/')
def home():
    return "<h1>Exchange is Running</h1><p>Check Telegram for Startup Message</p>"

@app.route('/api/order', methods=['POST'])
def create_order():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No Data"}), 400
        
    tx_id = str(uuid.uuid4())[:8].upper()
    msg = (
        f"📩 <b>سفارش جدید</b>\n"
        f"کد: {tx_id}\n"
        f"مقدار: {data.get('amount')} {data.get('currency')}\n"
        f"آدرس: {data.get('address')}"
    )
    
    sent = notify_admin(msg)
    return jsonify({"status": "success" if sent else "error", "id": tx_id})

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
