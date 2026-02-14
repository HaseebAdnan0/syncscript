"""
Integration tests for OAuth authentication flows (Google, GitHub).
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.models import User
from allauth.socialaccount.models import SocialAccount, SocialApp
from django.contrib.sites.models import Site


class OAuthFlowTestCase(TestCase):
    """Base test case for OAuth flows with common setup."""

    def setUp(self):
        self.client = APIClient()

        # Create site for allauth
        self.site = Site.objects.get_current()

        # Create Google OAuth app
        self.google_app = SocialApp.objects.create(
            provider='google',
            name='Google OAuth',
            client_id='test-google-client-id',
            secret='test-google-secret',
        )
        self.google_app.sites.add(self.site)

        # Create GitHub OAuth app
        self.github_app = SocialApp.objects.create(
            provider='github',
            name='GitHub OAuth',
            client_id='test-github-client-id',
            secret='test-github-secret',
        )
        self.github_app.sites.add(self.site)


class AccountLinkingTests(OAuthFlowTestCase):
    """Test account linking flow with password confirmation."""

    def setUp(self):
        super().setUp()
        self.link_url = reverse('users:oauth-link')

        # Create existing user with password
        self.existing_user = User.objects.create_user(
            email='existing@example.com',
            username='existinguser',
            password='SecureP@ss123!'
        )

    def test_link_oauth_validates_password(self):
        """Test that linking OAuth account validates password correctly."""
        # Authenticate as existing user
        self.client.force_authenticate(user=self.existing_user)

        # Store pending OAuth data in session
        session = self.client.session
        session['pending_oauth'] = {
            'provider': 'google',
            'uid': '123456789',
            'email': 'existing@example.com',
            'extra_data': {
                'email': 'existing@example.com',
                'name': 'Existing User',
                'picture': 'https://example.com/photo.jpg'
            }
        }
        session['oauth_needs_linking'] = True
        session.save()

        # Attempt to link with correct password
        data = {
            'password': 'SecureP@ss123!',
            'provider': 'google'
        }
        response = self.client.post(self.link_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Verify SocialAccount was created
        self.assertTrue(
            SocialAccount.objects.filter(
                user=self.existing_user,
                provider='google'
            ).exists()
        )

    def test_link_oauth_rejects_wrong_password(self):
        """Test that linking OAuth account rejects incorrect password."""
        self.client.force_authenticate(user=self.existing_user)

        # Store pending OAuth data in session
        session = self.client.session
        session['pending_oauth'] = {
            'provider': 'google',
            'uid': '123456789',
            'email': 'existing@example.com',
            'extra_data': {'email': 'existing@example.com'}
        }
        session['oauth_needs_linking'] = True
        session.save()

        # Attempt to link with wrong password
        data = {
            'password': 'WrongPassword!',
            'provider': 'google'
        }
        response = self.client.post(self.link_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

        # Verify SocialAccount was NOT created
        self.assertFalse(
            SocialAccount.objects.filter(
                user=self.existing_user,
                provider='google'
            ).exists()
        )


class UnlinkOAuthTests(OAuthFlowTestCase):
    """Test OAuth provider unlinking flow."""

    def setUp(self):
        super().setUp()

        # Create user with password and OAuth account
        self.user_with_both = User.objects.create_user(
            email='both@example.com',
            username='bothuser',
            password='SecureP@ss123!'
        )
        self.google_account = SocialAccount.objects.create(
            user=self.user_with_both,
            provider='google',
            uid='123456789',
            extra_data={'email': 'both@example.com'}
        )

        # Create OAuth-only user
        self.oauth_only_user = User.objects.create_user(
            email='oauth@example.com',
            username='oauthuser',
            password=None  # No password
        )
        self.oauth_only_user.set_unusable_password()
        self.oauth_only_user.save()

        self.oauth_account = SocialAccount.objects.create(
            user=self.oauth_only_user,
            provider='google',
            uid='987654321',
            extra_data={'email': 'oauth@example.com'}
        )

    def test_unlink_prevents_removing_last_auth_method(self):
        """Test that unlinking prevents removing the only auth method."""
        self.client.force_authenticate(user=self.oauth_only_user)

        unlink_url = reverse('users:oauth-disconnect', kwargs={'provider': 'google'})
        response = self.client.delete(unlink_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

        # Verify SocialAccount still exists
        self.assertTrue(
            SocialAccount.objects.filter(
                user=self.oauth_only_user,
                provider='google'
            ).exists()
        )

    def test_unlink_succeeds_when_password_exists(self):
        """Test that unlinking succeeds when user has password auth."""
        self.client.force_authenticate(user=self.user_with_both)

        unlink_url = reverse('users:oauth-disconnect', kwargs={'provider': 'google'})
        response = self.client.delete(unlink_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify SocialAccount was deleted
        self.assertFalse(
            SocialAccount.objects.filter(
                user=self.user_with_both,
                provider='google'
            ).exists()
        )


class ConnectedAccountsTests(OAuthFlowTestCase):
    """Test connected accounts endpoint."""

    def setUp(self):
        super().setUp()
        self.connected_url = reverse('users:oauth-connected')

        # Create user with multiple OAuth accounts
        self.user = User.objects.create_user(
            email='multi@example.com',
            username='multiuser',
            password='SecureP@ss123!'
        )

        # Create Google account
        self.google_account = SocialAccount.objects.create(
            user=self.user,
            provider='google',
            uid='123456789',
            extra_data={
                'email': 'multi@example.com',
                'name': 'Multi User',
                'picture': 'https://example.com/photo.jpg'
            }
        )

        # Create GitHub account
        self.github_account = SocialAccount.objects.create(
            user=self.user,
            provider='github',
            uid='987654321',
            extra_data={
                'email': 'multi@example.com',
                'login': 'multiuser',
                'avatar_url': 'https://github.com/avatar.png'
            }
        )

    def test_connected_accounts_returns_correct_data(self):
        """Test that connected accounts endpoint returns all providers with metadata."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.connected_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Check Google account data
        google_data = next(acc for acc in response.data if acc['provider'] == 'google')
        self.assertEqual(google_data['email'], 'multi@example.com')
        self.assertIn('profile_picture', google_data)
        self.assertEqual(google_data['profile_picture'], 'https://example.com/photo.jpg')

        # Check GitHub account data
        github_data = next(acc for acc in response.data if acc['provider'] == 'github')
        self.assertEqual(github_data['email'], 'multi@example.com')
        self.assertIn('username', github_data)
        self.assertEqual(github_data['username'], 'multiuser')
        self.assertIn('avatar_url', github_data)

    def test_connected_accounts_returns_empty_for_no_oauth(self):
        """Test that endpoint returns empty array when no OAuth accounts."""
        # Create user without OAuth accounts
        user_no_oauth = User.objects.create_user(
            email='nooauth@example.com',
            username='nooauthuser',
            password='SecureP@ss123!'
        )

        self.client.force_authenticate(user=user_no_oauth)
        response = self.client.get(self.connected_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class CompleteOAuthEmailTests(OAuthFlowTestCase):
    """Test OAuth email completion flow (for GitHub private email)."""

    def setUp(self):
        super().setUp()
        self.complete_email_url = reverse('users:oauth-complete-email')

    def test_complete_email_creates_user_when_email_new(self):
        """Test that completing email creates user when email is new."""
        # Store pending OAuth data in session
        session = self.client.session
        session['pending_oauth'] = {
            'provider': 'github',
            'uid': '123456789',
            'extra_data': {
                'login': 'testuser',
                'avatar_url': 'https://github.com/avatar.png'
            }
        }
        session['oauth_needs_email'] = True
        session['oauth_temp_token'] = 'test-temp-token-123'
        session.save()

        # Submit email
        data = {
            'email': 'newemail@example.com',
            'temp_token': 'test-temp-token-123'
        }
        response = self.client.post(self.complete_email_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)

        # Verify user and SocialAccount were created
        user = User.objects.get(email='newemail@example.com')
        self.assertTrue(user.email_verified)
        self.assertTrue(
            SocialAccount.objects.filter(
                user=user,
                provider='github'
            ).exists()
        )

    def test_complete_email_returns_link_required_when_email_exists(self):
        """Test that completing email returns link_required when email already exists."""
        # Create existing user
        existing_user = User.objects.create_user(
            email='existing@example.com',
            username='existinguser',
            password='SecureP@ss123!'
        )

        # Store pending OAuth data in session
        session = self.client.session
        session['pending_oauth'] = {
            'provider': 'github',
            'uid': '123456789',
            'extra_data': {'login': 'testuser'}
        }
        session['oauth_needs_email'] = True
        session['oauth_temp_token'] = 'test-temp-token-456'
        session.save()

        # Submit existing email
        data = {
            'email': 'existing@example.com',
            'temp_token': 'test-temp-token-456'
        }
        response = self.client.post(self.complete_email_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['link_required'])

        # Verify session updated for linking flow
        session = self.client.session
        self.assertTrue(session.get('oauth_needs_linking'))
        self.assertFalse(session.get('oauth_needs_email', False))
