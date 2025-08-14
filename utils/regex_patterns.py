import re

# Multiplication phrases (e.g., "3x5" or "5 x 3")
MULTIPLICATION_PATTERN = re.compile(r"(?:\d\s*)+x|x\s*(?:\d\s*)+", re.IGNORECASE)

# Give SOL phrases (e.g., "give 100 sol")
GIVE_SOL_PATTERN = re.compile(r"give\s*(\d+)\s*(sol|solana)", re.IGNORECASE)

# URL detection
URL_PATTERN = re.compile(r'https?://[^\s]+', re.IGNORECASE)

# Allowed X/Twitter links
X_TWITTER_PATTERN = re.compile(r'https?://(www\.)?(x\.com|twitter\.com)/[^\s]+', re.IGNORECASE)
