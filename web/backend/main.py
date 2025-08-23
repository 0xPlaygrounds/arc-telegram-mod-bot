from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import conn, cursor

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
    cursor.execute("SELECT id, username, text, label FROM messages ORDER BY id DESC LIMIT 100")
    rows = cursor.fetchall()
    return [{"id": r[0], "username": r[1], "text": r[2], "label": r[3]} for r in rows]

@app.post("/label/{msg_id}/{label}")
def label_message(msg_id: int, label: str):
    cursor.execute("UPDATE messages SET label=? WHERE id=?", (label, msg_id))
    conn.commit()
    return {"status": "ok", "id": msg_id, "label": label}
