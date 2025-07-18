import os
import re
import json
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

# ✅ Init bot, supabase, flask
bot = telebot.TeleBot(TOKEN)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app = Flask(__name__)

# ✅ Load used file IDs to prevent duplicates
USED_FILE_IDS_PATH = "/data/used_file_ids.json" if os.path.exists("/data") else "used_file_ids.json"
if os.path.exists(USED_FILE_IDS_PATH):
    with open(USED_FILE_IDS_PATH, "r") as f:
        used_file_ids = set(json.load(f))
else:
    used_file_ids = set()

def save_used_file_ids():
    with open(USED_FILE_IDS_PATH, "w") as f:
        json.dump(list(used_file_ids), f)

# ✅ User states and storage
user_states = {}
user_screenshots = {}
user_amounts = {}
user_emails = {}
user_ids = {}

# ✅ In-memory banned users set
banned_users = set()

# ================================
# /start command
# ================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id in banned_users:
        bot.send_message(chat_id, "⚠️ သင်သည် Bot ကိုအသုံးပြုခွင့် မရှိပါ။")
        return

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("အသုံးပြုနည်း✅", url="https://youtube.com"))
    markup.add(telebot.types.InlineKeyboardButton("💰 ငွေဖြည့်သွင်းမည်", callback_data="topup"))
    bot.send_message(
        chat_id,
        "K2 ငွေဖြည့်သွင်းစနစ်မှ ကြိုဆိုပါတယ်။\n\nငွေမသွင်းခင်အသုံးပြုနည်းကိုလေ့လာပါ‼️",
        reply_markup=markup
    )

# ================================
# /ID command - သုံးသူ ID ပြန်ပေးမယ့် handler
# ================================
@bot.message_handler(commands=['ID'])
def handle_id_command(message):
    user = message.from_user
    bot.reply_to(message, f"👤 သင့် ID: {user.id}\nUsername: @{user.username or 'မရှိသေးပါ'}", parse_mode='Markdown')

# ================================
# Handle button presses
# ================================
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if chat_id in banned_users:
        bot.answer_callback_query(call.id, "⚠️ သင်သည် Bot ကိုအသုံးပြုခွင့် မရှိပါ။")
        return

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
        bot.send_message(chat_id, "❌ ပယ်ဖျက်ပြီးပါပြီ။ အစကိုပြန်သွားရန် /start ကိုနှိပ်ပါ။ ✅")

    elif call.data == "retry_email":
        bot.send_message(chat_id, "📧 ကျေးဇူးပြု၍ မှန်ကန်သော Email ကို ပြန်ထည့်ပေးပါ။\n\nအကောင်းဆုံးနည်းလမ်းက 🤩 Website က Email ကို Copy ယူပါ။✅")
        user_states[chat_id] = 'WAITING_FOR_EMAIL'

    elif call.data == "restart":
        for d in [user_states, user_amounts, user_screenshots, user_emails, user_ids]:
            d.pop(chat_id, None)
        bot.send_message(chat_id, "အစကိုပြန်သွားရန် /start ကိုနှိပ်ပါ။ ✅")

    bot.answer_callback_query(call.id)

