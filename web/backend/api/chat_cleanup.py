from fastapi import APIRouter, HTTPException, Query
from telegram import Bot
import asyncio
import os

router = APIRouter()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set!")

bot = Bot(token=BOT_TOKEN)

# 👇 Usernames to delete messages from (no '@' prefix)
BOT_USERNAMES = ["BuyBot", "MissRose_bot", "GroupHelpBot", "SafeguardRobot", "safeguard"]


@router.post("/chat_cleanup")
async def chat_cleanup(limit: int = Query(1000, ge=10, le=5000)):
    """
    Deletes messages in the group that were sent by usernames listed in BOT_SPAM_USERNAMES.

    Args:
        limit (int): Number of recent messages to scan (default: 1000, max: 5000)

    Returns:
        JSON: Status and number of messages deleted.
    """
    deleted_count = 0

    try:
        print(f"Starting cleanup in chat {GROUP_CHAT_ID} for usernames: {BOT_USERNAMES}")

        async for msg in bot.get_chat_history(chat_id=GROUP_CHAT_ID, limit=limit):
            try:
                if msg.from_user and msg.from_user.username in BOT_USERNAMES:
                    await bot.delete_message(chat_id=GROUP_CHAT_ID, message_id=msg.message_id)
                    deleted_count += 1
                    await asyncio.sleep(0.1)  # avoid Telegram rate limits
            except Exception as e:
                print(f"Skipping message {getattr(msg, 'message_id', '?')}: {e}")

        print(f"✅ Cleanup complete — deleted {deleted_count} messages.")
        return {"status": "ok", "deleted": deleted_count}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {e}")
