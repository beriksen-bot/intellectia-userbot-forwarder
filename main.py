import os
import sys
import asyncio
import logging
from typing import Optional, Tuple, Union

from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("userbot-forwarder")


# ----------------------------
# Helpers
# ----------------------------
def env_required(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val.strip()


def parse_chat_ref(raw: str) -> Union[int, str]:
    """
    Accepts:
      - "-100123..." (channel id)
      - "123456"     (user/chat id)
      - "@username"
      - "username"
    Returns int for numeric, otherwise string username without @.
    """
    s = raw.strip()
    if s.startswith("@"):
        s = s[1:]

    # numeric?
    try:
        return int(s)
    except ValueError:
        return s  # username


async def build_dialog_index(client: TelegramClient) -> dict:
    """
    Build a map of:
      - id -> dialog
      - username -> dialog (if present)
      - title/name -> dialog (best-effort)
    """
    idx = {}
    async for d in client.iter_dialogs():
        # By id
        idx[str(d.id)] = d

        # By username if exists
        ent = d.entity
        username = getattr(ent, "username", None)
        if username:
            idx[username.lower()] = d

        # By title/name (best-effort, not unique)
        title = (d.name or "").strip()
        if title:
            idx[title.lower()] = d

    return idx


async def resolve_entity(
    client: TelegramClient,
    ref: Union[int, str],
    idx: dict,
    label: str
):
    """
    Resolve a chat/user/channel entity using the dialog index first (most reliable).
    If not found, tries Telethon get_entity as fallback.
    """
    # 1) Try dialog index
    if isinstance(ref, int):
        key = str(ref)
        if key in idx:
            return idx[key].entity
    else:
        key = ref.lower()
        if key in idx:
            return idx[key].entity

    # 2) Fallback: try Telethon resolution
    try:
        return await client.get_entity(ref)
    except Exception as e:
        # Provide a very actionable error message
        raise RuntimeError(
            f"Could not resolve {label}='{ref}'.\n"
            f"Most common cause: the logged-in Telegram *user* (SESSION_STRING) "
            f"is NOT a member of that private channel/chat, so Telethon can't see it.\n"
            f"Fix: add that user account to the destination channel, then restart.\n"
            f"Original error: {type(e).__name__}: {e}"
        )


def safe_preview(text: str, limit: int = 180) -> str:
    t = (text or "").replace("\n", " ").strip()
    return t[:limit] + ("…" if len(t) > limit else "")


# ----------------------------
# Main
# ----------------------------
async def main():
    # Required env vars
    api_id = int(env_required("API_ID"))
    api_hash = env_required("API_HASH")
    session_string = env_required("SESSION_STRING")

    source_raw = env_required("SOURCE_CHAT")   # e.g. @intellectia_1_bot_bot or numeric id
    dest_raw = env_required("DEST_CHAT")       # e.g. -1003724596299 (DT Relay channel id)

    source_ref = parse_chat_ref(source_raw)
    dest_ref = parse_chat_ref(dest_raw)

    log.info("Starting userbot...")
    log.info(f"Listening for messages from: {source_raw}")
    log.info(f"Forwarding to: {dest_raw}")

    client = TelegramClient(StringSession(session_string), api_id, api_hash)

    await client.connect()
    if not await client.is_user_authorized():
        raise RuntimeError(
            "Telethon session is not authorized. "
            "You need to regenerate SESSION_STRING (logged in) and update Railway."
        )

    me = await client.get_me()
    log.info(f"Userbot connected as: {getattr(me, 'first_name', '')} {getattr(me, 'last_name', '')}".strip())

    # IMPORTANT: build cache so ids like -100... resolve reliably
    log.info("Building dialog cache (this can take a few seconds)...")
    idx = await build_dialog_index(client)
    log.info(f"Dialog cache built. Entries: {len(idx)}")

    # Resolve entities from cache
    source_entity = await resolve_entity(client, source_ref, idx, "SOURCE_CHAT")
    dest_entity = await resolve_entity(client, dest_ref, idx, "DEST_CHAT")

    log.info("Resolved SOURCE_CHAT and DEST_CHAT successfully.")
    log.info("Forwarder is live.")

    @client.on(events.NewMessage(chats=source_entity))
    async def handler(event):
        try:
            msg = event.message
            # Forward the entire message (keeps media/formatting)
            await client.forward_messages(dest_entity, msg)
            log.info(f"Forwarded: {safe_preview(msg.message)}")
        except Exception as e:
            log.exception(f"Forward failed: {type(e).__name__}: {e}")

    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        log.error(str(e))
        raise
