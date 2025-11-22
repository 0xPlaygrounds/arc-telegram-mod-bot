"""
Main event handlers for the bot
"""

import re
import logging
from typing import List
from telegram import Update
from telegram.ext import CallbackContext

from .utils import (
    extract_message,
    get_media_type,
    detect_forward_info,
    log_message_received,
    normalize_name,
)
from .admin import get_admin_data
from .moderation import (
    handle_bot_spam,
    check_user_moderation,
    contains_suspicious_keyword,
    check_suspicious_bio,
    SUSPICIOUS_USERNAMES,
)
from .filters import handle_filter_responses, FILTERS
from web.backend.db import telegram_messages, save_message_to_db

logger = logging.getLogger(__name__)


def save_message_if_needed(message, message_text: str, user_id: int, admin_ids: List[int], filters_dict: dict):
    """Save message to DB if needed (not admin, not custom command)"""
    is_admin = user_id in admin_ids
    is_custom_command = (
        re.search(r'(?<!\w)/metrics(?!\w)', message_text) or
        re.search(r'(?<!\w)/growth(?!\w)', message_text) or
        re.search(r'(?<!\w)/news(?!\w)', message_text) or
        any(re.search(rf'(?<!\w)/?{re.escape(trigger)}(_\w+)?(?!\w)', message_text)
            for trigger in filters_dict.keys())
    )

    if not is_admin and not is_custom_command:
        existing_doc = telegram_messages.find_one({"text": message.text})
        if existing_doc:
            # Increment usage counter for duplicates
            telegram_messages.update_one(
                {"_id": existing_doc["_id"]},
                {"$inc": {"usage_count": 1}}
            )
            logger.debug(f"[DB] Message exists, incremented usage_count: '{message.text[:30]}...'")
        else:
            # Save new message
            save_message_to_db(message)
    else:
        if is_admin:
            logger.debug(f"[SKIP] Message from admin {user_id} not saved: '{message_text[:30]}...'")


def check_message(update: Update, context: CallbackContext):
    """Main message handler - orchestrates all message processing"""
    message = extract_message(update)
    if not message:
        logger.debug("==== No message detected in this update ====")
        return
    
    # Handle bot spam immediately
    if handle_bot_spam(message, context):
        return

    # Prepare message data
    raw_text = message.text or message.caption or ""
    message_text = raw_text.lower()
    media_type = get_media_type(message)
    is_forwarded, forward_info = detect_forward_info(message)
    
    # Get user and chat info
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user = update.effective_user
    
    # Log message
    log_message_received(message, user, user_id, media_type, is_forwarded, forward_info, raw_text)
    
    # Get admin data (cached)
    admin_ids, admin_names_normalized = get_admin_data(context, chat_id)
    
    # Perform moderation checks for non-admins
    if user_id not in admin_ids:
        if check_user_moderation(
            context, chat_id, user_id, user, message, message_text, 
            media_type, admin_ids, admin_names_normalized
        ):
            return  # Message was handled by moderation, stop processing
    
    # Save message if needed
    save_message_if_needed(message, message_text, user_id, admin_ids, FILTERS)
    
    # Handle filter responses and special commands
    handle_filter_responses(context, message, chat_id, message_text)


def handle_new_members(update, context):
    """Handle new member joins - perform security checks"""
    message = update.message
    if message is None or not message.new_chat_members:
        return

    chat_id = message.chat.id
    _, admin_names = get_admin_data(context, chat_id)

    for new_user in message.new_chat_members:
        name = new_user.full_name or "No Name"
        username = new_user.username
        user_id = new_user.id 

        name_info = f"Name: {name}, Username: @{username}" if username else f"Name: {name} (no username)"
        logger.info(f"[JOIN] {name_info} (ID: {user_id})")

        # Normalize names and usernames
        name_norm = normalize_name(name)
        username_norm = normalize_name(username) if username else ""

        # Check 1: Admin impersonation
        if name_norm in admin_names:
            try:
                context.bot.ban_chat_member(chat_id, user_id)
                logger.warning(f"[BANNED] Admin impersonation: '{name}' (normalized: '{name_norm}') | {name_info} (ID: {user_id})")
                continue
            except Exception as e:
                logger.error(f"[ERROR] Failed to ban user for admin impersonation {user_id}: {e}")

        # Check 2: Suspicious keywords or dot using whole word matching
        ban_reason = None
        if contains_suspicious_keyword(name_norm, SUSPICIOUS_USERNAMES):
            ban_reason = f"Suspicious name '{name_norm}' in blocklist"
        elif contains_suspicious_keyword(username_norm, SUSPICIOUS_USERNAMES):
            ban_reason = f"Suspicious username '{username_norm}' in blocklist"
        elif name_norm == ".":
            ban_reason = "Name is single dot"
        elif username_norm == ".":
            ban_reason = "Username is single dot"
        elif not username:
            ban_reason = "No username (hidden or missing)"
        elif username.lower() == "hidden":
            ban_reason = "Username is 'hidden'"

        if ban_reason:
            try:
                context.bot.ban_chat_member(chat_id, user_id)
                logger.warning(f"[BANNED] {ban_reason} | {name_info} (ID: {user_id})")
                continue
            except Exception as e:
                logger.error(f"[ERROR] Failed to ban {user_id} for '{ban_reason}': {e}")

        # Check 3: Suspicious bio content
        should_ban, violations = check_suspicious_bio(new_user.bio)
        if should_ban:
            try:
                context.bot.ban_chat_member(chat_id, user_id)
                logger.warning(f"[BANNED] Disallowed Bio Detected ({', '.join(violations)}) | {name_info} (ID: {user_id})")
                continue
            except Exception as e:
                logger.error(f"[ERROR] Failed to ban user {user_id}: {e}")

        # new user passed all checks
        logger.info(f"[JOIN APPROVED] User passed all security checks: {name_info} (ID: {user_id})")


def handle_message_reaction(update: Update, context: CallbackContext):
    """Handle emoji reactions and ban suspicious users"""
    # message_reaction_updated is the correct attribute
    if not hasattr(update, 'message_reaction_updated'):
        return
    
    message_reaction = update.message_reaction_updated
    if not message_reaction:
        return
    
    user = message_reaction.user
    chat_id = message_reaction.chat.id
    
    # Skip if no user info
    if not user:
        return
    
    user_id = user.id
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = user.username
    
    # Get admin IDs (cached) to skip admin reactions
    admin_ids, _ = get_admin_data(context, chat_id)
    
    # Skip admins
    if user_id in admin_ids:
        return
    
    # Normalize name and username
    name_normalized = normalize_name(full_name)
    username_normalized = normalize_name(username or "")
    
    logger.info(f"[REACTION] From {full_name} (@{username or 'N/A'} | ID: {user_id})")
    
    # Check for suspicious usernames
    ban_reason = None
    if any(susp in name_normalized for susp in SUSPICIOUS_USERNAMES):
        ban_reason = f"Suspicious name '{name_normalized}'"
    elif any(susp in username_normalized for susp in SUSPICIOUS_USERNAMES):
        ban_reason = f"Suspicious username '{username_normalized}'"
    elif name_normalized == ".":
        ban_reason = "Name is single dot"
    elif not username or username.lower() == "hidden":
        ban_reason = "No/hidden username"
    
    if ban_reason:
        try:
            context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            logger.warning(f"[BANNED] {ban_reason} | {full_name} (@{username or 'N/A'} | ID: {user_id})")
        except Exception as e:
            logger.error(f"[ERROR] Failed to ban user for reaction: {e}")