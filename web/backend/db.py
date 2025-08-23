# web/backend/db.py
from pymongo import MongoClient
from datetime import datetime

# from dotenv import load_dotenv
# import os

# load_dotenv()  # load environment variables from .env

# --- Temporary hardcoded URI for testing only ---
MONGO_URI = "mongodb+srv://arc_bot:pVwneyi8ATuJIM21@cluster0.dvafmmh.mongodb.net/"

# --- Uncomment below for production / env usage ---
# MONGO_URI = os.getenv("MONGO_URI")
# if not MONGO_URI:
#     raise ValueError("MONGO_URI environment variable not set")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["arc_bot"]
telegram_messages = db["telegram_messages"]

def save_message_to_db(message):
    """
    Save a Telegram message document to MongoDB.
    """
    try:
        doc = {
            "tg_message_id": message.message_id,
            "user_id": message.from_user.id if message.from_user else None,
            "username": message.from_user.username if message.from_user else None,
            "text": message.text or message.caption or "",
            "timestamp": message.date if hasattr(message, "date") else datetime.utcnow(),
            "label": None  # optional, can add later
        }
        telegram_messages.insert_one(doc)
        print(f"[DB] Saved message {doc['tg_message_id']} from {doc['username']}")
    except Exception as e:
        print(f"[DB] Failed to save message: {e}")
