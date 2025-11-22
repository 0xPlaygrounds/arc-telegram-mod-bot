"""
Filter and command handling - responses to user triggers
"""

import os
import json
import re
import asyncio
import logging
from typing import List
from telegram.ext import CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .config import (
    FILTERS_FILE,
    METRICS_FILE,
    NEWS_FILE,
    MEDIA_FOLDER,
    WHITELIST_FILTERS,
)
from .moderation import delete_message_safe
from api.arclan_turing import chat_endpoint
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# Load filters
def load_filters(file_path):
    """Load filters from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

FILTERS = load_filters(FILTERS_FILE)


# Load metrics 
def load_metrics(file_path):
    """Load metrics from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

METRICS = load_metrics(METRICS_FILE)


class ArcLanRequest(BaseModel):
    message: str
    telegram_user_id: str
    telegram_username: str
    conversation_history: str = ""


async def handle_arclan_command_async(user_message: str, telegram_user_id: str, telegram_username: str, conversation_history=""):    
    """Handle /arclan command asynchronously"""
    request_data = ArcLanRequest(
        message=user_message,
        telegram_user_id=telegram_user_id,
        telegram_username=telegram_username,
        conversation_history=conversation_history
    )
    response = await chat_endpoint(request_data)
    return response.reply


def disallowed_filters(message, context: CallbackContext) -> bool:
    """
    Check if message is a disallowed command and delete if so.
    Returns True if message was deleted, False if allowed.
    """
    message_text = message.text
    chat_id = message.chat_id
    message_id = message.message_id

    # Combine your filters with the static whitelist
    allowed_commands = set(WHITELIST_FILTERS + list(FILTERS.keys()))

    if message_text not in allowed_commands:
        delete_message_safe(
            context, chat_id, message_id,
            f"Disallowed message '{message_text}'",
            f"Message ID: {message_id}"
        )
        return True  # message deleted

    return False  # message is allowed


def handle_filter_responses(context: CallbackContext, message, chat_id: int, message_text: str):
    """Handle filter triggers and special commands (/metrics, /growth, /arclan, /posts)"""
    # Filter Responses (apply to all)
    for trigger, filter_data in FILTERS.items():
        normalized_trigger = trigger.strip().lower()
        # use word boundaries but allow underscores to be appended
        pattern = rf'(?<!\w)/?{re.escape(normalized_trigger)}(_\w+)?(?!\w)'
        
        if re.search(pattern, message_text):
            response_text = filter_data.get("response_text", "")
            media_file = filter_data.get("media")
            media_type = filter_data.get("type", "gif").lower()

            if media_file:
                media_path = os.path.join(MEDIA_FOLDER, media_file)
                if os.path.exists(media_path):
                    with open(media_path, 'rb') as media:
                        if media_type in ["gif", "animation"]:
                            context.bot.send_animation(chat_id=chat_id, animation=media, caption=response_text or None)
                        elif media_type == "image":
                            context.bot.send_photo(chat_id=chat_id, photo=media, caption=response_text or None)
                        elif media_type == "video":
                            context.bot.send_video(chat_id=chat_id, video=media, caption=response_text or None)
                elif response_text:
                    message.reply_text(response_text)
            elif response_text:
                message.reply_text(response_text)
            return True  # Handled, stop further processing
    
    # Special commands
    if re.search(r'(?<!\w)/metrics(?!\w)', message_text):
        try:
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            response_text = data.get("last_metrics_message", "⚠️ Metrics message is missing or invalid.")
            message.reply_text(response_text)
        except Exception as e:
            message.reply_text(f"⚠️ Error reading metrics: {e}")
        return True
    
    if re.search(r'(?<!\w)/growth(?!\w)', message_text):
        try:
            with open("filters/growth.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            response_text = data.get("last_weekly_metrics_message", "⚠️ Weekly metrics message is missing or invalid.")
            message.reply_text(response_text)
        except Exception as e:
            message.reply_text(f"⚠️ Error reading weekly metrics: {e}")
        return True
    
    if re.search(r'(?<!\w)/arclan(?!\w)', message_text):
        try:
            # Strip the /arclan command from the message
            user_message = re.sub(r'(?i)^/arclan\s*', '', message_text)

            # Call the async function and wait for reply
            response_text = asyncio.run(
                handle_arclan_command_async(
                    user_message,
                    str(message.from_user.id),
                    message.from_user.username or "",
                    conversation_history=""
                )
            )

            # Send reply in Telegram
            message.reply_text(response_text)
        except Exception:
            message.reply_text("⚠️ Error reaching arclan. Maybe he is sleeping? 😴")
        return True
    
    if re.search(r'(?<!\w)/posts(?!\w)', message_text):
        logger.info("[POSTS] /posts command triggered")
        try:
            with open(NEWS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            posts = data.get("latest_posts", [])
            if not posts:
                logger.debug("[POSTS] No posts available")
                return True  # silently do nothing if empty

            # Logo URL
            logo_url = "https://res.cloudinary.com/dmbswccbh/image/upload/v1757711188/_arc_logo_mintgreen_tgnj0x.png"

            # Build the text message
            from datetime import datetime
            text = "*Latest Posts in the Arc Complex*\n\n"
            for post in posts:
                author = post.get("author", "Unknown")
                summary = post.get("summary", "")
                timestamp_raw = post.get("timestamp")
                timestamp = ""
                if timestamp_raw:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_raw).strftime("%m/%d %H:%M")
                    except Exception:
                        pass

                # Format each post: bold author, italic timestamp, monospaced summary
                text += f"*{author}*"
                if timestamp:
                    text += f" (_{timestamp}_)"
                if summary:
                    text += f"\n`{summary}`"
                text += "\n\n"

            # Build inline buttons for the posts
            keyboard = []
            for post in posts:
                url = post.get("url")
                author = post.get("author", "Unknown")
                if url:
                    keyboard.append([InlineKeyboardButton(f"𝕏 {author}", url=url)])

            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

            # Send as photo with caption (logo + text)
            message.bot.send_photo(
                chat_id=message.chat_id,
                photo=logo_url,
                caption=text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

            logger.info("[POSTS] Inline buttons sent successfully")

        except Exception as e:
            logger.error(f"[POSTS] Failed to send posts: {e}")
        
        return True
    
    return False  # No filter/command matched


def list_filters(update, context: CallbackContext):
    """List all available filters"""
    # Load the latest filters
    with open(FILTERS_FILE, 'r', encoding='utf-8') as f:
        filters = json.load(f)

    # Get and sort all triggers alphabetically (removing leading slash only for sorting)
    sorted_triggers = sorted(filters.keys(), key=lambda k: k.lstrip('/').lower())

    # Re-apply slash only if the original trigger had it
    formatted_triggers = [f"`{trigger}`" for trigger in sorted_triggers]

    # Telegram messages max out at 4096 characters
    response = "*Available Filters:*\n" + "\n".join(formatted_triggers)
    if len(response) > 4000:
        for i in range(0, len(formatted_triggers), 80):  # 80 items per message chunk
            chunk = "*Available Filters:*\n" + "\n".join(formatted_triggers[i:i+80])
            update.message.reply_text(chunk, parse_mode="Markdown")
    else:
        update.message.reply_text(response, parse_mode="Markdown")

