"""
Integration tests for authentication flows (registration, verification, login, logout, token refresh, password reset).
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.models import User, EmailVerificationToken
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


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


class EmailVerificationFlowTests(TestCase):
    """Test email verification flow."""

    def setUp(self):
        self.client = APIClient()
        self.verify_url = reverse('users:verify-email')

        # Create a user for testing
        self.user = User.objects.create_user(
            email='verify@example.com',
            username='verifyuser',
            password='TestP@ss123',
            email_verified=False
        )

    def test_valid_token_activates_account(self):
        """Test that valid token sets email_verified to True."""
        # Create verification token
        token = EmailVerificationToken.objects.create(
            user=self.user,
            token='valid-token-12345',
            expires_at=timezone.now() + timedelta(hours=24)
        )

        data = {'token': 'valid-token-12345'}
        response = self.client.post(self.verify_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)

        # Check user is now verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

        # Check token was deleted
        self.assertFalse(EmailVerificationToken.objects.filter(token='valid-token-12345').exists())

    def test_expired_token_returns_error(self):
        """Test that expired token returns error and does not verify user."""
        # Create expired token (expires 1 hour ago)
        token = EmailVerificationToken.objects.create(
            user=self.user,
            token='expired-token-12345',
            expires_at=timezone.now() - timedelta(hours=1)
        )

        data = {'token': 'expired-token-12345'}
        response = self.client.post(self.verify_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

        # Check user is still unverified
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_invalid_token_returns_error(self):
        """Test that non-existent token returns error."""
        data = {'token': 'non-existent-token'}
        response = self.client.post(self.verify_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

        # Check user is still unverified
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_already_verified_user_handles_gracefully(self):
        """Test that verifying an already verified user handles gracefully."""
        # Set user as already verified
        self.user.email_verified = True
        self.user.save()

        # Create valid token
        token = EmailVerificationToken.objects.create(
            user=self.user,
            token='already-verified-token',
            expires_at=timezone.now() + timedelta(hours=24)
        )

        data = {'token': 'already-verified-token'}
        response = self.client.post(self.verify_url, data, format='json')

        # Should still succeed (idempotent)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # User still verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)


class LoginAndLogoutFlowTests(TestCase):
    """Test login and logout flows."""

    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('users:login')
        self.logout_url = reverse('users:logout')

        # Create a verified user for login tests
        self.verified_user = User.objects.create_user(
            email='verified@example.com',
            username='verifieduser',
            password='TestP@ss123',
            email_verified=True
        )

        # Create an unverified user for verification tests
        self.unverified_user = User.objects.create_user(
            email='unverified@example.com',
            username='unverifieduser',
            password='TestP@ss123',
            email_verified=False
        )

    def test_successful_login_returns_tokens(self):
        """Test that successful login returns access and refresh tokens."""
        data = {
            'email': 'verified@example.com',
            'password': 'TestP@ss123'
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'verified@example.com')

    def test_unverified_user_cannot_login(self):
        """Test that unverified user cannot login (returns 403)."""
        data = {
            'email': 'unverified@example.com',
            'password': 'TestP@ss123'
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
        self.assertIn('Email not verified', response.data['error'])

    def test_wrong_password_returns_401(self):
        """Test that wrong password returns 401 Unauthorized."""
        data = {
            'email': 'verified@example.com',
            'password': 'WrongP@ssw0rd!'
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertIn('Invalid email or password', response.data['error'])

    def test_logout_blacklists_refresh_token(self):
        """Test that logout blacklists the refresh token."""
        # First login to get tokens
        login_data = {
            'email': 'verified@example.com',
            'password': 'TestP@ss123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        refresh_token = login_response.data['refresh']

        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_response.data["access"]}')

        # Logout with refresh token
        logout_data = {'refresh': refresh_token}
        logout_response = self.client.post(self.logout_url, logout_data, format='json')

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertIn('message', logout_response.data)
        self.assertIn('Logout successful', logout_response.data['message'])

    def test_blacklisted_token_cannot_be_used(self):
        """Test that blacklisted token cannot be used to refresh."""
        # Login to get tokens
        login_data = {
            'email': 'verified@example.com',
            'password': 'TestP@ss123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']

        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_response.data["access"]}')

        # Logout (blacklist token)
        logout_data = {'refresh': refresh_token}
        self.client.post(self.logout_url, logout_data, format='json')

        # Try to use blacklisted token to refresh
        refresh_url = reverse('users:refresh')
        refresh_data = {'refresh': refresh_token}
        refresh_response = self.client.post(refresh_url, refresh_data, format='json')

        # Should return 401 Unauthorized (blacklisted token)
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', refresh_response.data)


class TokenRefreshFlowTests(TestCase):
    """Test token refresh flow."""

    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('users:login')
        self.refresh_url = reverse('users:refresh')

        # Create a verified user for testing
        self.user = User.objects.create_user(
            email='refreshtest@example.com',
            username='refreshuser',
            password='TestP@ss123',
            email_verified=True
        )

    def test_valid_refresh_token_returns_new_access_token(self):
        """Test that valid refresh token returns new access token."""
        # Login to get tokens
        login_data = {
            'email': 'refreshtest@example.com',
            'password': 'TestP@ss123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        refresh_token = login_response.data['refresh']

        # Use refresh token to get new access token
        refresh_data = {'refresh': refresh_token}
        refresh_response = self.client.post(self.refresh_url, refresh_data, format='json')

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        # Token rotation enabled, so new refresh token should be returned
        self.assertIn('refresh', refresh_response.data)

    def test_expired_refresh_token_returns_error(self):
        """Test that expired refresh token returns error."""
        # For this test, we need to create an expired token
        # We'll use a token that was created long ago (simulated by manipulating JWT)
        from rest_framework_simplejwt.tokens import RefreshToken
        from datetime import datetime, timedelta
        import time

        # Create a refresh token
        refresh = RefreshToken.for_user(self.user)

        # Manually expire the token by setting exp claim to past
        refresh.set_exp(lifetime=timedelta(seconds=-3600))  # Expired 1 hour ago

        expired_token = str(refresh)

        # Try to use expired token
        refresh_data = {'refresh': expired_token}
        refresh_response = self.client.post(self.refresh_url, refresh_data, format='json')

        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', refresh_response.data)

    def test_blacklisted_refresh_token_returns_error(self):
        """Test that blacklisted refresh token returns error."""
        # Login to get tokens
        login_data = {
            'email': 'refreshtest@example.com',
            'password': 'TestP@ss123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']

        # Blacklist the token via logout
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_response.data["access"]}')
        logout_url = reverse('users:logout')
        logout_data = {'refresh': refresh_token}
        self.client.post(logout_url, logout_data, format='json')

        # Try to use blacklisted token
        refresh_data = {'refresh': refresh_token}
        refresh_response = self.client.post(self.refresh_url, refresh_data, format='json')

        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', refresh_response.data)

    def test_token_rotation_invalidates_old_refresh_token(self):
        """Test that token rotation invalidates the old refresh token."""
        # Login to get tokens
        login_data = {
            'email': 'refreshtest@example.com',
            'password': 'TestP@ss123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        old_refresh_token = login_response.data['refresh']

        # Use refresh token to get new tokens
        refresh_data = {'refresh': old_refresh_token}
        refresh_response = self.client.post(self.refresh_url, refresh_data, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)

        new_refresh_token = refresh_response.data['refresh']

        # Verify that old and new refresh tokens are different (rotation occurred)
        self.assertNotEqual(old_refresh_token, new_refresh_token)

        # Try to use the old refresh token again (should fail because it's blacklisted)
        old_token_data = {'refresh': old_refresh_token}
        old_token_response = self.client.post(self.refresh_url, old_token_data, format='json')

        # Old token should be blacklisted after rotation
        self.assertEqual(old_token_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', old_token_response.data)


class PasswordResetFlowTests(TestCase):
    """Test password reset request and confirmation flows."""

    def setUp(self):
        self.client = APIClient()
        self.password_reset_url = reverse('users:password-reset')
        self.password_reset_confirm_url = reverse('users:password-reset-confirm')

        # Create a user for password reset tests
        self.user = User.objects.create_user(
            email='resettest@example.com',
            username='resetuser',
            password='OldP@ssw0rd123',
            email_verified=True
        )

    def test_password_reset_request_returns_success_for_existing_email(self):
        """Test that password reset request returns success for existing email."""
        data = {'email': 'resettest@example.com'}
        response = self.client.post(self.password_reset_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('If an account exists with this email', response.data['message'])

    def test_password_reset_request_returns_success_for_nonexistent_email(self):
        """Test that password reset request returns success even for non-existent email (prevents user enumeration)."""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(self.password_reset_url, data, format='json')

        # Should still return success to prevent user enumeration
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('If an account exists with this email', response.data['message'])

    def test_valid_reset_token_allows_password_change(self):
        """Test that valid reset token allows password to be changed."""
        # Generate valid reset token
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        # Reset password
        data = {
            'uid': uid,
            'token': token,
            'new_password': 'NewSecureP@ss123'
        }
        response = self.client.post(self.password_reset_confirm_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('Password reset successful', response.data['message'])

        # Verify password was changed by attempting login with new password
        login_url = reverse('users:login')
        login_data = {
            'email': 'resettest@example.com',
            'password': 'NewSecureP@ss123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_expired_reset_token_returns_error(self):
        """Test that expired reset token returns error."""
        # Create a token, then change user's password to invalidate it
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        # Change password to invalidate token (Django's token generator uses password hash)
        self.user.set_password('IntermediateP@ss456')
        self.user.save()

        # Try to use the now-invalid token
        data = {
            'uid': uid,
            'token': token,
            'new_password': 'AnotherNewP@ss789'
        }
        response = self.client.post(self.password_reset_confirm_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Invalid or expired reset token', response.data['error'])

    def test_new_password_must_meet_strength_requirements(self):
        """Test that new password must meet strength requirements (min 8 chars, not all numeric)."""
        # Generate valid reset token
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        # Try to set a weak password (too short)
        data = {
            'uid': uid,
            'token': token,
            'new_password': 'short'  # Less than 8 characters
        }
        response = self.client.post(self.password_reset_confirm_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)

    def test_invalid_uid_returns_error(self):
        """Test that invalid uid returns error."""
        # Generate valid token but use invalid uid
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self.user)
        invalid_uid = 'invalid-uid-string'

        data = {
            'uid': invalid_uid,
            'token': token,
            'new_password': 'NewSecureP@ss123'
        }
        response = self.client.post(self.password_reset_confirm_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Invalid reset link', response.data['error'])
