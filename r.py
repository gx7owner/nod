from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChannel
from time import sleep
import asyncio

api_id = 'YOUR_API_ID'
api_hash = 'YOUR_API_HASH'
group_file = 'group.txt'
message_text = "Hello, this is an automated message!"

async def main():
    async with TelegramClient('anon', api_id, api_hash) as client:
        dialogs = await client.get_dialogs()
        
        # Read group name from file
        with open(group_file, 'r') as f:
            group_name = f.read().strip()

        target_group = None
        for dialog in dialogs:
            if dialog.is_group or dialog.is_channel:
                if dialog.name == group_name:
                    target_group = dialog
                    break

        if not target_group:
            print(f"Group '{group_name}' not found.")
            return

        while True:
            await client.send_message(target_group.id, message_text)
            print(f"Message sent to {group_name}")
            sleep(10)

# Run the async main
asyncio.run(main())
