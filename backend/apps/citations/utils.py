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
    # metadata is a JSONField with default=dict, so it should never be None
    # but we check anyway for safety
    if not source.metadata or not isinstance(source.metadata, dict):
        return

    if 'citations' in source.metadata:
        del source.metadata['citations']
        source.save(update_fields=['metadata'])
