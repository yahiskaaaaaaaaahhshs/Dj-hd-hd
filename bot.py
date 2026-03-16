import telebot
import requests
import time
import random
import os
import threading
from flask import Flask
from datetime import datetime

# Bot configuration
BOT_TOKEN = "8531959574:AAGfNISvTHtlSO2LOYdKsVo6l56N-e9Sz-o"
OWNER_ID = 7904483885

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)
bot.parse_mode = 'HTML'

# Flask app for keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Start Flask in a thread
threading.Thread(target=run_flask, daemon=True).start()

print("🤖 Bot is starting...")
print(f"👑 Owner ID: {OWNER_ID}")

# BIN lookup API
def get_bin_info(bin_number):
    try:
        url = f"https://lookup.binlist.net/{bin_number}"
        headers = {'Accept-Version': '3', 'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def format_card_response(card, gate, response_text, user_id, username):
    parts = card.split('|')
    if len(parts) < 4:
        return None, None
    
    cc, mm, yy, cvv = [p.strip() for p in parts[:4]]
    
    if len(yy) == 2:
        yy = '20' + yy
    
    # Get BIN info
    bin_info = get_bin_info(cc[:6])
    
    if bin_info:
        scheme = bin_info.get('scheme', '').upper() or (
            "VISA" if cc.startswith('4') else
            "MASTERCARD" if cc.startswith('5') else
            "AMEX" if cc.startswith('3') else "UNKNOWN"
        )
        
        bank = bin_info.get('bank', {}).get('name', 'TRUIST BANKS, INC.').upper()
        country_info = bin_info.get('country', {})
        country = country_info.get('name', 'UNITED STATES').upper()
        code = country_info.get('alpha2', 'US')
        
        flags = {'US':'🇺🇸','GB':'🇬🇧','CA':'🇨🇦','AU':'🇦🇺','IN':'🇮🇳'}
        flag = flags.get(code, '🌍')
        
        card_type = scheme
        bank_name = bank
        country_display = f"{country} - [{flag}]"
        category = bin_info.get('type', 'CREDIT').upper()
    else:
        card_type = "VISA" if cc.startswith('4') else "MASTERCARD" if cc.startswith('5') else "AMEX" if cc.startswith('3') else "UNKNOWN"
        bank_name = "TRUIST BANKS, INC."
        country_display = "UNITED STATES - [🇺🇸]"
        category = "CREDIT"
    
    response_time = round(random.uniform(2.0, 12.0), 1)
    mention = f"<a href='tg://user?id={user_id}'>@{username if username else 'User'}</a>"
    
    return f"""
<b>CC :</b> <code>{cc}|{mm}|{yy}|{cvv}</code>
<b>Status :</b> Approved.!! ✅
<b>Response :</b> {response_text}
<b>Gate :</b> {gate}

<b>Info :</b> {card_type} - {category} - BUSINESS
<b>Bank :</b> {bank_name}
<b>Country :</b> {country_display}

<b>T/t :</b> {response_time}s
<b>User :</b> {mention}
""", response_time

def is_owner(user_id):
    return user_id == OWNER_ID

@bot.message_handler(commands=['start'])
def start_command(message):
    if is_owner(message.from_user.id):
        bot.reply_to(message, "<b>Welcome to Onyx Env Bot - Owner Mode</b>", parse_mode='HTML')
    else:
        bot.reply_to(message, "<b>Welcome to Onyx Env Bot</b>", parse_mode='HTML')

@bot.message_handler(commands=['chk', 'cc'])
def check_card(message):
    if not is_owner(message.from_user.id):
        return
    
    parts = message.text.strip().split(' ', 3)
    if len(parts) < 4:
        bot.reply_to(message, "<b>❌ Use: /chk CC|MM|YY|CVV STATUS GATE</b>", parse_mode='HTML')
        return
    
    try:
        card, status, gateway = parts[1].strip(), parts[2].upper(), parts[3]
        msg = bot.reply_to(message, "<b>🔄 Processing...</b>", parse_mode='HTML')
        
        time.sleep(random.uniform(2.0, 12.0))
        
        result, _ = format_card_response(
            card, gateway, status,
            message.from_user.id,
            message.from_user.username or message.from_user.first_name
        )
        
        if result:
            bot.delete_message(message.chat.id, msg.message_id)
            bot.reply_to(message, result, parse_mode='HTML')
        else:
            bot.edit_message_text("<b>❌ Invalid format</b>", message.chat.id, msg.message_id, parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"<b>❌ Error: {str(e)}</b>", parse_mode='HTML')

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    if is_owner(message.from_user.id):
        bot.reply_to(message, "<b>Use /chk command</b>", parse_mode='HTML')

print("Removing webhook...")
bot.remove_webhook()
time.sleep(2)

def run_bot():
    while True:
        try:
            print("Starting polling...")
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

threading.Thread(target=run_bot, daemon=True).start()
print("✅ Bot is running!")

if __name__ == "__main__":
    while True:
        time.sleep(60)
        print("Heartbeat: Bot running...")
