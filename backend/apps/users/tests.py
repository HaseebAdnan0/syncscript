"""
Tests for user registration and email verification.
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User


class UserModelTests(TestCase):
    """Tests for User model."""

    def test_create_user(self):
        """Test creating a user with email."""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPass123!'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertFalse(user.is_email_verified)
        self.assertTrue(user.check_password('TestPass123!'))

    def test_generate_verification_token(self):
        """Test verification token generation."""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPass123!'
        )
        token = user.generate_verification_token()
        self.assertIsNotNone(token)
        self.assertEqual(len(token), 64)
        self.assertEqual(user.email_verification_token, token)

    def test_verify_email(self):
        """Test email verification."""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPass123!'
        )
        user.generate_verification_token()
        token = user.email_verification_token

        user.verify_email()
        self.assertTrue(user.is_email_verified)
        self.assertIsNone(user.email_verification_token)


@override_settings(RATELIMIT_ENABLE=False)  # Disable rate limiting for tests
class RegistrationAPITests(APITestCase):
    """Tests for registration API endpoint."""

    def setUp(self):
        self.register_url = reverse('users:register')
        self.valid_payload = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'bio': 'Research scientist',
            'institution': 'MIT'
        }

    def test_register_user_success(self):
        """Test successful user registration."""
        response = self.client.post(self.register_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)

        # Verify user created
        user = User.objects.get(email='newuser@example.com')
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.bio, 'Research scientist')
        self.assertEqual(user.institution, 'MIT')
        self.assertFalse(user.is_email_verified)
        self.assertIsNotNone(user.email_verification_token)

        # Verify email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verify your SyncScript account', mail.outbox[0].subject)
        self.assertIn(user.email_verification_token, mail.outbox[0].body)

    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        User.objects.create_user(
            email='existing@example.com',
            username='existing',
            password='Pass123!'
        )

        payload = self.valid_payload.copy()
        payload['email'] = 'existing@example.com'
        payload['username'] = 'different'

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_duplicate_username(self):
        """Test registration with duplicate username."""
        User.objects.create_user(
            email='existing@example.com',
            username='existing',
            password='Pass123!'
        )

        payload = self.valid_payload.copy()
        payload['email'] = 'new@example.com'
        payload['username'] = 'existing'

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_register_password_mismatch(self):
        """Test registration with mismatched passwords."""
        payload = self.valid_payload.copy()
        payload['password_confirm'] = 'DifferentPass123!'

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)

    def test_register_weak_password(self):
        """Test registration with weak password."""
        payload = self.valid_payload.copy()
        payload['password'] = '123'
        payload['password_confirm'] = '123'

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_missing_required_fields(self):
        """Test registration with missing required fields."""
        response = self.client.post(self.register_url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('username', response.data)
        self.assertIn('password', response.data)

    def test_register_optional_fields(self):
        """Test registration without optional fields."""
        payload = {
            'email': 'minimal@example.com',
            'username': 'minimal',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='minimal@example.com')
        self.assertEqual(user.bio, '')
        self.assertEqual(user.institution, '')


@override_settings(RATELIMIT_ENABLE=False)
class EmailVerificationAPITests(APITestCase):
    """Tests for email verification API endpoint."""

    def setUp(self):
        self.verify_url = reverse('users:verify-email')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPass123!'
        )
        self.user.generate_verification_token()
        self.user.save()

    def test_verify_email_success(self):
        """Test successful email verification."""
        payload = {'token': self.user.email_verification_token}
        response = self.client.post(self.verify_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Verify user is now verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.assertIsNone(self.user.email_verification_token)

    def test_verify_email_invalid_token(self):
        """Test verification with invalid token."""
        payload = {'token': 'invalid-token-xyz'}
        response = self.client.post(self.verify_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_verify_email_already_verified(self):
        """Test verification when already verified."""
        self.user.verify_email()

        payload = {'token': 'any-token'}  # Token is cleared after verification
        response = self.client.post(self.verify_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_missing_token(self):
        """Test verification without token."""
        response = self.client.post(self.verify_url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('token', response.data)


@override_settings(RATELIMIT_ENABLE=False)
class ResendVerificationAPITests(APITestCase):
    """Tests for resend verification email endpoint."""

    def setUp(self):
        self.resend_url = reverse('users:resend-verification')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPass123!'
        )
        self.user.generate_verification_token()
        self.user.save()

    def test_resend_verification_success(self):
        """Test successful resend of verification email."""
        old_token = self.user.email_verification_token

        payload = {'email': 'test@example.com'}
        response = self.client.post(self.resend_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify new token generated
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.email_verification_token, old_token)

        # Verify email sent
        self.assertEqual(len(mail.outbox), 1)

    def test_resend_verification_already_verified(self):
        """Test resend when already verified."""
        self.user.verify_email()

        payload = {'email': 'test@example.com'}
        response = self.client.post(self.resend_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('already verified', response.data['message'])

    def test_resend_verification_nonexistent_email(self):
        """Test resend with nonexistent email (security - don't leak info)."""
        payload = {'email': 'nonexistent@example.com'}
        response = self.client.post(self.resend_url, payload, format='json')

        # Should return success to avoid email enumeration
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_verification_missing_email(self):
        """Test resend without email."""
        response = self.client.post(self.resend_url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


@override_settings(RATELIMIT_ENABLE=False)
class LoginAPITests(APITestCase):
    """Tests for JWT login API endpoint."""

    def setUp(self):
        self.login_url = reverse('users:login')
        # Create verified user
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPass123!'
        )
        self.user.is_email_verified = True
        self.user.save()

    def test_login_success(self):
        """Test successful login with email and password."""
        payload = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

        # Verify user data in response
        user_data = response.data['user']
        self.assertEqual(user_data['email'], 'test@example.com')
        self.assertEqual(user_data['username'], 'testuser')
        self.assertTrue(user_data['is_email_verified'])

    def test_login_with_httponly_cookie(self):
        """Test login with refresh token in httpOnly cookie."""
        payload = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'use_cookie': True
        }
        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        # Verify cookie is set
        self.assertIn('refresh_token', response.cookies)
        cookie = response.cookies['refresh_token']
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['samesite'], 'Lax')
        self.assertEqual(cookie['max-age'], 60 * 60 * 24 * 7)  # 7 days

    def test_login_invalid_email(self):
        """Test login with invalid email."""
        payload = {
            'email': 'wrong@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_invalid_password(self):
        """Test login with invalid password."""
        payload = {
            'email': 'test@example.com',
            'password': 'WrongPassword123!'
        }
        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_fields(self):
        """Test login with missing required fields."""
        response = self.client.post(self.login_url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_unverified_user(self):
        """Test login with unverified email (should still work but flag is in token)."""
        # Create unverified user
        unverified_user = User.objects.create_user(
            email='unverified@example.com',
            username='unverified',
            password='TestPass123!'
        )
        unverified_user.is_email_verified = False
        unverified_user.save()

        payload = {
            'email': 'unverified@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['user']['is_email_verified'])

    def test_login_case_insensitive_email(self):
        """Test login with different email case."""
        payload = {
            'email': 'TEST@EXAMPLE.COM',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_contains_custom_claims(self):
        """Test that JWT tokens contain user_id and email claims."""
        import jwt
        from django.conf import settings

        payload = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decode access token to verify claims
        access_token = response.data['access']
        decoded = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=['HS256']
        )

        self.assertIn('user_id', decoded)
        self.assertIn('email', decoded)
        self.assertIn('is_email_verified', decoded)
        self.assertEqual(decoded['email'], 'test@example.com')
        self.assertTrue(decoded['is_email_verified'])


@override_settings(RATELIMIT_ENABLE=False)
class TokenRefreshAPITests(APITestCase):
    """Tests for JWT token refresh endpoint."""

    def setUp(self):
        self.login_url = reverse('users:login')
        self.refresh_url = reverse('users:token-refresh')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPass123!'
        )
        self.user.is_email_verified = True
        self.user.save()

        # Get tokens
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }, format='json')
        self.refresh_token = response.data['refresh']

    def test_refresh_token_success(self):
        """Test successful token refresh."""
        payload = {'refresh': self.refresh_token}
        response = self.client.post(self.refresh_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_token_invalid(self):
        """Test refresh with invalid token."""
        payload = {'refresh': 'invalid-token'}
        response = self.client.post(self.refresh_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
