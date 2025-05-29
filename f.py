import logging
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# ---------------- Configuration ----------------
TOKEN = "8126587005:AAErZRKQCIIblybMZne-GZ2T2X_IbEX1yn4"  # Your bot token
OWNER_ID = 7792814115                                # Your Telegram user ID

# ---------------- Logging ----------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ---------------- Handlers ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.application.bot_data.setdefault("users", set()).add(user_id)
    await update.message.reply_text(
        "👋 Welcome to the File Library Bot!\n\n"
        "Use /help to see what I can do.\n"
        "Use /browse to explore available file categories."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *File Library Bot Commands:*\n\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "/browse - Browse and download files by category\n"
        "/broadcast <message> - (Owner only) Send message to all users\n\n"
        "*To upload files:* Send a document (owner only), then reply with the category name.",
        parse_mode="Markdown"
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 Unauthorized.")

    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("Usage: /broadcast Your message here")

    users = context.application.bot_data.get("users", set())
    count = 0
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=msg)
            count += 1
        except Exception as e:
            logging.warning(f"Could not send to {user_id}: {e}")
    
    await update.message.reply_text(f"✅ Broadcast sent to {count} users.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 Only the owner can upload files.")

    doc = update.message.document
    if doc:
        context.user_data["pending_file"] = doc
        await update.message.reply_text(
            "📁 Please reply with a *category name* for this file.",
            parse_mode="Markdown"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if "pending_file" in context.user_data:
        doc = context.user_data.pop("pending_file")
        category = text

        bot_data = context.application.bot_data
        bot_data.setdefault("files", {})
        bot_data["files"].setdefault(category, [])

        if (doc.file_id, doc.file_name) not in bot_data["files"][category]:
            bot_data["files"][category].append((doc.file_id, doc.file_name))
            await update.message.reply_text(
                f"✅ File saved under category: *{category}*",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("⚠️ This file already exists in the category.")

    elif text == "/browse":
        await show_categories(update, context)

    else:
        await update.message.reply_text("🤖 Unknown command or text. Use /help to see available options.")

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_data = context.application.bot_data
    file_store = bot_data.get("files", {})

    if not file_store or all(len(v) == 0 for v in file_store.values()):
        return await update.message.reply_text("📂 No categories available yet.")

    keyboard = [
        [InlineKeyboardButton(cat, callback_data=f"cat:{cat}")]
        for cat in sorted(file_store.keys())
    ]

    if update.effective_user.id == OWNER_ID:
        keyboard.append([
            InlineKeyboardButton("🗑️ Remove Category", callback_data="remove_category")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📚 Select a category to view files:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    bot_data = context.application.bot_data

    if data.startswith("cat:"):
        category = data.split(":", 1)[1]
        file_list = bot_data.get("files", {}).get(category, [])
        if file_list:
            for file_id, file_name in file_list:
                try:
                    await context.bot.send_document(
                        chat_id=query.message.chat.id,
                        document=file_id,
                        filename=file_name
                    )
                except Exception as e:
                    logging.warning(f"Failed to send file {file_name}: {e}")
        else:
            await query.message.reply_text("📁 No files in this category.")

    elif data == "remove_category":
        if update.effective_user.id != OWNER_ID:
            return await query.message.reply_text("🚫 Unauthorized.")
        keyboard = [
            [InlineKeyboardButton(cat, callback_data=f"delcat:{cat}")]
            for cat in sorted(bot_data.get("files", {}).keys())
        ]
        await query.message.reply_text(
            "🗑️ Select a category to delete:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("delcat:"):
        category = data.split(":", 1)[1]
        if category in bot_data.get("files", {}):
            del bot_data["files"][category]
            await query.message.reply_text(
                f"🗑️ Category *{category}* deleted.",
                parse_mode="Markdown"
            )
        else:
            await query.message.reply_text("❌ Category not found.")

# ---------------- Main ----------------

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Fix timezone issue for job_queue
    app.job_queue.scheduler.configure(timezone=pytz.UTC)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
