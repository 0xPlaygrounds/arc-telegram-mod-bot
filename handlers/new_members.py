from telegram import Update
from telegram.ext import CallbackContext
from utils.normalization import normalize_name

# Import suspicious phrases/constants from config or a separate module
from config import SUSPICIOUS_USERNAMES, BIO_PHRASES

def handle_new_members(update: Update, context: CallbackContext):
    message = update.message
    if not message or not message.new_chat_members:
        return

    chat_id = message.chat.id
    # Fetch normalized admin names
    admin_names = [normalize_name(admin.user.full_name)
                   for admin in context.bot.get_chat_administrators(chat_id)
                   if not admin.user.is_bot]

    for new_user in message.new_chat_members:
        name = new_user.full_name or "No Name"
        username = new_user.username or ""
        user_id = new_user.id
        name_norm = normalize_name(name)
        username_norm = normalize_name(username)

        # Auto-ban if matches admin
        if name_norm in admin_names:
            context.bot.ban_chat_member(chat_id, user_id)
            continue

        # Auto-ban suspicious usernames or bio phrases
        if any(keyword in name_norm or keyword in username_norm for keyword in SUSPICIOUS_USERNAMES + BIO_PHRASES):
            context.bot.ban_chat_member(chat_id, user_id)
