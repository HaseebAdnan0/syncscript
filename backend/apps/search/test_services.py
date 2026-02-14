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


class RecordSearchHistoryTest(TestCase):
    """Tests for record_search_history function"""

    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_creates_new_history_record(self):
        """Should create new SearchHistory record for new query"""
        query = "machine learning"
        result_count = 5

        record_search_history(self.user, query, result_count)

        # Verify record was created
        history = SearchHistory.objects.get(user=self.user, query=query)
        self.assertEqual(history.query, query)
        self.assertEqual(history.result_count, result_count)
        self.assertIsNotNone(history.created_at)

    def test_updates_timestamp_for_duplicate_query(self):
        """Should update timestamp instead of creating duplicate"""
        query = "python programming"

        # First search
        record_search_history(self.user, query, 3)
        first_history = SearchHistory.objects.get(user=self.user, query=query)
        first_timestamp = first_history.created_at

        # Wait a moment
        import time
        time.sleep(0.1)

        # Second search with same query
        record_search_history(self.user, query, 5)

        # Should still only have one record
        self.assertEqual(SearchHistory.objects.filter(user=self.user, query=query).count(), 1)

        # But timestamp should be updated
        updated_history = SearchHistory.objects.get(user=self.user, query=query)
        self.assertGreater(updated_history.created_at, first_timestamp)
        self.assertEqual(updated_history.result_count, 5)  # Result count also updated

    def test_limits_to_10_most_recent(self):
        """Should keep only 10 most recent searches per user"""
        # Create 15 search history entries
        for i in range(15):
            record_search_history(self.user, f"query {i}", i)

        # Should only have 10 records
        self.assertEqual(SearchHistory.objects.filter(user=self.user).count(), 10)

        # Verify we kept the most recent ones (5-14)
        queries = list(
            SearchHistory.objects.filter(user=self.user)
            .order_by('-created_at')
            .values_list('query', flat=True)
        )

        # Most recent should be "query 14" through "query 5"
        for i in range(5, 15):
            self.assertIn(f"query {i}", queries)

        # Oldest (query 0-4) should be deleted
        for i in range(5):
            self.assertNotIn(f"query {i}", queries)

    def test_strips_whitespace_from_query(self):
        """Should strip whitespace from query before storing"""
        query = "  django rest framework  "

        record_search_history(self.user, query, 10)

        history = SearchHistory.objects.get(user=self.user)
        self.assertEqual(history.query, "django rest framework")

    def test_ignores_empty_queries(self):
        """Should not create records for empty or whitespace-only queries"""
        queries = ["", "   ", "\t", "\n"]

        for query in queries:
            record_search_history(self.user, query, 0)

        # No records should be created
        self.assertEqual(SearchHistory.objects.filter(user=self.user).count(), 0)

    def test_separate_history_per_user(self):
        """Should maintain separate search history for different users"""
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

        # Both users search for same query
        record_search_history(self.user, "shared query", 5)
        record_search_history(user2, "shared query", 3)

        # Each user should have their own record
        self.assertEqual(SearchHistory.objects.filter(user=self.user).count(), 1)
        self.assertEqual(SearchHistory.objects.filter(user=user2).count(), 1)

        # Total should be 2
        self.assertEqual(SearchHistory.objects.count(), 2)

    def test_deduplication_updates_result_count(self):
        """When deduplicating, should update result_count to latest value"""
        query = "test query"

        # First search with 10 results
        record_search_history(self.user, query, 10)

        # Second search with 20 results
        record_search_history(self.user, query, 20)

        # Should only have one record with updated count
        history = SearchHistory.objects.get(user=self.user, query=query)
        self.assertEqual(history.result_count, 20)
