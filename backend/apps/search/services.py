"""Search service functions for analytics and history tracking."""
from django.utils import timezone
from .models import SearchAnalytics, SearchHistory


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


def record_search_history(user, query: str, result_count: int) -> None:
    """
    Record search query in user's search history for recent searches feature.

    Args:
        user: The User instance performing the search
        query: The search query string
        result_count: Number of results returned for this query

    Behavior:
    - Stores query, user, and result count
    - Limits to 10 most recent searches per user (deletes oldest on insert)
    - Deduplicates: if same query exists, updates timestamp instead of creating duplicate
    - Empty/whitespace queries are ignored
    """
    if not query or not query.strip():
        return

    query = query.strip()

    # Check if user already searched for this query
    existing = SearchHistory.objects.filter(user=user, query=query).first()

    if existing:
        # Update timestamp to make it most recent (Django auto-updates with auto_now_add=False)
        existing.result_count = result_count
        existing.created_at = timezone.now()
        existing.save(update_fields=['result_count', 'created_at'])
    else:
        # Create new search history entry
        SearchHistory.objects.create(
            user=user,
            query=query,
            result_count=result_count
        )

        # Keep only 10 most recent searches for this user
        user_searches = SearchHistory.objects.filter(user=user).order_by('-created_at')
        if user_searches.count() > 10:
            # Delete oldest searches beyond 10
            oldest_ids = list(user_searches.values_list('id', flat=True)[10:])
            SearchHistory.objects.filter(id__in=oldest_ids).delete()
