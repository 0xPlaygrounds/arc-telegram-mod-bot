import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from urllib.parse import urlparse

X_PROFILES = [
    "https://x.com/arcdotfun",
    "https://x.com/0thTachi",
    "https://x.com/Kezo_Futura"
]

def format_timestamp(iso_ts):
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        return dt.strftime("%m/%d/%Y %I:%M %p")
    except Exception:
        return "Unknown time"

def extract_username(url):
    parsed = urlparse(url)
    return parsed.path.strip("/").split("/")[0]

async def get_latest_posts_from_profile(url, max_scrolls=10):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(url)
            await page.wait_for_selector("[data-testid='cellInnerDiv']")

            seen_urls = set()
            results = []

            for _ in range(max_scrolls):
                posts = await page.query_selector_all("[data-testid='cellInnerDiv']")
                for post in posts:
                    time_element = await post.query_selector("time")
                    timestamp = await time_element.get_attribute("datetime") if time_element else None
                    if not timestamp:
                        continue

                    link_element = await post.query_selector("a[href*='/status/']")
                    relative_link = await link_element.get_attribute("href") if link_element else None
                    if not relative_link:
                        continue

                    full_link = f"https://x.com{relative_link}"
                    if full_link in seen_urls:
                        continue
                    seen_urls.add(full_link)

                    results.append({
                        "username": extract_username(url),
                        "url": full_link,
                        "timestamp": timestamp
                    })

                # Scroll to bottom and wait for new content
                await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)

            await browser.close()

            # Sort by timestamp descending
            sorted_results = sorted(results, key=lambda x: x["timestamp"], reverse=True)
            return sorted_results

    except Exception as e:
        print(f"Error fetching posts from {url}: {e}")
        return []

async def get_all_latest_posts():
    all_results = []
    for profile in X_PROFILES:
        posts = await get_latest_posts_from_profile(profile)
        all_results.extend(posts)
    return all_results

async def build_latest_posts_message():
    posts = await get_all_latest_posts()
    if not posts:
        return "⚠️ No posts found."

    message_lines = ["🧵 **Latest Posts:**"]
    for post in posts:
        formatted_time = format_timestamp(post['timestamp'])
        username = post['username']
        preview = (
            f"**{username}**  \n"
            f"🕒 {formatted_time}  \n"
            f"[View Post]({post['url']})"
        )
        message_lines.append(preview)

    return "\n\n---\n\n".join(message_lines)

async def main():
    message = await build_latest_posts_message()
    data = {
        "latest_posts_message": message
    }
    try:
        path = Path("filters/posts.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Successfully updated filters/posts.json")
    except Exception as e:
        print(f"Error writing posts.json: {e}")

# ✅ Local test helper:
async def test_profile(profile_url):
    print(f"\n🔍 Testing profile: {profile_url}")
    posts = await get_latest_posts_from_profile(profile_url, count=3)
    for i, post in enumerate(posts, 1):
        print(f"\nPost {i}:")
        print(f"Username: {post['username']}")
        print(f"Time: {format_timestamp(post['timestamp'])}")
        print(f"URL: {post['url']}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Example usage: python script.py test https://x.com/arcdotfun
        test_url = sys.argv[2] if len(sys.argv) > 2 else X_PROFILES[0]
        asyncio.run(test_profile(test_url))
    else:
        asyncio.run(main())
