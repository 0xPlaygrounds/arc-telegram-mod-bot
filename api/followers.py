import os
import json
import uuid
from datetime import datetime
import asyncio
from playwright.async_api import async_playwright

X_METRICS_FILE = "data/metrics/daily/x_follower_metrics.json"
X_PROFILE_URL = "https://x.com/arcdotfun"

async def scrape_x_profile(url: str) -> dict:
    xhr_calls = []

    def intercept_response(response):
        if response.request.resource_type == "xhr":
            xhr_calls.append(response)
        return response

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        page.on("response", intercept_response)
        await page.goto(url)
        await page.wait_for_selector("[data-testid='primaryColumn']")
        await page.wait_for_timeout(3000)

        user_calls = [r for r in xhr_calls if "UserBy" in r.url]
        for xhr in user_calls:
            data = await xhr.json()
            return data.get('data', {}).get('user', {}).get('result', None)

    return None

def save_followers_count(count):
    os.makedirs("data", exist_ok=True)
    now_iso = datetime.utcnow().isoformat() + "Z"
    new_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": now_iso,
        "followers": count
    }

    if os.path.exists(X_METRICS_FILE):
        with open(X_METRICS_FILE, "r") as f:
            try:
                data = json.load(f)
                if "entries" not in data:
                    data["entries"] = []
            except json.JSONDecodeError:
                data = {
                    "dataset_name": "x_follower_metrics",
                    "created_at": now_iso,
                    "entries": []
                }
    else:
        data = {
            "dataset_name": "x_follower_metrics",
            "created_at": now_iso,
            "entries": []
        }

    data["entries"].append(new_entry)

    with open(X_METRICS_FILE, "w") as f:
        json.dump(data, f, indent=2)

async def get_x_followers_stats():
    profile = await scrape_x_profile(X_PROFILE_URL)

    if profile and 'legacy' in profile and 'followers_count' in profile['legacy']:
        current_count = profile['legacy']['followers_count']
    else:
        current_count = 0

    save_followers_count(current_count)
    formatted_count = f"{current_count:,}"
    message = f"🐦 X Followers  >>  {formatted_count}"

    return {
        "id": str(uuid.uuid4()),
        "service": "x_followers",
        "data": {
            "followers": current_count,
            "message": message,
        }
    }

def fetch_x_followers():
    return asyncio.get_event_loop().run_until_complete(get_x_followers_stats())

if __name__ == "__main__":
    result = fetch_x_followers()
    print(result["data"]["message"])
