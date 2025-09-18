# web/backend/api/say_command.py
from fastapi import APIRouter, HTTPException
from telegram import Bot, ParseMode
import os

router = APIRouter()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set!")

main_bot = Bot(token=BOT_TOKEN)

@router.post("/say")
async def relay_say_command(text: str):
    """
    Relay a text message to the main Telegram group.
    """
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        main_bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=text,
            parse_mode=ParseMode.HTML
        )
        return {"status": "ok", "message": "Message relayed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to relay /say command: {e}")
