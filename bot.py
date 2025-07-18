import os
import re
import threading
from flask import Flask
from dotenv import load_dotenv
import telebot
from supabase import create_client

# ✅ ပတ်ဝန်းကျင် ပြင်ဆင်ချက်များ Load လုပ်ခြင်း
load_dotenv()
TOKEN = os.getenv('TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
ADMIN_GROUP_ID = int(os.getenv('ADMIN_GROUP_ID'))

# ✅ Bot နဲ့ Supabase ဆက်သွယ်မှုများ ပြင်ဆင်ခြင်း
bot = telebot.TeleBot(TOKEN)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app = Flask(__name__)

# ✅ အသုံးပြုသူ အခြေအနေ စုစည်းထားခြင်း
user_states = {}
user_screenshots = {}
user_amounts = {}
user_emails = {}
user_ids = {}

# ✅ /start command ကို သုံးသည့်အခါ
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("အသုံးပြုနည်း✅", url="https://youtube.com"))
    markup.add(telebot.types.InlineKeyboardButton("💰 ငွေဖြည့်သွင်းမည်", callback_data="topup"))
    bot.send_message(
        message.chat.id,
        "K2 ငွေဖြည့်သွင်းစနစ်မှ ကြိုဆိုပါတယ်။\n\nငွေမသွင်းခင်အသုံးပြုနည်းကိုလေ့လာပါ‼️",
        reply_markup=markup
    )

# ✅ Button နှိပ်သည့်အခါ Handling
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if call.data == "topup":
        bot.send_message(chat_id, "💰 ငွေဖြည့်သွင်းမည့် ပမာဏ ကိုရေးပါ\n\n1000 Ks အနည်းဆုံးဖြစ်ရပါမယ်။")
        user_states[chat_id] = 'WAITING_FOR_AMOUNT'
    elif call.data == "upload_screenshot":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="cancel_all"))
        bot.send_message(chat_id, "📸 ငွေလွဲပြေစာ ပို့ပေးပါ။\n\n‼️ ပုံတစ်ခုတည်းပေးပါ။", reply_markup=markup)
        user_states[chat_id] = 'WAITING_FOR_SCREENSHOT'
    elif call.data in ["cancel_topup", "cancel_all"]:
        for d in [user_states, user_amounts, user_screenshots, user_emails, user_ids]:
            d.pop(chat_id, None)
        bot.send_message(chat_id, "❌ ပယ်ဖျက်ပြီးပါပြီ။ အစက ပြန်စမယ်။")
        send_welcome(call.message)
    elif call.data == "retry_email":
        bot.send_message(chat_id, "📧 ကျေးဇူးပြု၍ မှန်ကန်သော Email ကို ပြန်ထည့်ပေးပါ။\n\nအကောင်းဆုံးနည်းလမ်းက 🤩 Website က Email ကို Copy ယူပါ။✅")
        user_states[chat_id] = 'WAITING_FOR_EMAIL'
        bot.answer_callback_query(call.id)
    elif call.data == "restart":
        for d in [user_states, user_amounts, user_screenshots, user_emails, user_ids]:
            d.pop(chat_id, None)
        send_welcome(call.message)
        bot.answer_callback_query(call.id)

