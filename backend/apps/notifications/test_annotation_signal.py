from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification, NotificationPreferences

User = get_user_model()


class AnnotationReplySignalTestCase(TestCase):
    """Test annotation_reply notification signal (US-015)."""

    def setUp(self) -> None:
        """Create test users, vault, source, and annotation."""
        from apps.vaults.models import Vault
        from apps.sources.models import Source
        from apps.annotations.models import Annotation

        self.user1 = User.objects.create_user(  # type: ignore[attr-defined]
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(  # type: ignore[attr-defined]
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.vault = Vault.objects.create(
            name='Test Vault',
            owner=self.user1
        )
        self.source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/paper',
            title='Test Paper',
            created_by=self.user1
        )
        # Create parent annotation
        self.parent_annotation = Annotation.objects.create(
            source=self.source,
            user=self.user1,
            content='This is the parent annotation'
        )

    def test_signal_creates_notification_on_reply(self) -> None:
        """Test notification created when someone replies to an annotation."""
        from apps.annotations.models import Annotation

        # User2 replies to user1's annotation
        reply = Annotation.objects.create(
            source=self.source,
            user=self.user2,
            content='This is a reply to the annotation',
            parent=self.parent_annotation
        )

        # Verify user1 received notification
        notifications = Notification.objects.filter(
            user=self.user1,
            type='annotation_reply'
        )
        self.assertEqual(notifications.count(), 1)

        notification = notifications.first()
        self.assertEqual(notification.title, 'Reply to your annotation')  # type: ignore[union-attr]
        self.assertIn(self.user2.username, notification.body)  # type: ignore[union-attr]
        self.assertIn(reply.content, notification.body)  # type: ignore[union-attr]

        # Verify data includes source, annotation, and reply info
        self.assertEqual(notification.data['source_id'], self.source.id)  # type: ignore[union-attr, index]
        self.assertEqual(notification.data['annotation_id'], reply.id)  # type: ignore[union-attr, index]
        self.assertEqual(notification.data['parent_id'], self.parent_annotation.id)  # type: ignore[union-attr, index]
        self.assertEqual(notification.data['replier_name'], self.user2.username)  # type: ignore[union-attr, index]
        self.assertIn('preview', notification.data)  # type: ignore[union-attr, index]

    def test_signal_truncates_long_preview(self) -> None:
        """Test preview is truncated to 100 characters."""
        from apps.annotations.models import Annotation

        # Create a long reply
        long_content = 'A' * 150
        Annotation.objects.create(
            source=self.source,
            user=self.user2,
            content=long_content,
            parent=self.parent_annotation
        )

        notification = Notification.objects.filter(
            user=self.user1,
            type='annotation_reply'
        ).first()

        preview = notification.data['preview']  # type: ignore[union-attr, index]
        self.assertEqual(len(preview), 103)  # 100 chars + "..."
        self.assertTrue(preview.endswith('...'))  # type: ignore[union-attr]

    def test_signal_does_not_notify_for_top_level_annotations(self) -> None:
        """Test signal doesn't fire for top-level annotations (no parent)."""
        from apps.annotations.models import Annotation

        # Clear notifications
        Notification.objects.all().delete()

        # Create top-level annotation (no parent)
        Annotation.objects.create(
            source=self.source,
            user=self.user2,
            content='This is a top-level annotation'
        )

        # Verify no notification was created
        notifications = Notification.objects.filter(type='annotation_reply')
        self.assertEqual(notifications.count(), 0)

    def test_signal_does_not_notify_self_reply(self) -> None:
        """Test user doesn't get notified when replying to their own annotation."""
        from apps.annotations.models import Annotation

        # Clear notifications
        Notification.objects.all().delete()

        # User1 replies to their own annotation
        Annotation.objects.create(
            source=self.source,
            user=self.user1,
            content='Reply to my own annotation',
            parent=self.parent_annotation
        )

        # Verify no notification was created
        notifications = Notification.objects.filter(
            user=self.user1,
            type='annotation_reply'
        )
        self.assertEqual(notifications.count(), 0)

    def test_signal_does_not_trigger_on_update(self) -> None:
        """Test signal doesn't fire when annotation is updated (only created)."""
        from apps.annotations.models import Annotation

        # Create reply
        reply = Annotation.objects.create(
            source=self.source,
            user=self.user2,
            content='Original reply',
            parent=self.parent_annotation
        )

        # Clear notifications
        Notification.objects.all().delete()

        # Update reply content
        reply.content = 'Updated reply'
        reply.save()

        # Verify no new notification was created
        notifications = Notification.objects.filter(type='annotation_reply')
        self.assertEqual(notifications.count(), 0)

    def test_signal_respects_email_mentions_preference(self) -> None:
        """Test signal respects email_mentions preference."""
        from apps.annotations.models import Annotation

        # User1 disables mention notifications
        prefs, _ = NotificationPreferences.objects.get_or_create(user=self.user1)
        prefs.email_mentions = False
        prefs.save()

        # User2 replies to user1's annotation
        Annotation.objects.create(
            source=self.source,
            user=self.user2,
            content='Reply with preference disabled',
            parent=self.parent_annotation
        )

        # Verify no notification was created (preference disabled)
        notifications = Notification.objects.filter(
            user=self.user1,
            type='annotation_reply'
        )
        self.assertEqual(notifications.count(), 0)
