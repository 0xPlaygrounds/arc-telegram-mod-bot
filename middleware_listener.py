import os
import re
from dotenv import load_dotenv
from telegram import Update, ParseMode, Bot
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

# Load .env variables
load_dotenv()

# Bot token and group chat ID
MIDDLEWARE_BOT_TOKEN = os.getenv("MIDDLEWARE_BOT_TOKEN")
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

BUY_BOT_GIF = "media/deluge/arc_gif.mp4"

# Separate instance of bot using the main group chat bot
main_bot = Bot(token=BOT_TOKEN)

def handle_say_command(update: Update, context: CallbackContext):
    message = update.message or update.channel_post
    if not message:
        return

    message_text = message.text or ""
    say_message = ""

    if message_text.lower().startswith('/say '):
        say_message = message_text[5:].strip()

    if say_message:
        try:
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
        except Exception as e:
            print(f"Failed to delete /say command: {e}")

        try:
            main_bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=say_message,
                parse_mode=ParseMode.HTML
            )
            print(f"Relayed /say command: {say_message}")
        except Exception as e:
            print(f"Failed to send /say message to main group: {e}")

def handle_buy_command(update: Update, context: CallbackContext):
    message = update.message or update.channel_post
    if not message:
        return

    message_text = message.text or ""
    buy_message = ""

    if message_text.lower().startswith('/buy '):
        buy_message = message_text[5:].strip()

    if buy_message:
        try:
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
        except Exception as e:
            print(f"Failed to delete /buy command: {e}")

        try:
            with open(BUY_BOT_GIF, "rb") as video:
                main_bot.send_video(
                    chat_id=GROUP_CHAT_ID,
                    video=video,
                    caption=buy_message,
                    parse_mode=ParseMode.HTML,
                    supports_streaming=True                )
            print(f"Relayed /buy command with video caption: {buy_message}")
        except Exception as e:
            print(f"Failed to send /buy video message to main group: {e}")

def main():
    updater = Updater(MIDDLEWARE_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.regex('^/say '), handle_say_command))
    dp.add_handler(MessageHandler(Filters.regex('^/buy '), handle_buy_command))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()