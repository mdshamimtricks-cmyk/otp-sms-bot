import os
import json
import telebot
import requests
from keep_alive import keep_alive

# টোকেন ও এপিআই কনফিগারেশন
BOT_TOKEN = "8647049648:AAHkN78MFc6Arb-AoPN1jgpEbFQYqdd_L1w"
API_KEY = "NURAD_FD980978DCC029BBA17259DB"
BASE_URL = "http://fastxotps.com"

# ওটিপি সফল হলে যে গ্রুপ/চ্যানেলে নোটিফিকেশন পাঠাতে চান তার আইডি (যেমন: -100xxxxxxxxx)
# যদি গ্রুপে পাঠাতে না চান, তবে এটি খালি রাখতে পারেন বা আপনার গ্রুপের আইডি বসিয়ে দিন
LOG_GROUP_ID = None 

bot = telebot.TeleBot(BOT_TOKEN)
user_sessions = {}

# প্রধান মেনু কিবোর্ড (আপনার ভিডিওর বটের মতো হুবহু ডিজাইন)
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = telebot.types.KeyboardButton("📲 Get Number")
    btn2 = telebot.types.KeyboardButton("🚀 Get 30 Number")
    btn3 = telebot.types.KeyboardButton("🔗 View Range")
    btn4 = telebot.types.KeyboardButton("💳 My Balance")
    btn5 = telebot.types.KeyboardButton("💸 Withdraw")
    btn6 = telebot.types.KeyboardButton("🆘 Help & Support")
    
    markup.add(btn1, btn2)
    markup.add(btn3)
    markup.add(btn4, btn5)
    markup.add(btn6)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **I can provide you with virtual numbers to receive SMS.**\n"
        "Use the menu below to get started:\n\n"
        "📲 **Get Number** → Request single number\n"
        "🚀 **Get 30 Number** → Request bulk numbers\n"
        "🔗 **View Range** → Join our range channel\n"
        "💳 **My Balance** → Check your current balance\n"
        "💸 **Withdraw** → Withdraw your money"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💳 My Balance")
