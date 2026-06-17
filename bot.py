import os
import json
import telebot
import requests
from keep_alive import keep_alive

# আপনার দেওয়া নতুন ফ্রেশ বট টোকেন
BOT_TOKEN = "8647049648:AAHkN78MFc6Arb-AoPN1jgpEbFQYqdd_L1w"

# প্যানেল থেকে নেওয়া আপনার আসল এপিআই কি
API_KEY = "NURAD_FD980978DCC029BBA17259DB"

# প্যানেল অনুযায়ী মেইন ইউআরএল (HTTP)
BASE_URL = "http://fastxotps.com"

bot = telebot.TeleBot(BOT_TOKEN)
user_sessions = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_get_num = telebot.types.KeyboardButton("📱 নতুন নাম্বার নিন (Get Number)")
    markup.add(btn_get_num)
    
    welcome_msg = (
        "👋 **income world 24 number bot**-এ আপনাকে স্বাগতম।\n\n"
        "নিচের বোতামে ক্লিক করে যেকোনো রেঞ্জের ভার্চুয়াল নাম্বার নিতে পারবেন।"
    )
    bot.reply_to(message, welcome_msg, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📱 নতুন নাম্বার নিন (Get Number)")
def ask_for_range(message):
    chat_id = message.chat.id
    msg = bot.send_message(
        chat_id, 
        "🔢 **দয়া করে আপনার কাঙ্ক্ষিত রেঞ্জটি টাইপ করে পাঠান।**\n\n"
        "👉 উদাহরণ: `224694XXXX`", 
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_number_request_with_range)

def process_number_request_with_range(message):
    chat_id = message.chat.id
    user_range = message.text.strip()

    if user_range.startswith('/') or len(user_range) < 5:
        bot.send_message(chat_id, "❌ ইনভ্যালিড রেঞ্জ ফরম্যাট! আবার সঠিক রেঞ্জ লিখুন।")
        return

    bot.send_message(chat_id, f"⏳ রেঞ্জ `{user_range}` থেকে নাম্বার খোঁজা হচ্ছে...", parse_mode="Markdown")

    # ওটিপি প্যানেল যেন কোনোভাবেই ব্লক না করতে পারে, সেজন্য ব্রাউজারের মতো কাস্টম হেডারস
    headers = {
        "X-API-Key": str(API_KEY).strip(),
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Connection": "keep-alive"
    }
    
    payload = {
        "range": str(user_range)
    }

    try:
        url = f"{BASE_URL}/api/getnum"
        
        # প্যানেল ব্যাকএন্ড টেস্টারের মতো হুবহু ডাটা স্ট্রিং ফরম্যাটে পাঠানো হচ্ছে
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        
        # ব্যাকআপ পদ্ধতি: যদি উপরের নিয়মে তাও এপিআই এরর আসে, তবে কুয়েরি প্যারামিটারে ডেটা পুশ করবে
        if response.status_code == 401 or "Invalid API key" in response.text:
            backup_url = f"{url}?range={user_range}"
            response = requests.post(backup_url, headers={"X-API-Key": API_KEY.strip(), "Content-Type": "application/json"})

        if response.status_code == 200:
            res_data = response.json()
            
            # প্যানেল অনুযায়ী সাকসেস চেক
            if res_data.get("meta", {}).get("code") == 200 or res_data.get("message") == "number allocated" or "data" in res_data:
                num_info = res_data.get("data", {})
                number_id = num_info.get("number_id")
                phone_number = num_info.get("full_number")
                country = num_info.get("country", "Virtual Country")
                
                if not phone_number:
                    # যদি ডাটা ফরম্যাট একটু ভিন্ন হয়
                    phone_number = res_data.get("full_number") or num_info.get("number")
                    number_id = res_data.get("number_id")
                
                user_sessions[chat_id] = {"number_id": number_id, "phone_number": phone_number}
                
                inline_markup = telebot.types.InlineKeyboardMarkup()
                btn_check_otp = telebot.types.InlineKeyboardButton("🔄 ওটিপি চেক করুন (Check OTP)", callback_data="check_otp")
                inline_markup.add(btn_check_otp)
                
                success_msg = (
                    f"✅ **নাম্বার সফলভাবে নেওয়া হয়েছে!**\n\n"
                    f"🌍 **দেশ:** {country}\n"
                    f"📞 **নাম্বার:** `{phone_number}`\n"
                    f"🆔 **নাম্বার আইডি:** {number_id}\n\n"
                    "⚠️ অ্যাপে নাম্বারটি বসিয়ে ওটিপি পাঠান, তারপর নিচের বোতামে ক্লিক করুন।"
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
        "X-API-Key": API_KEY.strip(),
        "Content-Type": "application/json"
    }
    
    try:
        url = f"{BASE_URL}/api/otps"
        # ওটিপি চেক করার জন্য ডাইরেক্ট আইডি প্যারামিটার পাস
        response = requests.get(f"{url}?number_id={number_id}", headers=headers)

        if response.status_code == 200:
            otp_data = response.json()
            sms_data = otp_data.get("data", {})
            
            if isinstance(sms_data, dict) and sms_data.get("otp"):
                received_otp = sms_data.get("otp")
                bot.send_message(chat_id, f"📩 **您的 OTP কোড:** `{received_otp}`", parse_mode="Markdown")
            elif "waiting" in str(otp_data) or otp_data.get("message") == "waiting for sms":
                bot.send_message(chat_id, f"⏳ `{phone_number}` নাম্বারে এখনো কোনো ওটিপি আসেনি। আপনার অ্যাপ থেকে ওটিপি রিকোয়েস্ট করে একটু পর আবার 'Check OTP' বাটনে ক্লিক করুন।")
            else:
                bot.send_message(chat_id, f"📩 `{phone_number}` নাম্বারে ওটিপি অপেক্ষমাণ। মেসেজ সার্ভারে পৌঁছালে কোড দেখতে পাবেন।")
        else:
            bot.send_message(chat_id, f"❌ ওটিপি এপিআই ত্রুটি! স্ট্যাটাস কোড: {response.status_code}")
            
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ ওটিপি চেক করতে সমস্যা হয়েছে: {str(e)}")

if __name__ == "__main__":
    keep_alive()
    print("Source code updated with secure browser payloads...")
    bot.infinity_polling()
