import logging
import requests
from random import randint, choice
from user_agent import generate_user_agent as ua
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

OWNER_ID = 7792814115  # Replace with your Telegram user ID
banned_links = set()

names = [
    "Rakesh", "rsmesh", "Aman", "avishek", "mohan", "Neha", "akhilesh", "sayam.",
    "robin", "rahul", "dev", "meera", "Anushka", "akshita", "manjeet", "manoj",
    "rakhi", "rampal", "sonu", "Subhashree", "Lakhan", "mohit", "mohini",
    "kakoli", "prince", "karan", "sushila", "sushil", "Krishna", "Ankit", "prakash"
]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def send_report(username: str) -> bool:
    message = f"""Hello sir/ma'am,

I would like to report a Telegram user who is engaging in suspicious and harmful activities. And child abusing. Their username is {username}. I believe they may be involved in scams and phishing attempts, which is causing harm to the community. I would appreciate it if you could look into this matter and take appropriate action.

Thank you for your attention to this matter.
"""
    try:
        email = f'{choice(names)}{randint(9392820,9994958)}@gmail.com'
        phone = "+91" + str(randint(9392823620,9994997058))

        res = requests.get('https://telegram.org/support', headers={
            "user-agent": ua(),
            "accept": "text/html",
        })
        stel = res.cookies.get('stel_ssid', '')

        data = {
            'message': message,
            'email': email,
            'phone': phone,
            'setln': ''
        }

        headers = {
            "user-agent": ua(),
            "accept": "text/html",
            "origin": "https://telegram.org",
            "content-type": "application/x-www-form-urlencoded",
            "referer": "https://telegram.org/support",
            "cookie": f"stel_ssid={stel}"
        }

        response = requests.post('https://telegram.org/support', data=data, headers=headers)
        return "Thanks" in response.text

    except Exception as e:
        logger.error(f"Error sending report: {e}")
        return False

def is_banned(username: str) -> bool:
    return any(banned in username for banned in banned_links)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Welcome to the Telegram Report Bot!\nUse /report <username> to report suspicious users.\nOwner can add banned links with /banlink <link>"
    )

def report(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /report <username>")
        return

    username = context.args[0].strip()

    if is_banned(username):
        update.message.reply_text("Sorry, this username contains a banned link and cannot be reported.")
        return

    update.message.reply_text(f"Reporting username: {username}...")
    success = send_report(username)
    if success:
        update.message.reply_text(f"Report for {username} sent successfully!")
    else:
        update.message.reply_text(f"Failed to send report for {username}.")

def banlink(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    if len(context.args) != 1:
        update.message.reply_text("Usage: /banlink <link>")
        return

    link = context.args[0].strip()
    banned_links.add(link)
    update.message.reply_text(f"Added banned link: {link}")

def listban(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    text = "Banned links:\n" + "\n".join(banned_links) if banned_links else "No banned links yet."
    update.message.reply_text(text)

def main():
    updater = Updater("7939492963:AAFLHNz7UeIiBziZ1xiwmgrlm0bZR3EK7aI", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("report", report))
    dp.add_handler(CommandHandler("banlink", banlink))
    dp.add_handler(CommandHandler("listban", listban))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
