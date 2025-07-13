import os
import re
import threading
from flask import Flask
from dotenv import load_dotenv
import telebot
from supabase import create_client

# ✅ Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
ADMIN_GROUP_ID = int(os.getenv('ADMIN_GROUP_ID'))

# ✅ Bot & Supabase setup
bot = telebot.TeleBot(TOKEN)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app = Flask(__name__)

# ✅ User States
user_states = {}
user_screenshots = {}
user_amounts = {}
user_emails = {}
user_ids = {}

# ✅ /start handler
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("အသုံးပြုနည်း✅", url="https://youtube.com"))
    markup.add(telebot.types.InlineKeyboardButton("💰 ငွေဖြည့်သွင်းမည်", callback_data="topup"))
    bot.send_message(
        message.chat.id,
        "K2 ငွေဖြည့်သွင်းစနစ်မှ ကြိုဆိုပါတယ်။\n\nငွေမသွင်းခင် အသုံးပြုနည်းကို လေ့လာပါ‼️",
        reply_markup=markup
    )

# ✅ Callback handler
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if call.data == "topup":
        bot.send_message(chat_id, "💰 ငွေဖြည့်သွင်းမည့် ပမာဏ ကိုရေးပါ\n\n1000 Ks အနည်းဆုံးဖြစ်ရပါမယ်။")
        user_states[chat_id] = 'WAITING_FOR_AMOUNT'
    elif call.data == "upload_screenshot":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="cancel_all"))
        bot.send_message(chat_id, "📸 ငွေလွဲပြေစာ ပို့ပေးပါ။\n‼️ တစ်ခြား ခလုတ်မနှိပ်ပဲ ပုံတစ်ခုတည်းပေးပါ။", reply_markup=markup)
        user_states[chat_id] = 'WAITING_FOR_SCREENSHOT'
    elif call.data in ["cancel_topup", "cancel_all"]:
        for d in [user_states, user_amounts, user_screenshots, user_emails, user_ids]:
            d.pop(chat_id, None)
        bot.send_message(chat_id, "❌ ပယ်ဖျက်ပြီးပါပြီ။ အစက ပြန်စမယ်။")
        send_welcome(call.message)
    elif call.data == "retry_email":
        bot.send_message(chat_id, "📧 ကျေးဇူးပြု၍ မှန်ကန်သော Email ကို ပြန်ထည့်ပေးပါ။")
        user_states[chat_id] = 'WAITING_FOR_EMAIL'
        bot.answer_callback_query(call.id)
    elif call.data == "restart":
        for d in [user_states, user_amounts, user_screenshots, user_emails, user_ids]:
            d.pop(chat_id, None)
        send_welcome(call.message)
        bot.answer_callback_query(call.id)

# ✅ Amount input
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'WAITING_FOR_AMOUNT')
def handle_amount(message):
    try:
        amount = int(message.text)
        if amount < 1000:
            bot.send_message(message.chat.id, "❌ 1000 Ks ထက်ကြီးတဲ့ ငွေပမာဏထည့်ပါ။")
            return
        user_amounts[message.chat.id] = amount
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📤 ငွေလွဲပြေစာပြရန်", callback_data="upload_screenshot"),
            telebot.types.InlineKeyboardButton("❌ ပယ်ဖျက်သည်", callback_data="cancel_all")
        )
        bot.send_message(
            message.chat.id,
            f"✅ {amount} Ks ထည့်မည်ဖြစ်သည်။\n\n"
            "💳 ငွေထည့်ရန်အချက်အလက်:\n\n"
            "🔵 KPAY - 09691706633 \nName - Aye Sandi Myint\n\n"
            "🟡 WAVE - 09664243450 \nName - Khin San Lwin\n\n"
            "🔴 AYA - 09664243450 \nName - Aye sandi myint\n\n"
            "🟢 UAB - 09664243450 \nName - Aye sandi myint\n\n"
            "⚠️ Note မှာ 'Shop' လို့သာရေးပေးပါ။",
            reply_markup=markup
        )
        user_states[message.chat.id] = 'WAITING_FOR_SCREENSHOT'
    except ValueError:
        bot.send_message(message.chat.id, "❌ ငွေပမာဏ မှားနေတယ်။ နံပါတ်သာရိုက်ထည့်ပါ။")
        # ✅ Screenshot handler
@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    if user_states.get(message.chat.id) == 'WAITING_FOR_SCREENSHOT':
        user_screenshots[message.chat.id] = message.photo[-1].file_id
        bot.send_message(message.chat.id, "📧 Website ထဲက Email ကို Copy ယူပြီး Paste လုပ်ပါ။\nဥပမာ - example@gmail.com")
        user_states[message.chat.id] = 'WAITING_FOR_EMAIL'
    else:
        bot.send_message(message.chat.id, "❌ ဓာတ်ပုံကို လိုအပ်ချိန်မှာပဲ တင်ပါ။")

