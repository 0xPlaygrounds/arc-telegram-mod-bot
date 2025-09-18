import os
from dotenv import load_dotenv
from telegram import Bot, Update, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
import threading
import time

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

MIDDLEWARE_BOT_TOKEN = os.getenv("MIDDLEWARE_BOT_TOKEN", "").strip()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

BUY_BOT_GIF = "media/deluge/arc_gif.mp4"

# Separate instance of bot using the main group chat bot
main_bot = Bot(token=BOT_TOKEN)

# -----------------------------
# Handlers
# -----------------------------
def handle_say_command(update: Update, context: CallbackContext):
    message = update.message or update.channel_post
    if not message:
        return

    text = message.text[5:].strip()
    if text:
        try:
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
        except Exception as e:
            print(f"Failed to delete /say command: {e}")

        try:
            main_bot.send_message(chat_id=GROUP_CHAT_ID, text=text, parse_mode=ParseMode.HTML)
            print(f"Relayed /say command: {text}")
        except Exception as e:
            print(f"Failed to send /say message to main group: {e}")


def handle_buy_command(update: Update, context: CallbackContext):
    message = update.message or update.channel_post
    if not message:
        return

    text = message.text[5:].strip()
    if text:
        try:
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
        except Exception as e:
            print(f"Failed to delete /buy command: {e}")

        try:
            with open(BUY_BOT_GIF, "rb") as video:
                main_bot.send_video(
                    chat_id=GROUP_CHAT_ID,
                    video=video,
                    caption=text,
                    parse_mode=ParseMode.HTML,
                    supports_streaming=True
                )
            print(f"Relayed /buy command with video caption: {text}")
        except Exception as e:
            print(f"Failed to send /buy video message to main group: {e}")


# -----------------------------
# Main polling function
# -----------------------------
def main():
    if not MIDDLEWARE_BOT_TOKEN:
        raise ValueError("MIDDLEWARE_BOT_TOKEN is not set!")

    updater = Updater(MIDDLEWARE_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.regex('^/say '), handle_say_command))
    dp.add_handler(MessageHandler(Filters.regex('^/buy '), handle_buy_command))

    updater.start_polling()
    print("Middleware bot started and polling in background thread")
    updater.idle()


# -----------------------------
# Start bot in background thread
# -----------------------------
def start_bot():
    threading.Thread(target=main, daemon=True).start()


# -----------------------------
# Run standalone
# -----------------------------
if __name__ == "__main__":
    start_bot()
    while True:
        time.sleep(60)
