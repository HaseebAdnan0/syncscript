"""
Storage quota management for vaults.

Provides functions to check storage usage against limits
and determine if warnings or blocks are needed.
"""

from typing import TypedDict
from django.conf import settings
from apps.sources.models import VaultStorageUsage


class StorageQuotaResult(TypedDict):
    """Result of storage quota check."""
    used_bytes: int
    limit_bytes: int
    percentage: float
    warning: bool
    exceeded: bool


def check_storage_quota(vault_id: int) -> StorageQuotaResult:
    """
    Check storage quota for a vault.

    Args:
        vault_id: ID of the vault to check

    Returns:
        Dictionary with quota information:
        - used_bytes: Current storage usage in bytes
        - limit_bytes: Storage limit in bytes (from settings)
        - percentage: Usage percentage (0.0 to 1.0+)
        - warning: True if usage >= warning threshold (80%)
        - exceeded: True if usage >= 100% of limit
    """
    # Get or create storage usage record
    storage_usage, _ = VaultStorageUsage.objects.get_or_create(
        vault_id=vault_id,
        defaults={'total_bytes': 0, 'file_count': 0}
    )

    used_bytes = storage_usage.total_bytes
    limit_bytes = settings.VAULT_STORAGE_LIMIT

    # Calculate percentage (can exceed 1.0)
    percentage = used_bytes / limit_bytes if limit_bytes > 0 else 0.0

    # Determine warning and exceeded states
    warning_threshold = settings.VAULT_STORAGE_WARNING_THRESHOLD
    warning = percentage >= warning_threshold
    exceeded = percentage >= 1.0

    return {
        'used_bytes': used_bytes,
        'limit_bytes': limit_bytes,
        'percentage': percentage,
        'warning': warning,
        'exceeded': exceeded,
    }
