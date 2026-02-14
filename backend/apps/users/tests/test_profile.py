from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User


class ProfileEndpointTests(TestCase):
    """Tests for profile management endpoints."""

    def setUp(self):
        """Create test user and API client."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='SecurePassword123',
            email_verified=True
        )
        self.profile_url = reverse('users:profile')

    def test_get_profile_returns_current_user_data(self):
        """Test GET /api/v1/users/profile/ returns authenticated user's data."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email_verified'], True)
        self.assertIn('id', response.data)
        self.assertIn('created_at', response.data)

    def test_patch_updates_allowed_fields(self):
        """Test PATCH /api/v1/users/profile/ successfully updates avatar_url, bio, institution."""
        self.client.force_authenticate(user=self.user)
        update_data = {
            'avatar_url': 'https://example.com/avatar.png',
            'bio': 'Updated bio for researcher',
            'institution': 'MIT'
        }
        response = self.client.patch(self.profile_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Profile updated successfully.')
        self.assertEqual(response.data['user']['avatar_url'], 'https://example.com/avatar.png')
        self.assertEqual(response.data['user']['bio'], 'Updated bio for researcher')
        self.assertEqual(response.data['user']['institution'], 'MIT')

        # Verify database was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.avatar_url, 'https://example.com/avatar.png')
        self.assertEqual(self.user.bio, 'Updated bio for researcher')
        self.assertEqual(self.user.institution, 'MIT')

    def test_patch_rejects_email_changes(self):
        """Test PATCH /api/v1/users/profile/ rejects attempts to change email."""
        self.client.force_authenticate(user=self.user)
        update_data = {
            'email': 'newemail@example.com'
        }
        response = self.client.patch(self.profile_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Email and password cannot be changed through this endpoint.')

        # Verify email was not changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'test@example.com')

    def test_patch_rejects_password_changes(self):
        """Test PATCH /api/v1/users/profile/ rejects attempts to change password."""
        self.client.force_authenticate(user=self.user)
        update_data = {
            'password': 'NewPassword123'
        }
        response = self.client.patch(self.profile_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Email and password cannot be changed through this endpoint.')

    def test_unauthenticated_request_returns_401(self):
        """Test unauthenticated requests to profile endpoint return 401."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.patch(self.profile_url, {'bio': 'Test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_field_length_validation_bio(self):
        """Test bio field length validation (max 500 chars)."""
        self.client.force_authenticate(user=self.user)
        long_bio = 'x' * 501
        update_data = {
            'bio': long_bio
        }
        response = self.client.patch(self.profile_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('bio', response.data)

    def test_field_length_validation_institution(self):
        """Test institution field length validation (max 200 chars)."""
        self.client.force_authenticate(user=self.user)
        long_institution = 'x' * 201
        update_data = {
            'institution': long_institution
        }
        response = self.client.patch(self.profile_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('institution', response.data)

    def test_partial_update_single_field(self):
        """Test partial updates only modify specified fields."""
        self.client.force_authenticate(user=self.user)
        # Set initial values
        self.user.bio = 'Original bio'
        self.user.institution = 'Stanford'
        self.user.save()

        # Update only avatar_url
        update_data = {
            'avatar_url': 'https://example.com/new-avatar.png'
        }
        response = self.client.patch(self.profile_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['avatar_url'], 'https://example.com/new-avatar.png')

        # Verify other fields remained unchanged
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'Original bio')
        self.assertEqual(self.user.institution, 'Stanford')
