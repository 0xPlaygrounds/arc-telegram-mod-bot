# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from web.backend.db import telegram_messages
from bson.objectid import ObjectId

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
        docs = telegram_messages.find().sort("timestamp", -1).limit(100)
        messages = []
        for doc in docs:
            messages.append({
                "id": str(doc["_id"]),           # MongoDB ObjectId as string
                "username": doc.get("username"),
                "text": doc.get("text"),
                "label": doc.get("label")
            })
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/label/{msg_id}/{label}")
def label_message(msg_id: str, label: str):
    """
    Set a label for a specific message by MongoDB _id
    """
    try:
        result = telegram_messages.update_one(
            {"_id": ObjectId(msg_id)},
            {"$set": {"label": label}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Message not found")
        return {"status": "ok", "id": msg_id, "label": label}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
