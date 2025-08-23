import sqlite3

# Create a connection (auto-creates messages.db if it doesn't exist)
conn = sqlite3.connect("messages.db", check_same_thread=False)
cursor = conn.cursor()

# Create messages table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_message_id INTEGER,
    user_id INTEGER,
    username TEXT,
    text TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    label TEXT
)
""")

conn.commit()
