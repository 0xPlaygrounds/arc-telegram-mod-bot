import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from datetime import datetime, timezone

SHOW_URL = "https://open.spotify.com/show/0zveSdaWCuEex4NI1d9SIl"

async def scrape_spotify_show():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(SHOW_URL, timeout=60000)
        await page.wait_for_selector("a[href*='/episode/']")

        episodes = await page.query_selector_all("a[href*='/episode/']")
        results = []
        for ep in episodes:
            url = await ep.get_attribute("href")
            title = await ep.inner_text()
            results.append({
                "title": title.strip(),
                "url": f"https://open.spotify.com{url}",
                "last_updated": datetime.now(timezone.utc).isoformat()
            })

        await browser.close()
        return results

if __name__ == "__main__":
    try:
        # Attempt to scrape episodes
        all_eps = asyncio.run(scrape_spotify_show())
        
        # Validate that we actually got data
        if not all_eps or len(all_eps) == 0:
            print("⚠️ No episodes found during scraping - keeping existing data unchanged")
            exit(1)
            
        print(f"Successfully scraped {len(all_eps)} episodes")

        # Make sure filters directory exists
        output_dir = Path(__file__).resolve().parent.parent / "filters"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "podcasts.json"

        # Load existing data to preserve message ID if it exists
        existing_data = {}
        if output_file.exists():
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    # Handle case where existing file is just an array
                    if isinstance(existing_data, list):
                        existing_data = {"podcasts": existing_data}
            except (json.JSONDecodeError, Exception) as e:
                print(f"Could not load existing data: {e}")
                existing_data = {}

        # Prepare new data structure
        new_data = {
            "podcasts": all_eps,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

        # Preserve the message ID if it exists
        if "last_podcast_message_id" in existing_data:
            new_data["last_podcast_message_id"] = existing_data["last_podcast_message_id"]

        # Write the updated data
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(all_eps)} episodes to {output_file}")
        if "last_podcast_message_id" in existing_data:
            print(f"✅ Preserved message ID: {existing_data['last_podcast_message_id']}")

    except asyncio.TimeoutError:
        print("Scraping timed out - existing data preserved")
    except Exception as e:
        print(f"Scraping failed: {e} - existing data preserved")