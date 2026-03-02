from telethon import TelegramClient, events
from telethon.sessions import StringSession
import os
import asyncio

# Load environment variables
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_string = os.getenv("SESSION_STRING")
source_chat = os.getenv("SOURCE_CHAT")
dest_chat = os.getenv("DEST_CHAT")

# Validate required variables
required = ["API_ID","API_HASH","SESSION_STRING","SOURCE_CHAT","DEST_CHAT"]
missing = [v for v in required if not os.getenv(v)]

if missing:
    print("Missing required env vars:", ", ".join(missing))
    exit(1)

# Create Telegram client
client = TelegramClient(
    StringSession(session_string),
    api_id,
    api_hash
)

@client.on(events.NewMessage(chats=source_chat))
async def handler(event):
    try:
        await client.forward_messages(dest_chat, event.message)
        print("Forwarded:", event.message.text[:80] if event.message.text else "Media")
    except Exception as e:
        print("Forward error:", e)

async def main():

    print("Starting userbot...")

    await client.start()

    print("Userbot connected.")
    print("Listening for messages from:", source_chat)
    print("Forwarding to:", dest_chat)

    await client.run_until_disconnected()


asyncio.run(main())
