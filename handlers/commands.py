from telegram import Update
from telegram.ext import CallbackContext
from utils.file_loaders import load_json
from config import FILTERS_FILE

def list_filters(update: Update, context: CallbackContext):
    filters = load_json(FILTERS_FILE)
    sorted_triggers = sorted(filters.keys(), key=lambda k: k.lstrip('/').lower())
    formatted_triggers = [f"`{trigger}`" for trigger in sorted_triggers]

    # Split messages to avoid Telegram 4096 char limit
    response = "*Available Filters:*\n" + "\n".join(formatted_triggers)
    if len(response) > 4000:
        for i in range(0, len(formatted_triggers), 80):
            chunk = "*Available Filters:*\n" + "\n".join(formatted_triggers[i:i+80])
            update.message.reply_text(chunk, parse_mode="Markdown")
    else:
        update.message.reply_text(response, parse_mode="Markdown")
