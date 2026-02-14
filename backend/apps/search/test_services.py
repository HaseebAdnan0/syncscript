from django.test import TestCase
from django.utils import timezone
from apps.users.models import User
from .models import SearchAnalytics, SearchHistory
from .services import track_search_analytics, record_search_history


class TrackSearchAnalyticsTest(TestCase):
    """Tests for track_search_analytics function"""

    def test_creates_new_analytics_record(self):
        """Should create new SearchAnalytics record for new query"""
        query = "Django Testing"

        track_search_analytics(query)

        # Verify record was created
        normalized = query.strip().lower()
        query_hash = SearchAnalytics.hash_query(normalized)
        analytics = SearchAnalytics.objects.get(query_hash=query_hash)

        self.assertEqual(analytics.query_normalized, "django testing")
        self.assertEqual(analytics.search_count, 0)  # First search, count is 0 on create
        self.assertIsNotNone(analytics.last_searched)

    def test_increments_count_for_existing_query(self):
        """Should increment search_count when query already exists"""
        query = "Python Programming"

        # First search
        track_search_analytics(query)

        # Second search
        track_search_analytics(query)

        # Verify count was incremented
        normalized = query.strip().lower()
        query_hash = SearchAnalytics.hash_query(normalized)
        analytics = SearchAnalytics.objects.get(query_hash=query_hash)

        self.assertEqual(analytics.search_count, 1)  # 0 on create, +1 on second call

    def test_normalizes_query(self):
        """Should normalize query to lowercase and strip whitespace"""
        queries = [
            "  Django REST Framework  ",
            "django rest framework",
            "DJANGO REST FRAMEWORK"
        ]

        for query in queries:
            track_search_analytics(query)

        # All should create/update the same record
        self.assertEqual(SearchAnalytics.objects.count(), 1)
        analytics = SearchAnalytics.objects.first()
        self.assertEqual(analytics.query_normalized, "django rest framework")

    def test_updates_last_searched_timestamp(self):
        """Should update last_searched timestamp on each call"""
        query = "Search Timestamp Test"

        # First search
        track_search_analytics(query)
        normalized = query.strip().lower()
        query_hash = SearchAnalytics.hash_query(normalized)
        analytics = SearchAnalytics.objects.get(query_hash=query_hash)
        first_timestamp = analytics.last_searched

        # Wait a moment and search again
        import time
        time.sleep(0.1)

        track_search_analytics(query)
        analytics.refresh_from_db()
        second_timestamp = analytics.last_searched

        self.assertGreater(second_timestamp, first_timestamp)

    def test_ignores_empty_queries(self):
        """Should not create records for empty or whitespace-only queries"""
        queries = ["", "   ", "\t", "\n"]

        for query in queries:
            track_search_analytics(query)

        # No records should be created
        self.assertEqual(SearchAnalytics.objects.count(), 0)

    def test_multiple_distinct_queries(self):
        """Should create separate records for different queries"""
        queries = [
            "Django",
            "Flask",
            "FastAPI"
        ]

        for query in queries:
            track_search_analytics(query)

        # Should have 3 distinct records
        self.assertEqual(SearchAnalytics.objects.count(), 3)

        # Verify each query is stored
        normalized_queries = [q.lower() for q in queries]
        db_queries = list(
            SearchAnalytics.objects.values_list('query_normalized', flat=True)
        )
        self.assertEqual(sorted(db_queries), sorted(normalized_queries))

    def test_privacy_hash_consistency(self):
        """Should generate consistent hash for same query"""
        query = "Privacy Test Query"

        # Track twice
        track_search_analytics(query)
        track_search_analytics(query)

        # Should only have one record (same hash)
        self.assertEqual(SearchAnalytics.objects.count(), 1)

        # Verify hash matches expected
        normalized = query.strip().lower()
        expected_hash = SearchAnalytics.hash_query(normalized)
        analytics = SearchAnalytics.objects.first()

        self.assertEqual(analytics.query_hash, expected_hash)
