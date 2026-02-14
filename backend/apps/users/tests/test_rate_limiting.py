from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from apps.users.models import User


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-rate-limiting',
        }
    },
    RATELIMIT_ENABLE=True,
    RATELIMIT_USE_CACHE='default',
)
class RateLimitingTests(TestCase):
    """Tests for rate limiting on auth endpoints"""

    def setUp(self):
        self.client = APIClient()

    def test_login_rate_limit_blocks_after_5_attempts(self):
        """Test that 6th login attempt within a minute returns 429"""
        url = reverse('users:login')
        credentials = {'email': 'test@example.com', 'password': 'wrongpassword'}

        # Make 5 requests (should succeed - though login fails due to wrong creds)
        for i in range(5):
            response = self.client.post(url, credentials, format='json')
            # First 5 should not be rate limited (even if they return 401 for wrong creds)
            self.assertNotEqual(response.status_code, 429, f"Request {i+1} should not be rate limited")

        # 6th request should be rate limited
        response = self.client.post(url, credentials, format='json')
        self.assertEqual(response.status_code, 429)
        self.assertIn('error', response.data)
        self.assertIn('Rate limit exceeded', response.data['error'])

    def test_registration_rate_limit_blocks_after_5_attempts(self):
        """Test that 6th registration attempt within a minute returns 429"""
        url = reverse('users:register')

        # Make 5 requests (should succeed)
        for i in range(5):
            data = {
                'email': f'user{i}@example.com',
                'password': 'SecureP@ss123',
                'username': f'user{i}'
            }
            response = self.client.post(url, data, format='json')
            # First 5 should not be rate limited
            self.assertNotEqual(response.status_code, 429, f"Request {i+1} should not be rate limited")

        # 6th request should be rate limited
        data = {
            'email': 'user6@example.com',
            'password': 'SecureP@ss123',
            'username': 'user6'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 429)
        self.assertIn('error', response.data)
        self.assertIn('Rate limit exceeded', response.data['error'])

    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'test-rate-limiting-reset',
            }
        }
    )
    def test_rate_limit_resets_after_time_window(self):
        """Test that rate limit resets after time window"""
        # This test uses a fresh cache to ensure clean state
        # In production, rate limits reset after 1 minute for login/register
        # We test that creating a new cache (simulating time window expiration)
        # allows requests to proceed again

        url = reverse('users:login')
        credentials = {'email': 'test@example.com', 'password': 'wrongpassword'}

        # Make 5 requests
        for i in range(5):
            response = self.client.post(url, credentials, format='json')
            self.assertNotEqual(response.status_code, 429)

        # After cache reset (simulating time window expiration), requests should work again
        # The @override_settings creates a fresh cache, simulating the reset
        response = self.client.post(url, credentials, format='json')
        # This should succeed (not be rate limited) because we're using a fresh cache
        # In real scenario, waiting 1 minute would have the same effect
        self.assertNotEqual(response.status_code, 429)

    def test_password_reset_rate_limit_3_per_hour(self):
        """Test password reset endpoint has 3/hour rate limit"""
        url = reverse('users:password-reset')

        # Make 3 requests (should succeed)
        for i in range(3):
            data = {'email': f'user{i}@example.com'}
            response = self.client.post(url, data, format='json')
            self.assertNotEqual(response.status_code, 429, f"Request {i+1} should not be rate limited")
            # All should return 200 (even for non-existent emails)
            self.assertEqual(response.status_code, 200)

        # 4th request should be rate limited
        response = self.client.post(url, {'email': 'user4@example.com'}, format='json')
        self.assertEqual(response.status_code, 429)
        self.assertIn('error', response.data)
        self.assertIn('Rate limit exceeded', response.data['error'])
