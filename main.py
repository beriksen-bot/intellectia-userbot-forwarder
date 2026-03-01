import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")  # <-- add this in Railway vars

SOURCE_CHAT = os.getenv("SOURCE_CHAT", "")        # e.g. @Intellectia_Bot or chat id
DEST_CHAT = os.getenv("DEST_CHAT", "")            # e.g. @IntellectiaDT

if not (API_ID and API_HASH and SESSION_STRING and SOURCE_CHAT and DEST_CHAT):
    raise SystemExit("Missing required env vars: API_ID, API_HASH, SESSION_STRING, SOURCE_CHAT, DEST_CHAT")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHAT))
async def handler(event):
    try:
        await client.forward_messages(DEST_CHAT, event.message)
        text_preview = (event.raw_text or "")[:120].replace("\n", " ")
        print(f"[FORWARDED] {SOURCE_CHAT} -> {DEST_CHAT} | {text_preview}")
    except Exception as e:
        print("[ERROR] Forward failed:", repr(e))

async def main():
    await client.start()
    me = await client.get_me()
    print(f"Userbot running as @{me.username or me.id}")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
