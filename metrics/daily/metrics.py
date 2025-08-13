import sys
from pathlib import Path
import os
import json
import asyncio
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from telegram import Bot
from api.telegram import get_telegram_stats
from api.holders import get_token_stats
from api.github import get_github_stats
from api.followers import get_x_followers_stats

from achievements.github_achievements import check_github_achievements
from achievements.telegram_achievements import check_telegram_achievements
from achievements.token_holder_achievements import check_token_holder_achievements
from achievements.x_follower_achievements import check_x_follower_achievements

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv("GROUP_CHAT_ID")

bot = Bot(token=BOT_TOKEN)

def send_update_to_tg(messages):
    """Sends a combined update message to the Telegram group."""
    full_message = "\n\n".join(messages)
    try:
        bot.send_message(chat_id=CHAT_ID, text=full_message)
    except Exception as e:
        print(f"Failed to send message to Telegram: {e}")
    return full_message

def save_last_metrics_message_as_filter(message):
    """Save the last sent message to /filters/metrics.json, overwriting previous content."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    filters_dir = os.path.join(project_root, "filters")
    os.makedirs(filters_dir, exist_ok=True)

    data = {"last_metrics_message": message}
    metrics_path = os.path.join(filters_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

async def main():
    # Telegram Metrics (sync)
    telegram_message = get_telegram_stats()
        
    # GitHub Metrics (sync)
    github_stats = get_github_stats()

    # Holders Metrics (sync)
    token_stats = get_token_stats()

    # Followers Metrics (async, so await it)
    x_followers_stats = await get_x_followers_stats()

    x_followers_message = x_followers_stats.get("data", {}).get("message", str(x_followers_stats))

    github_achievement_messages = check_github_achievements()
    telegram_achievement_messages = check_telegram_achievements() 
    token_holder_achievement_messages = check_token_holder_achievements()
    x_follower_achievement_messages = check_x_follower_achievements()

    # Create a list of messages
    core_messages = [
        github_stats,
        telegram_message,
        token_stats,
        x_followers_message
    ]

    messages = core_messages.copy()

    if github_achievement_messages or telegram_achievement_messages or token_holder_achievement_messages or x_follower_achievement_messages:
        separator = "────────────" * 3
        messages.append(separator)

    if github_achievement_messages:
        messages.extend(github_achievement_messages)

    if telegram_achievement_messages:
        messages.extend(telegram_achievement_messages)

    if token_holder_achievement_messages:
        messages.extend(token_holder_achievement_messages)

    if x_follower_achievement_messages:
        messages.extend(x_follower_achievement_messages)

    # Send all messages to Telegram (metrics + achievements)
    send_update_to_tg(messages)

    # Save only core metrics message (without achievements) as filter
    core_full_message = "\n\n".join(core_messages)
    save_last_metrics_message_as_filter(core_full_message)

if __name__ == "__main__":
    asyncio.run(main())
