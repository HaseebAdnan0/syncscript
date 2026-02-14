"""Tests for Pusher authentication endpoint."""
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User


class PusherAuthTestCase(TestCase):
    """Test Pusher channel authentication endpoint."""

    def setUp(self) -> None:
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/v1/notifications/pusher/auth/'

    def test_successful_auth(self) -> None:
        """Test successful Pusher channel authentication."""
        channel_name = f'private-user-{self.user.id}'
        socket_id = 'test-socket-123'

        mock_auth_response = {
            'auth': 'mock-auth-signature:abc123',
            'channel_data': None
        }

        with patch('apps.notifications.views.get_pusher_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.authenticate.return_value = mock_auth_response
            mock_get_client.return_value = mock_client

            response = self.client.post(
                self.url,
                {'channel_name': channel_name, 'socket_id': socket_id},
                format='json'
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, mock_auth_response)  # type: ignore[attr-defined]
            mock_client.authenticate.assert_called_once_with(
                channel=channel_name,
                socket_id=socket_id
            )

    def test_rejects_wrong_channel(self) -> None:
        """Test authentication fails when channel doesn't match user."""
        different_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass'
        )
        wrong_channel = f'private-user-{different_user.id}'

        response = self.client.post(
            self.url,
            {'channel_name': wrong_channel, 'socket_id': 'test-socket'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Unauthorized', str(response.data))  # type: ignore[attr-defined]

    def test_requires_channel_name(self) -> None:
        """Test channel_name is required."""
        response = self.client.post(
            self.url,
            {'socket_id': 'test-socket'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('channel_name and socket_id are required', str(response.data))  # type: ignore[attr-defined]

    def test_requires_socket_id(self) -> None:
        """Test socket_id is required."""
        response = self.client.post(
            self.url,
            {'channel_name': f'private-user-{self.user.id}'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('channel_name and socket_id are required', str(response.data))  # type: ignore[attr-defined]

    def test_pusher_not_configured(self) -> None:
        """Test graceful handling when Pusher is not configured."""
        channel_name = f'private-user-{self.user.id}'

        with patch('apps.notifications.views.get_pusher_client') as mock_get_client:
            mock_get_client.return_value = None  # Pusher not configured

            response = self.client.post(
                self.url,
                {'channel_name': channel_name, 'socket_id': 'test-socket'},
                format='json'
            )

            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            self.assertIn('Pusher not configured', str(response.data))  # type: ignore[attr-defined]

    def test_pusher_auth_exception(self) -> None:
        """Test graceful handling when Pusher authentication throws exception."""
        channel_name = f'private-user-{self.user.id}'

        with patch('apps.notifications.views.get_pusher_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.authenticate.side_effect = Exception('Pusher connection error')
            mock_get_client.return_value = mock_client

            response = self.client.post(
                self.url,
                {'channel_name': channel_name, 'socket_id': 'test-socket'},
                format='json'
            )

            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('Pusher authentication failed', str(response.data))  # type: ignore[attr-defined]

    def test_requires_authentication(self) -> None:
        """Test endpoint requires authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self.url,
            {'channel_name': 'private-user-123', 'socket_id': 'test-socket'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rejects_public_channel(self) -> None:
        """Test authentication rejects non-private channels."""
        response = self.client.post(
            self.url,
            {'channel_name': 'public-channel', 'socket_id': 'test-socket'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Unauthorized', str(response.data))  # type: ignore[attr-defined]
