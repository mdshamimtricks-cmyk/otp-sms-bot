import os
import telebot
import requests
from keep_alive import keep_alive

# Render Environment Variables থেকে টোকেন এবং কী নেওয়া হচ্ছে
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8825223673:AAF1_AwkZ0WAoQNDBHcxU2PlOxCkLsdCnZo")
API_KEY = os.environ.get("API_KEY", "NURAD_FD980978DCC029BBA17259DB") 

# প্যানেলের টেস্টার স্ক্রিনশট অনুযায়ী বেস ইউআরএল অবশ্যই HTTP (HTTPS নয়)
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
        "নিচের বোতামে ক্লিক করে সহজেই প্যানেল থেকে ভার্চুয়াল নাম্বার নিতে পারবেন।"
    )
    bot.reply_to(message, welcome_msg, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📱 নতুন নাম্বার নিন (Get Number)")
def get_number_request(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏳ সার্ভার থেকে নাম্বার খোঁজা হচ্ছে, দয়া করে অপেক্ষা করুন...")

    # প্যানেলের রিকোয়ারমেন্ট অনুযায়ী হেডার ফরম্যাট ফিক্স করা হয়েছে
    headers = {
        "X-API-Key": API_KEY.strip(),
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    # স্ক্রিনশটের রেঞ্জ অনুযায়ী পেলোড ডাটা
    payload = {
        "range": "224694XXXX" 
    }

    try:
        url = f"{BASE_URL}/api/getnum"
        response = requests.post(url, json=payload, headers=headers)
        
        # লগ দেখার জন্য কনসোলে প্রিন্ট করা হচ্ছে
        print(f"GetNum Response Code: {response.status_code}")
        print(f"GetNum Response Body: {response.text}")
        
        if response.status_code == 200:
            res_data = response.json()
            
            # প্যানেল সাকসেস মেটা চেক
            if res_data.get("meta", {}).get("code") == 200 or res_data.get("message") == "number allocated":
                num_info = res_data.get("data", {})
                number_id = num_info.get("number_id")
                phone_number = num_info.get("full_number")
                country = num_info.get("country", "Guinea")
                
                # ওটিপি চেকিংয়ের জন্য নাম্বার আইডি ও সেশন সেভ
                user_sessions[chat_id] = {"number_id": number_id, "phone_number": phone_number}
                
                inline_markup = telebot.types.InlineKeyboardMarkup()
                btn_check_otp = telebot.types.InlineKeyboardButton("🔄 ওটিপি চেক করুন (Check OTP)", callback_data="check_otp")
                inline_markup.add(btn_check_otp)
                
                success_msg = (
                    "✅ **নাম্বার সফলভাবে নেওয়া হয়েছে!**\n\n"
                    f"🌍 **দেশ:** {country}\n"
                    f"📞 **নাম্বার:** `{phone_number}`\n"
                    f"🆔 **নাম্বার আইডি:** {number_id}\n\n"
                    "⚠️ আপনার কাঙ্ক্ষিত অ্যাপে নাম্বারটি বসিয়ে ওটিপি পাঠান, তারপর নিচের বোতামে ক্লিক করুন।"
                )
                bot.send_message(chat_id, success_msg, parse_mode="Markdown", reply_markup=inline_markup)
            else:
                error_msg = res_data.get("message", "সার্ভার বর্তমানে কোনো নাম্বার দিতে পারেনি।")
                bot.send_message(chat_id, f"❌ সার্ভার মেসেজ: {error_msg}")
        
        elif response.status_code == 401:
            bot.send_message(chat_id, "❌ এপিআই সমস্যা (401): প্যানেল আপনার রিকোয়েস্ট ব্লক করেছে। API Key এর আগে বা পরে কোনো স্পেস বা ভুল ফরম্যাট আছে কিনা চেক করুন।")
        else:
            bot.send_message(chat_id, f"❌ এপিআই সমস্যা! স্ট্যাটাস কোড: {response.status_code}")
            
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
    
    # ওটিপি চেক করার সময় কোন নাম্বারের ওটিপি লাগবে তা বডিতে বা প্যারামিটারে পাঠানো আবশ্যক
    payload = {
        "number_id": number_id
    }
    
    try:
        url = f"{BASE_URL}/api/otps"
        # ওটিপি প্যানেল ভেদে GET বা POST দুটির যেকোনো একটিতে ডাটা নেয়, আমরা এখানে জেনারেলাইজড ট্রাই করছি
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            # যদি POST সাপোর্ট না করে, তবে ডাইরেক্ট GET ট্রাই করবে প্যারামিটারসহ
            response = requests.get(f"{url}?number_id={number_id}", headers=headers)

        print(f"OTP Response Code: {response.status_code}")
        print(f"OTP Response Body: {response.text}")

        if response.status_code == 200:
            otp_data = response.json()
            
            # প্যানেল থেকে ওটিপি টেক্সট বের করার লজিক
            # সাধারণত রেসপন্সে 'otp' বা 'sms' কি (key) থাকে
            sms_data = otp_data.get("data", {})
            
            if isinstance(sms_data, dict) and sms_data.get("otp"):
                received_otp = sms_data.get("otp")
                bot.send_message(chat_id, f"📩 **আপনার ওটিপি কোড:** `{received_otp}`", parse_mode="Markdown")
            elif isinstance(otp_data, dict) and otp_data.get("message") == "waiting for sms":
                bot.send_message(chat_id, f"⏳ `{phone_number}` নাম্বারে এখনো ওটিপি আসেনি। আপনার অ্যাপ থেকে ওটিপি রিকোয়েস্ট করে একটু পর আবার ট্রাই করুন।")
            else:
                bot.send_message(chat_id, f"📩 `{phone_number}` নাম্বারে ওটিপি অপেক্ষমাণ। মেসেজ সার্ভারে পৌঁছালে কোড চলে আসবে।")
        else:
            bot.send_message(chat_id, "❌ ওটিপি সার্ভার থেকে রেসপন্স পাওয়া যায়নি বা সাময়িক ত্রুটি।")
            
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ ওটিপি চেক করতে সমস্যা হয়েছে: {str(e)}")

if __name__ == "__main__":
    keep_alive()
    print("Bot architecture modified and updated...")
    bot.infinity_polling()
