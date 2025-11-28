"""
Pattern detection utilities for spam and suspicious content
UPDATED: Added fuzzy matching to prevent blocklist bypasses via special characters and typos
"""

import re
import unicodedata

def contains_multiplication_phrase(text: str) -> bool:
    """Detect multiplication spam like '2x', 'x3', etc."""
    if not text:
        return False
    text = text.lower()
    pattern = r"(?:\d\s*)+x|x\s*(?:\d\s*)+"
    return bool(re.search(pattern, text))


def contains_give_sol_phrase(text: str) -> bool:
    """Detect 'give x sol' spam pattern"""
    if not text:
        return False
    text = text.lower()
    pattern = r"give\s*(\d+)\s*(sol|solana)"
    return bool(re.search(pattern, text))


def contains_arrows(text: str) -> bool:
    """Detect arrow character in message"""
    if not text:
        return False
    return "→" in text


def contains_non_x_links(text: str) -> bool:
    """Check if text contains non-X/Twitter links"""
    if not text:
        return False
    url_pattern = r'(https?://[^\s]+)'
    urls = re.findall(url_pattern, text)
    for url in urls:
        if not re.search(r'https?://(www\.)?(x\.com|twitter\.com)/[^\s]+', url):
            return True
    return False


def contains_suspicious_keyword(text: str, suspicious_list: list) -> bool:
    """Check if text contains suspicious keyword with word boundaries"""
    if not text:
        return False
    for keyword in suspicious_list:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False