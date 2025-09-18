from fastapi import APIRouter
from bot import send_podcasts, updater
import logging

router = APIRouter()

logger = logging.getLogger("send_podcasts_message")
logger.setLevel(logging.INFO)

@router.post("/trigger/send-podcasts-message")
async def trigger_podcasts():
    try:
        logger.info("Received request to trigger podcasts job")

        # Call send_podcasts synchronously
        message_id = send_podcasts(updater.bot)

        logger.info(f"send_podcasts job completed successfully, message_id: {message_id}")

        return {"status": "ok", "message": "Podcast job triggered", "message_id": message_id}

    except Exception as e:
        logger.error(f"Error in trigger_podcasts endpoint: {e}")
        return {"status": "error", "detail": str(e)}
