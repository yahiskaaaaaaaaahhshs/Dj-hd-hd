import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import time
import random
import os
import sys
import threading
from flask import Flask
from datetime import datetime

# Bot configuration
BOT_TOKEN = "8531959574:AAFxoDFV5CE7e0yyEHBwxCssWfrsXkBZgqU"
OWNER_ID = 7310898934

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

# Print to Railway logs
print("🤖 Bot is starting...")
print(f"👑 Owner ID: {OWNER_ID}")
print("✅ Bot initialized")

# BIN lookup API
def get_bin_info(bin_number):
    try:
        url = f"https://lookup.binlist.net/{bin_number}"
        headers = {
            'Accept-Version': '3',
            'User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"BIN lookup error: {e}")
        return None

# Format card info for display
def format_card_response(card, gate, response_text, user_id, username):
    parts = card.split('|')
    if len(parts) >= 4:
        cc = parts[0].strip()
        mm = parts[1].strip()
        yy = parts[2].strip()
        cvv = parts[3].strip()
        
        if len(yy) == 2:
            yy = '20' + yy
        
        bin_number = cc[:6]
        bin_info = get_bin_info(bin_number)
        
        if bin_info:
            scheme = bin_info.get('scheme', '')
            if scheme:
                card_type = scheme.upper()
            else:
                if cc.startswith('4'):
                    card_type = "VISA"
                elif cc.startswith('5'):
                    card_type = "MASTERCARD"
                elif cc.startswith('3'):
                    card_type = "AMEX"
                else:
                    card_type = "UNKNOWN"
            
            card_category = bin_info.get('type', 'CREDIT').upper()
            bank_info = bin_info.get('bank', {})
            bank_name = bank_info.get('name', 'TRUIST BANKS, INC.').upper()
            country_info = bin_info.get('country', {})
            country_name = country_info.get('name', 'UNITED STATES').upper()
            country_code = country_info.get('alpha2', 'US')
            
            flag_emojis = {
                'US': '🇺🇸', 'GB': '🇬🇧', 'CA': '🇨🇦', 'AU': '🇦🇺',
                'IN': '🇮🇳', 'DE': '🇩🇪', 'FR': '🇫🇷', 'JP': '🇯🇵'
            }
            flag = flag_emojis.get(country_code, '🌍')
            country = f"{country_name} - [{flag}]"
        else:
            if cc.startswith('4'):
                card_type = "VISA"
            elif cc.startswith('5'):
                card_type = "MASTERCARD"
            elif cc.startswith('3'):
                card_type = "AMEX"
            else:
                card_type = "UNKNOWN"
            
            card_category = "CREDIT"
            bank_name = "TRUIST BANKS, INC."
            country = "UNITED STATES - [🇺🇸]"
        
        response_time = round(random.uniform(2.0, 12.0), 1)
        
        display_name = f"@{username}" if username and not username.startswith('@') else (username or "User")
        user_mention = f"<a href='tg://user?id={user_id}'>{display_name}</a>"
        
        formatted_response = f"""
<b>CC :</b> <code>{cc}|{mm}|{yy}|{cvv}</code>
<b>Status :</b> Approved.!! ✅
<b>Response :</b> {response_text}
<b>Gate :</b> {gate}

<b>Info :</b> {card_type} - {card_category} - BUSINESS
<b>Bank :</b> {bank_name}
<b>Country :</b> {country}

<b>T/t :</b> {response_time}s
<b>User :</b> {user_mention}
"""
        return formatted_response, response_time
    return None, None

def is_owner(user_id):
    return user_id == OWNER_ID

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if is_owner(user_id):
        bot.reply_to(message, "<b>Welcome to Onyx Env Bot - Owner Mode</b>", parse_mode='HTML')
    else:
        bot.reply_to(message, "<b>Welcome to Onyx Env Bot</b>", parse_mode='HTML')
    print(f"Start command from user: {user_id}")

@bot.message_handler(commands=['chk', 'cc'])
def check_card(message):
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        return
    
    text = message.text.strip()
    parts = text.split(' ', 3)
    
    if len(parts) < 4:
        bot.reply_to(message, "<b>❌ Use: /chk CC|MM|YY|CVV STATUS GATE</b>", parse_mode='HTML')
        return
    
    try:
        card_data = parts[1].strip()
        status = parts[2].strip().upper()
        gateway = parts[3].strip()
        
        processing = bot.reply_to(message, "<b>🔄 Processing...</b>", parse_mode='HTML')
        
        delay = random.uniform(2.0, 12.0)
        time.sleep(delay)
        
        result, resp_time = format_card_response(
            card_data, gateway, status, 
            user_id, message.from_user.username or message.from_user.first_name
        )
        
        if result:
            bot.delete_message(message.chat.id, processing.message_id)
            bot.reply_to(message, result, parse_mode='HTML')
        else:
            bot.edit_message_text("<b>❌ Error</b>", message.chat.id, processing.message_id, parse_mode='HTML')
            
    except Exception as e:
        bot.reply_to(message, f"<b>❌ Error: {str(e)}</b>", parse_mode='HTML')

# Important: Remove webhook and start polling
print("Removing webhook...")
bot.remove_webhook()
time.sleep(2)

print("Starting polling...")

# Start bot in a thread to not block Flask
def run_bot():
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        print(f"Bot error: {e}")
        time.sleep(5)
        run_bot()

threading.Thread(target=run_bot, daemon=True).start()

print("✅ Bot is running!")

# Keep the main thread alive
if __name__ == "__main__":
    while True:
        time.sleep(60)
        print("Heartbeat: Bot is still running...")
