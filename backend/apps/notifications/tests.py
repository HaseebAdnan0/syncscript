"""
Tests for notifications API endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Notification, NotificationPreferences, MutedVault

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


class NotificationPreferencesTestCase(TestCase):
    """Test notification preferences endpoints (US-009)."""

    def setUp(self) -> None:
        """Create test user."""
        self.user = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_preferences_returns_user_preferences(self) -> None:
        """Test GET /api/v1/notifications/preferences/ returns user's preferences."""
        response = self.client.get('/api/v1/notifications/preferences/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify response includes all expected fields
        self.assertIn('email_vault_activity', response.data)  # type: ignore[attr-defined]
        self.assertIn('email_mentions', response.data)  # type: ignore[attr-defined]
        self.assertIn('email_digest_frequency', response.data)  # type: ignore[attr-defined]
        self.assertIn('push_enabled', response.data)  # type: ignore[attr-defined]
        self.assertIn('push_sources', response.data)  # type: ignore[attr-defined]
        self.assertIn('push_annotations', response.data)  # type: ignore[attr-defined]

        # Verify default values
        self.assertTrue(response.data['email_vault_activity'])  # type: ignore[attr-defined]
        self.assertTrue(response.data['email_mentions'])  # type: ignore[attr-defined]
        self.assertEqual(response.data['email_digest_frequency'], 'daily')  # type: ignore[attr-defined]
        self.assertTrue(response.data['push_enabled'])  # type: ignore[attr-defined]
        self.assertTrue(response.data['push_sources'])  # type: ignore[attr-defined]
        self.assertTrue(response.data['push_annotations'])  # type: ignore[attr-defined]

    def test_get_preferences_auto_creates_if_missing(self) -> None:
        """Test GET auto-creates preferences if user doesn't have them yet."""
        # Delete any existing preferences (signal creates on user creation)
        NotificationPreferences.objects.filter(user=self.user).delete()

        # Verify no preferences exist
        self.assertFalse(NotificationPreferences.objects.filter(user=self.user).exists())

        # GET should auto-create
        response = self.client.get('/api/v1/notifications/preferences/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify preferences were created
        self.assertTrue(NotificationPreferences.objects.filter(user=self.user).exists())

    def test_patch_preferences_updates_fields(self) -> None:
        """Test PATCH /api/v1/notifications/preferences/ updates preferences."""
        # Update some preferences
        response = self.client.patch(
            '/api/v1/notifications/preferences/',
            data={
                'email_vault_activity': False,
                'email_digest_frequency': 'weekly',
                'push_enabled': False
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify response reflects updates
        self.assertFalse(response.data['email_vault_activity'])  # type: ignore[attr-defined]
        self.assertEqual(response.data['email_digest_frequency'], 'weekly')  # type: ignore[attr-defined]
        self.assertFalse(response.data['push_enabled'])  # type: ignore[attr-defined]

        # Verify database was updated
        prefs = NotificationPreferences.objects.get(user=self.user)
        self.assertFalse(prefs.email_vault_activity)
        self.assertEqual(prefs.email_digest_frequency, 'weekly')
        self.assertFalse(prefs.push_enabled)

    def test_patch_preferences_validates_frequency_choices(self) -> None:
        """Test PATCH validates email_digest_frequency choices."""
        response = self.client.patch(
            '/api/v1/notifications/preferences/',
            data={'email_digest_frequency': 'invalid_choice'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email_digest_frequency', response.data)  # type: ignore[attr-defined]

    def test_patch_preferences_partial_update(self) -> None:
        """Test PATCH allows partial updates without overwriting other fields."""
        # Set initial values
        prefs = NotificationPreferences.objects.get(user=self.user)
        prefs.email_vault_activity = False
        prefs.push_enabled = False
        prefs.save()

        # Update only one field
        response = self.client.patch(
            '/api/v1/notifications/preferences/',
            data={'email_digest_frequency': 'immediate'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify only specified field changed
        prefs.refresh_from_db()
        self.assertEqual(prefs.email_digest_frequency, 'immediate')
        self.assertFalse(prefs.email_vault_activity)  # Should remain unchanged
        self.assertFalse(prefs.push_enabled)  # Should remain unchanged

    def test_requires_authentication(self) -> None:
        """Test endpoint requires authentication."""
        client = APIClient()
        response = client.get('/api/v1/notifications/preferences/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = client.patch('/api/v1/notifications/preferences/', data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MutedVaultsTestCase(TestCase):
    """Test muted vaults endpoints (US-010)."""

    def setUp(self) -> None:
        """Create test user, vaults, and memberships."""
        # Import here to avoid circular dependency at module level
        from apps.vaults.models import Vault, VaultMembership

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

        # Create test vaults (owner membership auto-created by signal)
        self.vault1 = Vault.objects.create(
            name='Test Vault 1',
            owner=self.user
        )
        self.vault2 = Vault.objects.create(
            name='Test Vault 2',
            owner=self.other_user
        )

        # Add user as contributor to vault2 (vault1 membership already exists from owner signal)
        VaultMembership.objects.create(
            vault=self.vault2,
            user=self.user,
            role='CONTRIBUTOR'
        )

    def test_get_empty_muted_vaults(self) -> None:
        """Test GET /api/v1/notifications/muted-vaults/ returns empty list initially."""
        response = self.client.get('/api/v1/notifications/muted-vaults/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # type: ignore[attr-defined]

    def test_mute_vault(self) -> None:
        """Test POST /api/v1/notifications/muted-vaults/ mutes a vault."""
        response = self.client.post(
            '/api/v1/notifications/muted-vaults/',
            data={'vault_id': str(self.vault1.id)}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['vault_id'], self.vault1.id)  # type: ignore[attr-defined]
        self.assertEqual(response.data['vault_name'], self.vault1.name)  # type: ignore[attr-defined]

        # Verify muted vault was created in database
        self.assertTrue(
            MutedVault.objects.filter(user=self.user, vault=self.vault1).exists()
        )

    def test_mute_vault_idempotent(self) -> None:
        """Test muting same vault twice is idempotent."""
        # First mute
        response1 = self.client.post(
            '/api/v1/notifications/muted-vaults/',
            data={'vault_id': str(self.vault1.id)}
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second mute
        response2 = self.client.post(
            '/api/v1/notifications/muted-vaults/',
            data={'vault_id': str(self.vault1.id)}
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Verify only one MutedVault record exists
        self.assertEqual(
            MutedVault.objects.filter(user=self.user, vault=self.vault1).count(),
            1
        )

    def test_mute_vault_requires_vault_id(self) -> None:
        """Test POST without vault_id returns 400."""
        response = self.client.post(
            '/api/v1/notifications/muted-vaults/',
            data={}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('vault_id', response.data['detail'])  # type: ignore[attr-defined]

    def test_mute_vault_validates_membership(self) -> None:
        """Test cannot mute a vault user is not a member of."""
        from apps.vaults.models import Vault

        # Create a vault the user is not a member of
        vault_not_member = Vault.objects.create(
            name='Not Member Vault',
            owner=self.other_user
        )

        response = self.client.post(
            '/api/v1/notifications/muted-vaults/',
            data={'vault_id': str(vault_not_member.id)}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('member', response.data['detail'].lower())  # type: ignore[attr-defined]

    def test_mute_vault_validates_vault_exists(self) -> None:
        """Test muting non-existent vault returns 404."""
        import uuid
        fake_id = uuid.uuid4()

        response = self.client.post(
            '/api/v1/notifications/muted-vaults/',
            data={'vault_id': str(fake_id)}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_muted_vaults(self) -> None:
        """Test GET returns list of muted vaults with details."""
        # Mute both vaults
        MutedVault.objects.create(user=self.user, vault=self.vault1)
        MutedVault.objects.create(user=self.user, vault=self.vault2)

        response = self.client.get('/api/v1/notifications/muted-vaults/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # type: ignore[attr-defined]

        # Verify vault details are included
        vault_ids = [item['vault_id'] for item in response.data]  # type: ignore[attr-defined]
        self.assertIn(self.vault1.id, vault_ids)
        self.assertIn(self.vault2.id, vault_ids)

    def test_unmute_vault(self) -> None:
        """Test DELETE /api/v1/notifications/muted-vaults/{vault_id}/ unmutes a vault."""
        # Mute vault first
        MutedVault.objects.create(user=self.user, vault=self.vault1)

        response = self.client.delete(
            f'/api/v1/notifications/muted-vaults/{self.vault1.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify muted vault was deleted
        self.assertFalse(
            MutedVault.objects.filter(user=self.user, vault=self.vault1).exists()
        )

    def test_unmute_vault_idempotent(self) -> None:
        """Test unmuting a vault that isn't muted is idempotent."""
        response = self.client.delete(
            f'/api/v1/notifications/muted-vaults/{self.vault1.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_muted_vaults_filters_by_user(self) -> None:
        """Test GET only returns current user's muted vaults."""
        # User mutes vault1
        MutedVault.objects.create(user=self.user, vault=self.vault1)
        # Other user mutes vault2
        MutedVault.objects.create(user=self.other_user, vault=self.vault2)

        response = self.client.get('/api/v1/notifications/muted-vaults/')
        self.assertEqual(len(response.data), 1)  # type: ignore[attr-defined]
        self.assertEqual(response.data[0]['vault_id'], self.vault1.id)  # type: ignore[attr-defined]

    def test_requires_authentication(self) -> None:
        """Test muted vaults endpoints require authentication."""
        client = APIClient()

        response = client.get('/api/v1/notifications/muted-vaults/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = client.post('/api/v1/notifications/muted-vaults/', data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = client.delete(f'/api/v1/notifications/muted-vaults/{self.vault1.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
