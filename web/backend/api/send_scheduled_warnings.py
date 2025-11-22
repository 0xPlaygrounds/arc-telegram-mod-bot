from fastapi import APIRouter, Query
from bot_main import updater
from web.backend.db import save_last_scheduled_warning_message, last_scheduled_warning_message
from telegram import ParseMode
import logging
import os

router = APIRouter()
logger = logging.getLogger("send_scheduled_warnings")
logger.setLevel(logging.INFO)

GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

message_1 = """<b>Important Security Notice </b>

Arc complex admins will <b>NEVER DM</b> you first.  Ignore and block any unsolicited messages.

- No new launches or airdrops are happening.
- Always verify updates via pinned announcements.
- The user <b><i>Arc complex</i></b> will not post in this group.  Any usernames similar who post in group or DM you - please <b>REPORT</b> and block!
- Be mindful of Ex contributors who may send DMs.
- To obtain a current list of arc admins, please use this command: /adminlist"""

message_2 = """We're seeing increased attempts by scammers impersonating Arc leadership.

<b>IMPORTANT FACTS:</b>

Arc and its team are <b>NOT</b> involved in any "rugging," "scamming," or "shorting" activities. Scammers are creating fake accounts that look similar to our CEO and admins. Any screenshots with talks about manipulating price or special dapps should be reported and are not legitimate. These impersonators may contact you via DM or even post in community spaces.

<b>PROTECT YOURSELF:</b>

Arc admins will <b>NEVER</b> initiate DMs with community members. Be mindful of Ex contributors who may send DMs. All official announcements come <b>ONLY</b> through pinned messages in official channels.

Verify any concerning claims through official channels before taking action.

Immediately report and block any suspicious accounts.

<b>VERIFICATION:</b>

To see the list of legitimate Arc administrators, use: /adminlist

<b>Stay vigilant. Report suspicious activity. Trust only official channels.</b>"""

messages = [message_1, message_2]

@router.post("/trigger/send-scheduled-warning")
async def trigger_scheduled_warning(index: int = Query(0, ge=0, le=1, description="Message index (0 or 1)")):
    try:
        logger.info(f"Received request to trigger scheduled warning job with index {index}")

        # Fetch the last saved scheduled warning message
        last_record = last_scheduled_warning_message.find_one({"_id": "latest"})
        last_message_id = last_record["message_id"] if last_record else None

        # Unpin and delete the previous scheduled warning message if it exists
        if last_message_id:
            try:
                updater.bot.unpin_chat_message(chat_id=GROUP_CHAT_ID, message_id=last_message_id)
                logger.info(f"Unpinned previous scheduled warning message: {last_message_id}")
            except Exception as e:
                logger.warning(f"Failed to unpin previous scheduled warning message: {e}")
            
            try:
                updater.bot.delete_message(chat_id=GROUP_CHAT_ID, message_id=last_message_id)
                logger.info(f"Deleted previous scheduled warning message: {last_message_id}")
            except Exception as e:
                logger.warning(f"Failed to delete previous scheduled warning message: {e}")

        # Send the new scheduled warning message
        sent_message = updater.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=messages[index],
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
                logger.info(f"Pinned new scheduled warning message: {message_id}")
            except Exception as e:
                logger.error(f"Failed to pin scheduled warning message: {e}")
            
            # Save the new message ID to database
            save_last_scheduled_warning_message(sent_message)
            logger.info(f"Scheduled warning job completed successfully, message_id: {message_id}")
            
            return {"status": "ok", "message": f"Scheduled warning {index} triggered", "message_id": message_id}
        else:
            logger.warning("Failed to send scheduled warning message")
            return {"status": "error", "message": "Failed to send scheduled warning message"}

    except Exception as e:
        logger.error(f"Error in trigger_scheduled_warning endpoint: {e}")
        return {"status": "error", "detail": str(e)}