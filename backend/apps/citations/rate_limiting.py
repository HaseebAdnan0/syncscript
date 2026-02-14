"""
Rate limiting utilities for AI citation generation.

This module provides rate limiting functionality to control AI citation
generation costs and prevent abuse.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, TYPE_CHECKING

from django.core.cache import cache
from django.contrib.auth import get_user_model

if TYPE_CHECKING:
    from apps.vaults.models import Vault

User = get_user_model()


# Rate limits
USER_DAILY_LIMIT = 50  # AI citations per user per day
VAULT_DAILY_LIMIT = 200  # AI citations per vault per day


def _get_cache_key(prefix: str, identifier: int) -> str:
    """
    Generate cache key for rate limiting.

    Args:
        prefix: Key prefix ('ai_citation:user' or 'ai_citation:vault')
        identifier: User ID or Vault ID

    Returns:
        Redis cache key with date
    """
    today = datetime.now().strftime('%Y-%m-%d')
    return f"{prefix}:{identifier}:daily:{today}"


def _get_seconds_until_midnight() -> int:
    """
    Calculate seconds until midnight for cache expiry.

    Returns:
        Seconds until midnight
    """
    now = datetime.now()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((midnight - now).total_seconds())


def increment_ai_citation_counter(user_id: int, vault_id: int) -> None:
    """
    Increment AI citation usage counters for user and vault.

    Args:
        user_id: User ID
        vault_id: Vault ID
    """
    user_key = _get_cache_key('ai_citation:user', user_id)
    vault_key = _get_cache_key('ai_citation:vault', vault_id)
    ttl = _get_seconds_until_midnight()

    # Increment user counter
    current_user_count = cache.get(user_key, 0)
    cache.set(user_key, current_user_count + 1, timeout=ttl)

    # Increment vault counter
    current_vault_count = cache.get(vault_key, 0)
    cache.set(vault_key, current_vault_count + 1, timeout=ttl)


def check_ai_citation_rate_limit(user: Any, vault: Any) -> tuple[bool, str | None]:
    """
    Check if user or vault has exceeded AI citation rate limits.

    Args:
        user: User instance
        vault: Vault instance

    Returns:
        Tuple of (is_allowed, error_message)
        - is_allowed: True if within limits, False if exceeded
        - error_message: None if allowed, error message if exceeded
    """
    # Check user limit
    user_key = _get_cache_key('ai_citation:user', user.id)
    user_count = cache.get(user_key, 0)

    if user_count >= USER_DAILY_LIMIT:
        return False, f"Daily AI citation limit exceeded for user ({USER_DAILY_LIMIT} per day)"

    # Check vault limit
    vault_key = _get_cache_key('ai_citation:vault', vault.id)
    vault_count = cache.get(vault_key, 0)

    if vault_count >= VAULT_DAILY_LIMIT:
        return False, f"Daily AI citation limit exceeded for vault ({VAULT_DAILY_LIMIT} per day)"

    return True, None


def get_ai_citation_quota(user: Any, vault: Any) -> Dict[str, Any]:
    """
    Get current AI citation usage and remaining quota.

    Args:
        user: User instance
        vault: Vault instance

    Returns:
        Dictionary with usage information:
        - user_used: Citations used by user today
        - user_limit: User's daily limit
        - user_remaining: Remaining user quota
        - vault_used: Citations used by vault today
        - vault_limit: Vault's daily limit
        - vault_remaining: Remaining vault quota
        - reset_at: Timestamp when counters reset (midnight)
    """
    # Get user quota
    user_key = _get_cache_key('ai_citation:user', user.id)
    user_used = cache.get(user_key, 0)
    user_remaining = max(0, USER_DAILY_LIMIT - user_used)

    # Get vault quota
    vault_key = _get_cache_key('ai_citation:vault', vault.id)
    vault_used = cache.get(vault_key, 0)
    vault_remaining = max(0, VAULT_DAILY_LIMIT - vault_used)

    # Calculate reset time (midnight)
    now = datetime.now()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    return {
        'user_used': user_used,
        'user_limit': USER_DAILY_LIMIT,
        'user_remaining': user_remaining,
        'vault_used': vault_used,
        'vault_limit': VAULT_DAILY_LIMIT,
        'vault_remaining': vault_remaining,
        'reset_at': midnight.isoformat(),
    }
