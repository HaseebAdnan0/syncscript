"""
Tests for Pusher real-time notification integration (US-018).
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.notifications.services import create_notification

User = get_user_model()


class PusherIntegrationTestCase(TestCase):
    """Test Pusher integration in create_notification service."""

    def setUp(self) -> None:
        """Create test user."""
        self.user = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @patch('apps.notifications.services.get_pusher_client')
    def test_pusher_triggers_on_notification_creation(self, mock_get_client: MagicMock) -> None:
        """Test Pusher triggers notification event when notification is created."""
        # Setup mock client
        mock_pusher = MagicMock()
        mock_get_client.return_value = mock_pusher

        # Create notification (no vault_id to avoid UUID validation)
        notification = create_notification(
            user=self.user,
            notification_type='vault_invite',
            title='Test Notification',
            body='Test body',
            data={}
        )

        # Assert notification was created
        self.assertIsNotNone(notification)

        # Assert Pusher trigger was called twice (notification + badge_update)
        self.assertEqual(mock_pusher.trigger.call_count, 2)

        # Verify notification event
        first_call = mock_pusher.trigger.call_args_list[0]
        self.assertEqual(first_call[0][0], f'private-user-{self.user.id}')
        self.assertEqual(first_call[0][1], 'notification')
        # Verify payload contains notification data
        payload = first_call[0][2]
        self.assertEqual(payload['type'], 'vault_invite')
        self.assertEqual(payload['title'], 'Test Notification')

        # Verify badge_update event
        second_call = mock_pusher.trigger.call_args_list[1]
        self.assertEqual(second_call[0][0], f'private-user-{self.user.id}')
        self.assertEqual(second_call[0][1], 'badge_update')
        self.assertEqual(second_call[0][2]['count'], 1)

    @patch('apps.notifications.services.get_pusher_client')
    def test_badge_update_reflects_unread_count(self, mock_get_client: MagicMock) -> None:
        """Test badge_update event includes correct unread count."""
        # Setup mock client
        mock_pusher = MagicMock()
        mock_get_client.return_value = mock_pusher

        # Create first notification
        create_notification(
            user=self.user,
            notification_type='vault_invite',
            title='First',
            body='Body',
            data={}
        )

        # Create second notification
        create_notification(
            user=self.user,
            notification_type='source_added',
            title='Second',
            body='Body',
            data={}
        )

        # Last badge_update should show count of 2
        badge_calls = [
            call for call in mock_pusher.trigger.call_args_list
            if call[0][1] == 'badge_update'
        ]
        self.assertEqual(len(badge_calls), 2)
        self.assertEqual(badge_calls[1][0][2]['count'], 2)

    @patch('apps.notifications.services.get_pusher_client')
    def test_badge_count_excludes_read_notifications(self, mock_get_client: MagicMock) -> None:
        """Test badge count only includes unread notifications."""
        # Setup mock client
        mock_pusher = MagicMock()
        mock_get_client.return_value = mock_pusher

        # Create and mark as read
        notif1 = create_notification(
            user=self.user,
            notification_type='vault_invite',
            title='First',
            body='Body',
            data={}
        )
        assert notif1 is not None
        notif1.mark_as_read()

        # Create second (unread)
        create_notification(
            user=self.user,
            notification_type='source_added',
            title='Second',
            body='Body',
            data={}
        )

        # Last badge_update should show count of 1 (only unread)
        badge_calls = [
            call for call in mock_pusher.trigger.call_args_list
            if call[0][1] == 'badge_update'
        ]
        # Should have 2 badge updates total
        self.assertEqual(len(badge_calls), 2)
        # Last one should count only unread
        self.assertEqual(badge_calls[1][0][2]['count'], 1)

    @patch('apps.notifications.services.get_pusher_client')
    def test_pusher_skipped_when_not_configured(self, mock_get_client: MagicMock) -> None:
        """Test Pusher trigger is skipped when PUSHER_APP_ID is not configured."""
        # Return None to simulate no configuration
        mock_get_client.return_value = None

        # Create notification with no Pusher config
        notification = create_notification(
            user=self.user,
            notification_type='vault_invite',
            title='Test',
            body='Body',
            data={}
        )

        # Notification should still be created
        self.assertIsNotNone(notification)

        # get_pusher_client was called
        mock_get_client.assert_called_once()

    @patch('apps.notifications.services.get_pusher_client')
    def test_pusher_failure_does_not_block_notification(self, mock_get_client: MagicMock) -> None:
        """Test notification is created even if Pusher fails."""
        # Setup mock client that raises exception
        mock_pusher = MagicMock()
        mock_pusher.trigger.side_effect = Exception('Pusher error')
        mock_get_client.return_value = mock_pusher

        # Create notification
        notification = create_notification(
            user=self.user,
            notification_type='vault_invite',
            title='Test',
            body='Body',
            data={}
        )

        # Notification should still be created
        self.assertIsNotNone(notification)
        assert notification is not None
        self.assertEqual(notification.title, 'Test')

        # Pusher was attempted
        self.assertTrue(mock_pusher.trigger.called)

    @patch('apps.notifications.services.get_pusher_client')
    def test_pusher_uses_private_user_channel(self, mock_get_client: MagicMock) -> None:
        """Test Pusher uses correct private channel format."""
        # Setup mock client
        mock_pusher = MagicMock()
        mock_get_client.return_value = mock_pusher

        create_notification(
            user=self.user,
            notification_type='vault_invite',
            title='Test',
            body='Body',
            data={}
        )

        # Verify channel name format
        first_call = mock_pusher.trigger.call_args_list[0]
        channel_name = first_call[0][0]
        self.assertEqual(channel_name, f'private-user-{self.user.id}')
        self.assertTrue(channel_name.startswith('private-'))
