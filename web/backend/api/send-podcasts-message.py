# web/backend/api/send_podcasts_message.py

from fastapi import APIRouter
from telegram.ext import CallbackContext
from bot import send_podcasts, updater

router = APIRouter()

@router.post("/trigger/send-podcasts-message")
async def trigger_podcasts():
    try:
        # create a context from the existing bot instance
        context = CallbackContext.from_bot(updater.bot)
        send_podcasts(context)
        return {"status": "ok", "message": "Podcasts posted"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
