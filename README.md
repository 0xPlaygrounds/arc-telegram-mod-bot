## arc-telegram-mod-bot

### What it is
A Telegram moderation and content bot for a single group. It auto-moderates spam/phrases, posts scheduled security notices and brand assets, and serves media/text responses via configurable filters.

### Features
- **Auto-moderation**
  - **Admin-safe**: ignores group admins entirely.
  - **Auto-ban usernames**: bans non-admins whose full name/username contains suspicious keywords (e.g., "admin", "mod", "arc", etc.). See `SUSPICIOUS_USERNAMES` in `bot.py`.
  - **Short-message deletion**: deletes messages with length < 2.
  - **Multiplication spam**: deletes messages like "2x", "x3", etc.
  - **Rate-based spam mute**: if ≥ 3 identical messages are sent within 15s, all senders are muted for 3 days; same message stays hot for 5 minutes and mutes late senders too.
  - **Phrase actions** (non-admins only):
    - `blocklists/ban_phrases.txt` → ban sender
    - `blocklists/mute_phrases.txt` → mute sender for 3 days
    - `blocklists/delete_phrases.txt` → delete message
  - **Whitelist bypass**: exact matches in `whitelists/whitelist_phrases.txt` skip spam checks.
- **Content filters** (commands/keywords → responses)
  - Triggers configured in `filters/filters.json`.
  - Responds with text or media from `media/` (video/image/gif).
  - Triggers match with or without a leading slash; an underscore suffix is allowed (e.g., `/ready_ok`).
  - Command `/filters` lists all available triggers.
- **Scheduled posts**
  - Every 4 hours: cycles and pins a security notice from `combot/scheduled_warnings.py`.
  - 05:00 and 17:00 UTC daily: posts and pins brand assets message from `combot/brand_assets.py`.
- **Pinning**: scheduled messages are pinned quietly.

- **Metrics & achievements (optional)**
  - `api/` contains small utilities that fetch and append daily metrics as JSON under `data/metrics/daily/`:
    - `api/telegram.py` → Telegram member count
    - `api/followers.py` → X follower count (headless scrape with Playwright)
    - `api/github.py` → GitHub stars/forks and latest `rig-core` release tag for `REPO`
    - `api/holders.py` → On-chain token holder count via Helius
  - `achievements/` converts these metrics into milestone messages and writes to `data/achievements/*.json`.
  - `api/posts.py` scrapes latest X posts from a few profiles and writes a rich message to `filters/posts.json` (can be used in your filters if desired).

- **Middleware relay bot (optional)**
  - `middleware_listener.py` runs a second bot that listens for `/say` and `/buy` in a channel, deletes the command, and relays into the main group using the primary bot.

### Requirements
- Python 3.x runtime (Railway will install from `requirements.txt`).
- Bot must be added as an admin in your target group with permissions to delete, restrict, ban, and pin.

### Configuration
Set the following environment variables (Railway → Variables):
- `TELEGRAM_BOT_TOKEN`: Bot token from BotFather.
- `GROUP_CHAT_ID`: Your group’s numeric chat ID (supergroups start with `-100`).

Optional, if you use the new modules:
- `REPO`: GitHub `owner/repo` used by `api/github.py`.
- `TOKEN_ADDRESS`: SPL token mint address used by `api/holders.py`.
- `HELIUS_API_KEY`: API key for Helius RPC used by `api/holders.py`.
- `MIDDLEWARE_BOT_TOKEN`: Bot token for `middleware_listener.py`.

Example `.env` (for local runs):
```bash
TELEGRAM_BOT_TOKEN=123456:ABC...
GROUP_CHAT_ID=-1001234567890
```

### Railway deployment
This repo is pre-configured with `railway.json`.
1. Create a new Railway project and connect this repo.
2. Set variables `TELEGRAM_BOT_TOKEN` and `GROUP_CHAT_ID`.
3. Deploy. Railway will run `pip install -r requirements.txt` and then `python bot.py`.
4. Add the bot to your Telegram group as an admin.
5. Check logs on Railway; you should see it start polling.

Notes:
- The bot uses polling; no webhook setup needed.
- Ensure the bot has permissions to ban/restrict/delete/pin or actions will fail.

