from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from web.backend.db import telegram_messages
from bson.objectid import ObjectId
from datetime import datetime
import logging
import uvicorn
import os

# -----------------------------
# Setup logging
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web.backend.main")

# -----------------------------
# Initialize FastAPI
# -----------------------------
app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Global 404 handler to suppress stray requests
# -----------------------------
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    logger.debug(f"404 Not Found: {request.url}")
    return JSONResponse(status_code=404, content={"detail": "Not Found"})

# -----------------------------
# Print URL on startup
# -----------------------------
@app.on_event("startup")
async def startup_event():
    port = os.environ.get("PORT", 8080)
    host = "0.0.0.0"
    # Railway provides RAILWAY_STATIC_URL for frontend deployments, otherwise fallback to localhost
    public_url = os.environ.get("RAILWAY_STATIC_URL") or f"http://{host}:{port}"
    print(f"🚀 FastAPI is running on {host}:{port}")
    print(f"🌐 Public URL for frontend use: {public_url}")

# -----------------------------
# Routes
# -----------------------------
@app.get("/messages")
def get_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_key: str = Query("timestamp_message"),  # default sort
    sort_direction: str = Query("desc"),         # "asc" or "desc"
):
    try:
        skip_count = (page - 1) * page_size

        # Determine MongoDB sort order
        mongo_sort_dir = 1 if sort_direction == "asc" else -1

        # Sort by field
        docs_cursor = telegram_messages.find().sort(sort_key, mongo_sort_dir).skip(skip_count).limit(page_size)
        docs_list = list(docs_cursor)

        messages = [
            {
                "id": str(doc["_id"]),
                "username": doc.get("username"),
                "text": doc.get("text"),
                "label": doc.get("label"),
                "ai_prediction": doc.get("ai_prediction"),
                "ai_confidence": doc.get("ai_confidence"),
                "review_status": doc.get("review_status"),
                "usage_count": doc.get("usage_count", 1),
                "tags": doc.get("tags", []),
                "timestamp_message": doc.get("timestamp_message").isoformat() if doc.get("timestamp_message") else None
            }
            for doc in docs_list
        ]

        return {
            "messages": messages,
            "page": page,
            "page_size": page_size,
            "total_count": telegram_messages.count_documents({}),
            "sort_key": sort_key,
            "sort_direction": sort_direction
        }

    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/label/{msg_id}/{label}")
def label_message(msg_id: str, label: str, reviewer_username: str):
    try:
        now = datetime.utcnow()
        logger.info(f"Labeling message {msg_id} with label '{label}' by {reviewer_username}")

        result = telegram_messages.update_one(
            {"_id": ObjectId(msg_id)},
            {
                "$set": {
                    "label": label,
                    "label_updated_at": now,
                    "reviewed_by": reviewer_username,
                    "review_status": "reviewed"
                },
                "$push": {
                    "label_history": {
                        "label": label,
                        "changed_by": reviewer_username,
                        "changed_at": now
                    }
                }
            }
        )
        if result.matched_count == 0:
            logger.warning(f"Message {msg_id} not found for labeling")
            raise HTTPException(status_code=404, detail="Message not found")

        logger.info(f"Message {msg_id} labeled successfully")
        return {"status": "ok", "id": msg_id, "label": label}

    except Exception as e:
        logger.error(f"Error labeling message {msg_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# Run Uvicorn
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Railway assigns this automatically
    uvicorn.run(
        "web.backend.main:app",
        host="0.0.0.0",   # Bind to all interfaces for Railway
        port=port,
        log_level="warning",
        access_log=False
    )
