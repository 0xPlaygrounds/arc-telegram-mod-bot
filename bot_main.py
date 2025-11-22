"""
Main bot entry point - thin wrapper that imports from bot modules
Maintains backward compatibility for existing imports (updater, send_news, send_podcasts)
"""

import logging
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler

# Import from modules
from bot.config import BOT_TOKEN
from bot.handlers import check_message, handle_new_members
from bot.filters import list_filters
from bot.scheduled import send_news, send_podcasts

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot Initialization (exported for backward compatibility with web/backend/main.py)
updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher
job_queue = updater.job_queue

# Export scheduled functions for backward compatibility (used by web/backend/api/*.py)
__all__ = ['updater', 'dp', 'job_queue', 'send_news', 'send_podcasts', 'main']


def main():
    """Initialize and start the bot"""
    logger.info("Starting bot...")
    
    # /filters - Lists all available custom filters
    dp.add_handler(CommandHandler("filters", list_filters))

    # Handler: New member joins - Security checks for suspicious users
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, handle_new_members))

    # Handler: All message types - Main security and filter processing
    dp.add_handler(MessageHandler(
        Filters.all,
        check_message
    ))

    # Start polling (non-blocking)
    updater.start_polling()
    logger.info("Bot started and polling")


if __name__ == "__main__":
    main()
