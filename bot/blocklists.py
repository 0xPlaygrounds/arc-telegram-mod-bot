"""
Blocklist management - loading and pattern compilation
"""

import re
import logging
from typing import List
from pathlib import Path

from .config import (
    BAN_PHRASES_FILE,
    MUTE_PHRASES_FILE,
    DELETE_PHRASES_FILE,
    WHITELIST_PHRASES_FILE,
)

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


def compile_blocklist_patterns(phrases: List[str]) -> List[re.Pattern]:
    """Pre-compile regex patterns with word boundaries for blocklist phrases"""
    patterns = []
    for phrase in phrases:
        pattern = r'\b' + re.escape(phrase) + r'\b'
        patterns.append(re.compile(pattern, re.IGNORECASE))
    return patterns


# Load blocklists
BAN_PHRASES = load_phrases(BAN_PHRASES_FILE)
MUTE_PHRASES = load_phrases(MUTE_PHRASES_FILE)
DELETE_PHRASES = load_phrases(DELETE_PHRASES_FILE)
WHITELIST_PHRASES = load_phrases(WHITELIST_PHRASES_FILE)

# Pre-compile regex patterns for blocklists (performance optimization)
BAN_PATTERNS = compile_blocklist_patterns(BAN_PHRASES)
MUTE_PATTERNS = compile_blocklist_patterns(MUTE_PHRASES)
DELETE_PATTERNS = compile_blocklist_patterns(DELETE_PHRASES)

logger.info(
    f"Pre-compiled {len(BAN_PATTERNS)} BAN patterns, "
    f"{len(MUTE_PATTERNS)} MUTE patterns, "
    f"{len(DELETE_PATTERNS)} DELETE patterns"
)

