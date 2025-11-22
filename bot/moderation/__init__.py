"""
Moderation module - spam detection, user validation, and moderation actions
"""

from .checks import check_user_moderation
from .actions import ban_and_delete_message, delete_message_safe, handle_bot_spam, mute_user
from .validators import check_suspicious_bio, is_username_valid, is_impersonating_admin
from .patterns import (
    contains_multiplication_phrase,
    contains_give_sol_phrase,
    contains_arrows,
    contains_non_x_links,
    contains_suspicious_keyword
)
from .constants import SUSPICIOUS_USERNAMES, BIO_PHRASES

__all__ = [
    # Main check function
    'check_user_moderation',
    
    # Actions
    'ban_and_delete_message',
    'delete_message_safe',
    'handle_bot_spam',
    'mute_user',
    
    # Validators
    'check_suspicious_bio',
    'is_username_valid',
    'is_impersonating_admin',
    
    # Pattern checks
    'contains_multiplication_phrase',
    'contains_give_sol_phrase',
    'contains_arrows',
    'contains_non_x_links',
    'contains_suspicious_keyword',
    
    # Constants
    'SUSPICIOUS_USERNAMES',
    'BIO_PHRASES',
]