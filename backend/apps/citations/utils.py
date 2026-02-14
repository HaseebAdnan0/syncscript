"""
Utility functions for citation management.
"""
from apps.sources.models import Source


def invalidate_citation_cache(source: Source) -> None:
    """
    Invalidate all cached citations for a source.

    This removes the 'citations' key from source.metadata,
    forcing regeneration on next citation request.

    Args:
        source: Source instance to invalidate cache for

    Usage:
        invalidate_citation_cache(source)
    """
    if not source.metadata:
        return

    if 'citations' in source.metadata:
        del source.metadata['citations']
        source.save(update_fields=['metadata'])
