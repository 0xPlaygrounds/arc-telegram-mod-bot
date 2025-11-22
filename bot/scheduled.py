"""
Scheduled job handlers (news, podcasts)
"""

import json
import logging
from datetime import datetime
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup

from .config import NEWS_FILE, PODCASTS_FOLDER, GROUP_CHAT_ID

logger = logging.getLogger(__name__)


def send_news(bot, last_message_id=None):
    """Send news updates to the group"""
    logger.info("[NEWS] Job triggered")
    try:
        # Load latest posts from JSON file
        with open(NEWS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        news_items = data.get("latest_posts", [])
        if not news_items:
            logger.info("[NEWS] No posts available")
            return None

        # Delete previous news message if last_message_id is provided
        if last_message_id:
            try:
                bot.delete_message(chat_id=GROUP_CHAT_ID, message_id=last_message_id)
                logger.info(f"[NEWS] Deleted previous message {last_message_id}")
            except Exception as e:
                logger.warning(f"[NEWS] Could not delete previous message {last_message_id}: {e}")

        # Logo URL
        logo_url = "https://res.cloudinary.com/dmbswccbh/image/upload/v1757711188/arc/_arc_logo_mintgreen_tgnj0x.png"

        # Build the text message
        text = "*What is new in the Arc Complex*\n\n"
        for item in news_items:
            title = item.get("title", item.get("author", "News"))
            summary = item.get("summary", "")
            timestamp_raw = item.get("timestamp")
            timestamp = ""
            if timestamp_raw:
                try:
                    timestamp = datetime.fromisoformat(timestamp_raw).strftime("%m/%d %H:%M")
                except Exception:
                    pass

            # Each post: title bold, timestamp italic, summary monospaced
            text += f"*{title}*"
            if timestamp:
                text += f" (_{timestamp}_)"
            if summary:
                text += f"\n`{summary}`"
            text += "\n\n"

        # Build inline buttons for the posts
        keyboard = []
        for item in news_items:
            url = item.get("url")
            author = item.get("author", "Unknown")
            if url:
                keyboard.append([InlineKeyboardButton(f"𝕏 {author}", url=url)])

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

        # Send as photo with caption (logo + text)
        message = bot.send_photo(
            chat_id=GROUP_CHAT_ID,
            photo=logo_url,
            caption=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

        logger.info(f"[NEWS] Latest news posted successfully, message ID: {message.message_id}")
        return message
    except Exception as e:
        logger.error(f"[NEWS] Failed to post latest news: {e}")
        return None
    

def send_podcasts(bot, last_message_id=None):
    """Send podcast updates to the group"""
    logger.info("[PODCASTS] Job triggered")
    try:
        # Load podcasts from JSON
        with open(PODCASTS_FOLDER, "r", encoding="utf-8") as f:
            data = json.load(f)

        podcasts = []
        if isinstance(data, dict):
            podcasts = data.get("podcasts", [])
        elif isinstance(data, list):
            podcasts = data
        else:
            logger.warning("[PODCASTS] Invalid podcasts data format")
            return None

        # Delete previous podcast message if provided
        if last_message_id:
            try:
                bot.delete_message(chat_id=GROUP_CHAT_ID, message_id=last_message_id)
                logger.info(f"[PODCASTS] Deleted previous message {last_message_id}")
            except Exception as e:
                logger.warning(f"[PODCASTS] Could not delete previous message {last_message_id}: {e}")

        if not podcasts:
            logger.info("[PODCASTS] No podcasts available")
            return None

        # Logo
        logo_url = "https://res.cloudinary.com/dmbswccbh/image/upload/v1757728795/arc/ab67656300005f1fe2aa0d6fc0a3290a1d9e5624_wpq6zz.jpg"

        # Build the text message
        text = "*Latest Podcasts in the Arc Complex*\n\n"
        for pod in podcasts:
            title = pod.get("title", "Podcast")
            url = pod.get("url", "")
            text += f"*{title}*\n"
            if url:
                text += f"[Listen here]({url})\n"
            text += "\n"

        # Build inline buttons for podcasts
        keyboard = [
            [InlineKeyboardButton(pod.get("title", "Podcast")[:25] + "…", url=pod.get("url"))]
            for pod in podcasts if pod.get("url")
        ]
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

        # Send as photo + caption
        message = bot.send_photo(
            chat_id=GROUP_CHAT_ID,
            photo=logo_url,
            caption=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

        logger.info(f"[PODCASTS] Podcasts posted successfully, message ID: {message.message_id}")
        return message
    except Exception as e:
        logger.error(f"[PODCASTS] Failed to post podcasts: {e}")
        return None

