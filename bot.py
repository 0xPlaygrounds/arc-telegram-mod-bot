import os
import re
import json
import unicodedata
import logging
import threading
from dotenv import load_dotenv
from telegram import (
    Update, 
    ChatPermissions, 
    ParseMode, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Updater, 
    MessageHandler, 
    Filters, 
    CallbackContext, 
    CommandHandler,
)
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone, time
from combot.scheduled_warnings import messages
from combot.brand_assets import messages as brand_assets_messages
from web.backend.db import telegram_messages
from web.backend.db import save_message_to_db

from fastapi import FastAPI, Request

load_dotenv()  # Load .env vars

# Get bot token from environment
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

# -----------------------------
# Telegram Bot Initialization
# -----------------------------
updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher
job_queue = updater.job_queue

# configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# File path for filters
FILTERS_FILE = "filters/filters.json"

# File path for metrics
METRICS_FILE = "filters/metrics.json"

# File path for posts
NEWS_FILE = "filters/posts.json"

# File path for accompanying filter media
MEDIA_FOLDER = "media"

# File path for accompanying podcasts data including last message id
PODCASTS_FOLDER = "filters/podcasts.json"

# File paths for phrases
BAN_PHRASES_FILE = "blocklists/ban_phrases.txt"
MUTE_PHRASES_FILE = "blocklists/mute_phrases.txt"
DELETE_PHRASES_FILE = "blocklists/delete_phrases.txt"
WHITELIST_PHRASES_FILE = "whitelists/whitelist_phrases.txt"

# Whitelisted commands
WHITELIST_FILTERS = ["/growth", "/metrics", "/news", "/posts", "/report"]

# Mute duration in seconds (3 days)
MUTE_DURATION = 3 * 24 * 60 * 60

# Normalization helper must be defined before use
def normalize_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = ''.join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r'[^a-zA-Z0-9_ ]+', '', name)
    name = name.lower()
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)
    return name

# Suspicious names to auto-ban
SUSPICIOUS_USERNAMES = [normalize_name(name) for name in [
    "admin", "administrator", "mod", "moderator", "owner", "founder",
    "dev", "developer", "support", "helpdesk", "staff", "team", "manager",
    "arc", "arc_agent", "arc agent", "arch_agent", "arch agent",
    "arc_admin", "arc admin", "system", "bot", "official",
    "verification", "verify", "verify_account", "verify-account",
    "check", "checker", "t.me", "telegram", "tg", "contact",
    "info", "customer_support",
    "admin_", "_admin", "mod_", "_mod", "support_", "_support", "arc complex"
]]

BIO_PHRASES = [
    "verify in bio", "link in bio", "read bio", "look at bio", "info in bio",
    "check bio", "click bio", "bio link", "more info in bio", "see bio",
    "dm me", "message me", "dm for", "contact in bio", "send me", "message for",
    "free crypto", "free sol", "claim now", "airdrop", "giveaway",
    "50x", "100x", "50-x", "100-x", "50X", "100X", "50X+", "100X+",
    "click link", "follow for", "more info", "join now", "instant profit", "earn crypto"
]

def extract_message(update: Update):
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

def get_admin_ids(context, chat_id):
    # Fetch chat admins dynamically
    chat_admins = context.bot.get_chat_administrators(chat_id)
    return [admin.user.id for admin in chat_admins]

def get_admin_names(context, chat_id):
    """Return a list of normalized full names (lowercased, whitespace cleaned) for all human admins."""
    chat_admins = context.bot.get_chat_administrators(chat_id)
    return [normalize_name(admin.user.full_name) for admin in chat_admins if not admin.user.is_bot]

# combot security message
def post_security_message(context: CallbackContext, index: int):
    try:
        chat = context.bot.get_chat(GROUP_CHAT_ID)
        pinned = chat.pinned_message
        if pinned:
            try:
                context.bot.unpin_chat_message(chat_id=GROUP_CHAT_ID, message_id=pinned.message_id)
            except Exception as e:
                print(f"[Security] Failed to unpin message: {e}")
            try:
                context.bot.delete_message(chat_id=GROUP_CHAT_ID, message_id=pinned.message_id)
            except Exception as e:
                print(f"[Security] Failed to delete message: {e}")
    except Exception as e:
        print(f"[Security] Failed to retrieve chat or pinned message: {e}")
    try:
        message = messages[index]
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
        print(f"[Security] Failed to pin message: {e}")

