"""
Main bot entry point - sets up handlers and starts bot
"""

import logging
from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CommandHandler,
)

from .config import BOT_TOKEN
from .handlers import check_message, handle_new_members, handle_message_reaction
from .filters import list_filters

logger = logging.getLogger(__name__)

# Telegram Bot Initialization
updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher
job_queue = updater.job_queue


def main():
    """Initialize and start the bot"""
    logger.info("Starting bot...")
    
    # /filters - Lists all available custom filters
    dp.add_handler(CommandHandler("filters", list_filters))

    # Handler: New member joins - Security checks for suspicious users
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, handle_new_members))

    # Handler: Message reactions (emoji) - Ban suspicious users who only react
    # this isnt supported in tg 13, need to update entire bot and upgrade package
    # dp.add_handler(MessageReactionHandler(handle_message_reaction))

    # Handler: All message types - Main security and filter processing
    dp.add_handler(MessageHandler(
        Filters.all,
        check_message
    ))

    # Start polling (non-blocking)
    updater.start_polling()
    logger.info("Bot started and polling")

