"""
Tests for notifications API endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Notification

User = get_user_model()


class NotificationListTestCase(TestCase):
    """Test notification list endpoint (US-005)."""

    def setUp(self) -> None:
        """Create test user and notifications."""
        self.user = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(  # type: ignore[attr-defined]
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create test notifications
        self.notif1 = Notification.objects.create(
            user=self.user,
            type='vault_invite',
            title='Vault Invite',
            body='You were invited to a vault',
            data={}
        )
        self.notif2 = Notification.objects.create(
            user=self.user,
            type='source_added',
            title='Source Added',
            body='A new source was added',
            data={}
        )
        # Create notification for other user (should not appear)
        Notification.objects.create(
            user=self.other_user,
            type='mention',
            title='Mention',
            body='You were mentioned',
            data={}
        )

    def test_list_notifications(self) -> None:
        """Test GET /api/v1/notifications/ returns user's notifications."""
        response = self.client.get('/api/v1/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # type: ignore[attr-defined]
        self.assertEqual(len(response.data['results']), 2)  # type: ignore[attr-defined]

    def test_list_filters_by_user(self) -> None:
        """Test endpoint only returns authenticated user's notifications."""
        response = self.client.get('/api/v1/notifications/')
        notification_ids = [n['id'] for n in response.data['results']]  # type: ignore[attr-defined]
        self.assertIn(self.notif1.id, notification_ids)  # type: ignore[attr-defined]
        self.assertIn(self.notif2.id, notification_ids)  # type: ignore[attr-defined]

    def test_list_ordering(self) -> None:
        """Test notifications are ordered unread first, then by created_at desc."""
        # Mark second notification as read (created later)
        self.notif2.mark_as_read()

        response = self.client.get('/api/v1/notifications/')
        results = response.data['results']  # type: ignore[attr-defined]

        # Unread notification should come first (has NULL read_at)
        # Read notification comes second (has non-NULL read_at)
        unread_ids = [r['id'] for r in results if not r['is_read']]
        read_ids = [r['id'] for r in results if r['is_read']]

        self.assertIn(self.notif1.id, unread_ids)  # type: ignore[attr-defined]
        self.assertIn(self.notif2.id, read_ids)  # type: ignore[attr-defined]
        # Verify unread comes before read in the list
        self.assertFalse(results[0]['is_read'])
        self.assertTrue(results[1]['is_read'])

    def test_unread_only_filter(self) -> None:
        """Test ?unread_only=true filters to unread notifications."""
        # Mark one notification as read
        self.notif1.mark_as_read()

        response = self.client.get('/api/v1/notifications/?unread_only=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # type: ignore[attr-defined]
        self.assertEqual(response.data['results'][0]['id'], self.notif2.id)  # type: ignore[attr-defined]

    def test_pagination(self) -> None:
        """Test notifications are paginated with 20 items per page."""
        # Create 25 notifications
        for i in range(25):
            Notification.objects.create(
                user=self.user,
                type='vault_invite',
                title=f'Notification {i}',
                body='Test',
                data={}
            )

        response = self.client.get('/api/v1/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 20)  # type: ignore[attr-defined]
        self.assertEqual(response.data['count'], 27)  # type: ignore[attr-defined] # 25 + 2 from setUp

    def test_requires_authentication(self) -> None:
        """Test endpoint requires authentication."""
        client = APIClient()
        response = client.get('/api/v1/notifications/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MarkNotificationReadTestCase(TestCase):
    """Test mark notification as read endpoint (US-006)."""

    def setUp(self) -> None:
        """Create test user and notifications."""
        self.user = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(  # type: ignore[attr-defined]
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create test notification
        self.notification = Notification.objects.create(
            user=self.user,
            type='vault_invite',
            title='Vault Invite',
            body='You were invited to a vault',
            data={}
        )

    def test_mark_notification_as_read_patch(self) -> None:
        """Test PATCH /api/v1/notifications/{id}/mark-read/ marks notification as read."""
        self.assertIsNone(self.notification.read_at)

        response = self.client.patch(f'/api/v1/notifications/{self.notification.id}/mark-read/')  # type: ignore[attr-defined]
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify notification was marked as read
        self.notification.refresh_from_db()
        self.assertIsNotNone(self.notification.read_at)
        self.assertTrue(response.data['is_read'])  # type: ignore[attr-defined]

    def test_mark_notification_as_read_post(self) -> None:
        """Test POST /api/v1/notifications/{id}/mark-read/ marks notification as read."""
        self.assertIsNone(self.notification.read_at)

        response = self.client.post(f'/api/v1/notifications/{self.notification.id}/mark-read/')  # type: ignore[attr-defined]
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify notification was marked as read
        self.notification.refresh_from_db()
        self.assertIsNotNone(self.notification.read_at)
        self.assertTrue(response.data['is_read'])  # type: ignore[attr-defined]

    def test_mark_read_is_idempotent(self) -> None:
        """Test re-marking notification as read doesn't change timestamp."""
        # Mark as read first time
        response1 = self.client.patch(f'/api/v1/notifications/{self.notification.id}/mark-read/')  # type: ignore[attr-defined]
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        first_read_at = self.notification.read_at

        # Mark as read again
        response2 = self.client.patch(f'/api/v1/notifications/{self.notification.id}/mark-read/')  # type: ignore[attr-defined]
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()

        # Timestamp should not change
        self.assertEqual(self.notification.read_at, first_read_at)

    def test_only_owner_can_mark_read(self) -> None:
        """Test user can only mark their own notifications as read."""
        # Try to mark another user's notification
        other_notification = Notification.objects.create(
            user=self.other_user,
            type='mention',
            title='Mention',
            body='You were mentioned',
            data={}
        )

        response = self.client.patch(f'/api/v1/notifications/{other_notification.id}/mark-read/')  # type: ignore[attr-defined]
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_read_returns_updated_notification(self) -> None:
        """Test endpoint returns updated notification data."""
        response = self.client.patch(f'/api/v1/notifications/{self.notification.id}/mark-read/')  # type: ignore[attr-defined]
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify response includes notification data
        self.assertEqual(response.data['id'], self.notification.id)  # type: ignore[attr-defined]
        self.assertEqual(response.data['type'], 'vault_invite')  # type: ignore[attr-defined]
        self.assertTrue(response.data['is_read'])  # type: ignore[attr-defined]

    def test_requires_authentication(self) -> None:
        """Test endpoint requires authentication."""
        client = APIClient()
        response = client.patch(f'/api/v1/notifications/{self.notification.id}/mark-read/')  # type: ignore[attr-defined]
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UnreadCountTestCase(TestCase):
    """Test unread notification count endpoint (US-005)."""

    def setUp(self) -> None:
        """Create test user and notifications."""
        self.user = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_unread_count_with_no_notifications(self) -> None:
        """Test GET /api/v1/notifications/unread-count/ returns 0 when no notifications."""
        response = self.client.get('/api/v1/notifications/unread-count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'count': 0})  # type: ignore[attr-defined]

    def test_unread_count_with_unread_notifications(self) -> None:
        """Test unread count returns correct number of unread notifications."""
        # Create 3 unread notifications
        for i in range(3):
            Notification.objects.create(
                user=self.user,
                type='vault_invite',
                title=f'Notification {i}',
                body='Test',
                data={}
            )

        response = self.client.get('/api/v1/notifications/unread-count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'count': 3})  # type: ignore[attr-defined]

    def test_unread_count_excludes_read_notifications(self) -> None:
        """Test unread count only counts notifications with read_at=NULL."""
        # Create 5 notifications
        for i in range(5):
            notif = Notification.objects.create(
                user=self.user,
                type='vault_invite',
                title=f'Notification {i}',
                body='Test',
                data={}
            )
            # Mark first 2 as read
            if i < 2:
                notif.mark_as_read()

        response = self.client.get('/api/v1/notifications/unread-count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'count': 3})  # type: ignore[attr-defined] # 5 total - 2 read = 3 unread

    def test_unread_count_filters_by_user(self) -> None:
        """Test unread count only includes current user's notifications."""
        other_user = User.objects.create_user(  # type: ignore[attr-defined]
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        # Create notifications for both users
        Notification.objects.create(
            user=self.user,
            type='vault_invite',
            title='User notification',
            body='Test',
            data={}
        )
        Notification.objects.create(
            user=other_user,
            type='vault_invite',
            title='Other user notification',
            body='Test',
            data={}
        )

        response = self.client.get('/api/v1/notifications/unread-count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'count': 1})  # type: ignore[attr-defined] # Only current user's notification

    def test_requires_authentication(self) -> None:
        """Test endpoint requires authentication."""
        client = APIClient()
        response = client.get('/api/v1/notifications/unread-count/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MarkAllReadTestCase(TestCase):
    """Test mark all notifications as read endpoint (US-005)."""

    def setUp(self) -> None:
        """Create test user and notifications."""
        self.user = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_mark_all_read_with_no_notifications(self) -> None:
        """Test POST /api/v1/notifications/mark-all-read/ returns 0 when no notifications."""
        response = self.client.post('/api/v1/notifications/mark-all-read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'updated': 0})  # type: ignore[attr-defined]

    def test_mark_all_read_updates_all_unread(self) -> None:
        """Test mark all read updates all unread notifications for user."""
        # Create 5 unread notifications
        notifications = []
        for i in range(5):
            notif = Notification.objects.create(
                user=self.user,
                type='vault_invite',
                title=f'Notification {i}',
                body='Test',
                data={}
            )
            notifications.append(notif)

        response = self.client.post('/api/v1/notifications/mark-all-read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'updated': 5})  # type: ignore[attr-defined]

        # Verify all notifications are now read
        for notif in notifications:
            notif.refresh_from_db()
            self.assertIsNotNone(notif.read_at)
            self.assertTrue(notif.is_read)

    def test_mark_all_read_only_updates_unread(self) -> None:
        """Test mark all read only updates unread notifications, not already read ones."""
        # Create 5 notifications, mark 2 as read
        for i in range(5):
            notif = Notification.objects.create(
                user=self.user,
                type='vault_invite',
                title=f'Notification {i}',
                body='Test',
                data={}
            )
            if i < 2:
                notif.mark_as_read()

        response = self.client.post('/api/v1/notifications/mark-all-read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'updated': 3})  # type: ignore[attr-defined] # Only 3 were unread

        # Verify all 5 are now read
        unread_count = Notification.objects.filter(user=self.user, read_at__isnull=True).count()
        self.assertEqual(unread_count, 0)

    def test_mark_all_read_filters_by_user(self) -> None:
        """Test mark all read only affects current user's notifications."""
        other_user = User.objects.create_user(  # type: ignore[attr-defined]
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        # Create notifications for both users
        Notification.objects.create(
            user=self.user,
            type='vault_invite',
            title='User notification',
            body='Test',
            data={}
        )
        other_notif = Notification.objects.create(
            user=other_user,
            type='vault_invite',
            title='Other user notification',
            body='Test',
            data={}
        )

        response = self.client.post('/api/v1/notifications/mark-all-read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'updated': 1})  # type: ignore[attr-defined]

        # Verify other user's notification is still unread
        other_notif.refresh_from_db()
        self.assertIsNone(other_notif.read_at)
        self.assertFalse(other_notif.is_read)

    def test_requires_authentication(self) -> None:
        """Test endpoint requires authentication."""
        client = APIClient()
        response = client.post('/api/v1/notifications/mark-all-read/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
