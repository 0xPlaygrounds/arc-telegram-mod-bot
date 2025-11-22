"""
Main moderation check orchestration
"""

import logging
from typing import List
from telegram.ext import CallbackContext

from ..utils import normalize_name
from ..blocklists import BAN_PATTERNS, MUTE_PATTERNS, DELETE_PATTERNS, BAN_PHRASES, MUTE_PHRASES, DELETE_PHRASES
from .actions import ban_and_delete_message, delete_message_safe, mute_user
from .patterns import (
    contains_multiplication_phrase, 
    contains_give_sol_phrase, 
    contains_arrows, 
    contains_non_x_links,
    contains_suspicious_keyword
)
from .validators import is_username_valid, is_impersonating_admin
from .constants import SUSPICIOUS_USERNAMES

logger = logging.getLogger(__name__)


def check_user_moderation(context: CallbackContext, chat_id: int, user_id: int, user, 
                         message, message_text: str, media_type: str, 
                         admin_ids: List[int], admin_names_normalized: List[str]) -> bool:
    """
    Perform all moderation checks for non-admin users.
    
    Returns:
        True if message processing should stop (user was banned/muted/message deleted)
    """
    # Construct full name & username explicitly
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    name_normalized = normalize_name(full_name)
    username_normalized = normalize_name(user.username or "")

    # Delete any media from non-admins
    if media_type:
        delete_message_safe(
            context, chat_id, message.message_id,
            f"{media_type} from non-admin",
            f"{full_name} (@{user.username or 'N/A'} | ID: {user_id})"
        )
        return True

    # Check for suspicious keywords or dot in name/username
    if (
        contains_suspicious_keyword(name_normalized, SUSPICIOUS_USERNAMES) or
        contains_suspicious_keyword(username_normalized, SUSPICIOUS_USERNAMES) or
        name_normalized == "." or
        username_normalized == "."
    ):
        ban_and_delete_message(
            context, chat_id, user_id, message.message_id,
            "Suspicious keyword or dot in name/username",
            f"{full_name} (@{user.username})"
        )
        return True

    # Check for missing or hidden username
    if not is_username_valid(user.username):
        ban_and_delete_message(
            context, chat_id, user_id, message.message_id,
            "User has missing or hidden username",
            f"{full_name} (ID: {user_id})"
        )
        return True

    # Check for impersonation
    if is_impersonating_admin(name_normalized, admin_names_normalized):
        ban_and_delete_message(
            context, chat_id, user_id, message.message_id,
            "Impersonation detected: matched an admin name",
            f"{full_name} (@{user.username})"
        )
        return True

    # Check if message is too short
    if len(message_text.strip()) < 2:
        delete_message_safe(
            context, chat_id, message.message_id, 
            "Message too short (< 2 chars)", 
            f"User {user_id}"
        )
        return True
    
    # Delete message if it contains non-X links
    if contains_non_x_links(message.text):
        delete_message_safe(
            context, chat_id, message.message_id,
            "Message contains non-X links",
            f"User {user_id}"
        )
        return True

    # Check for multiplication spam
    if contains_multiplication_phrase(message_text):
        delete_message_safe(
            context, chat_id, message.message_id, 
            "Multiplication spam detected", 
            f"User {user_id}"
        )
        return True
    
    # Check for "give x sol" or "give x solana" spam
    if contains_give_sol_phrase(message_text):
        delete_message_safe(
            context, chat_id, message.message_id, 
            "Give sol spam detected", 
            f"User {user_id}"
        )
        return True
    
    # Check for arrow character (ban)
    if contains_arrows(message_text):
        ban_and_delete_message(
            context, chat_id, user.id, message.message_id,
            f"Arrow '→' found in message",
            f"{full_name} (@{user.username})"
        )
        return True
    
    # Check for disallowed commands (only if it starts with '/')
    if message_text.startswith("/"):
        from ..filters import disallowed_filters
        if disallowed_filters(message, context):
            return True

    # Check blocklists (BAN, MUTE, DELETE)
    normalized = message_text.strip().lower()
    
    # Check for banned phrases (pre-compiled regex patterns)
    for i, pattern in enumerate(BAN_PATTERNS):
        if pattern.search(normalized):
            phrase = BAN_PHRASES[i]
            ban_and_delete_message(
                context, chat_id, user.id, message.message_id,
                f"Phrase found: '{phrase}' in message",
                f"User {user.id}: '{message_text[:50]}...'"
            )
            return True

    # Check for muted phrases (pre-compiled regex patterns)
    for i, pattern in enumerate(MUTE_PATTERNS):
        if pattern.search(normalized):
            phrase = MUTE_PHRASES[i]
            logger.warning(f"[MUTE MATCH] Phrase found: '{phrase}' in message: '{message_text}'")
            mute_user(
                context, chat_id, user.id, user.first_name, message,
                f"Phrase found: '{phrase}'"
            )
            return True

    # Check for deleted phrases (pre-compiled regex patterns)
    for i, pattern in enumerate(DELETE_PATTERNS):
        if pattern.search(normalized):
            phrase = DELETE_PHRASES[i]
            delete_message_safe(
                context, chat_id, message.message_id,
                f"Phrase found: '{phrase}' in message",
                f"User {user.id}: '{message_text[:50]}...'"
            )
            return True
    
    return False  # No moderation action taken, continue processing