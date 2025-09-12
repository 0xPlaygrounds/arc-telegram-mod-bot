import os
import json
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Load bearer token
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
if not BEARER_TOKEN:
    raise ValueError("X_BEARER_TOKEN is not set in your environment")

HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}
POSTS_FILE = "filters/posts.json"


def get_tweet_id(url: str) -> str | None:
    """Extract tweet ID from X URL"""
    path = urlparse(url).path
    parts = path.strip("/").split("/")
    if len(parts) >= 3 and parts[-2] == "status":
        return parts[-1]
    return None


def fetch_tweet_data(tweet_id: str) -> dict | None:
    """Fetch tweet text and media from X API v2"""
    url = f"https://api.twitter.com/2/tweets/{tweet_id}"
    params = {
        "tweet.fields": "created_at,text",
        "expansions": "attachments.media_keys",
        "media.fields": "url,type"
    }
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code != 200:
        print(f"Error fetching tweet {tweet_id}: {resp.status_code} {resp.text}")
        return None

    data = resp.json()
    tweet_data = data.get("data", {})
    includes = data.get("includes", {})

    summary = tweet_data.get("text", "")

    # Default empty image
    image_url = ""
    media_list = includes.get("media", [])
    if media_list:
        for media in media_list:
            if media.get("type") == "photo":
                image_url = media.get("url", "")
                break

    return {"summary": summary, "image_url": image_url}


def update_posts_json():
    """Update posts.json with latest tweet summaries and images"""
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        posts = json.load(f).get("latest_posts", [])

    for post in posts:
        tweet_url = post.get("url", "")
        tweet_id = get_tweet_id(tweet_url)
        if not tweet_id:
            print(f"[WARN] Skipping invalid URL: {tweet_url}")
            continue

        data = fetch_tweet_data(tweet_id)
        if not data:
            print(f"[WARN] Failed to fetch data for tweet {tweet_id}")
            continue

        post["summary"] = data["summary"]
        post["image_url"] = data["image_url"]

    # Save updated posts.json
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"latest_posts": posts}, f, indent=2, ensure_ascii=False)

    print("[INFO] posts.json updated successfully!")


if __name__ == "__main__":
    update_posts_json()
