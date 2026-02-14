from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.notifications.mentions import extract_mentions, resolve_mentions

User = get_user_model()


class ExtractMentionsTestCase(TestCase):
    """Test extract_mentions utility function (US-016)."""

    def test_extract_single_mention(self) -> None:
        """Test extracting a single mention from text."""
        text = "@alice what do you think?"
        mentions = extract_mentions(text)
        self.assertEqual(mentions, ['alice'])

    def test_extract_multiple_mentions(self) -> None:
        """Test extracting multiple mentions from text."""
        text = "Hey @bob and @charlie, check this out!"
        mentions = extract_mentions(text)
        self.assertEqual(mentions, ['bob', 'charlie'])

    def test_mention_at_start_of_text(self) -> None:
        """Test mention at the very start of text."""
        text = "@alice here's something interesting"
        mentions = extract_mentions(text)
        self.assertEqual(mentions, ['alice'])

    def test_mention_after_whitespace(self) -> None:
        """Test mentions after various whitespace."""
        text = "Hello @alice\nWhat about @bob?\tAnd @charlie"
        mentions = extract_mentions(text)
        self.assertEqual(mentions, ['alice', 'bob', 'charlie'])

    def test_mention_after_punctuation(self) -> None:
        """Test mentions after punctuation with space."""
        text = "Great point, @alice! What do you think, @bob?"
        mentions = extract_mentions(text)
        self.assertEqual(mentions, ['alice', 'bob'])

    def test_ignore_email_addresses(self) -> None:
        """Test that email addresses are not treated as mentions."""
        text = "Contact me at email@example.com or user@domain.org"
        mentions = extract_mentions(text)
        self.assertEqual(mentions, [])

    def test_mention_with_underscores_and_numbers(self) -> None:
        """Test mentions with underscores and numbers in username."""
        text = "@user_123 and @test_user_456"
        mentions = extract_mentions(text)
        self.assertEqual(mentions, ['user_123', 'test_user_456'])

    def test_duplicate_mentions_deduplicated(self) -> None:
        """Test duplicate mentions are deduplicated."""
        text = "@alice what do you think? @bob and @alice again"
        mentions = extract_mentions(text)
        self.assertEqual(mentions, ['alice', 'bob'])

    def test_empty_text(self) -> None:
        """Test empty text returns empty list."""
        mentions = extract_mentions("")
        self.assertEqual(mentions, [])

    def test_text_without_mentions(self) -> None:
        """Test text without mentions returns empty list."""
        text = "This is just regular text without any mentions"
        mentions = extract_mentions(text)
        self.assertEqual(mentions, [])

    def test_mention_preserves_order(self) -> None:
        """Test that mention order is preserved (first occurrence)."""
        text = "@alice @bob @charlie @bob @alice"
        mentions = extract_mentions(text)
        self.assertEqual(mentions, ['alice', 'bob', 'charlie'])


class ResolveMentionsTestCase(TestCase):
    """Test resolve_mentions utility function (US-016)."""

    def setUp(self) -> None:
        """Create test users and vault."""
        from apps.vaults.models import Vault, VaultMembership

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
        self.non_member = User.objects.create_user(  # type: ignore[attr-defined]
            username='outsider',
            email='outsider@example.com',
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

    def test_resolve_valid_members(self) -> None:
        """Test resolving usernames that are vault members."""
        usernames = ['alice', 'bob']
        users = resolve_mentions(usernames, self.vault.id)

        self.assertEqual(len(users), 2)
        usernames_resolved = [u.username for u in users]
        self.assertIn('alice', usernames_resolved)
        self.assertIn('bob', usernames_resolved)

    def test_resolve_ignores_non_members(self) -> None:
        """Test that non-members are ignored."""
        usernames = ['alice', 'bob', 'outsider']
        users = resolve_mentions(usernames, self.vault.id)

        # Only alice and bob should be returned (outsider is not a member)
        self.assertEqual(len(users), 2)
        usernames_resolved = [u.username for u in users]
        self.assertIn('alice', usernames_resolved)
        self.assertIn('bob', usernames_resolved)
        self.assertNotIn('outsider', usernames_resolved)

    def test_resolve_ignores_invalid_usernames(self) -> None:
        """Test that non-existent usernames are ignored."""
        usernames = ['alice', 'nonexistent', 'bob']
        users = resolve_mentions(usernames, self.vault.id)

        # Only alice and bob should be returned
        self.assertEqual(len(users), 2)
        usernames_resolved = [u.username for u in users]
        self.assertIn('alice', usernames_resolved)
        self.assertIn('bob', usernames_resolved)

    def test_resolve_empty_list(self) -> None:
        """Test resolving empty username list."""
        users = resolve_mentions([], self.vault.id)
        self.assertEqual(users, [])

    def test_resolve_invalid_vault_id(self) -> None:
        """Test resolving with non-existent vault ID."""
        usernames = ['alice', 'bob']
        users = resolve_mentions(usernames, 99999)
        self.assertEqual(users, [])

    def test_resolve_all_vault_members(self) -> None:
        """Test resolving all vault members."""
        usernames = ['alice', 'bob', 'charlie']
        users = resolve_mentions(usernames, self.vault.id)

        self.assertEqual(len(users), 3)
        usernames_resolved = [u.username for u in users]
        self.assertIn('alice', usernames_resolved)
        self.assertIn('bob', usernames_resolved)
        self.assertIn('charlie', usernames_resolved)

    def test_resolve_with_duplicates(self) -> None:
        """Test resolving with duplicate usernames (should not duplicate results)."""
        usernames = ['alice', 'bob', 'alice']
        users = resolve_mentions(usernames, self.vault.id)

        # Should only return unique users
        self.assertEqual(len(users), 2)
        usernames_resolved = [u.username for u in users]
        self.assertIn('alice', usernames_resolved)
        self.assertIn('bob', usernames_resolved)
