from fastapi import APIRouter
from bot import send_podcasts, updater
import threading
import logging

router = APIRouter()

logger = logging.getLogger("send_podcasts_message")
logger.setLevel(logging.INFO)

@router.post("/trigger/send-podcasts-message")
async def trigger_podcasts():
    try:
        logger.info("Received request to trigger podcasts job")

        def run_job():
            try:
                logger.info("Starting send_podcasts job in background thread")
                send_podcasts(updater.bot)
                logger.info("send_podcasts job completed successfully")
            except Exception as e:
                logger.error(f"send_podcasts job failed: {e}")

        threading.Thread(target=run_job, daemon=True).start()

        return {"status": "ok", "message": "Podcast job triggered"}
    except Exception as e:
        logger.error(f"Error in trigger_podcasts endpoint: {e}")
        return {"status": "error", "detail": str(e)}
