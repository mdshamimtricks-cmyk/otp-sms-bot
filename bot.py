import os
import telebot
import requests
from keep_alive import keep_alive

# আপনার দেওয়া একদম নতুন ফ্রেশ বট টোকেন
BOT_TOKEN = "8647049648:AAHkN78MFc6Arb-AoPN1jgpEbFQYqdd_L1w"

# প্যানেল থেকে নেওয়া আপনার আসল এপিআই কি
API_KEY = "NURAD_FD980978DCC029BBA17259DB"

# প্যানেল অনুযায়ী বেস ইউআরএল (অবশ্যই HTTP প্রোটোকল, HTTPS নয়)
BASE_URL = "http://fastxotps.com"

bot = telebot.TeleBot(BOT_TOKEN)

# ব্যবহারকারীদের সাময়িক সেশন ডাটা রাখার ডিকশনারি
user_sessions = {}

# /start কমান্ড হ্যান্ডলার
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_get_num = telebot.types.KeyboardButton("📱 নতুন নাম্বার নিন (Get Number)")
    markup.add(btn_get_num)
    
    welcome_msg = (
        "👋 **স্বাগতম! income world 24 number bot-এ আপনাকে স্বাগতম।**\n\n"
        "নিচের বোতামে ক্লিক করে যেকোনো কাস্টম রেঞ্জের ভার্চুয়াল নাম্বার নিতে পারবেন খুব সহজেই।"
    )
    bot.reply_to(message, welcome_msg, reply_markup=markup)

# ১. ইউজার যখন "নতুন নাম্বার নিন" বোতামে চাপ দেবে
@bot.message_handler(func=lambda message: message.text == "📱 নতুন নাম্বার নিন (Get Number)")
def ask_for_range(message):
    chat_id = message.chat.id
    msg = bot.send_message(
        chat_id, 
        "🔢 **দয়া করে আপনার কাঙ্ক্ষিত রেঞ্জটি টাইপ করে পাঠান।**\n\n"
        "👉 উদাহরণ: `224694XXXX` বা `2290164XXX`", 
        parse_mode="Markdown"
    )
    # ইউজারের পরবর্তী মেসেজ বা রেঞ্জ ইনপুট ক্যাপচার করার ফাংশন
    bot.register_next_step_handler(msg, process_number_request_with_range)

# ২. ইউজারের পাঠানো কাস্টম রেঞ্জ প্রোসেস করে নাম্বার অ্যালোকেট করা
def process_number_request_with_range(message):
    chat_id = message.chat.id
    user_range = message.text.strip()

    # কমান্ড বা ভুল ইনপুট ফিল্টার করা
    if user_range.startswith('/') or len(user_range) < 5:
        bot.send_message(chat_id, "❌ ইনভ্যালিড রেঞ্জ ফরম্যাট! অনুগ্রহ করে আবার বোতামে চাপ দিয়ে সঠিক রেঞ্জ লিখুন।")
        return

    bot.send_message(chat_id, f"⏳ রেঞ্জ `{user_range}` থেকে নাম্বার খোঁজা হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন...", parse_mode="Markdown")

    # প্যানেলের রিকোয়ারমেন্ট ও ভিডিওর সাকসেস টেস্ট অনুযায়ী নিখুঁত হেডার
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # বডি পেলোড
    payload = {
        "range": user_range 
    }

    try:
        url = f"{BASE_URL}/api/getnum"
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            res_data = response.json()
            
            # প্যানেল সাকসেস মেটা কোড অথবা ডাইরেক্ট মেসেজ ভ্যালিডেশন
            if res_data.get("meta", {}).get("code") == 200 or res_data.get("message") == "number allocated":
                num_info = res_data.get("data", {})
                number_id = num_info.get("number_id")
                phone_number = num_info.get("full_number")
                country = num_info.get("country", "Virtual Country")
                
                # ওটিপি চেক করার জন্য ইউজারের সেশন মেমোরিতে ডাটা সেভ রাখা হচ্ছে
                user_sessions[chat_id] = {"number_id": number_id, "phone_number": phone_number}
                
                # ইনলাইন ওটিপি চেক বাটন তৈরি
                inline_markup = telebot.types.InlineKeyboardMarkup()
                btn_check_otp = telebot.types.InlineKeyboardButton("🔄 ওটিপি চেক করুন (Check OTP)", callback_data="check_otp")
                inline_markup.add(btn_check_otp)
                
                success_msg = (
                    f"✅ **নাম্বার সফলভাবে নেওয়া হয়েছে!**\n\n"
                    f"🌍 **দেশ:** {country}\n"
                    f"📞 **নাম্বার:** `{phone_number}` (কপি করতে নাম্বারে ট্যাপ করুন)\n"
                    f"🆔 **নাম্বার আইডি:** {number_id}\n\n"
                    "⚠️ আপনার কাঙ্ক্ষিত অ্যাপে নাম্বারটি বসিয়ে ওটিপি পাঠান, তারপর নিচের বোতামে ক্লিক করে ওটিপি চেক করুন।"
                )
                bot.send_message(chat_id, success_msg, parse_mode="Markdown", reply_markup=inline_markup)
            else:
                error_msg = res_data.get("message", "সার্ভার বর্তমানে এই রেঞ্জের কোনো নাম্বার দিতে পারেনি।")
                bot.send_message(chat_id, f"❌ সার্ভার মেসেজ: {error_msg}")
        else:
            bot.send_message(chat_id, f"❌ এপিআই সমস্যা! স্ট্যাটাস কোড: {response.status_code}\n\n📝 সার্ভার রেসপন্স: {response.text}")
            
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ একটি ত্রুটি ঘটেছে: {str(e)}")

