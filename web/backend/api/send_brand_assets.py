from fastapi import APIRouter
from bot import updater
from web.backend.db import save_last_brand_assets_message, last_brand_assets_message
from telegram import ParseMode
import logging
import os

router = APIRouter()
logger = logging.getLogger("send_brand_assets")
logger.setLevel(logging.INFO)

GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

message_1 = """<b>arc_BRAND_ASSETS</b>

dear complex,

feel free to use these for your content, posts, and MEMES.

- logos with transparent backgrounds  
- wordmark  
- vector files  
- banners  
- gifs  

find <a href="https://drive.google.com/drive/folders/1_YcVZLHifPU8tBgXJ8Ecbb8vEnNONcKD"><b><i>here</i></b></a> - and we shall keep updating these.  
So make sure you <b>BOOKMARK</b> it."""

@router.post("/trigger/send-brand-assets")
async def trigger_brand_assets():
    try:
        logger.info("Received request to trigger brand assets job")

        # Fetch the last saved brand assets message
        last_record = last_brand_assets_message.find_one({"_id": "latest"})
        last_message_id = last_record["message_id"] if last_record else None

        # Unpin and delete the previous brand assets message if it exists
        if last_message_id:
            try:
                updater.bot.unpin_chat_message(chat_id=GROUP_CHAT_ID, message_id=last_message_id)
                logger.info(f"Unpinned previous brand assets message: {last_message_id}")
            except Exception as e:
                logger.warning(f"Failed to unpin previous brand assets message: {e}")
            
            try:
                updater.bot.delete_message(chat_id=GROUP_CHAT_ID, message_id=last_message_id)
                logger.info(f"Deleted previous brand assets message: {last_message_id}")
            except Exception as e:
                logger.warning(f"Failed to delete previous brand assets message: {e}")

        # Send the new brand assets message
        sent_message = updater.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message_1,
            parse_mode=ParseMode.HTML
        )

        if sent_message:
            message_id = sent_message.message_id
            
            # Pin the new message
            try:
                updater.bot.pin_chat_message(
                    chat_id=GROUP_CHAT_ID,
                    message_id=message_id,
                    disable_notification=True
                )
                logger.info(f"Pinned new brand assets message: {message_id}")
            except Exception as e:
                logger.error(f"Failed to pin brand assets message: {e}")
            
            # Save the new message ID to database
            save_last_brand_assets_message(sent_message)
            logger.info(f"Brand assets job completed successfully, message_id: {message_id}")
            
            return {"status": "ok", "message": "Brand assets job triggered", "message_id": message_id}
        else:
            logger.warning("Failed to send brand assets message")
            return {"status": "error", "message": "Failed to send brand assets message"}

    except Exception as e:
        logger.error(f"Error in trigger_brand_assets endpoint: {e}")
        return {"status": "error", "detail": str(e)}