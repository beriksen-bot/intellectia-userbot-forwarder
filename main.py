import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession


def require_env(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        raise RuntimeError(f"Missing env var {name}")
    return val


def parse_chat_ref(raw: str):
    """
    Accepts:
      - @username
      - username
      - numeric id like -100123...
      - numeric id like 12345
    Returns either int (for ids) or str (for usernames).
    """
    s = raw.strip()
    if not s:
        raise ValueError("Empty chat ref")

    # If it's numeric (possibly negative), treat as id
    try:
        # int("-100...") works; int("100...") works
        return int(s)
    except ValueError:
        pass

    # Otherwise treat as username (strip leading @ if provided)
    return s[1:] if s.startswith("@") else s


async def resolve_entity(client: TelegramClient, chat_ref, label: str):
    """
    Resolves a chat/entity from either:
      - id (int)
      - username (str)
    Strategy:
      1) preload dialogs
      2) try match by dialog id if int
      3) fallback to get_entity
    """
    # Preload dialogs to populate the entity cache
    dialogs = await client.get_dialogs(limit=200)

    # If it's an id, try direct match in dialogs first
    if isinstance(chat_ref, int):
        for d in dialogs:
            if d.id == chat_ref:
                print(f"[RESOLVE] {label} matched dialog cache: name='{d.name}' id={d.id}")
                return d.entity

        # Fallback: ask Telegram for it
        try:
            ent = await client.get_entity(chat_ref)
            print(f"[RESOLVE] {label} resolved via get_entity(id): id={chat_ref}")
            return ent
        except Exception as e:
            raise RuntimeError(
                f"[RESOLVE-FAIL] Could not resolve {label} by id={chat_ref}. "
                f"Make sure the account in SESSION_STRING is a member of that chat/channel. "
                f"Original error: {e}"
            )

    # If it's a username, use get_entity(username)
    try:
        ent = await client.get_entity(chat_ref)
        print(f"[RESOLVE] {label} resolved via username: @{chat_ref}")
        return ent
    except Exception as e:
        raise RuntimeError(
            f"[RESOLVE-FAIL] Could not resolve {label} by username='@{chat_ref}'. "
            f"Original error: {e}"
        )


async def main():
    API_ID = int(require_env("API_ID"))
    API_HASH = require_env("API_HASH")
    SESSION_STRING = require_env("SESSION_STRING")

    SOURCE_CHAT_RAW = require_env("SOURCE_CHAT")      # e.g. "@intellectia_1_bot_bot"
    DEST_CHAT_RAW = require_env("DEST_CHAT")          # e.g. "-1003724596299"

    source_ref = parse_chat_ref(SOURCE_CHAT_RAW)
    dest_ref = parse_chat_ref(DEST_CHAT_RAW)

    print("[BOOT] Starting userbot...")
    print(f"[BOOT] SOURCE_CHAT={SOURCE_CHAT_RAW}")
    print(f"[BOOT] DEST_CHAT={DEST_CHAT_RAW}")

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    await client.start()
    me = await client.get_me()
    print(f"[BOOT] Logged in as: {getattr(me, 'first_name', '')} (id={me.id})")
    print("[BOOT] Preloading dialogs...")

    # Resolve source/dest entities *once*
    source_entity = await resolve_entity(client, source_ref, "SOURCE_CHAT")
    dest_entity = await resolve_entity(client, dest_ref, "DEST_CHAT")

    print("[OK] Userbot connected.")
    print(f"[OK] Listening for messages from: {SOURCE_CHAT_RAW}")
    print(f"[OK] Forwarding to: {DEST_CHAT_RAW}")

    @client.on(events.NewMessage(chats=source_entity))
    async def handler(event):
        try:
            # forward the exact message (keeps formatting/media)
            await client.forward_messages(dest_entity, event.message)
            print("[FORWARD] forwarded 1 message")
        except Exception as e:
            print(f"[FORWARD-ERROR] {e}")

    # Keep running forever
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
