"""
User validation functions - bio checks, username checks, impersonation detection
"""

from typing import List, Tuple
from .patterns import contains_multiplication_phrase, contains_non_x_links
from .constants import BIO_PHRASES


def check_suspicious_bio(bio_text: str) -> Tuple[bool, List[str]]:
    """
    Check bio for suspicious content.
    
    Returns:
        (should_ban, violations): Tuple of boolean and list of violation types
    """
    detected = []
    bio_cleaned = (bio_text or "").strip().replace("\u200b", "").lower()
    
    if any(keyword in bio_cleaned for keyword in BIO_PHRASES):
        detected.append("bio phrase")
    if contains_multiplication_phrase(bio_cleaned):
        detected.append("multiplication")
    if contains_non_x_links(bio_cleaned):
        detected.append("non-X link")
    
    return (len(detected) > 0, detected)


def is_username_suspicious(username: str, suspicious_list: List[str]) -> bool:
    """Check if username matches suspicious patterns"""
    from .patterns import contains_suspicious_keyword
    return contains_suspicious_keyword(username, suspicious_list)


def is_username_valid(username: str) -> bool:
    """Check if user has a valid username (not missing or hidden)"""
    if not username:
        return False
    if username.lower() == "hidden":
        return False
    return True


def is_impersonating_admin(user_name: str, admin_names: List[str]) -> bool:
    """Check if user name contains any admin names (impersonation check)"""
    user_name_lower = user_name.lower()
    return any(admin_name in user_name_lower for admin_name in admin_names)