"""
Constants for moderation system - suspicious patterns and keywords
"""

from ..utils import normalize_name

# Suspicious names to auto-ban (normalized)
SUSPICIOUS_USERNAMES = [normalize_name(name) for name in [
    "admin", "administrator", "mod", "moderator", "owner", "founder",
    "dev", "developer", "support", "helpdesk", "staff", "team", "manager",
    "arc", "arc_agent", "arc agent", "arch_agent", "arch agent",
    "arc_admin", "arc admin", "system", "bot", "official",
    "verification", "verify", "verify_account", "verify-account",
    "check", "checker", "t.me", "telegram", "tg", "contact",
    "info", "customer_support", "airdrop", "binance",
    "admin_", "_admin", "mod_", "_mod", "support_", "_support", "arc complex"
]]

# Suspicious phrases in user bios
BIO_PHRASES = [
    "verify in bio", "link in bio", "read bio", "look at bio", "info in bio",
    "check bio", "click bio", "bio link", "more info in bio", "see bio",
    "dm me", "message me", "dm for", "contact in bio", "send me", "message for",
    "free crypto", "free sol", "claim now", "airdrop", "giveaway",
    "50x", "100x", "50-x", "100-x", "50X", "100X", "50X+", "100X+",
    "click link", "follow for", "more info", "join now", "instant profit", "earn crypto",
    "manager", "fourtis", "contact me", "dm", "binance", "listing", "listing partner"
]