import logging
import re
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OWNER_IDS = {7792814115}  # Set of owner/admin IDs

DB_PATH = "botdata.db"

# Connect DB and create tables if not exist
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS banned_links (
    link TEXT PRIMARY KEY
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reporter_id INTEGER,
    reported_username TEXT,
    reason TEXT,
    report_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS rate_limits (
    user_id INTEGER PRIMARY KEY,
    last_report_time TIMESTAMP,
    reports_today INTEGER DEFAULT 0
)''')

conn.commit()

USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_]{5,32}$')
MAX_REPORTS_PER_DAY = 5

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

def valid_username(username: str) -> bool:
    return USERNAME_REGEX.fullmatch(username) is not None

def can_report(user_id: int) -> bool:
    cursor.execute("SELECT last_report_time, reports_today FROM rate_limits WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    now = datetime.utcnow()

    if not row:
        cursor.execute("INSERT INTO rate_limits (user_id, last_report_time, reports_today) VALUES (?, ?, ?)",
                       (user_id, now, 0))
        conn.commit()
        return True

    last_report_time, reports_today = row
    last_report_time = datetime.fromisoformat(last_report_time)

    # Reset daily count if day changed
    if now.date() != last_report_time.date():
        cursor.execute("UPDATE rate_limits SET reports_today=0 WHERE user_id=?", (user_id,))
        conn.commit()
        reports_today = 0

    if reports_today >= MAX_REPORTS_PER_DAY:
        return False

    # Optional cooldown, e.g., 30 seconds between reports
    cooldown = timedelta(seconds=30)
    if now - last_report_time < cooldown:
        return False

    return True

def record_report(user_id: int):
    now = datetime.utcnow()
    cursor.execute("SELECT reports_today FROM rate_limits WHERE user_id=?", (user_id,))
    reports_today = cursor.fetchone()[0]
    reports_today += 1
    cursor.execute("UPDATE rate_limits SET last_report_time=?, reports_today=? WHERE user_id=?",
                   (now, reports_today, user_id))
    conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user.id,))
    conn.commit()

    await update.message.reply_text(
        "Welcome to the Advanced Telegram Report Bot!\n"
        "Use /report <username> <reason> to report.\n"
        "Owners can manage banned links and broadcast messages."
    )

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /report <username> <reason>")
        return

    username = context.args[0].strip()
    reason = " ".join(context.args[1:]).strip()

    if not valid_username(username):
        await update.message.reply_text("Invalid username format.")
        return

    # Check rate limit
    if not can_report(user.id):
        await update.message.reply_text("You have reached your daily report limit or are reporting too fast. Try later.")
        return

    # Check banned links
    cursor.execute("SELECT 1 FROM banned_links WHERE ? LIKE '%' || link || '%'", (username,))
    if cursor.fetchone():
        await update.message.reply_text("Username contains a banned link; cannot report.")
        return

    # Log report to DB
    cursor.execute("INSERT INTO reports (reporter_id, reported_username, reason) VALUES (?, ?, ?)",
                   (user.id, username, reason))
    conn.commit()

    record_report(user.id)

    # TODO: You can integrate your send_report function here asynchronously

    await update.message.reply_text(f"Report sent for {username} with reason: {reason}")

# Add handlers for /banlink, /listban, /broadcast similarly with DB

def main():
    app = ApplicationBuilder().token("7939492963:AAFLHNz7UeIiBziZ1xiwmgrlm0bZR3EK7aI").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report))
    # Add other handlers...

    app.run_polling()

if __name__ == "__main__":
    main()
