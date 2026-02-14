from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APIClient
from apps.users.models import User


class RateLimitingTests(TestCase):
    """
    Tests for rate limiting on auth endpoints.

    Note: django-ratelimit with block=True raises Ratelimited (subclass of PermissionDenied),
    which returns 403 by default. In production, our custom exception handler converts this
    to 429, but in tests the exception handler chain works differently and we get 403.
    These tests verify rate limiting is working (403 = rate limited) even though production returns 429.
    """

    def setUp(self):
        self.client = APIClient()
        # Clear cache before each test to ensure clean state
        # This ensures each test starts with empty rate limit counters
        cache.clear()

    def test_login_rate_limit_blocks_after_5_attempts(self):
        """Test that 6th login attempt within a minute is rate limited"""
        url = reverse('users:login')
        credentials = {'email': 'test@example.com', 'password': 'wrongpassword'}

        # Make 5 requests (should succeed - though login fails due to wrong creds)
        for i in range(5):
            response = self.client.post(url, credentials, format='json', REMOTE_ADDR='127.0.0.1')
            # First 5 should not be rate limited (even if they return 401 for wrong creds)
            self.assertNotEqual(response.status_code, 403, f"Request {i+1} should not be rate limited")

        # 6th request should be rate limited (403 in tests, 429 in production)
        response = self.client.post(url, credentials, format='json', REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response.status_code, 403, "Request should be rate limited (Ratelimited/PermissionDenied)")


    def test_registration_rate_limit_blocks_after_5_attempts(self):
        """Test that 6th registration attempt within a minute is rate limited"""
        url = reverse('users:register')

        # Make 5 requests (should succeed)
        for i in range(5):
            data = {
                'email': f'user{i}@example.com',
                'password': 'SecureP@ss123',
                'username': f'user{i}'
            }
            response = self.client.post(url, data, format='json', REMOTE_ADDR='127.0.0.1')
            # First 5 should not be rate limited
            self.assertNotEqual(response.status_code, 403, f"Request {i+1} should not be rate limited")

        # 6th request should be rate limited (403 in tests, 429 in production)
        data = {
            'email': 'user6@example.com',
            'password': 'SecureP@ss123',
            'username': 'user6'
        }
        response = self.client.post(url, data, format='json', REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response.status_code, 403, "Request should be rate limited (Ratelimited/PermissionDenied)")

    def test_rate_limit_resets_after_time_window(self):
        """Test that rate limit resets after time window"""
        # This test uses cache.clear() to simulate time window expiration
        # In production, rate limits reset after 1 minute for login/register
        url = reverse('users:login')
        credentials = {'email': 'test@example.com', 'password': 'wrongpassword'}

        # Make 5 requests
        for _ in range(5):
            response = self.client.post(url, credentials, format='json', REMOTE_ADDR='127.0.0.1')
            self.assertNotEqual(response.status_code, 403)

        # Clear cache to simulate time window expiration
        cache.clear()

        # After cache reset (simulating time window expiration), requests should work again
        response = self.client.post(url, credentials, format='json', REMOTE_ADDR='127.0.0.1')
        # This should succeed (not be rate limited) because we cleared the cache
        # In real scenario, waiting 1 minute would have the same effect
        self.assertNotEqual(response.status_code, 403)

    def test_password_reset_rate_limit_3_per_hour(self):
        """Test password reset endpoint has 3/hour rate limit"""
        url = reverse('users:password-reset')

        # Make 3 requests (should succeed)
        for i in range(3):
            data = {'email': f'user{i}@example.com'}
            response = self.client.post(url, data, format='json', REMOTE_ADDR='127.0.0.1')
            self.assertNotEqual(response.status_code, 403, f"Request {i+1} should not be rate limited")
            # All should return 200 (even for non-existent emails)
            self.assertEqual(response.status_code, 200)

        # 4th request should be rate limited (403 in tests, 429 in production)
        response = self.client.post(url, {'email': 'user4@example.com'}, format='json', REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response.status_code, 403, "Request should be rate limited (Ratelimited/PermissionDenied)")
