"""
Admin utilities - caching and fetching admin data
"""

import logging
from datetime import datetime
from typing import Dict, Tuple, List

from .utils import normalize_name
from .config import ADMIN_CACHE_TTL

logger = logging.getLogger(__name__)

# Admin cache with TTL
_admin_cache: Dict[int, Tuple[List[int], List[str], datetime]] = {}


def get_admin_data(context, chat_id) -> Tuple[List[int], List[str]]:
    """
    Get admin IDs and normalized names, cached with TTL.
    Returns: (admin_ids, admin_names_normalized)
    """
    now = datetime.now()
    
    # Check cache
    if chat_id in _admin_cache:
        admin_ids, admin_names, cached_time = _admin_cache[chat_id]
        age = (now - cached_time).total_seconds()
        
        if age < ADMIN_CACHE_TTL:
            logger.debug(f"Admin cache hit for chat {chat_id} (age: {age:.1f}s)")
            return admin_ids, admin_names
    
    # Cache miss or expired - fetch fresh data
    logger.debug(f"Admin cache miss for chat {chat_id} - fetching fresh data")
    try:
        chat_admins = context.bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in chat_admins]
        admin_names = [normalize_name(admin.user.full_name) for admin in chat_admins if not admin.user.is_bot]
        
        # Update cache
        _admin_cache[chat_id] = (admin_ids, admin_names, now)
        logger.debug(f"Cached admin data for chat {chat_id}: {len(admin_ids)} admins")
        
        return admin_ids, admin_names
    except Exception as e:
        logger.error(f"Failed to fetch admins for chat {chat_id}: {e}")
        # Return cached data even if expired, or empty lists
        if chat_id in _admin_cache:
            admin_ids, admin_names, _ = _admin_cache[chat_id]
            logger.warning(f"Using stale admin cache for chat {chat_id} due to error")
            return admin_ids, admin_names
        return [], []


def get_admin_ids(context, chat_id):
    """Get admin IDs (backward compatibility wrapper)"""
    admin_ids, _ = get_admin_data(context, chat_id)
    return admin_ids


def get_admin_names(context, chat_id):
    """Get admin names (backward compatibility wrapper)"""
    _, admin_names = get_admin_data(context, chat_id)
    return admin_names

