import os
import re
import json
from dotenv import load_dotenv
from telegram import Update, ChatPermissions, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler, JobQueue
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone, time
from combot.scheduled_warnings import messages
from combot.brand_assets import messages as brand_assets_messages

load_dotenv()  # Load .env vars

# Get bot token from environment
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

# File path for filters
FILTERS_FILE = "filters/filters.json"

# File path for accompanying filter media
MEDIA_FOLDER = "media"

# File paths for phrases
BAN_PHRASES_FILE = "blocklists/ban_phrases.txt"
MUTE_PHRASES_FILE = "blocklists/mute_phrases.txt"
DELETE_PHRASES = "blocklists/delete_phrases.txt"
WHITELIST_PHRASES = "whitelists/whitelist_phrases.txt"

# Suspicious names to auto-ban
SUSPICIOUS_USERNAMES = [
    "dev", "developer", "admin", "mod", "owner", "arc", "arc_agent", "arc agent" "arch_agent", "arch agent", "support", "helpdesk", "administrator", "arc admin", "arc_admin"
]

# Mute duration in seconds (3 days)
MUTE_DURATION = 3 * 24 * 60 * 60

# auto spam detection variables
SPAM_THRESHOLD = 3
TIME_WINDOW = timedelta(seconds=15)
SPAM_TRACKER = defaultdict(lambda: deque(maxlen=SPAM_THRESHOLD))
SPAM_RECORDS = {} # stores flagged spam messages for 5 minutes
SPAM_RECORD_DURATION = timedelta(minutes=5)

# combot security message index
message_index = 0

# combot security message
def post_security_message(context: CallbackContext):
    global message_index
    message = messages[message_index]
    sent_message = context.bot.send_message(
        chat_id=GROUP_CHAT_ID, 
        text=message, 
        parse_mode=ParseMode.HTML
    )
    # Pin the sent message
    context.bot.pin_chat_message(
        chat_id=GROUP_CHAT_ID, 
        message_id=sent_message.message_id, 
        disable_notification=True  # No loud ping
    )
    message_index = (message_index + 1) % len(messages)

# combot brand assets
def post_brand_assets(context: CallbackContext):
    for message in brand_assets_messages:
        sent_message = context.bot.send_message(
            chat_id=GROUP_CHAT_ID, 
            text=message, 
            parse_mode=ParseMode.HTML
        )
        # Pin the sent message
        context.bot.pin_chat_message(
            chat_id=GROUP_CHAT_ID, 
            message_id=sent_message.message_id, 
            disable_notification=True
        )

