from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

SPAM_THRESHOLD = 3
TIME_WINDOW = timedelta(seconds=15)
SPAM_TRACKER = defaultdict(lambda: deque(maxlen=SPAM_THRESHOLD))
SPAM_RECORDS = {}
SPAM_RECORD_DURATION = timedelta(minutes=5)

def check_for_spam(message_text, user_id):
    now = datetime.now(timezone.utc)
    SPAM_TRACKER[message_text].append((user_id, now))
    recent = [entry for entry in SPAM_TRACKER[message_text] if now - entry[1] <= TIME_WINDOW]
    SPAM_TRACKER[message_text] = deque(recent)

    if len(recent) >= SPAM_THRESHOLD:
        SPAM_RECORDS[message_text] = now
        return list(set([entry[0] for entry in recent]))
    elif recent and len(recent) < SPAM_THRESHOLD and (now - recent[0][1] > TIME_WINDOW):
        SPAM_TRACKER.pop(message_text, None)
    return []

def check_recent_spam(message_text):
    now = datetime.now(timezone.utc)
    timestamp = SPAM_RECORDS.get(message_text)
    return timestamp and (now - timestamp <= SPAM_RECORD_DURATION)

def cleanup_spam_records():
    now = datetime.now(timezone.utc)
    expired = [msg for msg, ts in list(SPAM_RECORDS.items()) if now - ts > SPAM_RECORD_DURATION]
    for msg in expired:
        del SPAM_RECORDS[msg]
