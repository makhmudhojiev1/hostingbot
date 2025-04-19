from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import mysql.connector
import requests
import json
import os
from datetime import datetime
import ftplib
from urllib.parse import quote
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()
API_KEY = os.getenv('TELEGRAM_API_KEY')
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
ISP_IP = os.getenv('ISP_IP')
ISP_LOG = os.getenv('ISP_LOG')
ISP_PASS = os.getenv('ISP_PASS')

ADMIN_ID = "7670526250"  # Admin ID
bot = Bot(token=API_KEY)

# Database connection
db_config = {
    'host': MYSQL_HOST,
    'user': MYSQL_USER,
    'password': MYSQL_PASSWORD,
    'database': MYSQL_DATABASE
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Helper functions
def get_step(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT stop, telegram FROM users WHERE chat_id = %s", (chat_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result['stop'] if result else None

def set_step(step, chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET stop = %s WHERE chat_id = %s", (step, chat_id))
    conn.commit()
    cursor.close()
    conn.close()

def join_chat(chat_id, message_id):
    try:
        response = bot.get_chat_member(chat_id="-1001318719633", user_id=chat_id)
        status = response.status
        if status in ["creator", "administrator", "member"]:
            return True
        else:
            bot.send_message(
                chat_id=chat_id,
                text="<b>Quyidagi kanallarimizga obuna boʻling. Botni keyin toʻliq ishlatishingiz mumkin!</b>",
                parse_mode="HTML",
                reply_to_message_id=message_id,
                disable_web_page_preview=True,
                reply_markup={
                    "inline_keyboard": [
                        [{"text": "➕ A‘zo bo‘lish", "url": "https://t.me/infotuit"}],
                        [{"text": "✅ Tasdiqlash", "callback_data": "result"}]
                    ]
                }
            )
            return False
    except Exception as e:
        print(f"Error in join_chat: {e}")
        return False

def api_query(url):
    response = requests.get(url, verify=False)
    return response.text

def get_user_data(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE chat_id = %s", (chat_id,))
    user = cursor.fetchone()
    cursor.execute("SELECT * FROM tarux WHERE chat_id = %s", (chat_id,))
    tarux = cursor.fetchone()
    cursor.execute("SELECT * FROM server")
    server = cursor.fetchone()
    cursor.close()
    conn.close()
    return user, tarux, server

# Load menu
with open('templates/menu.json', 'r', encoding='utf-8') as f:
    menu = json.load(f)

# Telegram handlers
def start(update: Update, context):
    chat_id = update.effective_chat.id
    message_id = update.message.message_id
    text = update.message.text
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user exists, if not, insert
    cursor.execute("SELECT * FROM users WHERE chat_id = %s", (chat_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (chat_id) VALUES (%s)", (chat_id,))
    cursor.execute("SELECT * FROM tarux WHERE chat_id = %s", (chat_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO tarux (chat_id, phpuz, ssluz) VALUES (%s, '7.1 ✅', 'Yo`q ❌')", (chat_id,))
    conn.commit()
    cursor.close()
    conn.close()

    if join_chat(chat_id, message_id):
        user, tarux, server = get_user_data(chat_id)
        if user and user['ok'] == str(chat_id):
            content = api_query(f"https://{server['ip']}/ispmgr?func=userstat&out=xml&authinfo={user['isp_log']}:{user['isp_pass']}")
            parse_xml = ET.fromstring(content)
            disk = f"{parse_xml.find('.//elem[19]/usages_used').text} MB {parse_xml.find('.//elem[19]/usages_total').text}"
            bot.send_message(
                chat_id=chat_id,
                text=f"👋Salom: <b>{user['ism']}</b> ☺️\n🌐Domen: {user['isp_log']}.c7.uz\n💰Balans: {user['pul']} so`m\n🎯Tarif: {user['tarif']}\n___________________________\n⚙️Php versiya: {tarux['phpuz']}\n🛡Ssl holati: {tarux['ssluz']}\n💾Disk: {disk}!",
                parse_mode="HTML",
                reply_markup=menu
            )
        else:
            bot.send_message(
                chat_id=chat_id,
                text="*Assalomu alaykum, www.tuit.ru sayti rasmiy telegram botiga xush kelibsiz.\nBu bot orqali hech qanday web saytga kirmasdan serverdan joy olsangiz bo'ladi.\n\nTelegram kanal: @infoTUIT️*️",
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup={
                    "inline_keyboard": [
                        [{"text": "Ro`yxatdan o`tish", "callback_data": "tarif11"}],
                        [{"text": "💰Hisobni to`ldirish va Texnik qo`llab-quvvatlas", "callback_data": "balnss"}],
                        [{"text": "🤝Referal", "callback_data": "referal"}]
                    ]
                }
            )

def panel(update: Update, context):
    chat_id = update.effective_chat.id
    if str(chat_id) == ADMIN_ID:
        bot.send_message(
            chat_id=chat_id,
            text="Salom admin panelga xush kelibsiz!",
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup={
                "inline_keyboard": [
                    [{"text": "🎯Barchaga xabar yuborish", "callback_data": "uyga11"}],
                    [{"text": "🎯Barchaga forward qilish", "callback_data": "Forward12"}],
                    [{"text": "💰Hisobni to`ldirish", "callback_data": "pulberish"}],
                    [{"text": "⛔️Cheklov qo`yish", "callback_data": "ban"}],
                    [{"text": "🟢Cheklov olish", "callback_data": "uyg1a5"}],
                    [{"text": "👁Foydalanuvchini kuzatish", "callback_data": "stat"}],
                    [{"text": "🏠Bosh sahifa", "callback_data": "boshsahifauz"}]
                ]
            }
        )

def stat(update: Update, context):
    chat_id = update.effective_chat.id
    if str(chat_id) == ADMIN_ID:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM users")
        user_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        bot.send_message(
            chat_id=chat_id,
            text=f"📈 Bot a'zolari:\n👤 Userlar: {user_count}",
            show_alert=True
        )

def handle_document(update: Update, context):
    chat_id = update.effective_chat.id
    message_id = update.message.message_id
    doc = update.message.document
    doc_id = doc.file_id
    doc_name = doc.file_name
    user, tarux, server = get_user_data(chat_id)

    # Download file
    file_info = bot.get_file(doc_id)
    file_url = f"https://api.telegram.org/file/bot{API_KEY}/{file_info.file_path}"
    response = requests.get(file_url)
    os.makedirs("/tmp/telegram", exist_ok=True)
    file_path = f"/tmp/telegram/{doc_name}.zip"
    with open(file_path, 'wb') as f:
        f.write(response.content)

    # FTP upload
    ftp_server = "ok.c7.uz"
    ftp_port = 21
    ftp_user = user['isp_log']
    ftp_pass = user['isp_pass']
    try:
        ftp = ftplib.FTP()
        ftp.connect(ftp_server, ftp_port, timeout=20)
        ftp.login(ftp_user, ftp_pass)
        ftp.set_pasv(True)
        with open(file_path, 'rb') as f:
            ftp.storbinary(f"STOR {doc_name}", f)
        ftp.quit()
        bot.send_message(
            chat_id=chat_id,
            text="✅Muvaffaqqiyat fayl yuklab olindi",
            parse_mode="HTML",
            reply_markup=menu
        )
        for i in range(-4, 6):
            try:
                bot.delete_message(chat_id=chat_id, message_id=message_id + i)
            except:
                pass
        os.unlink(file_path)
    except Exception as e:
        for i in range(-4, 6):
            try:
                bot.delete_message(chat_id=chat_id, message_id=message_id + i)
            except:
                pass
        bot.send_message(
            chat_id=chat_id,
            text="❌ Kechirasiz siz yuborga faylni xajmi katta, 20-Mb kichik bo'lgan fayl yuboring!",
            parse_mode="HTML",
            reply_markup=menu
        )
        if os.path.exists(file_path):
            os.unlink(file_path)

def callback_query(update: Update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    data = query.data
    user, tarux, server = get_user_data(chat_id)

    if data == "result":
        if join_chat(chat_id, message_id):
            if user and user['ok'] == str(chat_id):
                content = api_query(f"https://{server['ip']}/ispmgr?func=userstat&out=xml&authinfo={user['isp_log']}:{user['isp_pass']}")
                parse_xml = ET.fromstring(content)
                disk = f"{parse_xml.find('.//elem[19]/usages_used').text} MB {parse_xml.find('.//elem[19]/usages_total').text}"
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"👋Salom: <b>{user['ism']}</b> ☺️\n🌐Domen: {user['isp_log']}.c7.uz\n💰Balans: {user['pul']} so`m\n🎯Tarif: {user['tarif']}\n___________________________\n⚙️Php versiya: {tarux['phpuz']}\n🛡Ssl holati: {tarux['ssluz']}\n💾Disk: {disk}!",
                    parse_mode="HTML",
                    reply_markup=menu
                )
            else:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="*Assalomu alaykum, www.tuit.ru sayti rasmiy telegram botiga xush kelibsiz.\nBu bot orqali hech qanday web saytga kirmasdan serverdan joy olsangiz bo'ladi.\n\nTelegram kanal: @infoTUIT️*️",
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                    reply_markup={
                        "inline_keyboard": [
                            [{"text": "Ro`yxatdan o`tish", "callback_data": "tarif11"}],
                            [{"text": "💰Hisobni to`ldirish va Texnik qo`llab-quvvatlas", "callback_data": "balnss"}],
                            [{"text": "🤝Referal", "callback_data": "referal"}]
                        ]
                    }
                )
        else:
            bot.answer_callback_query(callback_query_id=query.id, text="Siz hali kanallarga aʼzo boʻlmadingiz!", show_alert=False)

# Flask webhook endpoint
@app.route('/', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = Update.de_json(request.get_json(), bot)
        dispatcher.process_update(update)
        return jsonify({"status": "ok"})
    return 'OK'

@app.route('/')
def index():
    return 'Telegram bot is running!'

# Set up Telegram handlers
dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("panel", panel))
dispatcher.add_handler(CommandHandler("stat", stat))
dispatcher.add_handler(MessageHandler(Filters.document, handle_document))
dispatcher.add_handler(CallbackQueryHandler(callback_query))

# For Vercel deployment
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