# ✅ ငွေပမာဏ ရိုက်သောအခါ
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'WAITING_FOR_AMOUNT')
def handle_amount(message):
    try:
        amount = int(message.text)
        if amount < 1000:
            bot.send_message(message.chat.id, "❌ 1000 Ks နှင့်အထက်များတဲ့ ငွေပမာဏထည့်ပါ။")
            return
        user_amounts[message.chat.id] = amount
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("✅ ငွေလွဲပြေစာပြရန်", callback_data="upload_screenshot"),
            telebot.types.InlineKeyboardButton("❌ ပယ်ဖျက်သည်", callback_data="cancel_all")
        )
        bot.send_message(
            message.chat.id,
            f"✅ {amount} Ks ထည့်မည်ဖြစ်သည်။\n\n"
            "💳 ငွေလွဲရန်အချက်အလက်:\n\n"
            "🔵 KPAY - 09691706633 \nName - Aye Sandi Myint\n\n"
            "🟡 WAVE - 09664243450 \nName - Khin San Lwin\n\n"
            "🔴 AYA - 09664243450 \nName - Aye sandi myint\n\n"
            "🟢 UAB - 09664243450 \nName - Aye sandi myint\n\n"
            "⚠️ Note မှာ 'Shop' လို့သာရေးပေးပါ။\n\nငွေလွဲပြီးပါက‌ငွေလွဲပြေစာပြရန်ကိုနှိပ်ပါ☑️\n\n ငွေလွဲပြီး 15Minutes အတွင်းပို့ပေးဖို့အကြံပေးပါတယ်။ ",
            reply_markup=markup
        )
        user_states[message.chat.id] = 'WAITING_FOR_SCREENSHOT'
    except ValueError:
        bot.send_message(message.chat.id, "❌ ငွေပမာဏ မှားနေတယ်။ နံပါတ်သာရိုက်ထည့်ပါ။")
        # ✅ ဓာတ်ပုံ ပို့သောအခါ
@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    if user_states.get(message.chat.id) == 'WAITING_FOR_SCREENSHOT':
        user_screenshots[message.chat.id] = message.photo[-1].file_id
        bot.send_message(message.chat.id, "စာလုံး အကြီး အသေးအကုန် တူ ရပါမယ်။‼️\n\nWebsite ထဲက Email ကို Copy ယူ ပြီး Paste လုပ်ပါ။✅\n\nဥပမာ 👇\nexample@gmail.com\nexample@Gmail.com")
        user_states[message.chat.id] = 'WAITING_FOR_EMAIL'
    else:
        bot.send_message(message.chat.id, "❌ ဓာတ်ပုံကို လိုအပ်ချိန်မှာပဲ တင်ပါ။")

# ✅ Email ရိုက်သောအခါ
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
        f"🎉 Email: \n{email}\n\nငွေဖြည့်မှု စာရင်းသွင်းပြီးပါပြီ။✅\\nn⚠️ Website ထဲ ငွေရောက်ပါကစာ ပြန်ပို့ပေးပါမည်။။",
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

# ✅ Admin /Yes မှတဆင့် လက်ခံသည့်အခါ
@bot.message_handler(commands=['Yes'], func=lambda m: m.chat.type in ['group', 'supergroup'])
def handle_yes(message):
    if not message.reply_to_message:
        return bot.reply_to(message, "❗️ ဒီ Command ကို Bot ပေးတဲ့ Message ကို Reply ပြန်ပြီး သုံးပါ။")
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

# ✅ Admin /No သုံးပြီး ပယ်ဖျက်သောအခါ
@bot.message_handler(commands=['No'], func=lambda m: m.chat.type in ['group', 'supergroup'])
def handle_no(message):
    if not message.reply_to_message:
        return bot.reply_to(message, "❗️ ဒီ Command ကို Bot ပေးတဲ့ Message ကို Reply ပြန်ပြီး သုံးပါ။")
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
                "ငွေမရောက်ပါ ‼️\n(Or)\n Email မှားနေသည်‼️\n\nငွေလွဲလိုက်ကြောင်း မှန်ကန်ပါက Email ပြန်ရိုက်ရန် ကိုနှိပ်ပါ ✅\n\nမှားလုပ်မိပါကအစကိုပြန်သွားရန် ☑️",
                reply_markup=markup
            )
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ User ထံမပို့နိုင်ပါ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ User ID မတွေ့ပါ။")

# ✅ Flask Webserver Root Route
@app.route('/')
def home():
    return "Bot is running!"

# ✅ Bot ကို Thread ထဲမှာ run လုပ်ခြင်း
if __name__ == "__main__":
    threading.Thread(target=bot.infinity_polling).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
