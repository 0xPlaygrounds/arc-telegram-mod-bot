"""
Configuration and constants
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Load .env vars

# Bot configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

# File paths
FILTERS_FILE = "filters/filters.json"
METRICS_FILE = "filters/metrics.json"
NEWS_FILE = "filters/posts.json"
MEDIA_FOLDER = "media"
PODCASTS_FOLDER = "filters/podcasts.json"

# Blocklist file paths
BAN_PHRASES_FILE = "blocklists/ban_phrases.txt"
MUTE_PHRASES_FILE = "blocklists/mute_phrases.txt"
DELETE_PHRASES_FILE = "blocklists/delete_phrases.txt"
WHITELIST_PHRASES_FILE = "whitelists/whitelist_phrases.txt"

# Whitelisted commands
WHITELIST_FILTERS = ["/growth", "/metrics", "/news", "/posts", "/report"]

# Bot spam usernames to auto-delete
BOT_SPAM_USERNAMES = ["BuyBot", "MissRose_bot", "GroupHelpBot", "SafeguardRobot", "safeguard"]

# Mute duration in seconds (3 days)
MUTE_DURATION = 3 * 24 * 60 * 60

# Admin cache TTL in seconds
ADMIN_CACHE_TTL = 60