# ✅ Email handler
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'WAITING_FOR_EMAIL')
def handle_email(message):
    chat_id = message.chat.id
    email = message.text.strip()
    if '@' not in email:
        bot.send_message(chat_id, "❌ Email မှားနေပါတယ်။ @ ပါရမယ်။ ထပ်မံထည့်ပါ။")
        return
    user_emails[chat_id] = email
    user_ids[email] = chat_id
    user_states[chat_id] = None
    amount = user_amounts.get(chat_id, 'Unknown')
    file_id = user_screenshots.get(chat_id)

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("💰 ငွေထပ်မံဖြည့်မည်", callback_data="topup"))

    bot.send_message(
        chat_id,
        f"🎉 Email: {email}\n\n✔️ ငွေဖြည့်မှု စာရင်းသွင်းပြီးပါပြီ။\n📌 Website ထဲငွေရောက်ပါက အကြောင်းကြားပေးပါမည်။",
        reply_markup=markup
    )
    bot.send_photo(
        ADMIN_GROUP_ID,
        file_id,
        caption=(
            f"🆕 ငွေဖြည့်မှုအသစ်\n\n"
            f"💸 Amount: {amount} Ks\n"
            f"📧 Email: {email}\n"
            f"🆔 Telegram: @{message.from_user.username or 'N/A'}\n"
            f"📩 Reply ပြန်ပြီး /Yes သို့မဟုတ် /No ဖြင့်တုန့်ပြန်ပါ။"
        )
    )

# ✅ Admin /Yes command
@bot.message_handler(commands=['Yes'], func=lambda m: m.chat.type in ['group', 'supergroup'])
def handle_yes(message):
    if not message.reply_to_message:
        return bot.reply_to(message, "❗ ဒီ Command ကို Bot ပေးတဲ့ Message ကို Reply ပြန်ပြီး သုံးပါ။")

    original = message.reply_to_message.caption or ""
    email = re.search(r"Email:\s*(\S+)", original)
    amount = re.search(r"Amount:\s*(\d+)", original)

    if not email or not amount:
        return bot.reply_to(message, "❌ Email သို့မဟုတ် Amount မတွေ့ပါ။")

    email = email.group(1)
    amount = int(amount.group(1))
    admin = f"@{message.from_user.username or message.from_user.first_name}"

    try:
        result = supabase.table("users").select("*").eq("email", email).single().execute()
        if result.data:
            old = result.data.get("balance") or 0
            new = old + amount
            supabase.table("users").update({"balance": new}).eq("email", email).execute()
            bot.send_message(message.chat.id, f"📋 Admin Log:\n{admin} ➕ {amount} Ks → {email} ကို လက်ခံလိုက်သည်။")
            uid = user_ids.get(email)
            if uid:
                bot.send_message(uid, f"🎉 သင်၏ balance ကို {amount} Ks ဖြင့် တိုးလိုက်ပါပြီ။\n💰 လက်ကျန်: {new} Ks")
            else:
                bot.send_message(message.chat.id, "⚠️ User ID မတွေ့ပါ။")
        else:
            bot.send_message(message.chat.id, f"❌ Supabase မှာ {email} ကို မတွေ့ပါ။")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

# ✅ Admin /No command
@bot.message_handler(commands=['No'], func=lambda m: m.chat.type in ['group', 'supergroup'])
def handle_no(message):
    if not message.reply_to_message:
        return bot.reply_to(message, "❗ ဒီ Command ကို Bot ပေးတဲ့ Message ကို Reply ပြန်ပြီး သုံးပါ။")

    original = message.reply_to_message.caption or ""
    email_match = re.search(r"Email:\s*(\S+)", original)
    if not email_match:
        return bot.reply_to(message, "❌ Email မတွေ့ပါ။")

    email = email_match.group(1)
    admin = f"@{message.from_user.username or message.from_user.first_name}"
    bot.send_message(message.chat.id, f"📋 Admin Log:\n{admin} ❌ {email} ကို ပယ်ဖျက်လိုက်သည်။")
    uid = user_ids.get(email)
    if uid:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📧 Email ပြန်ရိုက်ရန်", callback_data="retry_email"),
            telebot.types.InlineKeyboardButton("🔄 အစပြန်စရန်", callback_data="restart")
        )
        try:
            bot.send_message(
                uid,
                "❌ Your Information Is Wrong\n\n"
                "❗ ငွေမရောက်ပါ ‼️\n (Or) Email မှားနေသည်‼️\n\n"
                "📧 ငွေလွဲမှန်ကန်ပါက Email ပြန်လည် ရိုက်ရန်ကို နှိပ်ပါ။\n\n"
                "♻️ အစကို ပြန်စလိုပါက အောက်က Button ကို နှိပ်ပါ။",
                reply_markup=markup
            )
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ User ထံမပို့နိုင်ပါ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ User ID မတွေ့ပါ။")

# ✅ Flask Root Route
@app.route('/')
def home():
    return "Bot is running!"

# ✅ Start Bot in Thread
if __name__ == "__main__":
    threading.Thread(target=bot.infinity_polling).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