# combot brand assets
def post_brand_assets(context: CallbackContext, index: int = 0):
    try:
        chat = context.bot.get_chat(GROUP_CHAT_ID)
        pinned = chat.pinned_message
        if pinned:
            try:
                context.bot.unpin_chat_message(chat_id=GROUP_CHAT_ID, message_id=pinned.message_id)
            except Exception as e:
                print(f"[Brand Assets] Failed to unpin message: {e}")
            try:
                context.bot.delete_message(chat_id=GROUP_CHAT_ID, message_id=pinned.message_id)
            except Exception as e:
                print(f"[Brand Assets] Failed to delete message: {e}")
    except Exception as e:
        print(f"[Brand Assets] Failed to retrieve chat or pinned message: {e}")
    try:
        message = brand_assets_messages[index]
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
        print(f"[Brand Assets] Failed to send or pin message: {e}")

# Load filters as dict
def load_filters(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

FILTERS = load_filters(FILTERS_FILE)

# Load metrics 
def load_metrics(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

METRICS = load_metrics(METRICS_FILE)

# Load blocklist/whitelisted words/phrases from files
def load_phrases(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip().lower() for line in file.readlines()]

BAN_PHRASES = load_phrases(BAN_PHRASES_FILE)
MUTE_PHRASES = load_phrases(MUTE_PHRASES_FILE)
DELETE_PHRASES = load_phrases(DELETE_PHRASES_FILE)
WHITELIST_PHRASES = load_phrases(WHITELIST_PHRASES_FILE)

def send_news(bot, last_message_id=None):
    print("[NEWS] Job triggered")
    try:
        # Load latest posts from JSON file
        with open(NEWS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        news_items = data.get("latest_posts", [])
        if not news_items:
            print("[NEWS] No posts available")
            return None

        # Delete previous news message if last_message_id is provided
        if last_message_id:
            try:
                bot.delete_message(chat_id=GROUP_CHAT_ID, message_id=last_message_id)
                print(f"[NEWS] Deleted previous message {last_message_id}")
            except Exception as e:
                print(f"[NEWS] Could not delete previous message {last_message_id}: {e}")

        # Logo URL (top-left)
        logo_url = "https://res.cloudinary.com/dmbswccbh/image/upload/v1757711188/arc/_arc_logo_mintgreen_tgnj0x.png"

        # Build the text message
        text = "*What is new in the Arc Complex*\n\n"  # header
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

        print(f"[NEWS] Latest news posted successfully, message ID: {message.message_id}")
        return message  # return the message object so API can save last_message_id

    except Exception as e:
        print(f"[NEWS] Failed to post latest news: {e}")
        return None
    
def send_podcasts(bot, last_message_id=None):
    print("[PODCASTS] Job triggered")
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
            print("[PODCASTS] Invalid podcasts data format")
            return None

        # Delete previous podcast message if provided
        if last_message_id:
            try:
                bot.delete_message(chat_id=GROUP_CHAT_ID, message_id=last_message_id)
                print(f"[PODCASTS] Deleted previous message {last_message_id}")
            except Exception as e:
                print(f"[PODCASTS] Could not delete previous message {last_message_id}: {e}")

        if not podcasts:
            print("[PODCASTS] No podcasts available")
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

        print(f"[PODCASTS] Podcasts posted successfully, message ID: {message.message_id}")

        return message  # return full message object so API can store ID in DB

    except Exception as e:
        print(f"[PODCASTS] Failed to post podcasts: {e}")
        return None

def contains_multiplication_phrase(text):
    text = text.lower()
    # Match digit(s) possibly separated by spaces, next to an 'x'
    pattern = r"(?:\d\s*)+x|x\s*(?:\d\s*)+"
    return re.search(pattern, text)

def contains_give_sol_phrase(text):
    text = text.lower()
    # Match 'give' followed by a number and then 'sol' or 'solana'
    pattern = r"give\s*(\d+)\s*(sol|solana)"
    return re.search(pattern, text)

def contains_arrows(message_text):
    """
    Returns True if the message contains the → character, False otherwise.
    """
    return "→" in message_text

def disallowed_filters(update, context):
    """
    Deletes a message if it is not in the whitelist filters or custom filters.
    Caller should decide whether to run this check (e.g., only for commands starting with '/').
    """
    message_text = update.message.text
    chat_id = update.message.chat_id
    message_id = update.message.message_id

    # Combine your filters with the static whitelist
    allowed_commands = set(WHITELIST_FILTERS + list(FILTERS.keys()))

    if message_text not in allowed_commands:
        print(f"[DELETE MATCH] Disallowed message '{message_text}' found. Deleting message.")
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        return True  # message deleted

    return False  # message is allowed

def contains_non_x_links(text: str) -> bool:
    # Matches all URLs
    url_pattern = r'(https?://[^\s]+)'
    urls = re.findall(url_pattern, text)

    for url in urls:
        # Allow only Twitter/X links
        if not re.search(r'https?://(www\.)?(x\.com|twitter\.com)/[^\s]+', url):
            return True  # Found a non-X link
    return False

# Suspicious auto-ban function
def handle_new_members(update, context):
    message = update.message
    if message is None or not message.new_chat_members:
        return

    chat_id = message.chat.id
    admin_names = get_admin_names(context, chat_id)

    for new_user in message.new_chat_members:
        name = new_user.full_name or "No Name"
        username = new_user.username or "No Username"
        user_id = new_user.id

        name_info = f"Name: {name}, Username: @{username}" if new_user.username else f"Name: {name} (no username)"
        print(f"[JOIN] {name_info} (ID: {user_id})")

        # Normalize names and usernames
        name_norm = normalize_name(name)
        username_norm = normalize_name(username)

        # Combine normalized name + username for keyword checks
        combined_identity = f"{name_norm} {username_norm}"

        if name_norm in admin_names:
            try:
                context.bot.ban_chat_member(chat_id, user_id)
                print(f"[BANNED] Name '{name}' normalized to '{name_norm}' matches an admin name. Banned for impersonation.")
                continue
            except Exception as e:
                print(f"[ERROR] Failed to ban user with admin name {user_id}: {e}")

        # Check for suspicious keywords
        if name_norm in SUSPICIOUS_USERNAMES or username_norm in SUSPICIOUS_USERNAMES:
            try:
                context.bot.ban_chat_member(chat_id, user_id)
                print(f"[BANNED] Suspicious user auto-banned: {name_info}")
                continue
            except Exception as e:
                print(f"[ERROR] Failed to ban {user_id}: {e}")

        # Check for bio phrases
        if (
            any(keyword in combined_identity for keyword in BIO_PHRASES) or
            contains_multiplication_phrase(combined_identity) or
            contains_non_x_links(combined_identity)
        ):
            try:
                context.bot.ban_chat_member(chat_id, user_id)
                print(f"[BANNED] User with suspicious content on join: {name_info}")
                continue
            except Exception as e:
                print(f"[ERROR] Failed to ban user {user_id}: {e}")

def list_filters(update: Update, context: CallbackContext):
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

def check_message(update: Update, context: CallbackContext):
    message = extract_message(update)
    if not message:
        print("==== No message detected in this update ====")
        return

    # Normalize text/caption for spam/filter checks
    raw_text = message.text or message.caption or ""
    message_text = raw_text.lower()

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user = update.effective_user

    should_skip_spam_check = False

    # --- Detect if message is forwarded ---
    is_forwarded = False
    forward_info = {}
    linked_telegram_channels = []

    # Classic forward detection
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

    # Scan for Telegram group/channel links in text or entities
    def extract_telegram_links(msg):
        links = []
        entities = msg.entities or []
        if getattr(msg, "caption_entities", None):
            entities += msg.caption_entities

        for ent in entities:
            if ent.type in ["text_link", "url"]:
                if ent.type == "text_link":
                    url = ent.url
                else:
                    url = msg.text[ent.offset : ent.offset + ent.length]

                if re.match(r"https?://t\.me/[^\s]+", url):
                    links.append(url)

        # Extra check: scan raw text/caption for any t.me links not marked as entities
        raw_text = msg.text or msg.caption or ""
        extra_links = re.findall(r"https?://t\.me/[^\s]+", raw_text)
        for url in extra_links:
            if url not in links:
                links.append(url)
        return links

    linked_telegram_channels = extract_telegram_links(message)
    if linked_telegram_channels:
        is_forwarded = True
        forward_info["linked_telegram_channels"] = linked_telegram_channels

    # --- Logging ---
    if is_forwarded:
        print(f"[FORWARDED / LINK MESSAGE] From {user.full_name} (@{user.username} | {user_id})")
        for k, v in forward_info.items():
            print(f"  {k}: {v}")
        print(f"  Text/Capt: {raw_text}")
    else:
        print(f"[GROUP MESSAGE] From {user.full_name} (@{user.username} | {user_id})")
        print(f"  Text/Capt: {raw_text}")

    # Fetch chat admins to prevent acting on their messages
    chat_admins = context.bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in chat_admins]

    # Normalize and fetch admin names for impersonation check
    admin_names_normalized = get_admin_names(context, chat_id)
    name_normalized = normalize_name(user.full_name)
    username_normalized = normalize_name(user.username or "")
    
    # Ignore messages from admins
    if user_id not in admin_ids:

        combined_identity = f"{name_normalized} {username_normalized} {message_text.lower()}"

        # Check for suspicious keywords
        if name_normalized in SUSPICIOUS_USERNAMES or username_normalized in SUSPICIOUS_USERNAMES:
            try:
                # ban the user
                context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)

                # delete triggering message
                context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)

                # log result
                print(f"[BANNED] Suspicious keyword match in name/username: {user.full_name} (@{user.username})")
                return
            except Exception as e:
                # log error
                print(f"[ERROR] Failed to ban suspicious user {user_id}: {e}")

        # Check for bio-like phrases
        if (
            any(keyword in combined_identity for keyword in BIO_PHRASES) or
            contains_multiplication_phrase(combined_identity) or
            contains_non_x_links(combined_identity)
        ):
            try:
                # ban the user
                context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)

                # delete triggering message
                context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)

                # log result
                print(f"[BANNED] Suspicious content detected: {combined_identity}")
                return
            except Exception as e:
                # log error
                print(f"[ERROR] Failed to ban user {user_id}: {e}")

        # Check for impersonation
        if name_normalized in admin_names_normalized:
            try:
                # ban the user
                context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)

                # delete triggering message
                context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)

                # log result
                print(f"[BANNED] Impersonation detected: {user.full_name} matched an admin name")
                return
            except Exception as e:
                # log error
                print(f"[ERROR] Failed to ban impersonator {user_id}: {e}")

        # check if message is too short
        if len(message_text.strip()) < 2:
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            return
        
        # Delete message if it contains non-X links
        if contains_non_x_links(message.text):
            print(f"[LINK FILTER] Message from user {user_id} contains non-X links. Deleting.")
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            return

        # Check for multiplication spam
        if contains_multiplication_phrase(message_text):
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            return
        
        # Check for "give x sol" or "give x solana" spam
        if contains_give_sol_phrase(message_text):
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            return
        
        if contains_arrows(message_text):
            print(f"[BAN MATCH] Arrow '→' found in message: '{message_text}'")
            context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            return
        
        # Check for disallowed commands (only if it starts with '/')
        if message_text.startswith("/"):
            if disallowed_filters(update, context):
                # Message was deleted, no further processing needed
                return

        # Normalize the message
        normalized = message_text.strip().lower()

        # Check for banned phrases (exact match only)
        for phrase in BAN_PHRASES:
            if normalized == phrase.lower():
                try:
                    # ban the user
                    context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)

                    # delete triggering message
                    context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)

                    # log result
                    print(f"[BANNED] Exact match: '{phrase}' in message '{message_text}' from user {user.id}")

                except Exception as e:
                    # log error
                    print(f"[ERROR] Failed to ban/delete user {user.id} for banned phrase '{phrase}': {e}")

                return  # Stop further processing

        # Check for muted phrases (exact match only)
        for phrase in MUTE_PHRASES:
            if normalized == phrase.lower():
                print(f"[MUTE MATCH] Exact phrase: '{phrase}' matched in message: '{message_text}'")
                until_date = message.date + timedelta(seconds=MUTE_DURATION)
                permissions = ChatPermissions(can_send_messages=False)

                try:
                    context.bot.restrict_chat_member(
                        chat_id=chat_id, 
                        user_id=user.id, 
                        permissions=permissions, 
                        until_date=until_date
                    )
                    print(f"Muted user {user.id} until {until_date}")
                except Exception as e:
                    print(f"Failed to mute user {user.id}: {e}")

                try:
                    message.reply_text(f"{user.first_name} has been muted for 3 days.")
                except Exception as e:
                    print(f"Failed to send mute reply: {e}")

                return  # Stop further processing

        # Check for deleted phrases (exact match only)
        for phrase in DELETE_PHRASES:
            if normalized == phrase.lower():
                print(f"[DELETE MATCH] Exact phrase: '{phrase}' matched in message: '{message_text}'")

                try:
                    context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                    print(f"Deleted message {message.message_id} from user {user.id}")
                except Exception as e:
                    print(f"Failed to delete message {message.message_id}: {e}")

                return  # Stop further processing
            
    # Determine if message should be saved
    is_admin = user_id in admin_ids
    is_custom_command = (
        re.search(r'(?<!\w)/metrics(?!\w)', message_text) or
        re.search(r'(?<!\w)/growth(?!\w)', message_text) or
        re.search(r'(?<!\w)/news(?!\w)', message_text) or
        any(re.search(rf'(?<!\w)/?{re.escape(trigger)}(_\w+)?(?!\w)', message_text)
            for trigger in FILTERS.keys())
    )

    if not is_admin and not is_custom_command:
        existing_doc = telegram_messages.find_one({"text": message.text})
        if existing_doc:
            # Increment usage counter for duplicates
            telegram_messages.update_one(
                {"_id": existing_doc["_id"]},
                {"$inc": {"usage_count": 1}}
            )
            print(f"[DB] Message exists, incremented usage_count: '{message.text[:30]}...'")
        else:
            # Save new message
            save_message_to_db(message)
    else:
        if is_admin:
            print(f"[SKIP] Message from admin {user_id} not saved: '{message_text[:30]}...'")

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
            return  # Respond only once
        
    if re.search(r'(?<!\w)/metrics(?!\w)', message_text):
        try:
            with open("filters/metrics.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            response_text = data.get("last_metrics_message", "⚠️ Metrics message is missing or invalid.")
            message.reply_text(response_text)
        except Exception as e:
            message.reply_text(f"⚠️ Error reading metrics: {e}")
        return
    
    if re.search(r'(?<!\w)/growth(?!\w)', message_text):
        try:
            with open("filters/growth.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            response_text = data.get("last_weekly_metrics_message", "⚠️ Weekly metrics message is missing or invalid.")
            message.reply_text(response_text)
        except Exception as e:
            message.reply_text(f"⚠️ Error reading weekly metrics: {e}")
        return
    
    if re.search(r'(?<!\w)/posts(?!\w)', message_text):
        print("[POSTS] /posts command triggered")
        try:
            # Use the same NEWS_FILE variable
            with open(NEWS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            posts = data.get("latest_posts", [])
            if not posts:
                print("[POSTS] No posts available")
                return  # silently do nothing if empty

            # Logo URL (top-left)
            logo_url = "https://res.cloudinary.com/dmbswccbh/image/upload/v1757711188/_arc_logo_mintgreen_tgnj0x.png"

            # Build the text message
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

            print("[POSTS] Inline buttons sent successfully")

        except Exception as e:
            # fail silently, but log for debugging
            print(f"[POSTS] Failed to send posts: {e}")
            return

def main():
    logger.info("Starting bot...")

    # Scheduled jobs
    job_queue.run_daily(lambda context: post_security_message(context, 0), time=time(hour=8, minute=0))  
    job_queue.run_daily(lambda context: post_security_message(context, 1), time=time(hour=16, minute=0))
    job_queue.run_daily(post_brand_assets, time=time(hour=0, minute=0))
    
    # Handlers
    dp.add_handler(CommandHandler("filters", list_filters))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, handle_new_members))
    dp.add_handler(MessageHandler(Filters.text | Filters.command, check_message))

    # Start polling (non-blocking)
    updater.start_polling()
    logger.info("Bot started and polling")