"""Tests for AI app functionality."""

from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from apps.users.models import User
from apps.ai.services.usage import log_usage, get_daily_usage, get_remaining_requests
from apps.ai.models import AIUsageLog
from apps.ai.decorators import ai_rate_limit


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


class RateLimitDecoratorTestCase(APITestCase):
    """Test AI rate limiting decorator."""

    def setUp(self):
        """Create test user and view."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

        # Create a test view wrapped with the decorator
        @api_view(['GET'])
        @ai_rate_limit
        def test_view(request):
            return Response({"message": "success"}, status=status.HTTP_200_OK)

        self.test_view = test_view

    def test_allows_request_within_limit(self):
        """Test that requests within limit are allowed."""
        # Create a mock request with force_authenticate
        from rest_framework.test import APIRequestFactory, force_authenticate
        factory = APIRequestFactory()
        request = factory.get('/test/')
        force_authenticate(request, user=self.user)

        response = self.test_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'success')

    def test_blocks_request_at_limit(self):
        """Test that requests are blocked when limit is reached."""
        # Use up all requests
        for _ in range(20):
            log_usage(self.user, 'summary', 100)

        # Try one more request
        from rest_framework.test import APIRequestFactory, force_authenticate
        factory = APIRequestFactory()
        request = factory.get('/test/')
        force_authenticate(request, user=self.user)

        response = self.test_view(request)
        self.assertEqual(response.status_code, 429)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'AI request limit reached')

    def test_rate_limit_response_format(self):
        """Test that rate limit response has correct format."""
        # Use up all requests
        for _ in range(20):
            log_usage(self.user, 'summary', 100)

        # Try blocked request
        from rest_framework.test import APIRequestFactory, force_authenticate
        factory = APIRequestFactory()
        request = factory.get('/test/')
        force_authenticate(request, user=self.user)

        response = self.test_view(request)
        self.assertEqual(response.status_code, 429)

        # Check response format
        self.assertIn('error', response.data)
        self.assertIn('resets_at', response.data)
        self.assertIn('cached_available', response.data)
        self.assertEqual(response.data['cached_available'], True)

        # Verify resets_at is a valid ISO timestamp
        resets_at = response.data['resets_at']
        self.assertIsInstance(resets_at, str)
        # Should be parseable as datetime
        from datetime import datetime
        parsed = datetime.fromisoformat(resets_at.replace('Z', '+00:00'))
        self.assertIsNotNone(parsed)

    def test_rate_limit_resets_at_midnight(self):
        """Test that resets_at is tomorrow at midnight UTC."""
        # Use up all requests
        for _ in range(20):
            log_usage(self.user, 'summary', 100)

        # Try blocked request
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.get('/test/')
        request.user = self.user

        response = self.test_view(request)
        resets_at_str = response.data['resets_at']

        # Parse the timestamp
        from datetime import datetime
        resets_at = datetime.fromisoformat(resets_at_str.replace('Z', '+00:00'))

        # Should be midnight
        self.assertEqual(resets_at.hour, 0)
        self.assertEqual(resets_at.minute, 0)
        self.assertEqual(resets_at.second, 0)

        # Should be tomorrow (or later today if it's currently before midnight)
        now = timezone.now()
        self.assertGreater(resets_at, now)
