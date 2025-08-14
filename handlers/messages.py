from telegram.ext import CallbackContext
from telegram import ParseMode
from config import GROUP_CHAT_ID
from combot.scheduled_warnings import messages
from combot.brand_assets import messages as brand_assets_messages

def post_security_message(context: CallbackContext, index: int):
    _send_and_pin(context, messages, index, "[Security]")

def post_brand_assets(context: CallbackContext, index: int = 0):
    _send_and_pin(context, brand_assets_messages, index, "[Brand Assets]")

def _send_and_pin(context: CallbackContext, message_list, index: int, log_prefix: str):
    try:
        chat = context.bot.get_chat(GROUP_CHAT_ID)
        pinned = chat.pinned_message
        if pinned:
            try:
                context.bot.unpin_chat_message(chat_id=GROUP_CHAT_ID, message_id=pinned.message_id)
            except Exception as e:
                print(f"{log_prefix} Failed to unpin: {e}")
            try:
                context.bot.delete_message(chat_id=GROUP_CHAT_ID, message_id=pinned.message_id)
            except Exception as e:
                print(f"{log_prefix} Failed to delete: {e}")

        message = message_list[index]
        sent_message = context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message,
            parse_mode=ParseMode.HTML
        )
        context.bot.pin_chat_message(
            chat_id=GROUP_CHAT_ID,
            message_id=sent_message.message_id,
            disable_notification=True
        )
    except Exception as e:
        print(f"{log_prefix} Failed to send/pin message: {e}")
