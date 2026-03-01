from telethon import TelegramClient, events
import os

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
phone = os.getenv("PHONE_NUMBER")

source_chat = os.getenv("SOURCE_CHAT")
dest_chat = os.getenv("DEST_CHAT")

client = TelegramClient('userbot', api_id, api_hash)

@client.on(events.NewMessage(chats=source_chat))
async def handler(event):
    try:
        await client.forward_messages(dest_chat, event.message)
        print("[FORWARDED]", event.message.text[:100])
    except Exception as e:
        print("[ERROR]", e)

async def main():
    await client.start(phone)
    print("Userbot running...")
    await client.run_until_disconnected()

client.loop.run_until_complete(main())
