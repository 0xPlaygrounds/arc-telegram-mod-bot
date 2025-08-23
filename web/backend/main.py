from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db import telegram_messages
from bson.objectid import ObjectId
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/messages")
def get_messages():
    """
    Fetch last 100 messages, sorted by timestamp descending
    """
    try:
        docs_cursor = telegram_messages.find().sort("timestamp", -1).limit(100)
        docs_list = list(docs_cursor)
        logger.info(f"Fetched {len(docs_list)} messages from MongoDB")

        messages = []
        for doc in docs_list:
            messages.append({
                "id": str(doc["_id"]),           # MongoDB ObjectId as string
                "username": doc.get("username"),
                "text": doc.get("text"),
                "label": doc.get("label")
            })
        logger.info("Returning messages JSON")
        return messages
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/label/{msg_id}/{label}")
def label_message(msg_id: str, label: str):
    """
    Set a label for a specific message by MongoDB _id
    """
    try:
        logger.info(f"Labeling message {msg_id} with label '{label}'")
        result = telegram_messages.update_one(
            {"_id": ObjectId(msg_id)},
            {"$set": {"label": label}}
        )
        if result.matched_count == 0:
            logger.warning(f"Message {msg_id} not found for labeling")
            raise HTTPException(status_code=404, detail="Message not found")
        logger.info(f"Message {msg_id} labeled successfully")
        return {"status": "ok", "id": msg_id, "label": label}
    except Exception as e:
        logger.error(f"Error labeling message {msg_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
