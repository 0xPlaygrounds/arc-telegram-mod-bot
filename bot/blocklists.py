"""
Blocklist management - loading and pattern compilation
UPDATED: Now uses fuzzy matching instead of regex patterns
"""

import logging
from typing import List
from pathlib import Path

from .config import (
    BAN_PHRASES_FILE,
    MUTE_PHRASES_FILE,
    DELETE_PHRASES_FILE,
    WHITELIST_PHRASES_FILE,
)
from .moderation.patterns import compile_enhanced_blocklist_patterns

logger = logging.getLogger(__name__)


def load_phrases(file_path):
    """Load phrases from a file, returning list of lowercased phrases"""
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"Blocklist file not found: {file_path}")
        return []
    
    with open(path, 'r', encoding='utf-8') as file:
        phrases = [line.strip().lower() for line in file.readlines() if line.strip()]
    return phrases


# Load blocklists
BAN_PHRASES = load_phrases(BAN_PHRASES_FILE)
MUTE_PHRASES = load_phrases(MUTE_PHRASES_FILE)
DELETE_PHRASES = load_phrases(DELETE_PHRASES_FILE)
WHITELIST_PHRASES = load_phrases(WHITELIST_PHRASES_FILE)

# Compile enhanced patterns for fuzzy matching (catches obfuscation)
# Returns list of tuples: [(original_phrase, normalized_phrase), ...]
BAN_PATTERNS = compile_enhanced_blocklist_patterns(BAN_PHRASES)
MUTE_PATTERNS = compile_enhanced_blocklist_patterns(MUTE_PHRASES)
DELETE_PATTERNS = compile_enhanced_blocklist_patterns(DELETE_PHRASES)

logger.info(
    f"Loaded fuzzy-match blocklists - "
    f"{len(BAN_PATTERNS)} BAN, "
    f"{len(MUTE_PATTERNS)} MUTE, "
    f"{len(DELETE_PATTERNS)} DELETE"
)