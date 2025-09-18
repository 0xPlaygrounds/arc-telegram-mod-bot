# web/backend/api/send_podcasts_message.py

from fastapi import APIRouter
from bot import send_podcasts, start_bot
import threading
import logging

router = APIRouter()

# Setup logger for this module
logger = logging.getLogger("send_podcasts_message")
logger.setLevel(logging.INFO)

# Ensure the bot is running
start_bot()  # Launch Telegram bot in background if not already running

@router.post("/trigger/send-podcasts-message")
async def trigger_podcasts():
    try:
        logger.info("Received request to trigger podcasts job")

        def run_job():
            try:
                logger.info("Starting send_podcasts job in background thread")
                # Access the updater globally
                from bot import updater
                send_podcasts(updater.bot)  # pass the bot directly
                logger.info("send_podcasts job completed successfully")
            except Exception as e:
                logger.error(f"send_podcasts job failed: {e}")

        # Run in background thread to avoid blocking HTTP response
        threading.Thread(target=run_job, daemon=True).start()

        return {"status": "ok", "message": "Podcast job triggered"}
    except Exception as e:
        logger.error(f"Error in trigger_podcasts endpoint: {e}")
        return {"status": "error", "detail": str(e)}
