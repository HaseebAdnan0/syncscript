"""
Integration tests for authentication flows (registration, verification, login, logout, token refresh, password reset).
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.models import User, EmailVerificationToken


class RegistrationFlowTests(TestCase):
    """Test user registration flow."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('users:register')

    def test_successful_registration_returns_201(self):
        """Test that successful registration returns 201 status."""
        data = {
            'email': 'newuser@example.com',
            'password': 'SecureP@ssw0rd!',
            'username': 'newuser',
            'bio': 'Test bio',
            'institution': 'Test University'
        }
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
        self.assertIn('message', response.data)

    def test_registration_creates_unverified_user(self):
        """Test that registration creates user with email_verified=False."""
        data = {
            'email': 'unverified@example.com',
            'password': 'SecureP@ssw0rd!',
            'username': 'unverifieduser'
        }
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check user in database
        user = User.objects.get(email='unverified@example.com')
        self.assertFalse(user.email_verified)

        # Check verification token was created
        self.assertTrue(EmailVerificationToken.objects.filter(user=user).exists())

    def test_duplicate_email_returns_400(self):
        """Test that registering with duplicate email returns 400 error."""
        # Create existing user
        User.objects.create_user(
            email='existing@example.com',
            username='existinguser',
            password='ExistingP@ss123'
        )

        # Attempt to register with same email
        data = {
            'email': 'existing@example.com',
            'password': 'NewP@ssw0rd!',
            'username': 'newuser'
        }
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_weak_password_returns_400(self):
        """Test that weak password returns 400 error."""
        data = {
            'email': 'weakpass@example.com',
            'password': '12345678',  # Common weak password
            'username': 'weakpassuser'
        }
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
