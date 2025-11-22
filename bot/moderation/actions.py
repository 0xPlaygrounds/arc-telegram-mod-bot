"""
Moderation actions - ban, mute, delete operations
"""

import logging
from datetime import timedelta
from telegram import ChatPermissions
from telegram.ext import CallbackContext
from ..config import BOT_SPAM_USERNAMES, MUTE_DURATION

logger = logging.getLogger(__name__)


def ban_and_delete_message(context: CallbackContext, chat_id: int, user_id: int, 
                           message_id: int, reason: str, user_info: str = ""):
    """Ban user and delete triggering message"""
    try:
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        logger.warning(f"[BANNED] {reason} | {user_info}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to ban/delete user {user_id} for '{reason}': {e}")


def delete_message_safe(context: CallbackContext, chat_id: int, message_id: int, 
                        reason: str, user_info: str = ""):
    """Delete message safely with error handling"""
    try:
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"[DELETED] {reason} | {user_info}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to delete message {message_id} for '{reason}': {e}")


def mute_user(context: CallbackContext, chat_id: int, user_id: int, 
              user_first_name: str, message, reason: str = ""):
    """Mute user for configured duration"""
    until_date = message.date + timedelta(seconds=MUTE_DURATION)
    permissions = ChatPermissions(can_send_messages=False)
    
    try:
        context.bot.restrict_chat_member(
            chat_id=chat_id, 
            user_id=user_id, 
            permissions=permissions, 
            until_date=until_date
        )
        logger.info(f"[MUTED] User {user_id} until {until_date} | {reason}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to mute user {user_id}: {e}")
        return False
    
    try:
        message.reply_text(f"{user_first_name} has been muted for 3 days.")
    except Exception as e:
        logger.error(f"[ERROR] Failed to send mute reply: {e}")
    
    return True


def handle_bot_spam(message, context: CallbackContext) -> bool:
    """
    Handle bot spam messages.
    
    Returns:
        True if message was spam and handled, False otherwise
    """
    if message.from_user and message.from_user.username in BOT_SPAM_USERNAMES:
        delete_message_safe(
            context, message.chat_id, message.message_id,
            f"Bot spam from @{message.from_user.username}",
            f"Message ID: {message.message_id}"
        )
        return True
    return False