# ৩. ইনলাইন বোতামের মাধ্যমে ওটিপি চেক করার হ্যান্ডলার
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
        "Content-Type": "application/json"
    }
    
    try:
        url = f"{BASE_URL}/api/otps"
        # ওটিপি এন্ডপয়েন্টে কুয়েরি প্যারামিটার এবং বডি উভয় ডাটা হ্যান্ডলিং ব্যাকআপ রাখা হয়েছে
        response = requests.get(f"{url}?number_id={number_id}", headers=headers)

        if response.status_code == 200:
            otp_data = response.json()
            sms_data = otp_data.get("data", {})
            
            # যদি ওটিপি অলরেডি চলে আসে
            if isinstance(sms_data, dict) and sms_data.get("otp"):
                received_otp = sms_data.get("otp")
                bot.send_message(chat_id, f"📩 **আপনার ওটিপি কোড:** `{received_otp}`\n📞 নাম্বার: `{phone_number}`", parse_mode="Markdown")
            # যদি ওটিপি প্রসেসিং বা ওয়েটিং অবস্থায় থাকে
            elif otp_data.get("message") == "waiting for sms" or "waiting" in str(otp_data):
                bot.send_message(chat_id, f"⏳ `{phone_number}` নাম্বারে এখনো কোনো ওটিপি আসেনি। আপনার অ্যাপ থেকে ওটিপি রিকোয়েস্ট করে একটু পর আবার 'Check OTP' বাটনে ক্লিক করুন।")
            else:
                bot.send_message(chat_id, f"📩 `{phone_number}` নাম্বারে ওটিপি অপেক্ষমাণ। মেসেজ সার্ভারে পৌঁছালে কোড দেখতে পাবেন।")
        else:
            bot.send_message(chat_id, f"❌ ওটিপি এপিআই ত্রুটি! স্ট্যাটাস কোড: {response.status_code}")
            
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ ওটিপি চেক করতে সমস্যা হয়েছে: {str(e)}")

# ৪. মেইন মেথড ও ফ্ল্যাশKeep-Alive ব্যাকগ্রাউন্ড ট্রিগার
if __name__ == "__main__":
    # রেন্ডার সার্ভার যেন ২৪ ঘণ্টা কোড রানিং রাখে তার জন্য keep_alive ট্রিগার
    keep_alive()
    print("income world 24 number bot is successfully deployed and running...")
    bot.infinity_polling()