# Load filters as dict
def load_filters(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

FILTERS = load_filters(FILTERS_FILE)

# Load blocklist/whitelisted words/phrases from files
def load_phrases(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip().lower() for line in file.readlines()]

BAN_PHRASES = load_phrases(BAN_PHRASES_FILE)
MUTE_PHRASES = load_phrases(MUTE_PHRASES_FILE)
DELETE_PHRASES = load_phrases(DELETE_PHRASES)
WHITELIST_PHRASES = load_phrases(WHITELIST_PHRASES)

def contains_multiplication_phrase(text):
    text = text.lower()
    # Match digit(s) possibly separated by spaces, next to an 'x'
    pattern = r"(?:\d\s*)+x|x\s*(?:\d\s*)+"
    return re.search(pattern, text)

# check for spam
def check_for_spam(message_text, user_id):
    now = datetime.now(timezone.utc)
    # track user and timestamp of the message
    print(f"Checking for spam: {message_text} from user: {user_id}")
    SPAM_TRACKER[message_text].append((user_id, now))

    # Filter out old messages that are outside of the time window
    recent = [entry for entry in SPAM_TRACKER[message_text] if now - entry[1] <= TIME_WINDOW]
    SPAM_TRACKER[message_text] = deque(recent)

    print(f"Recent messages for '{message_text}': {recent}")

    # If recent messages exceed the threshold, flag as spam
    if len(recent) >= SPAM_THRESHOLD:
        print(f"Spam detected for message: '{message_text}'")
        # flag message as spam and store for 5 minutes in memory
        SPAM_RECORDS[message_text] = now # only store message and timestamp
        spammer_ids = list(set([entry[0] for entry in recent])) # Return list of user_ids to mute
        print(f"Flagging {len(spammer_ids)} users for spam: {spammer_ids}") 
        return spammer_ids
    
    elif recent and len(recent) < SPAM_THRESHOLD and (now - recent[0][1] > TIME_WINDOW):
        # Not spam, expired window – clean it up
        SPAM_TRACKER.pop(message_text, None)

    return []

# check for recent spam and mute spammers
def check_recent_spam(message_text):
    now = datetime.now(timezone.utc)
    timestamp = SPAM_RECORDS.get(message_text)
    if timestamp:
        print(f"Message '{message_text}' is flagged as spam, timestamp: {timestamp}")
    return timestamp and (now - timestamp <= SPAM_RECORD_DURATION)

# clean up spam records
def cleanup_spam_records(context: CallbackContext):
    now = datetime.now(timezone.utc)
    expired_messages = []

    for message_text, timestamp in list(SPAM_RECORDS.items()):
        if now - timestamp > SPAM_RECORD_DURATION:
            expired_messages.append(message_text)
            del SPAM_RECORDS[message_text]
            print(f"[CLEANUP] Removed expired spam record: '{message_text}'")

    if not expired_messages:
        print("[CLEANUP] No expired spam messages to remove.")


def check_message(update: Update, context: CallbackContext):
    should_skip_spam_check = False
    
    message = update.message or update.channel_post  # Handle both messages and channel posts
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user = update.effective_user
    message_text = message.text.lower()

    # Fetch chat admins to prevent acting on their messages
    chat_admins = context.bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in chat_admins]

    if not message or not message.text:
        return  # Skip non-text or unsupported messages
    
    # Ignore messages from admins
    if user_id not in admin_ids:

        # check if message is too short
        if len(message_text.strip()) < 2:
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            return

        # Auto-ban based on suspicious name or username
        name_username = f"{user.full_name} {user.username or ''}".lower()
        if any(keyword in name_username for keyword in SUSPICIOUS_USERNAMES):
            context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            return

        # Check for multiplication spam
        if contains_multiplication_phrase(message_text):
            context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            return
        
        # 1. autospam - check if its a command or matches a filter
        for trigger in FILTERS.keys():
            normalized_trigger = trigger.strip().lower()
            pattern = rf'(?<!\w)/?{re.escape(normalized_trigger)}(_\w+)?(?!\w)'
            if re.search(pattern, message_text):
                should_skip_spam_check = True
                print(f"[SPAM CHECK SKIPPED] Message '{message_text}' matched FILTER trigger: '{trigger}'")
                break

        # 2. autospam - check whitelist
        if not should_skip_spam_check:
            if message_text.strip() in WHITELIST_PHRASES:
                print(f"[SPAM CHECK SKIPPED] Message '{message_text}' matched WHITELIST.")
                should_skip_spam_check = True

        # 3. autospam - check for spam
        if not should_skip_spam_check:
            # Run spam detection only if no FILTER trigger matched
            spammer_ids = check_for_spam(message_text, user_id)

            if check_recent_spam(message_text) and user_id not in spammer_ids:
                spammer_ids.append(user_id)

            if spammer_ids:
                print(f"Muting spammers for message: '{message_text}'")
                for spammer_id in set(spammer_ids):
                    try:
                        until_date = message.date + timedelta(seconds=MUTE_DURATION)
                        permissions = ChatPermissions(can_send_messages=False)
                        context.bot.restrict_chat_member(chat_id=chat_id, user_id=spammer_id, permissions=permissions, until_date=until_date)
                        context.bot.send_message(chat_id=chat_id, text=f"User {spammer_id} has been muted for 3 days.")
                        print(f"Muted user {spammer_id} for spam message.")
                    except Exception as e:
                        print(f"Failed to mute spammer {spammer_id}: {e}")
                return
    
        # Check for banned phrases
        for phrase in BAN_PHRASES:
            # Use word boundaries to match exact words
            if re.search(r'\b' + re.escape(phrase) + r'\b', message_text):
                print(f"[BAN MATCH] Phrase: '{phrase}' matched in message: '{message_text}'")
                context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
                message.reply_text(f"arc angel fallen. {user.first_name} has been banned.")
                return

        # Check for muted phrases
        for phrase in MUTE_PHRASES:
            # Use word boundaries to match exact words
            if re.search(r'\b' + re.escape(phrase) + r'\b', message_text):
                print(f"[MUTE MATCH] Phrase: '{phrase}' matched in message: '{message_text}'")
                until_date = message.date + timedelta(seconds=MUTE_DURATION)
                permissions = ChatPermissions(can_send_messages=False)
                context.bot.restrict_chat_member(chat_id=chat_id, user_id=user.id, permissions=permissions, until_date=until_date)
                message.reply_text(f"{user.first_name} has been muted for 3 days.")
                return

        # Check for deleted phrases
        for phrase in DELETE_PHRASES:
            # Use word boundaries to match exact words
            if re.search(r'\b' + re.escape(phrase) + r'\b', message_text):
                print(f"[DELETE MATCH] Phrase: '{phrase}' matched in message: '{message_text}'")
                context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                return

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

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Get the JobQueue from the dispatcher
    job_queue = updater.job_queue

    # Post security message every 4 hours
    job_queue.run_repeating(post_security_message, interval=4 * 60 * 60, first=0)

    # Post brand assets message at 00:00 and 12:00 (5:00 and 17:00 UTC)
    job_queue.run_daily(post_brand_assets, time=time(hour=5, minute=0))
    job_queue.run_daily(post_brand_assets, time=time(hour=17, minute=0))

    # check for expiring SPAM_RECORDS
    job_queue.run_repeating(cleanup_spam_records, interval=60, first=60)

    # output filters
    dp.add_handler(CommandHandler("filters", list_filters))

    # Add text and command message handler
    dp.add_handler(MessageHandler(Filters.text | Filters.command, check_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
