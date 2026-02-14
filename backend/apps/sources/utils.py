"""
Utility functions for source and PDF file management.
"""
from typing import Dict
from django.core.cache import cache
from django.db.models import Sum, Count
from .models import PDFUpload, VaultStorageUsage


def update_vault_storage_usage(vault_id: int) -> VaultStorageUsage:
    """
    Recalculate and update storage usage for a vault.

    Aggregates total_bytes and file_count from non-deleted PDFUploads,
    calculates per-user breakdown as JSON, updates or creates VaultStorageUsage record,
    and invalidates Redis cache.

    Args:
        vault_id: ID of the vault to update storage usage for

    Returns:
        VaultStorageUsage: The updated storage usage record
    """
    # Query all non-deleted PDF uploads for this vault
    pdf_uploads = PDFUpload.objects.filter(
        vault_id=vault_id,
        deleted_at__isnull=True
    )

    # Aggregate total bytes and file count
    aggregation = pdf_uploads.aggregate(
        total_bytes=Sum('file_size'),
        file_count=Count('id')
    )

    total_bytes = aggregation['total_bytes'] or 0
    file_count = aggregation['file_count'] or 0

    # Calculate per-user breakdown
    user_breakdown: Dict[str, int] = {}
    user_aggregates = pdf_uploads.values('uploaded_by_id').annotate(
        user_bytes=Sum('file_size')
    )

    for row in user_aggregates:
        user_id = str(row['uploaded_by_id'])
        user_breakdown[user_id] = row['user_bytes'] or 0

    # Update or create VaultStorageUsage record
    storage_usage, created = VaultStorageUsage.objects.update_or_create(
        vault_id=vault_id,
        defaults={
            'total_bytes': total_bytes,
            'file_count': file_count,
            'user_breakdown': user_breakdown,
        }
    )

    # Invalidate Redis cache
    cache_key = f'vault_storage:{vault_id}'
    cache.delete(cache_key)

    return storage_usage