# ================================
# Handle amount input
# ================================
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'WAITING_FOR_AMOUNT')
def handle_amount(message):
    chat_id = message.chat.id
    try:
        amount = int(message.text)
        if amount < 1000:
            bot.send_message(chat_id, "❌ 1000 Ks နှင့်အထက်များတဲ့ ငွေပမာဏထည့်ပါ။")
            return

        user_amounts[chat_id] = amount
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("✅ ငွေလွဲပြေစာပြရန်", callback_data="upload_screenshot"),
            telebot.types.InlineKeyboardButton("❌ ပယ်ဖျက်သည်", callback_data="cancel_all")
        )
        bot.send_message(
            chat_id,
            f"✅ {amount} Ks ထည့်မည်ဖြစ်သည်။\n\n"
            "💳 ငွေလွဲရန်အချက်အလက်:\n\n"
            "🔵 KPAY - 09691706633 \nName - Aye Sandi Myint\n\n"
            "🟡 WAVE - 09664243450 \nName - Khin San Lwin\n\n"
            "🔴 AYA - 09664243450 \nName - Aye sandi myint\n\n"
            "🟢 UAB - 09664243450 \nName - Aye sandi myint\n\n"
            "⚠️ Note မှာ 'Shop' လို့သာရေးပေးပါ။\n\n"
            "ငွေလွဲပြီးပါက‌ငွေလွဲပြေစာပြရန်ကိုနှိပ်ပါ☑️\n\n"
            "ငွေလွဲပြီး 15Minutes အတွင်းပို့ပေးဖို့အကြံပေးပါတယ်။",
            reply_markup=markup
        )
        user_states[chat_id] = 'WAITING_FOR_SCREENSHOT'
    except ValueError:
        bot.send_message(chat_id, "❌ ငွေပမာဏ မှားနေတယ်။ နံပါတ်သာရိုက်ထည့်ပါ။")

# ================================
# Handle screenshot
# ================================
@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    chat_id = message.chat.id
    if user_states.get(chat_id) == 'WAITING_FOR_SCREENSHOT':
        file_id = message.photo[-1].file_id
        if file_id in used_file_ids:
            bot.send_message(chat_id, "❌ ဓာတ်ပုံကို ယခင်မှာ အသုံးပြုပြီးသားဖြစ်ပါတယ်။ တခြား Screenshot တင်ပါ။")
            return
        used_file_ids.add(file_id)
        save_used_file_ids()
        user_screenshots[chat_id] = file_id
        bot.send_message(
            chat_id,
            "စာလုံး အကြီး အသေးအကုန် တူ ရပါမယ်‼️\n\nWebsite ထဲက Email ကို Copy ယူ ပြီး Paste လုပ်ပါ။✅\n\nဥပမာ 👇\nexample@gmail.com\nexample@Gmail.com"
        )
        user_states[chat_id] = 'WAITING_FOR_EMAIL'
    else:
        bot.send_message(chat_id, "❌ ဓာတ်ပုံကို လိုအပ်ချိန်မှာပဲ တင်ပါ။")

# ================================
# Handle email input
# ================================
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
        f"🎉 Email: \n{email}\n\nငွေဖြည့်မှု စာရင်းသွင်းပြီးပါပြီ✅\n⚠️ Website ထဲ ငွေရောက်ပါကစာ ပြန်ပို့ပေးပါမည်။။",
        reply_markup=markup
    )

    if file_id:
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
    else:
        bot.send_message(
            ADMIN_GROUP_ID,
            f"🆕 ငွေဖြည့်မှုအသစ်\n\n"
            f"💸 Amount: {amount} Ks\n"
            f"📧 Email: {email}\n"
            f"🆔 Telegram: @{message.from_user.username or 'N/A'}\n"
            f"❌ ဓာတ်ပုံမပါရှိပါ။"
        )
# ================================
# Admin accepts top-up
# ================================
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

# ================================
# Admin rejects top-up
# ================================
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
            telebot.types.InlineKeyboardButton("🔄 အစကိုပြန်သွားရန် /start ကိုနှိပ်ပါ။ ✅", callback_data="restart")
        )
        try:
            bot.send_message(
                uid,
                "ငွေမရောက်ပါ‼️\n(Or)\nEmail မှားနေသည်‼️\n\nငွေလွဲလိုက်ကြောင်း မှန်ကန်ပါက Email ပြန်ရိုက်ရန် ကိုနှိပ်ပါ ✅\n\nမှားလုပ်မိပါက အစကိုပြန်သွားရန် /start ကိုနှိပ်ပါ။ ✅",
                reply_markup=markup
            )
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ User ထံမပို့နိုင်ပါ: {e}")
    else:
        bot.send_message(message.chat.id, "⚠️ User ID မတွေ့ပါ။")

# ================================
# Flask
# ================================
@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    threading.Thread(target=bot.infinity_polling).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
