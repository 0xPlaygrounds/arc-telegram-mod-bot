from dotenv import load_dotenv
import os
from pathlib import Path
import requests
import json
import time

# 1️⃣ Load .env from project root if it exists
project_root = Path(__file__).resolve().parent.parent  # one level up from api/
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# 2️⃣ Load environment variable (Railway or local .env)
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
USERNAMES = ["arcdotfun", "ryzomeai", "0thTachi", "kezo_futura"]

if not BEARER_TOKEN:
    raise ValueError("Please set your X_BEARER_TOKEN environment variable (Railway or local .env).")

# Step 1: Get the user ID for a username
def get_user_id(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    
    print(f"🔍 Looking up user ID for @{username}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 429:
        print(f"⚠️ Rate limited on user lookup for {username}. This is unusual for free tier!")
        print(f"Response headers: {dict(response.headers)}")
        return None
    
    response.raise_for_status()
    data = response.json()
    return data["data"]["id"]

# Step 2: Get the most recent post (any type)
def get_latest_post(user_id):
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    params = {
        "max_results": 5,  # Reduced from 10 to save on quota
        "tweet.fields": "created_at,public_metrics"  # Simplified fields
    }
    
    print(f"📱 Fetching tweets for user ID {user_id}...")
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 429:
        print(f"⚠️ Rate limited on tweets fetch! This shouldn't happen with free tier limits.")
        print(f"Response headers: {dict(response.headers)}")
        if 'x-rate-limit-remaining' in response.headers:
            print(f"Rate limit remaining: {response.headers['x-rate-limit-remaining']}")
        if 'x-rate-limit-reset' in response.headers:
            reset_time = int(response.headers['x-rate-limit-reset'])
            print(f"Rate limit resets at: {time.ctime(reset_time)}")
        return None
    
    # Print response for debugging
    if response.status_code != 200:
        print(f"❌ API Error {response.status_code}: {response.text}")
        return None
        
    response.raise_for_status()
    data = response.json()
    
    if "data" in data and len(data["data"]) > 0:
        # Get the first tweet (should be most recent)
        return data["data"][0]
    return None

def main():
    latest_posts_message = "🧵 **Latest Posts:**\n\n"
    errors = []
    
    for username in USERNAMES:
        try:
            print(f"🔄 Fetching {username}...")
            user_id = get_user_id(username)
            print(f"✅ Got user ID for {username}: {user_id}")
            
            # Add a small delay between requests to be respectful
            time.sleep(1)
            
            tweet = get_latest_post(user_id)
            if tweet:
                tweet_url = f"https://x.com/{username}/status/{tweet['id']}"
                latest_posts_message += f"---\n\n**{username}**  \n🕒 {tweet['created_at']}  \n[View Post]({tweet_url})\n\n"
                print(f"✅ Got latest tweet for {username}")
            else:
                latest_posts_message += f"---\n\n**{username}**  \nNo posts found.\n\n"
                print(f"⚠️ No tweets found for {username}")
                
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error fetching {username}: {e}")
            print(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            errors.append(username)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error fetching {username}: {e}")
            errors.append(username)
            
        except Exception as e:
            print(f"❌ Unexpected error fetching {username}: {e}")
            errors.append(username)
    
    if errors:
        print(f"⚠️ Not updating posts.json due to errors for: {', '.join(errors)}")
        return  # exit without writing
    
    # Write to filters/posts.json only if no errors
    posts_json_path = project_root / "filters" / "posts.json"
    posts_json_path.parent.mkdir(exist_ok=True)  # make sure 'filters' folder exists
    with open(posts_json_path, "w", encoding="utf-8") as f:
        json.dump({"latest_posts_message": latest_posts_message.strip()}, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Successfully updated {posts_json_path}")

if __name__ == "__main__":
    main()