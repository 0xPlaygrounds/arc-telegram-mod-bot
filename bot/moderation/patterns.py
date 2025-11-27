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


# ============================================================================
# NEW FUZZY MATCHING FUNCTIONS FOR BLOCKLIST BYPASS PREVENTION
# ============================================================================

def normalize_text_aggressive(text: str) -> str:
    """
    Aggressively normalize text to catch obfuscation attempts:
    - Removes ALL special characters (_, ^, -, *, etc.)
    - Replaces number substitutions (0→o, 1→i, 3→e, etc.)
    - Removes accents and unicode lookalikes
    - Converts to lowercase
    
    Examples:
        "pri-vate" → "private"
        "mes^sage" → "message"  
        "ad_ded" → "added"
        "sp0t" → "spot"
        "hølders" → "holders"
    """
    if not text:
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Remove accents/diacritics (é→e, ø→o, etc.)
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    
    # Replace common number/symbol substitutions
    substitutions = {
        '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', 
        '7': 't', '8': 'b', '9': 'g', '@': 'a', '$': 's', 
        '!': 'i', '|': 'l'
    }
    for char, replacement in substitutions.items():
        text = text.replace(char, replacement)
    
    # Remove ALL non-alphanumeric characters (keeps only a-z)
    # This strips: _ ^ - * spaces punctuation etc.
    text = re.sub(r'[^a-z]', '', text)
    
    return text


def check_fuzzy_match(phrase: str, text: str, threshold: float = 0.85) -> bool:
    """
    Check if phrase appears in text with fuzzy matching.
    Allows for typos, missing letters, and doubled letters.
    
    Args:
        phrase: The blocklist phrase (normalized)
        text: The message text (normalized)
        threshold: Match threshold (0.85 = 85% of characters must match)
    
    Examples:
        "privategroup" matches "privategro oup" (with typo)
        "specialdrop" matches "specialdropp" (extra letter)
    
    Returns:
        True if phrase fuzzy-matches in text
    """
    phrase_len = len(phrase)
    if phrase_len == 0:
        return False
    
    # First try exact substring match (fastest path)
    if phrase in text:
        return True
    
    # Text too short to contain phrase
    text_len = len(text)
    if text_len < phrase_len * 0.7:
        return False
    
    # Sliding window fuzzy match
    for i in range(len(text) - phrase_len + 1):
        window = text[i:i + phrase_len]
        matches = sum(1 for a, b in zip(phrase, window) if a == b)
        similarity = matches / phrase_len
        
        if similarity >= threshold:
            return True
    
    # Try with length flexibility (for missing/extra chars)
    max_len = min(phrase_len + 3, text_len)
    for i in range(len(text) - phrase_len + 1):
        for length in range(max(phrase_len - 2, 1), max_len + 1):
            if i + length > text_len:
                continue
            window = text[i:i + length]
            # Count how many phrase characters appear in window
            matches = sum(1 for c in phrase if c in window)
            similarity = matches / phrase_len
            
            if similarity >= threshold:
                return True
    
    return False


def check_phrase_in_text(phrase: str, text: str) -> bool:
    """
    Check if blocklist phrase appears in text using normalization + fuzzy matching.
    
    This catches:
    - Exact matches: "private message"
    - Special char insertion: "pri-vate mes^sage"  
    - Number substitution: "pr1vate mess@ge"
    - Typos/missing letters: "privte messge"
    - Doubled letters: "grooup" matching "group"
    
    Args:
        phrase: Original phrase from blocklist (e.g., "private message")
        text: User's message text
    
    Returns:
        True if phrase is found in text (with obfuscation tolerance)
    """
    # Normalize both phrase and text
    normalized_phrase = normalize_text_aggressive(phrase)
    normalized_text = normalize_text_aggressive(text)
    
    # Check fuzzy match
    return check_fuzzy_match(normalized_phrase, normalized_text)


def compile_enhanced_blocklist_patterns(phrases: list) -> list:
    """
    Prepare blocklist phrases for fuzzy matching.
    Returns list of tuples: (original_phrase, normalized_phrase)
    
    This replaces regex pattern compilation with normalization prep.
    """
    return [(phrase, normalize_text_aggressive(phrase)) for phrase in phrases]