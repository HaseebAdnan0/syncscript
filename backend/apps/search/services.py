"""Search service functions for analytics and history tracking."""
from django.utils import timezone
from .models import SearchAnalytics


def track_search_analytics(query: str) -> None:
    """
    Track search query for analytics without storing user identity.

    Args:
        query: The search query string to track

    Creates or updates SearchAnalytics record:
    - Normalizes query to lowercase and strips whitespace
    - Hashes query with SHA-256 for privacy
    - Increments search_count if record exists
    - Updates last_searched timestamp
    """
    if not query or not query.strip():
        return

    normalized_query = query.strip().lower()
    query_hash = SearchAnalytics.hash_query(normalized_query)

    # Get or create analytics record
    analytics, created = SearchAnalytics.objects.get_or_create(
        query_hash=query_hash,
        defaults={
            'query_normalized': normalized_query,
            'search_count': 0,
            'last_searched': timezone.now()
        }
    )

    # Increment count and update timestamp
    if not created:
        analytics.search_count += 1
        analytics.last_searched = timezone.now()
        analytics.save(update_fields=['search_count', 'last_searched'])
