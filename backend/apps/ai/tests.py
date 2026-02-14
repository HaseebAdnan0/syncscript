"""Tests for AI app functionality."""

from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.ai.services.usage import log_usage, get_daily_usage, get_remaining_requests
from apps.ai.models import AIUsageLog

User = get_user_model()


class UsageTrackingTestCase(TestCase):
    """Test AI usage tracking service."""

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_log_usage(self):
        """Test logging AI usage."""
        log = log_usage(self.user, 'summary', 100)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.request_type, 'summary')
        self.assertEqual(log.tokens_used, 100)

    def test_get_daily_usage_empty(self):
        """Test getting daily usage when no usage exists."""
        usage = get_daily_usage(self.user)
        self.assertEqual(usage['tokens_used'], 0)
        self.assertEqual(usage['request_count'], 0)

    def test_get_daily_usage_with_logs(self):
        """Test getting daily usage with existing logs."""
        log_usage(self.user, 'summary', 100)
        log_usage(self.user, 'insights', 200)
        log_usage(self.user, 'question', 50)

        usage = get_daily_usage(self.user)
        self.assertEqual(usage['tokens_used'], 350)
        self.assertEqual(usage['request_count'], 3)

    def test_get_daily_usage_ignores_old_logs(self):
        """Test that daily usage only counts today's logs."""
        # Create an old log
        old_log = AIUsageLog.objects.create(
            user=self.user,
            request_type='summary',
            tokens_used=1000
        )
        old_log.created_at = datetime.now() - timedelta(days=2)
        old_log.save()

        # Create today's log
        log_usage(self.user, 'summary', 100)

        usage = get_daily_usage(self.user)
        self.assertEqual(usage['tokens_used'], 100)
        self.assertEqual(usage['request_count'], 1)

    def test_get_remaining_requests_full_allowance(self):
        """Test remaining requests with no usage."""
        remaining = get_remaining_requests(self.user)
        self.assertEqual(remaining, 20)  # Default limit

    def test_get_remaining_requests_partial_usage(self):
        """Test remaining requests with some usage."""
        for _ in range(5):
            log_usage(self.user, 'summary', 100)

        remaining = get_remaining_requests(self.user)
        self.assertEqual(remaining, 15)

    def test_get_remaining_requests_limit_exceeded(self):
        """Test remaining requests when limit is exceeded."""
        for _ in range(25):
            log_usage(self.user, 'summary', 100)

        remaining = get_remaining_requests(self.user)
        self.assertEqual(remaining, 0)
