import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import re
import time
import random
import json
import os
import threading
from datetime import datetime
from flask import Flask

# Bot configuration
BOT_TOKEN = "8531959574:AAFxoDFV5CE7e0yyEHBwxCssWfrsXkBZgqU"
OWNER_ID = 7310898934
CHANNEL_LINK = "https://t.me/+_M6T0R2KiSNmOTRh"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)
bot.parse_mode = 'HTML'

# Store user states
user_data = {}

# Flask app for keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Start Flask in a separate thread
threading.Thread(target=run_flask, daemon=True).start()

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

# Format card info for display with BIN lookup
def format_card_response(card, gate, response_text, user_id, username):
    # Parse card details
    parts = card.split('|')
    if len(parts) >= 4:
        cc = parts[0].strip()
        mm = parts[1].strip()
        yy = parts[2].strip()
        cvv = parts[3].strip()
        
        # Format year if it's 2 digits
        if len(yy) == 2:
            yy = '20' + yy
        
        # Get BIN info (first 6 digits)
        bin_number = cc[:6]
        bin_info = get_bin_info(bin_number)
        
        if bin_info:
            # Extract card type/scheme
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
                elif cc.startswith('6'):
                    card_type = "DISCOVER"
                else:
                    card_type = "UNKNOWN"
            
            # Extract card category
            card_category = bin_info.get('type', 'CREDIT').upper()
            
            # Extract bank info
            bank_info = bin_info.get('bank', {})
            bank_name = bank_info.get('name', 'UNKNOWN BANK')
            if not bank_name or bank_name == '':
                bank_name = "TRUIST BANKS, INC."
            else:
                bank_name = bank_name.upper()
            
            # Extract country info
            country_info = bin_info.get('country', {})
            country_name = country_info.get('name', 'UNITED STATES').upper()
            country_code = country_info.get('alpha2', 'US')
            
            # Create country flag emoji
            flag_emojis = {
                'US': '🇺🇸', 'GB': '🇬🇧', 'CA': '🇨🇦', 'AU': '🇦🇺',
                'IN': '🇮🇳', 'DE': '🇩🇪', 'FR': '🇫🇷', 'JP': '🇯🇵',
                'CN': '🇨🇳', 'BR': '🇧🇷', 'MX': '🇲🇽', 'AE': '🇦🇪'
            }
            flag = flag_emojis.get(country_code, '🌍')
            
            country = f"{country_name} - [{flag}]"
        else:
            # Fallback if BIN lookup fails
            if cc.startswith('4'):
                card_type = "VISA"
            elif cc.startswith('5'):
                card_type = "MASTERCARD"
            elif cc.startswith('3'):
                card_type = "AMEX"
            elif cc.startswith('6'):
                card_type = "DISCOVER"
            else:
                card_type = "UNKNOWN"
            
            card_category = "CREDIT"
            bank_name = "TRUIST BANKS, INC."
            country = "UNITED STATES - [🇺🇸]"
        
        # Generate random response time between 2-12 seconds
        response_time = round(random.uniform(2.0, 12.0), 1)
        
        # Create user mention (blue clickable link)
        display_name = f"@{username}" if username and not username.startswith('@') else (username or "User")
        user_mention = f"<a href='tg://user?id={user_id}'>{display_name}</a>"
        
        # Format the response with bold tags
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
    else:
        return None, None

# Check if user is owner
def is_owner(user_id):
    return user_id == OWNER_ID

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    if is_owner(user_id):
        # Owner sees full welcome
        welcome_text = """
<b>╔══════════════════════╗</b>
<b>  WELCOME TO ONYX ENV BOT</b>
<b>╚══════════════════════╝</b>

<b>┏━━━━━━━━━━━━━━━━━━━━━━┓</b>
<b>┃ ✅ Owner Access Granted</b>
<b>┃ </b>
<b>┃ 📌 Use: /chk CC|MM|YY|CVV STATUS GATE</b>
<b>┃ </b>
<b>┃ Example:</b>
<b>┃ /chk 4111111111111111|12|25|123 APPROVED BRAINTREE</b>
<b>┗━━━━━━━━━━━━━━━━━━━━━━┛</b>
"""
        bot.reply_to(message, welcome_text, parse_mode='HTML')
    else:
        # Users see only welcome message
        bot.reply_to(message, "<b>Welcome to Onyx Env Bot</b>", parse_mode='HTML')

@bot.message_handler(commands=['chk', 'cc'])
def check_card(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Check if user is owner
    if not is_owner(user_id):
        # Non-owners get no response
        return
    
    # Parse command
    text = message.text.strip()
    command_parts = text.split(' ', 3)
    
    if len(command_parts) < 4:
        # Show format to owner only
        format_text = """
<b>❌ Wrong Format!</b>

<b>✅ Correct Format:</b>
<code>/chk CC|MM|YY|CVV STATUS GATEWAY</code>

<b>📝 Example:</b>
<code>/chk 4111111111111111|12|25|123 APPROVED BRAINTREE</code>
"""
        bot.reply_to(message, format_text, parse_mode='HTML')
        return
    
    try:
        # Extract card data
        card_data = command_parts[1].strip()
        
        # Check if card format is valid
        card_parts = card_data.split('|')
        if len(card_parts) < 4:
            bot.reply_to(message, "<b>❌ Invalid card format! Use: CC|MM|YY|CVV</b>", parse_mode='HTML')
            return
        
        # Get status and gateway
        status = command_parts[2].strip().upper()
        gateway = command_parts[3].strip()
        
        # Send processing message
        processing_msg = bot.reply_to(
            message,
            "<b>🔄 Processing... Please wait</b>",
            parse_mode='HTML'
        )
        
        # Generate random delay between 2-12 seconds
        delay = random.uniform(2.0, 12.0)
        time.sleep(delay)
        
        # Format the response
        result, response_time = format_card_response(
            card_data, 
            gateway, 
            status, 
            user_id, 
            username
        )
        
        if result:
            # Delete processing message
            bot.delete_message(message.chat.id, processing_msg.message_id)
            
            # Send the formatted response
            bot.reply_to(message, result, parse_mode='HTML')
        else:
            bot.edit_message_text(
                "<b>❌ Error formatting card data!</b>",
                message.chat.id,
                processing_msg.message_id,
                parse_mode='HTML'
            )
            
    except Exception as e:
        bot.reply_to(
            message,
            f"<b>❌ Error: {str(e)}</b>",
            parse_mode='HTML'
        )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    
    # Only owner gets response
    if is_owner(user_id):
        bot.reply_to(
            message,
            "<b>Use /chk command with proper format</b>",
            parse_mode='HTML'
        )
    # Non-owners get no response

# Remove webhook and start bot
bot.remove_webhook()
time.sleep(1)

# Start the bot
if __name__ == "__main__":
    print("🤖 ONYX ENV BOT is starting...")
    print(f"👑 Owner ID: {OWNER_ID}")
    print("✅ Bot is running...")
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
