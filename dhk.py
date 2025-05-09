import os
from telethon import TelegramClient, events
import asyncio

# Telegram API credentials
api_id = '22564049'  # Replace with your API ID
api_hash = 'c60ebbfdbf49d845e66ebf2407feadd3'  # Replace with your API Hash

# Path to text files
welcome_file = 'welcome.txt'
group_file = 'group.txt'

# Initialize Telegram Client
client = TelegramClient('session_name', api_id, api_hash)

# Load welcome message from welcome.txt
def load_welcome_message():
    if os.path.exists(welcome_file):
        with open(welcome_file, 'r') as file:
            return file.read()
    return "Welcome to my Telegram!"

# Load group message from group.txt
def load_group_message():
    if os.path.exists(group_file):
        with open(group_file, 'r') as file:
            return file.read()
    return "Thanks for your message in the group!"

# Respond to Direct Messages
@client.on(events.NewMessage(incoming=True))
async def handler(event):
    # Respond to direct messages
    if event.is_private:
        welcome_message = load_welcome_message()
        await event.reply(welcome_message)
        print(f"Replied to DM with: {welcome_message}")

    # Respond to messages in groups
    elif event.is_group:
        group_message = load_group_message()
        await event.reply(group_message)
        print(f"Replied to group with: {group_message}")

# Start the Telegram client
async def main():
    await client.start()
    print("Bot is running...")
    await client.run_until_disconnected()

# Run the bot
if __name__ == '__main__':
    asyncio.run(main())
    
