from fastapi import APIRouter
from bot import send_news, updater
from web.backend.db import save_last_news_message, last_news_message
import logging

router = APIRouter()
logger = logging.getLogger("send_news_message")
logger.setLevel(logging.INFO)

@router.post("/trigger/send-news-message")
async def trigger_news():
    try:
        logger.info("Received request to trigger news job")

        # Fetch the last saved news message
        last_record = last_news_message.find_one({"_id": "latest"})
        last_message_id = last_record["message_id"] if last_record else None

        # Call send_news synchronously and pass last_message_id to delete
        message = send_news(updater.bot, last_message_id=last_message_id)

        if message:
            message_id = message.message_id
            # Save/update the last news message in its dedicated collection
            save_last_news_message(message)
            logger.info(f"send_news job completed successfully, message_id: {message_id}")
        else:
            message_id = None
            logger.warning("send_news returned no message")

        return {"status": "ok", "message": "News job triggered", "message_id": message_id}

    except Exception as e:
        logger.error(f"Error in trigger_news endpoint: {e}")
        return {"status": "error", "detail": str(e)}
