import os
import telebot
import requests
from keep_alive import keep_alive

# Render Environment Variables থেকে টোকেন এবং কী নেওয়া হচ্ছে
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8825223673:AAF1_AwkZ0WAoQNDBHcxU2PlOxCkLsdCnZo")
API_KEY = os.environ.get("API_KEY", "NURAD_FD980978DCC029BBA17259DB") 

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
        "নিচের বোতামে ক্লিক করে সহজেই গিনির (Guinea) ভার্চুয়াল নাম্বার নিতে পারবেন।"
    )
    bot.reply_to(message, welcome_msg, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📱 নতুন নাম্বার নিন (Get Number)")
def get_number_request(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏳ সার্ভার থেকে নাম্বার খোঁজা হচ্ছে, দয়া করে অপেক্ষা করুন...")

    # ওটিপি প্যানেল অনুযায়ী সঠিক হেডারস
    headers = {
        "X-API-Key": API_KEY.strip(),  # কোনো স্পেস থাকলে তা রিমুভ করবে
        "Content-Type": "application/json"
    }
    payload = {
        "range": "224694XXXX" 
    }

    try:
        response = requests.post(f"{BASE_URL}/api/getnum", json=payload, headers=headers)
        
        if response.status_code == 200:
            res_data = response.json()
            
            if res_data.get("meta", {}).get("status") == "ok" or res_data.get("message") == "number allocated":
                num_info = res_data.get("data", {})
                number_id = num_info.get("number_id")
                phone_number = num_info.get("full_number")
                country = num_info.get("country", "Guinea")
                
                user_sessions[chat_id] = {"number_id": number_id, "phone_number": phone_number}
                
                inline_markup = telebot.types.InlineKeyboardMarkup()
                btn_check_otp = telebot.types.InlineKeyboardButton("🔄 ওটিপি চেক করুন (Check OTP)", callback_data="check_otp")
                inline_markup.add(btn_check_otp)
                
                success_msg = (
                    "✅ **নাম্বার সফলভাবে নেওয়া হয়েছে!**\n\n"
                    f"🌍 **দেশ:** {country}\n"
                    f"📞 **নাম্বার:** `{phone_number}` (কপি করতে নাম্বারে চাপুন)\n"
                    f"🆔 **নাম্বার আইডি:** {number_id}\n\n"
                    "⚠️ আপনার অ্যাপে নাম্বারটি বসিয়ে ওটিপি পাঠান, তারপর নিচের বোতামে ক্লিক করে ওটিপি চেক করুন।"
                )
                bot.send_message(chat_id, success_msg, parse_mode="Markdown", reply_markup=inline_markup)
            else:
                error_msg = res_data.get("message", "সার্ভার বর্তমানে কোনো নাম্বার দিতে পারেনি।")
                bot.send_message(chat_id, f"❌ সার্ভার মেসেজ: {error_msg}")
        else:
            bot.send_message(chat_id, f"❌ এপিআই সমস্যা! স্ট্যাটাস কোড: {response.status_code}\n(আপনার API Key টি সঠিক কিনা প্যানেল থেকে চেক করুন)")
            
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
        "X-API-Key": API_KEY.strip()
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/otps", headers=headers)
        
        if response.status_code == 200:
            bot.send_message(chat_id, f"📩 `{phone_number}` নাম্বারে এখনো কোনো ওটিপি আসেনি। আপনার অ্যাপ থেকে ওটিপি রিকোয়েস্ট করে আবার ট্রাই করুন।", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "❌ ওটিপি সার্ভার থেকে রেসপন্স পাওয়া যায়নি।")
            
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ ওটিপি চেক করতে সমস্যা হয়েছে: {str(e)}")

if __name__ == "__main__":
    keep_alive()
    print("Bot is successfully deploying on Render...")
    bot.infinity_polling()
