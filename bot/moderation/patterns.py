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
        '!': 'i', '|': 'l', 'ø': 'o', 'ö': 'o', 'ó': 'o',
        'ò': 'o', 'õ': 'o', 'é': 'e', 'è': 'e', 'ê': 'e',
        'ë': 'e', 'ε': 'e', 'í': 'i', 'ì': 'i', 'î': 'i',
        'ï': 'i', 'á': 'a', 'à': 'a', 'â': 'a', 'ä': 'a',
        'α': 'a', 'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u'
    }
    for char, replacement in substitutions.items():
        text = text.replace(char, replacement)
    
    # Remove ALL non-alphanumeric characters (keeps only a-z)
    text = re.sub(r'[^a-z]', '', text)
    
    return text


def check_fuzzy_match(phrase: str, text: str, threshold: float = 0.65) -> bool:
    """
    Check if phrase appears in text with fuzzy matching.
    Very aggressive matching with vowel-aware tolerance.
    """
    phrase_len = len(phrase)
    if phrase_len == 0:
        return False
    
    # Exact match
    if phrase in text:
        return True
    
    text_len = len(text)
    if text_len < phrase_len * 0.35:
        return False
    
    # Helper: Check if character is a vowel
    def is_vowel(c):
        return c in 'aeiou'
    
    # Method 1: Sliding window with exact phrase length
    for i in range(len(text) - phrase_len + 1):
        window = text[i:i + phrase_len]
        matches = sum(1 for a, b in zip(phrase, window) if a == b)
        if matches / phrase_len >= threshold:
            return True
    
    # Method 2: Sequential matching with flexible window - VOWEL AWARE
    min_len = max(phrase_len - 6, 1)
    max_len = min(phrase_len + 7, text_len)
    
    for i in range(text_len):
        for length in range(min_len, max_len + 1):
            if i + length > text_len:
                continue
            window = text[i:i + length]
            
            phrase_idx = 0
            matches = 0
            consonant_matches = 0
            phrase_consonants = sum(1 for c in phrase if not is_vowel(c))
            
            for char in window:
                if phrase_idx < phrase_len and char == phrase[phrase_idx]:
                    matches += 1
                    if not is_vowel(char):
                        consonant_matches += 1
                    phrase_idx += 1
            
            # Two checks: overall match OR consonant-heavy match
            overall_similarity = matches / phrase_len
            consonant_similarity = consonant_matches / phrase_consonants if phrase_consonants > 0 else 0
            
            if overall_similarity >= threshold or consonant_similarity >= 0.75:
                return True
    
    # Method 3: Extra lenient for short phrases
    if phrase_len <= 6:
        for i in range(text_len):
            for length in range(max(phrase_len - 3, 1), phrase_len + 5):
                if i + length > text_len or length < 1:
                    continue
                window = text[i:i + length]
                
                phrase_idx = 0
                matches = 0
                for char in window:
                    if phrase_idx < phrase_len and char == phrase[phrase_idx]:
                        matches += 1
                        phrase_idx += 1
                
                if matches / phrase_len >= 0.50:  # 50% for short phrases
                    return True
    
    # Method 4: Longer phrases with more tolerance
    if phrase_len > 10:
        for i in range(text_len):
            for length in range(phrase_len - 7, phrase_len + 8):
                if i + length > text_len or length < 1:
                    continue
                window = text[i:i + length]
                
                phrase_idx = 0
                matches = 0
                for char in window:
                    if phrase_idx < phrase_len and char == phrase[phrase_idx]:
                        matches += 1
                        phrase_idx += 1
                
                if matches / phrase_len >= 0.58:  # 58% for longer phrases
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
    normalized_phrase = normalize_text_aggressive(phrase)
    normalized_text = normalize_text_aggressive(text)
    return check_fuzzy_match(normalized_phrase, normalized_text)


def compile_enhanced_blocklist_patterns(phrases: list) -> list:
    """
    Prepare blocklist phrases for fuzzy matching.
    Returns list of tuples: (original_phrase, normalized_phrase)
    
    This replaces regex pattern compilation with normalization prep.
    """
    return [(phrase, normalize_text_aggressive(phrase)) for phrase in phrases]