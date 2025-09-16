from dotenv import load_dotenv
import os
from pathlib import Path
import requests
import json
import time

# Load .env
project_root = Path(__file__).resolve().parent.parent  # one level up from api/
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Load environment variable
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
USERNAMES = ["arcdotfun", "ryzomeai", "0thTachi", "kezo_futura"]

if not BEARER_TOKEN:
    raise ValueError("Please set your X_BEARER_TOKEN environment variable.")

# Paths
posts_json_path = project_root / "filters" / "posts.json"
user_ids_path = project_root / "filters" / "user_ids.json"
posts_json_path.parent.mkdir(exist_ok=True)

# Load cached user IDs ---
if user_ids_path.exists():
    with open(user_ids_path, "r", encoding="utf-8") as f:
        cached_ids = json.load(f)
else:
    cached_ids = {}

# Get user ID (with cache) ---
def get_user_id(username):
    if username in cached_ids:
        return cached_ids[username]

    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 429:
        print(f"Rate limited on user lookup for {username}")
        return None
    response.raise_for_status()

    user_id = response.json()["data"]["id"]
    cached_ids[username] = user_id

    # Save cache
    with open(user_ids_path, "w", encoding="utf-8") as f:
        json.dump(cached_ids, f, ensure_ascii=False, indent=2)

    return user_id

# Get latest post ---
def get_latest_post(user_id):
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    params = {"max_results": 5, "tweet.fields": "created_at,text,attachments"}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 429:
        print("Rate limited on tweets fetch!")
        return None
    response.raise_for_status()

    data = response.json()
    if "data" in data and len(data["data"]) > 0:
        tweet = data["data"][0]
        image_url = ""
        return {
            "timestamp": tweet["created_at"],
            "url": f"https://x.com/i/status/{tweet['id']}",  # actual tweet URL
            "summary": tweet.get("text", ""),
            "image_url": image_url
        }
    return None

def main():
    # Load existing JSON or initialize
    if posts_json_path.exists():
        with open(posts_json_path, "r", encoding="utf-8") as f:
            posts_data = json.load(f)
    else:
        posts_data = {"latest_posts": [], "last_updated_index": 0}

    # Preserve the message ID if it exists
    last_news_message_id = posts_data.get("last_news_message_id")

    # Determine next account to update
    next_index = posts_data.get("last_updated_index", 0) % len(USERNAMES)
    username = USERNAMES[next_index]
    print(f"Updating posts for: {username}")

    try:
        user_id = get_user_id(username)
        if not user_id:
            print(f"Skipping {username} due to rate limit / missing ID")
            return

        time.sleep(1)  # delay
        post = get_latest_post(user_id)
        if not post:
            print(f"No post found for {username}")
            return

        post["author"] = username

        # Update or append in JSON
        updated = False
        for i, rec in enumerate(posts_data["latest_posts"]):
            if rec["author"].lower() == username.lower():
                posts_data["latest_posts"][i] = post
                updated = True
                break
        if not updated:
            posts_data["latest_posts"].append(post)

        # Update last_updated_index
        posts_data["last_updated_index"] = (next_index + 1) % len(USERNAMES)

        # Restore the message ID if it existed
        if last_news_message_id is not None:
            posts_data["last_news_message_id"] = last_news_message_id
            print(f"Preserved message ID: {last_news_message_id}")

        # Write JSON
        with open(posts_json_path, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, ensure_ascii=False, indent=2)

        print(f"Successfully updated posts for {username}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed for {username}: {e}")
    except Exception as e:
        print(f"Unexpected error for {username}: {e}")

if __name__ == "__main__":
    main()