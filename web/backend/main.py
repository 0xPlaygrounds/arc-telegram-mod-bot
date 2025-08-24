from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from web.backend.db import telegram_messages
from bson.objectid import ObjectId
from datetime import datetime
import logging
import uvicorn

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
    # Log at DEBUG level only so stray /api requests do not appear in INFO logs
    logger.debug(f"404 Not Found: {request.url}")
    return JSONResponse(status_code=404, content={"detail": "Not Found"})

# -----------------------------
# Routes
# -----------------------------
@app.get("/messages")
def get_messages(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    try:
        skip_count = (page - 1) * page_size
        docs_cursor = telegram_messages.find().sort("timestamp_message", -1).skip(skip_count).limit(page_size)
        docs_list = list(docs_cursor)
        logger.info(f"Fetched {len(docs_list)} messages from MongoDB (page {page}, page_size {page_size})")

        messages = []
        for doc in docs_list:
            messages.append({
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
            })

        return {
            "messages": messages,
            "page": page,
            "page_size": page_size,
            "total_count": telegram_messages.count_documents({})
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
    uvicorn.run(
        "web.backend.main:app",
        host="127.0.0.1",
        port=8080,
        reload=True,
        log_level="warning",  # Only warnings/errors; suppress INFO access logs
        access_log=False      # Disable default HTTP access logs (removes /api 404s)
    )
