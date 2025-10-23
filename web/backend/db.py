# web/backend/db.py
from pymongo import MongoClient
from datetime import datetime
import os

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["arc_bot"]

# Collections
telegram_messages = db["telegram_messages"]
last_podcast_message = db["last_podcast_message"]
last_news_message = db["last_news_message"]
last_brand_assets_message = db["last_brand_assets_message"]
last_scheduled_warning_message = db["last_scheduled_warning_message"]

def save_message_to_db(message):
    """
    Save a Telegram message document to MongoDB with full metadata.
    """
    try:
        doc = {
            # Telegram message info
            "tg_message_id": message.message_id,
            "user_id": message.from_user.id if message.from_user else None,
            "username": message.from_user.username if message.from_user else None,
            "text": message.text or message.caption or "",
            
            # Core timestamps
            "timestamp_message": message.date if hasattr(message, "date") else datetime.utcnow(),
            "created_at": datetime.utcnow(),
            
            # Labeling info
            "label": None,
            "label_updated_at": None,
            "label_history": [],  # e.g. [{"label": "spam", "changed_by": "admin", "changed_at": datetime}]
            
            # Manual review info
            "reviewed_by": None,
            
            # AI prediction info
            "ai_prediction": None,
            "ai_confidence": None,
            "ai_model_version": None,
            "prediction_timestamp": None,
            
            # Extra metadata
            "review_status": "pending",  # pending -> ai_predicted -> reviewed
            "source": "telegram",
            "tags": [],
            
            # Usage counter for repeated messages
            "usage_count": 1,

            "blocklist_status": None,
        }

        telegram_messages.insert_one(doc)
        print(f"[DB] Saved message {doc['tg_message_id']} from {doc['username']}")

    except Exception as e:
        print(f"[DB] Failed to save message: {e}")


def save_last_podcast_message(message):
    """
    Save or update the last podcast message in its own collection.
    Always keeps a single document with _id='latest'.
    """
    try:
        last_podcast_message.update_one(
            {"_id": "latest"},
            {
                "$set": {
                    "message_id": message.message_id,
                    "text": message.caption or "",
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        print(f"[DB] Saved last podcast message, message ID: {message.message_id}")
    except Exception as e:
        print(f"[DB] Failed to save last podcast message: {e}")

def save_last_news_message(message):
    """
    Save or update the last news message in its own collection.
    Always keeps a single document with _id='latest'.
    """
    try:
        last_news_message.update_one(
            {"_id": "latest"},
            {
                "$set": {
                    "message_id": message.message_id,
                    "text": message.caption or "",
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        print(f"[DB] Saved last news message, message ID: {message.message_id}")
    except Exception as e:
        print(f"[DB] Failed to save last news message: {e}")

def save_last_brand_assets_message(message):
    """
    Save or update the last brand assets message in its own collection.
    Always keeps a single document with _id='latest'.
    """
    try:
        last_brand_assets_message.update_one(
            {"_id": "latest"},
            {
                "$set": {
                    "message_id": message.message_id,
                    "text": message.text or "",
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        print(f"[DB] Saved last brand assets message, message ID: {message.message_id}")
    except Exception as e:
        print(f"[DB] Failed to save last brand assets message: {e}")

def save_last_scheduled_warning_message(message):
    """
    Save or update the last scheduled warning message in its own collection.
    Always keeps a single document with _id='latest'.
    """
    try:
        last_scheduled_warning_message.update_one(
            {"_id": "latest"},
            {
                "$set": {
                    "message_id": message.message_id,
                    "text": message.text or "",
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        print(f"[DB] Saved last scheduled warning message, message ID: {message.message_id}")
    except Exception as e:
        print(f"[DB] Failed to save last scheduled warning message: {e}")