def check_balance(message):
    # ডামি বা ইউজারের ড্যাশবোর্ড ব্যালেন্স (আপনার ভিডিওর মতো মেলাতে)
    balance_msg = (
        "💰 **Your Current Balance:** `0.00৳`\n"
        "📊 **Total OTP Received:** `0`"
    )
    bot.reply_to(message, balance_msg, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🔗 View Range")
def view_range(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("👉 Click to Join Range Channel", url="https://t.me/Top_Range_Channel")
    markup.add(btn)
    bot.send_message(message.chat.id, "Click the button below to see the ranges:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["釐 Get Number", "📲 Get Number"])
def ask_for_range(message):
    msg = bot.send_message(message.chat.id, "⌨️ **Enter Range ID (1 Number):**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_range_request)

def process_range_request(message):
    chat_id = message.chat.id
    user_range = message.text.strip()

    if user_range.startswith('/') or len(user_range) < 4:
        bot.send_message(chat_id, "❌ Invalid Range Format. Please click 'Get Number' again.")
        return

    status_msg = bot.send_message(chat_id, "🔍 **Searching for number...**", parse_mode="Markdown")

    headers = {
        "X-API-Key": str(API_KEY).strip(),
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    payload = {"range": str(user_range)}

    try:
        url = f"{BASE_URL}/api/getnum"
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        if response.status_code == 200:
            res_data = response.json()
            
            if res_data.get("meta", {}).get("code") == 200 or "data" in res_data:
                num_info = res_data.get("data", {})
                number_id = num_info.get("number_id")
                phone_number = num_info.get("full_number") or num_info.get("number")
                country = num_info.get("country", "Central African Republic")
                
                # সেশন ডাটা সেভ রাখা
                user_sessions[chat_id] = {"number_id": number_id, "phone_number": phone_number, "range": user_range, "country": country}
                
                # আপনার ভিডিওর মতো হুবহু ইন্টারফেস ডিজাইন
                response_msg = (
                    f"✅ **YOUR NUMBER**\n"
                    f"📊 **Range:** {user_range}\n"
                    f"🌍 **Country:** {country}\n"
                    f"📞 **Number:** `{phone_number}`\n"
                    f"💬 **SMS Status:** Waiting..."
                )
                
                inline_markup = telebot.types.InlineKeyboardMarkup()
                btn_change = telebot.types.InlineKeyboardButton("🔄 Change Number", callback_data="change_number")
                btn_otp = telebot.types.InlineKeyboardButton("📩 View OTP", callback_data="view_otp")
                inline_markup.add(btn_change)
                inline_markup.add(btn_otp)
                
                # আগের Searching মেসেজটি এডিট করে আউটপুট দেখানো
                bot.edit_message_text(response_msg, chat_id=chat_id, message_id=status_msg.message_id, reply_markup=inline_markup, parse_mode="Markdown")
            else:
                bot.edit_message_text(f"❌ Server Message: {res_data.get('message', 'No number available.')}", chat_id=chat_id, message_id=status_msg.message_id)
        else:
            bot.edit_message_text(f"❌ API Error! Status Code: {response.status_code}", chat_id=chat_id, message_id=status_msg.message_id)
            
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ Error: {str(e)}")

# বাটনের অ্যাকশন হ্যান্ডলারসমূহ
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    
    if call.data == "change_number":
        bot.answer_callback_query(call.id, "Requesting a new number...")
        if chat_id in user_sessions:
            # আগের রেঞ্জ ধরে অটো নতুন নাম্বার রিকোয়েস্ট করা
            class DummyMessage:
                def __init__(self, chat_id, text):
                    self.chat = type('obj', (object,), {'id': chat_id})
                    self.text = text
            process_range_request(DummyMessage(chat_id, user_sessions[chat_id]["range"]))
            
    elif call.data == "view_otp":
        if chat_id not in user_sessions:
            bot.answer_callback_query(call.id, "❌ Session expired. Please request a new number.", show_alert=True)
            return
            
        number_id = user_sessions[chat_id]["number_id"]
        phone_number = user_sessions[chat_id]["phone_number"]
        user_range = user_sessions[chat_id]["range"]
        country = user_sessions[chat_id]["country"]
        
        bot.answer_callback_query(call.id, "Checking for SMS...")
        
        headers = {"X-API-Key": API_KEY.strip(), "Content-Type": "application/json"}
        
        try:
            url = f"{BASE_URL}/api/otps?number_id={number_id}"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                otp_data = response.json()
                sms_data = otp_data.get("data", {})
                
                if isinstance(sms_data, dict) and sms_data.get("otp"):
                    received_otp = sms_data.get("otp")
                    
                    # বটে ওটিপি সাকসেস মেসেজ পাঠানো
                    success_ui = (
                        f"✅ **OTP Received Successfully**\n\n"
                        f"🌍 **Country:** {country}\n"
                        f"📞 **Number:** `{phone_number}`\n"
                        f"🔑 **OTP Code:** `{received_otp}`"
                    )
                    bot.send_message(chat_id, success_ui, parse_mode="Markdown")
                    
                    # গ্রুপ লগে ওটিপি ফরোয়ার্ড করা (ভিডিওর মতো গ্রুপ সেটআপ থাকলে)
                    if LOG_GROUP_ID:
                        try:
                            group_msg = (
                                f"🔥 **2nd high traffic bot**\n"
                                f"✅ **OTP Received Successfully**\n\n"
                                f"🌍 **Country:** {country}\n"
                                f"📊 **Range:** {user_range}\n"
                                f"📞 **Number:** `{phone_number}`\n"
                                f"💬 **OTP:** `{received_otp}`"
                            )
                            bot.send_message(LOG_GROUP_ID, group_msg, parse_mode="Markdown")
                        except:
                            pass
                else:
                    bot.send_message(chat_id, "⏳ **SMS not received yet.** Please request OTP in your app and try again.", parse_mode="Markdown")
            else:
                bot.send_message(chat_id, f"❌ OTP Checking Failed. Status Code: {response.status_code}")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ Error: {str(e)}")

if __name__ == "__main__":
    keep_alive()
    print("Premium OTP Traffic Bot is Deployed...")
    bot.infinity_polling()
