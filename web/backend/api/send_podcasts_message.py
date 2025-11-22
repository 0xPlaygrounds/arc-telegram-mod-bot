from fastapi import APIRouter
from bot_main import send_podcasts, updater
from web.backend.db import save_last_podcast_message, last_podcast_message
import logging

router = APIRouter()
logger = logging.getLogger("send_podcasts_message")
logger.setLevel(logging.INFO)

@router.post("/trigger/send-podcasts-message")
async def trigger_podcasts():
    try:
        logger.info("Received request to trigger podcasts job")

        # Fetch the last saved podcast message
        last_record = last_podcast_message.find_one({"_id": "latest"})
        last_message_id = last_record["message_id"] if last_record else None

        # Call send_podcasts synchronously and pass last_message_id to delete
        message = send_podcasts(updater.bot, last_message_id=last_message_id)

        if message:
            message_id = message.message_id
            # Save/update the last podcast message in its dedicated collection
            save_last_podcast_message(message)
            logger.info(f"send_podcasts job completed successfully, message_id: {message_id}")
        else:
            message_id = None
            logger.warning("send_podcasts returned no message")

        return {"status": "ok", "message": "Podcast job triggered", "message_id": message_id}

    except Exception as e:
        logger.error(f"Error in trigger_podcasts endpoint: {e}")
        return {"status": "error", "detail": str(e)}
