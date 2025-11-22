"""
Moderation logic - spam detection, user validation, and moderation actions
"""

import re
import logging
from typing import List, Tuple
from datetime import timedelta
from telegram import ChatPermissions
from telegram.ext import CallbackContext

from .utils import normalize_name
from .blocklists import BAN_PATTERNS, MUTE_PATTERNS, DELETE_PATTERNS, BAN_PHRASES, MUTE_PHRASES, DELETE_PHRASES
from .config import MUTE_DURATION, BOT_SPAM_USERNAMES
from .admin import get_admin_data

logger = logging.getLogger(__name__)

# Suspicious names to auto-ban (normalized)
SUSPICIOUS_USERNAMES = [normalize_name(name) for name in [
    "admin", "administrator", "mod", "moderator", "owner", "founder",
    "dev", "developer", "support", "helpdesk", "staff", "team", "manager",
    "arc", "arc_agent", "arc agent", "arch_agent", "arch agent",
    "arc_admin", "arc admin", "system", "bot", "official",
    "verification", "verify", "verify_account", "verify-account",
    "check", "checker", "t.me", "telegram", "tg", "contact",
    "info", "customer_support", "airdrop", "binance",
    "admin_", "_admin", "mod_", "_mod", "support_", "_support", "arc complex"
]]

BIO_PHRASES = [
    "verify in bio", "link in bio", "read bio", "look at bio", "info in bio",
    "check bio", "click bio", "bio link", "more info in bio", "see bio",
    "dm me", "message me", "dm for", "contact in bio", "send me", "message for",
    "free crypto", "free sol", "claim now", "airdrop", "giveaway",
    "50x", "100x", "50-x", "100-x", "50X", "100X", "50X+", "100X+",
    "click link", "follow for", "more info", "join now", "instant profit", "earn crypto",
    "manager", "fourtis", "contact me", "dm", "binance", "listing", "listing partner"
]


# Spam pattern detection
def contains_multiplication_phrase(text):
    """Detect multiplication spam like '2x', 'x3', etc."""
    text = text.lower()
    pattern = r"(?:\d\s*)+x|x\s*(?:\d\s*)+"
    return re.search(pattern, text)


def contains_give_sol_phrase(text):
    """Detect 'give x sol' spam pattern"""
    text = text.lower()
    pattern = r"give\s*(\d+)\s*(sol|solana)"
    return re.search(pattern, text)


def contains_arrows(message_text):
    """Detect arrow character in message"""
    return "→" in message_text


def contains_non_x_links(text: str) -> bool:
    """Check if text contains non-X/Twitter links"""
    if not text:
        return False
    url_pattern = r'(https?://[^\s]+)'
    urls = re.findall(url_pattern, text)
    for url in urls:
        if not re.search(r'https?://(www\.)?(x\.com|twitter\.com)/[^\s]+', url):
            return True
    return False


def contains_suspicious_keyword(text: str, suspicious_list: list) -> bool:
    """Check if text contains suspicious keyword with word boundaries"""
    if not text:
        return False
    for keyword in suspicious_list:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def check_suspicious_bio(bio_text: str) -> Tuple[bool, List[str]]:
    """Check bio for suspicious content. Returns (should_ban, violations)"""
    detected = []
    bio_cleaned = (bio_text or "").strip().replace("\u200b", "").lower()
    
    if any(keyword in bio_cleaned for keyword in BIO_PHRASES):
        detected.append("bio phrase")
    if contains_multiplication_phrase(bio_cleaned):
        detected.append("multiplication")
    if contains_non_x_links(bio_cleaned):
        detected.append("non-X link")
    
    return (len(detected) > 0, detected)


# Moderation action helpers
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


def handle_bot_spam(message, context: CallbackContext) -> bool:
    """Handle bot spam messages. Returns True if message was spam and handled."""
    if message.from_user and message.from_user.username in BOT_SPAM_USERNAMES:
        delete_message_safe(
            context, message.chat_id, message.message_id,
            f"Bot spam from @{message.from_user.username}",
            f"Message ID: {message.message_id}"
        )
        return True
    return False


def check_user_moderation(context: CallbackContext, chat_id: int, user_id: int, user, 
                         message, message_text: str, media_type: str, 
                         admin_ids: List[int], admin_names_normalized: List[str]) -> bool:
    """
    Perform all moderation checks for non-admin users.
    Returns True if message processing should stop (user was banned/muted/message deleted).
    """
    # Construct full name & username explicitly
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    name_normalized = normalize_name(full_name)
    username_normalized = normalize_name(user.username or "")

    # Bio check for existing members
    try:
        chat_member = context.bot.get_chat_member(chat_id, user_id)
        user_bio = chat_member.user.bio or ""
        should_ban, violations = check_suspicious_bio(user_bio)
        if should_ban:
            ban_and_delete_message(
                context, chat_id, user_id, message.message_id,
                f"Suspicious bio ({', '.join(violations)})",
                f"{full_name} (@{user.username})"
            )
            return True
    except Exception as e:
        logger.error(f"[ERROR] Failed to check bio for user {user_id}: {e}")

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
    if not user.username or (user.username.lower() == "hidden"):
        ban_and_delete_message(
            context, chat_id, user_id, message.message_id,
            "User has missing or hidden username",
            f"{full_name} (ID: {user_id})"
        )
        return True

    # Check for impersonation
    if any(admin_name in name_normalized for admin_name in admin_names_normalized):
        ban_and_delete_message(
            context, chat_id, user_id, message.message_id,
            "Impersonation detected: matched an admin name",
            f"{full_name} (@{user.username})"
        )
        return True

    # Check if message is too short
    if len(message_text.strip()) < 2:
        delete_message_safe(context, chat_id, message.message_id, "Message too short (< 2 chars)", f"User {user_id}")
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
        delete_message_safe(context, chat_id, message.message_id, "Multiplication spam detected", f"User {user_id}")
        return True
    
    # Check for "give x sol" or "give x solana" spam
    if contains_give_sol_phrase(message_text):
        delete_message_safe(context, chat_id, message.message_id, "Give sol spam detected", f"User {user_id}")
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
    # Import here to avoid circular dependency
    if message_text.startswith("/"):
        from .filters import disallowed_filters
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
            until_date = message.date + timedelta(seconds=MUTE_DURATION)
            permissions = ChatPermissions(can_send_messages=False)

            try:
                context.bot.restrict_chat_member(
                    chat_id=chat_id, 
                    user_id=user.id, 
                    permissions=permissions, 
                    until_date=until_date
                )
                logger.info(f"Muted user {user.id} until {until_date}")
            except Exception as e:
                logger.error(f"Failed to mute user {user.id}: {e}")

            try:
                message.reply_text(f"{user.first_name} has been muted for 3 days.")
            except Exception as e:
                logger.error(f"Failed to send mute reply: {e}")

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

