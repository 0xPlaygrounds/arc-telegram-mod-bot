import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

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
                "url": f"https://open.spotify.com{url}"
            })

        await browser.close()
        return results

if __name__ == "__main__":
    all_eps = asyncio.run(scrape_spotify_show())

    # Make sure filters directory exists
    output_dir = Path(__file__).resolve().parent.parent / "filters"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "podcasts.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_eps, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(all_eps)} episodes to {output_file}")
