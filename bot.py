import os
import telebot
import requests
from keep_alive import keep_alive

# টোকেন ভ্যারিয়েবল
BOT_TOKEN = "8825223673:AAEl-C6aGSJrg8KgzYSypRvH_PwwbZb3EtU"

# আপনার প্যানেলের সম্পূর্ণ API Key (কোড নিজেই ভেতরের সব স্পেস বা এন্টার কেটে ফ্রেশ করে নেবে)
RAW_API_KEY = """
NURAD_FD980978DCC029BBA17259DB
"""
# কী-এর ভেতরের যেকোনো অদৃশ্য স্পেস, ট্যাব বা নিউ-লাইন পরিষ্কার করার লজিক
API_KEY = RAW_API_KEY.replace("\n", "").replace("\r", "").strip()

# প্যানেল অনুযায়ী বেস ইউআরএল (HTTP প্রোটোকল)
BASE_URL = "http://fastxotps.com"

bot = telebot.TeleBot(BOT_TOKEN)
user_sessions = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_get_num = telebot.types.KeyboardButton("📱 নতুন নাম্বার নিন (Get Number)")
    markup.add(btn_get_num)
    
    welcome_msg = (
        "👋 স্বাগতম! এটি একটি ওটিপি এবং নাম্বার অ্যালোকেশন বট।\n\n"
        "নিচের বোতামে ক্লিক করে যেকোনো কাস্টম রেঞ্জের ভার্চুয়াল নাম্বার নিতে পারবেন।"
    )
    bot.reply_to(message, welcome_msg, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📱 নতুন নাম্বার নিন (Get Number)")
def ask_for_range(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "🔢 **দয়া করে আপনার কাঙ্ক্ষিত রেঞ্জটি টাইপ করে পাঠান।**\n\n👉 উদাহরণ: `224694XXXX` বা `226234XXXX`", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_number_request_with_range)

def process_number_request_with_range(message):
    chat_id = message.chat.id
    user_range = message.text.strip()

    if user_range.startswith('/') or len(user_range) < 5:
        bot.send_message(chat_id, "❌ ইনভ্যালিড রেঞ্জ ফরম্যাট! আবার বোতামে চাপ দিয়ে সঠিক রেঞ্জ লিখুন।")
        return

    bot.send_message(chat_id, f"⏳ রেঞ্জ `{user_range}` থেকে নাম্বার খোঁজা হচ্ছে...", parse_mode="Markdown")

    # ওটিপি প্যানেল ডকস অনুযায়ী কাস্টম হেডার ফরম্যাট
    headers = {
        "X-API-Key": API_KEY,
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "range": user_range 
    }

    try:
        url = f"{BASE_URL}/api/getnum"
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            res_data = response.json()
            
            if res_data.get("meta", {}).get("code") == 200 or res_data.get("message") == "number allocated":
                num_info = res_data.get("data", {})
                number_id = num_info.get("number_id")
                phone_number = num_info.get("full_number")
                country = num_info.get("country", "Unknown Country")
                
                user_sessions[chat_id] = {"number_id": number_id, "phone_number": phone_number}
                
                inline_markup = telebot.types.InlineKeyboardMarkup()
                btn_check_otp = telebot.types.InlineKeyboardButton("🔄 ওটিপি চেক করুন (Check OTP)", callback_data="check_otp")
                inline_markup.add(btn_check_otp)
                
                success_msg = (
                    f"✅ **নাম্বার সফলভাবে নেওয়া হয়েছে! (Range: {user_range})**\n\n"
                    f"🌍 **দেশ:** {country}\n"
                    f"📞 **নাম্বার:** `{phone_number}`\n"
                    f"🆔 **নাম্বার আইডি:** {number_id}\n\n"
                    "⚠️ আপনার কাঙ্ক্ষিত অ্যাপে নাম্বারটি বসিয়ে ওটিপি পাঠান, তারপর নিচের বোতামে ক্লিক করুন।"
                )
                bot.send_message(chat_id, success_msg, parse_mode="Markdown", reply_markup=inline_markup)
            else:
                error_msg = res_data.get("message", "সার্ভার বর্তমানে এই রেঞ্জের কোনো নাম্বার দিতে পারেনি।")
                bot.send_message(chat_id, f"❌ সার্ভার মেসেজ: {error_msg}")
        else:
            bot.send_message(chat_id, f"❌ এপিআই সমস্যা! স্ট্যাটাস কোড: {response.status_code}\n\n📝 সার্ভার রেসপন্স: {response.text}")
            
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ একটি ত্রুটি ঘটেছে: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == "check_otp")
def check_otp_callback(call):
    chat_id = call.message.chat.id
    
    if chat_id not in user_sessions:
        bot.answer_callback_query(call.id, "❌ কোনো সক্রিয় নাম্বারের রেকর্ড পাওয়া যায়নি। নতুন করে নাম্বার নিন।", show_alert=True)
        return
        
    number_id = user_sessions[chat_id]["number_id"]
    phone_number = user_sessions[chat_id]["phone_number"]
    
    bot.answer_callback_query(call.id, "⏳ ওটিপি চেক করা হচ্ছে...")
    
    headers = {
        "X-API-Key": API_KEY,
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "number_id": number_id
    }
    
    try:
        url = f"{BASE_URL}/api/otps"
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            response = requests.get(f"{url}?number_id={number_id}", headers=headers)

        if response.status_code == 200:
            otp_data = response.json()
            sms_data = otp_data.get("data", {})
            
            if isinstance(sms_data, dict) and sms_data.get("otp"):
                received_otp = sms_data.get("otp")
                bot.send_message(chat_id, f"📩 **আপনার ওটিপি কোড:** `{received_otp}`", parse_mode="Markdown")
            elif isinstance(otp_data, dict) and otp_data.get("message") == "waiting for sms":
                bot.send_message(chat_id, f"⏳ `{phone_number}` নাম্বারে এখনো ওটিপি আসেনি। একটু পর আবার ট্রাই করুন।")
            else:
                bot.send_message(chat_id, f"📩 `{phone_number}` নাম্বারে ওটিপি অপেক্ষমাণ। মেসেজ সার্ভারে পৌঁছালে কোড চলে আসবে।")
        else:
            bot.send_message(chat_id, f"❌ ওটিপি এপিআই ত্রুটি! স্ট্যাটাস কোড: {response.status_code}\n\n📝 রেসপন্স: {response.text}")
            
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ ওটিপি চেক করতে সমস্যা হয়েছে: {str(e)}")

if __name__ == "__main__":
    keep_alive()
    print("Bot completely fixed with Auto-Cleaning API configuration...")
    bot.infinity_polling()
