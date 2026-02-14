from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification, NotificationPreferences

User = get_user_model()


class MentionSignalTestCase(TestCase):
    """Test mention notification signal (US-017)."""

    def setUp(self) -> None:
        """Create test users, vault, source."""
        from apps.vaults.models import Vault, VaultMembership
        from apps.sources.models import Source

        self.user1 = User.objects.create_user(  # type: ignore[attr-defined]
            username='alice',
            email='alice@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(  # type: ignore[attr-defined]
            username='bob',
            email='bob@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(  # type: ignore[attr-defined]
            username='charlie',
            email='charlie@example.com',
            password='testpass123'
        )

        self.vault = Vault.objects.create(
            name='Test Vault',
            owner=self.user1
        )
        # Add user2 and user3 as members
        VaultMembership.objects.create(
            vault=self.vault,
            user=self.user2,
            added_by=self.user1
        )
        VaultMembership.objects.create(
            vault=self.vault,
            user=self.user3,
            added_by=self.user1
        )

        self.source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/paper',
            title='Test Paper',
            created_by=self.user1
        )

    def test_signal_creates_mention_notification(self) -> None:
        """Test notification created when user is mentioned."""
        from apps.annotations.models import Annotation

        # Clear vault invite notifications
        Notification.objects.all().delete()

        # User1 mentions user2 in annotation
        Annotation.objects.create(
            source=self.source,
            user=self.user1,
            content='Hey @bob what do you think about this?'
        )

        # Verify user2 received mention notification
        notifications = Notification.objects.filter(
            user=self.user2,
            type='mention'
        )
        self.assertEqual(notifications.count(), 1)

        notification = notifications.first()
        self.assertEqual(notification.title, f'{self.user1.username} mentioned you')  # type: ignore[union-attr]
        self.assertIn(self.user1.username, notification.body)  # type: ignore[union-attr]
        self.assertIn('mentioned you', notification.body)  # type: ignore[union-attr]

        # Verify data
        self.assertEqual(notification.data['source_id'], self.source.id)  # type: ignore[union-attr, index]
        self.assertEqual(notification.data['mentioner_name'], self.user1.username)  # type: ignore[union-attr, index]
        self.assertIn('preview', notification.data)  # type: ignore[union-attr, index]

    def test_signal_creates_multiple_mention_notifications(self) -> None:
        """Test notifications created for multiple mentions."""
        from apps.annotations.models import Annotation

        # Clear vault invite notifications
        Notification.objects.all().delete()

        # User1 mentions both user2 and user3
        Annotation.objects.create(
            source=self.source,
            user=self.user1,
            content='Hey @bob and @charlie, check this out!'
        )

        # Verify user2 received notification
        user2_notifications = Notification.objects.filter(
            user=self.user2,
            type='mention'
        )
        self.assertEqual(user2_notifications.count(), 1)

        # Verify user3 received notification
        user3_notifications = Notification.objects.filter(
            user=self.user3,
            type='mention'
        )
        self.assertEqual(user3_notifications.count(), 1)

    def test_signal_does_not_notify_self_mention(self) -> None:
        """Test user doesn't get notified when mentioning themselves."""
        from apps.annotations.models import Annotation

        # Clear notifications
        Notification.objects.all().delete()

        # User1 mentions themselves
        Annotation.objects.create(
            source=self.source,
            user=self.user1,
            content='Reminding myself: @alice don\'t forget this'
        )

        # Verify user1 did NOT receive mention notification
        notifications = Notification.objects.filter(
            user=self.user1,
            type='mention'
        )
        self.assertEqual(notifications.count(), 0)

    def test_signal_does_not_duplicate_annotation_reply_notification(self) -> None:
        """Test no duplicate if mentioned user is also parent annotation author."""
        from apps.annotations.models import Annotation

        # Clear notifications
        Notification.objects.all().delete()

        # User2 creates an annotation
        parent = Annotation.objects.create(
            source=self.source,
            user=self.user2,
            content='This is the parent annotation'
        )

        # User1 replies and mentions user2
        Annotation.objects.create(
            source=self.source,
            user=self.user1,
            content='@bob I agree with your point',
            parent=parent
        )

        # Verify user2 only got annotation_reply notification, not duplicate mention
        reply_notifications = Notification.objects.filter(
            user=self.user2,
            type='annotation_reply'
        )
        self.assertEqual(reply_notifications.count(), 1)

        mention_notifications = Notification.objects.filter(
            user=self.user2,
            type='mention'
        )
        self.assertEqual(mention_notifications.count(), 0)

    def test_signal_respects_email_mentions_preference(self) -> None:
        """Test signal respects email_mentions preference."""
        from apps.annotations.models import Annotation

        # User2 disables mention notifications
        prefs, _ = NotificationPreferences.objects.get_or_create(user=self.user2)
        prefs.email_mentions = False
        prefs.save()

        # User1 mentions user2
        Annotation.objects.create(
            source=self.source,
            user=self.user1,
            content='Hey @bob what do you think?'
        )

        # Verify no notification was created (preference disabled)
        notifications = Notification.objects.filter(
            user=self.user2,
            type='mention'
        )
        self.assertEqual(notifications.count(), 0)

    def test_signal_ignores_non_vault_members(self) -> None:
        """Test mentions of non-vault members are ignored."""
        from apps.annotations.models import Annotation

        # Create a user who is not a vault member
        non_member = User.objects.create_user(  # type: ignore[attr-defined]
            username='outsider',
            email='outsider@example.com',
            password='testpass123'
        )

        # Clear notifications
        Notification.objects.all().delete()

        # User1 mentions non-member
        Annotation.objects.create(
            source=self.source,
            user=self.user1,
            content='Hey @outsider this is interesting'
        )

        # Verify no notification was created for non-member
        notifications = Notification.objects.filter(
            user=non_member,
            type='mention'
        )
        self.assertEqual(notifications.count(), 0)

    def test_signal_handles_mention_and_reply_to_different_user(self) -> None:
        """Test both annotation_reply and mention notifications can be created."""
        from apps.annotations.models import Annotation

        # Clear notifications
        Notification.objects.all().delete()

        # User2 creates an annotation
        parent = Annotation.objects.create(
            source=self.source,
            user=self.user2,
            content='What do you all think?'
        )

        # User1 replies to user2 and mentions user3
        Annotation.objects.create(
            source=self.source,
            user=self.user1,
            content='@charlie you should see this too',
            parent=parent
        )

        # Verify user2 got annotation_reply notification
        user2_notifications = Notification.objects.filter(
            user=self.user2,
            type='annotation_reply'
        )
        self.assertEqual(user2_notifications.count(), 1)

        # Verify user3 got mention notification
        user3_notifications = Notification.objects.filter(
            user=self.user3,
            type='mention'
        )
        self.assertEqual(user3_notifications.count(), 1)
