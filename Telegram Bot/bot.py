import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import whois
from datetime import datetime
import os
from dotenv import load_dotenv
import sys
import re
import time
import requests

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    print("ERROR: Kunde inte hitta TELEGRAM_BOT_TOKEN i .env-filen")
    sys.exit(1)

# Konfigurera för PythonAnywhere
telebot.apihelper.RETRY_ON_ERROR = True
telebot.apihelper.CONNECT_TIMEOUT = 30
session = requests.Session()
session.trust_env = False  # Ignorera miljövariabler för proxy
bot = telebot.TeleBot(BOT_TOKEN, threaded=False, session=session)

def create_inline_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("🔍 Kolla domän", callback_data="check_domain")
    )
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 Hej! Jag är en bot som kan hjälpa dig att:\n\n"
        "🌐 Kolla åldern på hemsidor\n\n"
        "Du kan antingen:\n"
        "• Skicka en länk direkt till mig\n"
        "• Använda knappen nedan\n"
        "• Eller använd kommandot /domain"
    )
    bot.reply_to(message, welcome_text, reply_markup=create_inline_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "check_domain")
def callback_check_domain(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "🌐 Skriv in domänen du vill kolla (t.ex. google.com):")

def extract_domain(text):
    # Matchar både rena domäner och URLs
    url_pattern = re.compile(
        r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+)'
    )
    match = url_pattern.search(text)
    return match.group(1) if match else None

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    text = message.text.lower()
    
    # Kolla om meddelandet innehåller en URL eller domän
    domain = extract_domain(text)
    if domain:
        check_domain_age(message, domain)
        return

def check_domain_age(message, domain=None):
    try:
        if domain is None:
            domain = message.text.split()[-1]  # Ta sista ordet som domän
        
        w = whois.whois(domain)
        creation_date = w.creation_date
        
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
            
        age = datetime.now() - creation_date
        years = age.days // 365
        remaining_days = age.days % 365
        
        response = (
            f"🌐 *Domäninformation*\n\n"
            f"Domän: `{domain}`\n"
            f"📅 Registrerad: `{creation_date.strftime('%Y-%m-%d')}`\n"
            f"⏳ Ålder: `{years} år och {remaining_days} dagar`\n"
        )
        
        # Skapa en ny knapp för att kolla en annan domän
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("🔍 Kolla en annan domän", callback_data="check_domain")
        )
        
        bot.reply_to(message, response, parse_mode='Markdown', reply_markup=keyboard)
    except Exception as e:
        bot.reply_to(message, f"❌ Ett fel uppstod: {str(e)}")

print("🤖 Bot starting...")
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"❌ Ett fel uppstod: {e}")
        time.sleep(15)  # Vänta 15 sekunder innan återanslutning 