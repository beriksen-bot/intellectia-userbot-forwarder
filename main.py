import os
import sys
from telethon import TelegramClient, events
from telethon.sessions import StringSession

REQUIRED_VARS = ["API_ID", "API_HASH", "SESSION_STRING", "SOURCE_CHAT", "DEST_CHAT"]

def getenv_required(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val

def main():
    missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
    if missing:
        print(f"Missing required env vars: {', '.join(missing)}")
        sys.exit(1)

    api_id = int(getenv_required("API_ID"))
    api_hash = getenv_required("API_HASH")
    session_string = getenv_required("SESSION_STRING")
    source_chat = getenv_required("SOURCE_CHAT")   # e.g. "@Intellectia_Bot"
    dest_chat = getenv_required("DEST_CHAT")       # e.g. "@IntellectiaDT"

    client = TelegramClient(StringSession(session_string), api_id, api_hash)

    @client.on(events.NewMessage(chats=source_chat))
    async def handler(event):
        try:
            # Forward the exact message (preserves "Forwarded from" and media)
            await client.forward_messages(dest_chat, event.message)
            preview = (event.raw_text or "").replace("\n", " ")[:120]
            print(f"[FORWARDED] {source_chat} -> {dest_chat} | {preview}")
        except Exception as e:
            print(f"[ERROR] forward failed: {e}")

    print(f"[BOOT] Listening on {source_chat} and forwarding to {dest_chat}")
    client.run_until_disconnected()

if __name__ == "__main__":
    main()
