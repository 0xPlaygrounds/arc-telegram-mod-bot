import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urlparse
from datetime import datetime

X_PROFILES = [
    "https://x.com/0thTachi",
]

def extract_username(url: str) -> str:
    parsed = urlparse(url)
    return parsed.path.strip("/").split("/")[0]

def normalize_tweet_url(url: str) -> str:
    if "/status/" not in url:
        return None
    parts = url.split("/status/")
    tweet_id = parts[1].split("/")[0]
    return f"https://x.com/{parts[0].split('/')[-1]}/status/{tweet_id}"

async def click_latest_tab(page):
    """Try to click the 'Posts' / 'Latest' tab on the profile."""
    try:
        # Different profiles label it differently ("Posts", "Latest", or localized)
        latest_button = await page.query_selector('a[href*="/with_replies"], a:has-text("Posts"), a:has-text("Latest")')
        if latest_button:
            print("🖱️ Clicking Latest/Posts tab...")
            await latest_button.click()
            await page.wait_for_timeout(2000)
    except Exception as e:
        print("⚠️ Could not click Latest tab:", e)

async def scan_timeline_for_urls(page, max_scrolls=20):
    """Scrape tweets in DOM order (newest first)."""
    seen_urls = []
    seen_set = set()
    for scroll in range(max_scrolls):
        print(f"📜 Scroll attempt {scroll+1}/{max_scrolls}")
        articles = await page.query_selector_all('article[role="article"] a[href*="/status/"]')
        for link_elem in articles:
            link = await link_elem.get_attribute("href")
            if link and not any(x in link for x in ["/analytics", "/photo/"]):
                full_link = f"https://x.com{link}" if link.startswith("/") else link
                if full_link not in seen_set:
                    seen_urls.append(full_link)
                    seen_set.add(full_link)
        await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1500)
    return seen_urls

async def scrape_tweet(page, url: str):
    await page.goto(url)
    await page.wait_for_selector('article[role="article"]', timeout=10000)

    article = await page.query_selector('article[role="article"]')
    if not article:
        return None

    # Tweet text
    text_elem = await article.query_selector('[data-testid="tweetText"]')
    tweet_text = await text_elem.inner_text() if text_elem else ""

    # Username
    username_elem = await article.query_selector('div[dir="ltr"] > span')
    username = await username_elem.inner_text() if username_elem else extract_username(url)

    # Timestamp
    time_elem = await article.query_selector('time')
    timestamp = None
    if time_elem:
        ts_attr = await time_elem.get_attribute("datetime")
        if ts_attr:
            try:
                timestamp = datetime.fromisoformat(ts_attr.replace("Z", "+00:00"))
            except Exception:
                timestamp = datetime.now()
    if not timestamp:
        timestamp = datetime.now()

    # Engagement
    replies, retweets, likes = 0, 0, 0
    stats_elems = await article.query_selector_all('[data-testid$="-count"]')
    for elem in stats_elems:
        label = await elem.get_attribute("data-testid")
        count_text = await elem.inner_text()
        try:
            count = int(count_text.replace(",", ""))
        except:
            count = 0
        if label == "reply-count":
            replies = count
        elif label == "retweet-count":
            retweets = count
        elif label == "like-count":
            likes = count

    return {
        "url": url,
        "username": username,
        "text": tweet_text,
        "timestamp": timestamp,
        "replies": replies,
        "retweets": retweets,
        "likes": likes
    }

async def process_profile(profile_url, headless=True, max_scrolls=20):
    print(f"\n🔹 Processing profile: {profile_url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        await page.goto(profile_url)
        await page.wait_for_selector('article[role="article"]', timeout=15000)

        # ✅ Force into Latest tab before scraping
        await click_latest_tab(page)

        tweet_urls = await scan_timeline_for_urls(page, max_scrolls=max_scrolls)
        print(f"Found {len(tweet_urls)} tweet URLs")

        tweets_data = []
        for url in tweet_urls:
            clean_url = normalize_tweet_url(url)
            if not clean_url:
                continue
            print(f"📝 Scraping tweet: {clean_url}")
            tweet_info = await scrape_tweet(page, clean_url)
            if tweet_info:
                tweets_data.append(tweet_info)
                print(f"   @{tweet_info['username']} | {tweet_info['timestamp'].isoformat()} | Likes: {tweet_info['likes']}, Retweets: {tweet_info['retweets']}, Replies: {tweet_info['replies']}")
                print(f"   Text: {tweet_info['text'][:150]}...\n")
            else:
                print("   ⚠️ Tweet could not be scraped")

        await browser.close()

        # Sort tweets newest first
        tweets_data.sort(key=lambda x: x["timestamp"], reverse=True)
        return tweets_data

async def main():
    all_tweets = []
    for profile in X_PROFILES:
        profile_tweets = await process_profile(profile, headless=True, max_scrolls=20)
        all_tweets.extend(profile_tweets)

    print(f"\nTotal tweets collected: {len(all_tweets)}")
    for tweet in all_tweets:
        print(f"{tweet['timestamp'].isoformat()} - @{tweet['username']}: {tweet['text'][:150]}...")

if __name__ == "__main__":
    asyncio.run(main())
