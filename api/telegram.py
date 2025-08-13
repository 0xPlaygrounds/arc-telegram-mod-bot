import os
import json
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
DATA_FILE = "data/metrics/daily/telegram_metrics.json"

def load_data():
    """Load the full dataset, return dict with dataset_name, created_at, entries"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
                # Ensure keys exist for backward compatibility
                if "entries" not in data:
                    data = {
                        "dataset_name": "telegram_metrics",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "entries": []
                    }
                return data
            except json.JSONDecodeError:
                pass
    # Return default structure if no file or error
    return {
        "dataset_name": "telegram_metrics",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "entries": []
    }

def save_data(data):
    """Save the full dataset, update created_at timestamp"""
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def log_member_count(count):
    """Append a new member count entry with id and timestamp"""
    data = load_data()
    new_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "member_count": count
    }
    data["entries"].append(new_entry)
    save_data(data)
    return new_entry

def get_latest_member_count():
    """Return the last recorded member count, or 0 if none."""
    data = load_data()
    if data["entries"]:
        return data["entries"][-1]["member_count"]
    return 0

def get_telegram_stats():
    """Fetch current member count, log it, and return formatted message."""
    try:
        current_count = bot.get_chat_member_count(GROUP_CHAT_ID)
        log_member_count(current_count)
        formatted_count = "{:,}".format(current_count)
        return f"👥 Telegram Members  >>  {formatted_count}"
    except Exception as e:
        print(f"Error fetching Telegram stats: {e}")
        return "❌ Error fetching Telegram member count."
