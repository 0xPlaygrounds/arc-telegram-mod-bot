"""
Utility functions for message processing
"""

import re
import unicodedata
import logging

logger = logging.getLogger(__name__)


def normalize_name(name: str) -> str:
    """Normalize name by removing unicode, special chars, normalizing whitespace"""
    if not name:
        return ""
    name = unicodedata.normalize("NFKD", name)
    name = ''.join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r'[^a-zA-Z0-9_ ]+', '', name)
    name = name.lower()
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)
    return name


def get_media_type(message) -> str:
    """Detect media type from message"""
    if message.photo:
        return "PHOTO"
    elif message.video:
        return "VIDEO"
    elif message.document:
        return "DOCUMENT"
    elif message.animation:
        return "GIF/ANIMATION"
    elif message.sticker:
        return "STICKER"
    elif message.voice:
        return "VOICE"
    elif message.video_note:
        return "VIDEO_NOTE"
    return None


def detect_forward_info(message):
    """Detect if message is forwarded and extract forward info"""
    is_forwarded = False
    forward_info = {}
    
    if getattr(message, "forward_date", None):
        is_forwarded = True
        forward_info["forward_date"] = message.forward_date
    
    if getattr(message, "forward_from", None):
        is_forwarded = True
        forward_info["forward_from_user"] = f"{message.forward_from.full_name} (@{message.forward_from.username})"
    
    if getattr(message, "forward_from_chat", None):
        is_forwarded = True
        forward_info["forward_from_chat"] = f"{message.forward_from_chat.title} ({message.forward_from_chat.id})"
    
    if getattr(message, "forward_sender_name", None):
        is_forwarded = True
        forward_info["forward_sender_name"] = message.forward_sender_name
    
    return is_forwarded, forward_info


def log_message_received(message, user, user_id, media_type, is_forwarded, forward_info, raw_text):
    """Log received message with appropriate detail level"""
    media_indicator = f" [{media_type}]" if media_type else ""
    user_info = f"{user.full_name} (@{user.username} | {user_id})"
    
    if is_forwarded:
        logger.info(f"[FORWARDED / LINK MESSAGE]{media_indicator} From {user_info}")
        for k, v in forward_info.items():
            logger.debug(f"  {k}: {v}")
        logger.debug(f"  Text/Capt: {raw_text}")
    else:
        logger.info(f"[GROUP MESSAGE]{media_indicator} From {user_info}")
        logger.debug(f"  Text/Capt: {raw_text}")


def extract_message(update):
    """
    Returns a message-like object from an update,
    handling message, edited_message, channel_post, etc.
    Returns None if no valid message found.
    """
    for attr in ["message", "edited_message", "channel_post", "edited_channel_post"]:
        msg = getattr(update, attr, None)
        if msg:
            return msg
    return None

