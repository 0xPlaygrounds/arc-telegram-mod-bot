from fastapi import APIRouter
from bot import send_podcasts, updater
from web.backend.db import telegram_messages
import logging
from datetime import datetime

router = APIRouter()

logger = logging.getLogger("send_podcasts_message")
logger.setLevel(logging.INFO)

@router.post("/trigger/send-podcasts-message")
async def trigger_podcasts():
    try:
        logger.info("Received request to trigger podcasts job")

        # Fetch the last saved message ID from DB
        last_record = telegram_messages.find_one({"type": "podcasts"}, sort=[("created_at", -1)])
        last_message_id = last_record["message_id"] if last_record else None

        # Call send_podcasts synchronously and pass last_message_id to delete
        message = send_podcasts(updater.bot, last_message_id=last_message_id)

        if message:
            message_id = message.message_id
            # Save the new message ID to DB
            telegram_messages.update_one(
                {"type": "podcasts"},
                {
                    "$set": {
                        "message_id": message_id,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            logger.info(f"send_podcasts job completed successfully, message_id: {message_id}")
        else:
            message_id = None
            logger.warning("send_podcasts returned no message")

        return {"status": "ok", "message": "Podcast job triggered", "message_id": message_id}

    except Exception as e:
        logger.error(f"Error in trigger_podcasts endpoint: {e}")
        return {"status": "error", "detail": str(e)}
