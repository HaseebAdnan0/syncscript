"""Tests for notification cleanup task"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.notifications.models import Notification
from apps.notifications.tasks import cleanup_old_notifications

User = get_user_model()


class CleanupNotificationsTaskTestCase(TestCase):
    """Test cases for cleanup_old_notifications task"""

    def setUp(self):
        """Set up test users and notifications"""
        self.user = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_deletes_read_notifications_older_than_7_days(self):
        """Test that read notifications older than 7 days are deleted"""
        # Create read notification older than 7 days
        old_read = Notification.objects.create(
            user=self.user,
            type='vault_invite',
            title='Old Read',
            body='Old read notification',
            data={},
            read_at=timezone.now() - timedelta(days=8)
        )
        # Update created_at to match read_at
        old_read.created_at = timezone.now() - timedelta(days=8)
        old_read.save()

        # Create recent read notification (should not be deleted)
        recent_read = Notification.objects.create(
            user=self.user,
            type='vault_invite',
            title='Recent Read',
            body='Recent read notification',
            data={},
            read_at=timezone.now() - timedelta(days=3)
        )

        # Run cleanup
        result = cleanup_old_notifications()

        # Verify old read was deleted
        self.assertFalse(Notification.objects.filter(id=old_read.id).exists())  # type: ignore[attr-defined]
        # Verify recent read still exists
        self.assertTrue(Notification.objects.filter(id=recent_read.id).exists())  # type: ignore[attr-defined]
        # Check result
        self.assertEqual(result['read_deleted'], 1)

    def test_deletes_unread_notifications_older_than_30_days(self):
        """Test that unread notifications older than 30 days are deleted"""
        # Create unread notification older than 30 days
        old_unread = Notification.objects.create(
            user=self.user,
            type='source_added',
            title='Old Unread',
            body='Old unread notification',
            data={}
        )
        # Update created_at using update() to bypass auto_now_add
        Notification.objects.filter(id=old_unread.id).update(  # type: ignore[attr-defined]
            created_at=timezone.now() - timedelta(days=31)
        )

        # Create recent unread notification (should not be deleted)
        recent_unread = Notification.objects.create(
            user=self.user,
            type='source_added',
            title='Recent Unread',
            body='Recent unread notification',
            data={}
        )

        # Run cleanup
        result = cleanup_old_notifications()

        # Verify old unread was deleted
        self.assertFalse(Notification.objects.filter(id=old_unread.id).exists())  # type: ignore[attr-defined]
        # Verify recent unread still exists
        self.assertTrue(Notification.objects.filter(id=recent_unread.id).exists())  # type: ignore[attr-defined]
        # Check result
        self.assertEqual(result['unread_deleted'], 1)

    def test_keeps_unread_notifications_under_30_days(self):
        """Test that unread notifications under 30 days are kept"""
        # Create unread notifications at various ages
        unread_20_days = Notification.objects.create(
            user=self.user,
            type='mention',
            title='20 Days Old',
            body='Unread notification 20 days old',
            data={}
        )
        Notification.objects.filter(id=unread_20_days.id).update(  # type: ignore[attr-defined]
            created_at=timezone.now() - timedelta(days=20)
        )

        unread_5_days = Notification.objects.create(
            user=self.user,
            type='mention',
            title='5 Days Old',
            body='Unread notification 5 days old',
            data={}
        )
        Notification.objects.filter(id=unread_5_days.id).update(  # type: ignore[attr-defined]
            created_at=timezone.now() - timedelta(days=5)
        )

        # Run cleanup
        result = cleanup_old_notifications()

        # Verify both still exist
        self.assertTrue(Notification.objects.filter(id=unread_20_days.id).exists())  # type: ignore[attr-defined]
        self.assertTrue(Notification.objects.filter(id=unread_5_days.id).exists())  # type: ignore[attr-defined]
        # No unread should be deleted
        self.assertEqual(result['unread_deleted'], 0)

    def test_keeps_read_notifications_under_7_days(self):
        """Test that read notifications under 7 days are kept"""
        # Create read notification 3 days old
        recent_read = Notification.objects.create(
            user=self.user,
            type='annotation_reply',
            title='Recent',
            body='Recently read notification',
            data={},
            read_at=timezone.now() - timedelta(days=3)
        )

        # Run cleanup
        result = cleanup_old_notifications()

        # Verify it still exists
        self.assertTrue(Notification.objects.filter(id=recent_read.id).exists())  # type: ignore[attr-defined]
        # No read should be deleted
        self.assertEqual(result['read_deleted'], 0)

    def test_logs_deletion_counts(self):
        """Test that cleanup returns correct counts"""
        # Create old read notifications
        for i in range(3):
            notif = Notification.objects.create(
                user=self.user,
                type='vault_invite',
                title=f'Old Read {i}',
                body='Body',
                data={},
                read_at=timezone.now() - timedelta(days=10)
            )
            # Update created_at using update() to bypass auto_now_add
            Notification.objects.filter(id=notif.id).update(  # type: ignore[attr-defined]
                created_at=timezone.now() - timedelta(days=10)
            )

        # Create old unread notifications
        for i in range(2):
            notif = Notification.objects.create(
                user=self.user,
                type='source_added',
                title=f'Old Unread {i}',
                body='Body',
                data={}
            )
            # Update created_at using update() to bypass auto_now_add
            Notification.objects.filter(id=notif.id).update(  # type: ignore[attr-defined]
                created_at=timezone.now() - timedelta(days=35)
            )

        # Run cleanup
        result = cleanup_old_notifications()

        # Verify counts
        self.assertEqual(result['read_deleted'], 3)
        self.assertEqual(result['unread_deleted'], 2)
        self.assertEqual(result['total'], 5)

    def test_handles_empty_database(self):
        """Test that cleanup works when there are no notifications"""
        # Run cleanup on empty database
        result = cleanup_old_notifications()

        # Verify zero counts
        self.assertEqual(result['read_deleted'], 0)
        self.assertEqual(result['unread_deleted'], 0)
        self.assertEqual(result['total'], 0)

    def test_mixed_notifications_cleanup(self):
        """Test cleanup with mix of old and recent notifications"""
        # Old read (should be deleted)
        old_read = Notification.objects.create(
            user=self.user,
            type='vault_invite',
            title='Old Read',
            body='Body',
            data={},
            read_at=timezone.now() - timedelta(days=8)
        )
        Notification.objects.filter(id=old_read.id).update(  # type: ignore[attr-defined]
            created_at=timezone.now() - timedelta(days=8)
        )

        # Recent read (should be kept)
        recent_read = Notification.objects.create(
            user=self.user,
            type='member_joined',
            title='Recent Read',
            body='Body',
            data={},
            read_at=timezone.now() - timedelta(days=2)
        )

        # Old unread (should be deleted)
        old_unread = Notification.objects.create(
            user=self.user,
            type='source_added',
            title='Old Unread',
            body='Body',
            data={}
        )
        Notification.objects.filter(id=old_unread.id).update(  # type: ignore[attr-defined]
            created_at=timezone.now() - timedelta(days=35)
        )

        # Recent unread (should be kept)
        recent_unread = Notification.objects.create(
            user=self.user,
            type='mention',
            title='Recent Unread',
            body='Body',
            data={}
        )

        # Run cleanup
        result = cleanup_old_notifications()

        # Verify old notifications deleted
        self.assertFalse(Notification.objects.filter(id=old_read.id).exists())  # type: ignore[attr-defined]
        self.assertFalse(Notification.objects.filter(id=old_unread.id).exists())  # type: ignore[attr-defined]

        # Verify recent notifications kept
        self.assertTrue(Notification.objects.filter(id=recent_read.id).exists())  # type: ignore[attr-defined]
        self.assertTrue(Notification.objects.filter(id=recent_unread.id).exists())  # type: ignore[attr-defined]

        # Verify counts
        self.assertEqual(result['read_deleted'], 1)
        self.assertEqual(result['unread_deleted'], 1)
        self.assertEqual(result['total'], 2)
