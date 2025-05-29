import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

TOKEN = "8126587005:AAErZRKQCIIblybMZne-GZ2T2X_IbEX1yn4"  # Replace with your real token
OWNER_ID = 7792814115      # Replace with your Telegram user ID

# In-memory storage
users = set()
files = {}  # category -> list of (file_id, file_name)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users.add(user_id)
    
    keyboard = [[InlineKeyboardButton("📂 Browse Library", callback_data="browse")]]
    await update.message.reply_text(
        "Welcome! Use the button below to browse available files.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# /broadcast command (owner only)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("Unauthorized.")
    
    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("Usage: /broadcast Your message here")

    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=msg)
        except Exception as e:
            logging.warning(f"Could not send to {user_id}: {e}")
    
    await update.message.reply_text("Broadcast sent.")

# Handle uploaded documents
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    doc = update.message.document
    if doc:
        context.user_data["pending_file"] = doc
        await update.message.reply_text("Please reply with a category name to save this file.")

# Handle text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if "pending_file" in context.user_data:
        doc = context.user_data.pop("pending_file")
        if text:
            files.setdefault(text, [])
            if (doc.file_id, doc.file_name) not in files[text]:
                files[text].append((doc.file_id, doc.file_name))
            await update.message.reply_text(f"✅ File saved under category: {text}")
        else:
            await update.message.reply_text("⚠️ Category name cannot be empty.")
    elif text == "/browse":
        await show_categories(update, context)
    else:
        await update.message.reply_text("Unknown input or command.")

# Show category buttons
async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not files:
        return await update.message.reply_text("No categories available.")

    keyboard = [
        [InlineKeyboardButton(cat, callback_data=f"cat:{cat}")]
        for cat in sorted(files.keys())
    ]
    
    if update.effective_user.id == OWNER_ID:
        keyboard.append([
            InlineKeyboardButton("❌ Remove Category", callback_data="remove_category")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📚 Choose a category to get files:", reply_markup=reply_markup)

# Handle button presses
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "browse":
        return await show_categories(update, context)

    elif data.startswith("cat:"):
        category = data.split(":", 1)[1]
        file_list = files.get(category, [])
        if file_list:
            for file_id, file_name in file_list:
                await context.bot.send_document(
                    chat_id=query.message.chat.id,
                    document=file_id,
                    filename=file_name
                )
        else:
            await query.message.reply_text("⚠️ No files in this category.")

    elif data == "remove_category":
        if update.effective_user.id != OWNER_ID:
            return await query.message.reply_text("Unauthorized.")
        keyboard = [
            [InlineKeyboardButton(cat, callback_data=f"delcat:{cat}")]
            for cat in sorted(files.keys())
        ]
        await query.message.reply_text(
            "Select a category to delete:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("delcat:"):
        category = data.split(":", 1)[1]
        if category in files:
            del files[category]
            await query.message.reply_text(f"🗑️ Category '{category}' deleted.")
        else:
            await query.message.reply_text("⚠️ Category not found.")

# Main function
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
