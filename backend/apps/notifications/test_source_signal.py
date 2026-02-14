from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification, NotificationPreferences, MutedVault

User = get_user_model()


class SourceAddedSignalTestCase(TestCase):
    """Test source_added notification signal (US-014)."""

    def setUp(self) -> None:
        """Create test users, vault, and members."""
        from apps.vaults.models import Vault, VaultMembership

        self.owner = User.objects.create_user(  # type: ignore[attr-defined]
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
        self.member1 = User.objects.create_user(  # type: ignore[attr-defined]
            username='member1',
            email='member1@example.com',
            password='testpass123'
        )
        self.member2 = User.objects.create_user(  # type: ignore[attr-defined]
            username='member2',
            email='member2@example.com',
            password='testpass123'
        )
        self.vault = Vault.objects.create(
            name='Test Vault',
            owner=self.owner
        )
        # Add members to vault
        VaultMembership.objects.create(
            vault=self.vault,
            user=self.member1,
            added_by=self.owner
        )
        VaultMembership.objects.create(
            vault=self.vault,
            user=self.member2,
            added_by=self.owner
        )

    def test_signal_creates_notifications_for_all_members(self) -> None:
        """Test all vault members except creator are notified of new source."""
        from apps.sources.models import Source

        # Owner adds a source (triggers signal)
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/paper',
            title='Test Research Paper',
            created_by=self.owner
        )

        # Verify member1 received notification
        member1_notifications = Notification.objects.filter(
            user=self.member1,
            type='source_added'
        )
        self.assertEqual(member1_notifications.count(), 1)

        notification = member1_notifications.first()
        self.assertEqual(notification.title, f'New source in {self.vault.name}')  # type: ignore[union-attr]
        self.assertIn(self.owner.username, notification.body)  # type: ignore[union-attr]
        self.assertIn(source.title, notification.body)  # type: ignore[union-attr]
        self.assertIn(self.vault.name, notification.body)  # type: ignore[union-attr]

        # Verify data includes vault, source, and creator info
        self.assertEqual(notification.data['vault_id'], str(self.vault.id))  # type: ignore[union-attr, index]
        self.assertEqual(notification.data['vault_name'], self.vault.name)  # type: ignore[union-attr, index]
        self.assertEqual(notification.data['source_id'], source.id)  # type: ignore[union-attr, index]
        self.assertEqual(notification.data['source_title'], source.title)  # type: ignore[union-attr, index]
        self.assertEqual(notification.data['creator_name'], self.owner.username)  # type: ignore[union-attr, index]

        # Verify member2 also received notification
        member2_notifications = Notification.objects.filter(
            user=self.member2,
            type='source_added'
        )
        self.assertEqual(member2_notifications.count(), 1)

    def test_signal_does_not_notify_creator(self) -> None:
        """Test creator doesn't get notified about their own source."""
        from apps.sources.models import Source

        # Clear notifications from setUp (vault invites)
        Notification.objects.all().delete()

        # Owner adds a source
        Source.objects.create(
            vault=self.vault,
            url='https://example.com/paper',
            title='Test Research Paper',
            created_by=self.owner
        )

        # Verify owner did NOT receive source_added notification
        owner_notifications = Notification.objects.filter(
            user=self.owner,
            type='source_added'
        )
        self.assertEqual(owner_notifications.count(), 0)

    def test_signal_does_not_trigger_on_source_update(self) -> None:
        """Test signal doesn't fire when source is updated (only created)."""
        from apps.sources.models import Source

        # Create source
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/paper',
            title='Test Research Paper',
            created_by=self.owner
        )

        # Clear notifications
        Notification.objects.all().delete()

        # Update source title
        source.title = 'Updated Title'
        source.save()

        # Verify no new notifications were created
        notifications = Notification.objects.filter(type='source_added')
        self.assertEqual(notifications.count(), 0)

    def test_signal_respects_muted_vault(self) -> None:
        """Test signal respects muted vaults."""
        from apps.sources.models import Source

        # Member1 mutes the vault
        MutedVault.objects.create(user=self.member1, vault=self.vault)

        # Owner adds a source
        Source.objects.create(
            vault=self.vault,
            url='https://example.com/paper',
            title='Test Research Paper',
            created_by=self.owner
        )

        # Verify member1 did NOT receive notification (vault is muted)
        member1_notifications = Notification.objects.filter(
            user=self.member1,
            type='source_added'
        )
        self.assertEqual(member1_notifications.count(), 0)

        # Verify member2 still received notification
        member2_notifications = Notification.objects.filter(
            user=self.member2,
            type='source_added'
        )
        self.assertEqual(member2_notifications.count(), 1)

    def test_signal_respects_email_vault_activity_preference(self) -> None:
        """Test signal respects email_vault_activity preference."""
        from apps.sources.models import Source

        # Member1 disables vault activity notifications
        prefs, _ = NotificationPreferences.objects.get_or_create(user=self.member1)
        prefs.email_vault_activity = False
        prefs.save()

        # Owner adds a source
        Source.objects.create(
            vault=self.vault,
            url='https://example.com/paper',
            title='Test Research Paper',
            created_by=self.owner
        )

        # Verify member1 did NOT receive notification (preference disabled)
        member1_notifications = Notification.objects.filter(
            user=self.member1,
            type='source_added'
        )
        self.assertEqual(member1_notifications.count(), 0)

        # Verify member2 still received notification
        member2_notifications = Notification.objects.filter(
            user=self.member2,
            type='source_added'
        )
        self.assertEqual(member2_notifications.count(), 1)

    def test_signal_handles_unknown_creator(self) -> None:
        """Test signal handles case where created_by is None."""
        from apps.sources.models import Source

        # Add source without creator
        Source.objects.create(
            vault=self.vault,
            url='https://example.com/paper',
            title='Test Research Paper',
            created_by=None
        )

        # Verify notifications were created with "Unknown" as creator
        notifications = Notification.objects.filter(type='source_added')
        # All 3 members should receive notification (no creator to skip)
        self.assertEqual(notifications.count(), 3)

        notification = notifications.first()
        self.assertEqual(notification.data['creator_name'], 'Unknown')  # type: ignore[union-attr, index]