### Usage
- In the group, use `/filters` to see all configured triggers.
- Use any trigger defined in `filters/filters.json`, e.g. `/ready`, `/arc_begins`, `/which_pill`. Some triggers are plain words (no slash) like `search`.
- Moderation runs automatically for non-admins: bans/mutes/deletes per blocklists, spam muting, short-message deletion, multiplication spam removal.

Optional commands/flows (if enabled):
- `/say <message>` in the middleware channel will be relayed into the main group (requires `middleware_listener.py`).
- `/buy <caption>` in the middleware channel will relay a predefined video with your caption.

### Customize responses
- Edit `filters/filters.json` to add/update triggers. Fields:
  - `response_text`: optional text caption/response.
  - `media`: filename in `media/` (video/image/gif supported).
  - `type`: one of `video`, `image`, `gif`/`animation`, or `text`.
- Place media files in `media/` and reference them by filename.
- Important: the bot loads filters and blocklists at startup. After changing `filters/*.json` or `blocklists/*.txt`, redeploy or restart the bot so changes take effect.

Notes for the new helpers:
- `api/posts.py` writes `filters/posts.json` with a ready-to-post message. You can wire this into your filters or post it manually.

### Moderation lists
- Ban phrases: `blocklists/ban_phrases.txt`
- Mute phrases: `blocklists/mute_phrases.txt`
- Delete-only phrases: `blocklists/delete_phrases.txt`
- Whitelist exact messages: `whitelists/whitelist_phrases.txt`

Each file is line-delimited, matched case-insensitively with word boundaries (exact words).

### Local run (optional)
```bash
pip install -r requirements.txt
# Set TELEGRAM_BOT_TOKEN and GROUP_CHAT_ID in your env or a .env file
python bot.py
```

If you plan to use X scraping helpers (`api/followers.py`, `api/posts.py`), install Playwright browsers once:
```bash
python -m playwright install
```

Run optional utilities locally:
```bash
# X followers (prints a summary and appends JSON under data/metrics/)
python api/followers.py | cat

# Build latest posts message into filters/posts.json
python api/posts.py | cat

# Compute achievements from metrics (writes data/achievements/*.json)
python achievements/github_achievements.py | cat
python achievements/telegram_achievements.py | cat
python achievements/token_holder_achievements.py | cat
python achievements/x_follower_achievements.py | cat
```

Environment for other helpers:
- `api/github.py` requires `REPO` env var.
- `api/holders.py` requires `TOKEN_ADDRESS` and `HELIUS_API_KEY`.

### Operational tips
- If scheduled posts pin too often for your group, adjust intervals in `bot.py` (`post_security_message`, `post_brand_assets`).
- Review `SUSPICIOUS_USERNAMES` in `bot.py` to avoid over-aggressive bans for your community.
- Mute duration is currently 3 days; change `MUTE_DURATION` in `bot.py` to adjust.

Middleware relay bot:
- To run the optional relay, set `MIDDLEWARE_BOT_TOKEN`, `TELEGRAM_BOT_TOKEN`, and `GROUP_CHAT_ID`, then run:
```bash
python middleware_listener.py
```
It listens for `/say` and `/buy` and relays into the main group.

### File map
- `bot.py`: main bot logic, scheduling, moderation, and filters dispatcher
- `filters/filters.json`: trigger → response mapping
- `media/`: media assets referenced by filters
- `blocklists/*.txt`, `whitelists/*.txt`: moderation lists
- `combot/scheduled_warnings.py`: rotating security messages (pinned)
- `combot/brand_assets.py`: daily brand assets message (pinned)
- `api/*`: metric scrapers and post builder (optional)
- `achievements/*`: milestone detectors writing `data/achievements/*.json` (optional)
- `middleware_listener.py`: optional relay bot for `/say` and `/buy`
- `railway.json`: Railway build/run config
- `requirements.txt`: Python deps

### Troubleshooting
- Bot not responding: confirm it’s admin in the target group and that `GROUP_CHAT_ID` matches that group.
- Can’t find chat ID: add the bot to the group, then use a helper like `@userinfobot` or `@getidsbot` to reveal the chat ID, or log updates from a simple script.
- Media not sending: ensure the file exists in `media/` and `type` matches the file kind.
- Phrase lists not applied: restart the bot after editing blocklist/whitelist files.
 - Playwright errors: ensure `python -m playwright install` has been run on the host.
