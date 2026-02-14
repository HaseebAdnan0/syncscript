"""Tests for onboarding service (US-004) and API endpoints (US-005)."""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User


class DemoVaultServiceTests(TestCase):
    """Tests for demo vault creation service (US-004)."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPass123!'
        )

    def test_create_demo_vault_success(self):
        """Test creating demo vault creates vault with sources and annotations."""
        from apps.users.services import create_demo_vault
        from apps.vaults.models import Vault
        from apps.sources.models import Source
        from apps.annotations.models import Annotation

        vault = create_demo_vault(self.user)

        # Verify vault created
        self.assertIsNotNone(vault)
        self.assertEqual(vault.name, "AI Research Papers 2025")
        self.assertEqual(vault.owner, self.user)
        self.assertIn("AI research", vault.description)

        # Verify sources created (should have 10 from fixture)
        sources = Source.objects.filter(vault=vault)
        self.assertEqual(sources.count(), 10)

        # Verify annotations created (should have 18 from fixture)
        annotations = Annotation.objects.filter(source__vault=vault)
        self.assertEqual(annotations.count(), 18)

        # Verify all annotations created by user
        for annotation in annotations:
            self.assertEqual(annotation.user, self.user)

        # Verify threaded annotations work
        threaded_annotations = annotations.filter(parent__isnull=False)
        self.assertGreater(threaded_annotations.count(), 0)

        # Verify user is owner member
        from apps.vaults.models import VaultMembership, RoleChoices
        membership = VaultMembership.objects.get(vault=vault, user=self.user)
        self.assertEqual(membership.role, RoleChoices.OWNER)

    def test_create_demo_vault_idempotent(self):
        """Test creating demo vault is idempotent (doesn't create duplicates)."""
        from apps.users.services import create_demo_vault
        from apps.vaults.models import Vault

        # Create first time
        vault1 = create_demo_vault(self.user)

        # Create second time
        vault2 = create_demo_vault(self.user)

        # Should return same vault
        self.assertEqual(vault1.id, vault2.id)

        # Should only have one vault with this name
        count = Vault.objects.filter(
            owner=self.user,
            name="AI Research Papers 2025"
        ).count()
        self.assertEqual(count, 1)

    def test_create_demo_vault_sources_metadata(self):
        """Test demo vault sources have proper metadata."""
        from apps.users.services import create_demo_vault
        from apps.sources.models import Source

        vault = create_demo_vault(self.user)
        sources = Source.objects.filter(vault=vault)

        # Verify first source (Transformer paper)
        transformer_source = sources.filter(title__icontains="Attention").first()
        self.assertIsNotNone(transformer_source)
        self.assertIn("arxiv.org", transformer_source.url)
        self.assertEqual(transformer_source.source_type, "URL")
        self.assertIn("authors", transformer_source.metadata)
        self.assertIn("year", transformer_source.metadata)

    def test_create_demo_vault_annotation_threading(self):
        """Test demo vault annotations have proper threading."""
        from apps.users.services import create_demo_vault
        from apps.annotations.models import Annotation

        vault = create_demo_vault(self.user)

        # Find an annotation with replies
        parent_annotation = Annotation.objects.filter(
            source__vault=vault,
            parent__isnull=True
        ).first()

        # Check if any annotation has replies
        has_replies = Annotation.objects.filter(
            source__vault=vault,
            parent__isnull=False
        ).exists()

        self.assertTrue(has_replies, "Demo vault should have threaded annotations")

    def test_create_demo_vault_transaction_rollback(self):
        """Test that vault creation rolls back on error."""
        from apps.users.services import create_demo_vault
        from apps.vaults.models import Vault
        from apps.sources.models import Source
        from unittest.mock import patch

        # Mock Annotation creation to fail
        with patch('apps.annotations.models.Annotation.objects.create', side_effect=Exception("Test error")):
            with self.assertRaises(Exception):
                create_demo_vault(self.user)

        # Verify nothing was created
        vault_count = Vault.objects.filter(owner=self.user).count()
        source_count = Source.objects.filter(created_by=self.user).count()

        self.assertEqual(vault_count, 0)
        self.assertEqual(source_count, 0)


class DemoVaultResetAPITests(TestCase):
    """Tests for demo vault reset API endpoint (US-005)."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPass123!'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('users:demo-vault-reset')

    def test_reset_demo_vault_success(self):
        """Test resetting demo vault deletes old and creates new one."""
        from apps.users.services import create_demo_vault
        from apps.vaults.models import Vault
        from apps.sources.models import Source
        from apps.annotations.models import Annotation

        # Create initial demo vault
        old_vault = create_demo_vault(self.user)
        old_vault_id = old_vault.id

        # Modify the vault to verify it gets reset
        old_vault.description = "Modified description"
        old_vault.save()

        # Reset demo vault
        response = self.client.post(self.url)

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('vault', response.data)

        # Verify old vault was deleted
        old_vault_exists = Vault.objects.filter(id=old_vault_id).exists()
        self.assertFalse(old_vault_exists)

        # Verify new vault was created
        new_vault = Vault.objects.get(
            owner=self.user,
            name="AI Research Papers 2025"
        )
        self.assertNotEqual(new_vault.id, old_vault_id)
        self.assertNotEqual(new_vault.description, "Modified description")

        # Verify new vault has all sources and annotations
        sources = Source.objects.filter(vault=new_vault)
        annotations = Annotation.objects.filter(source__vault=new_vault)
        self.assertEqual(sources.count(), 10)
        self.assertEqual(annotations.count(), 18)

    def test_reset_demo_vault_no_existing(self):
        """Test resetting demo vault when none exists creates new one."""
        from apps.vaults.models import Vault

        # Ensure no demo vault exists
        Vault.objects.filter(
            owner=self.user,
            name="AI Research Papers 2025"
        ).delete()

        # Reset demo vault (should create new one)
        response = self.client.post(self.url)

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('vault', response.data)

        # Verify vault was created
        vault_exists = Vault.objects.filter(
            owner=self.user,
            name="AI Research Papers 2025"
        ).exists()
        self.assertTrue(vault_exists)

    def test_reset_demo_vault_unauthenticated(self):
        """Test resetting demo vault requires authentication."""
        # Logout
        self.client.force_authenticate(user=None)

        # Attempt to reset
        response = self.client.post(self.url)

        # Verify unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reset_demo_vault_cascade_delete(self):
        """Test resetting demo vault deletes all related data."""
        from apps.users.services import create_demo_vault
        from apps.sources.models import Source
        from apps.annotations.models import Annotation

        # Create demo vault
        old_vault = create_demo_vault(self.user)

        # Get counts of related objects
        old_source_ids = list(Source.objects.filter(vault=old_vault).values_list('id', flat=True))
        old_annotation_ids = list(Annotation.objects.filter(source__vault=old_vault).values_list('id', flat=True))

        # Reset demo vault
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify old sources and annotations were deleted
        remaining_sources = Source.objects.filter(id__in=old_source_ids).count()
        remaining_annotations = Annotation.objects.filter(id__in=old_annotation_ids).count()

        self.assertEqual(remaining_sources, 0)
        self.assertEqual(remaining_annotations, 0)

    def test_reset_demo_vault_returns_vault_data(self):
        """Test reset endpoint returns complete vault data."""
        response = self.client.post(self.url)

        # Verify response structure
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('vault', response.data)

        vault_data = response.data['vault']
        self.assertIn('id', vault_data)
        self.assertIn('name', vault_data)
        self.assertIn('description', vault_data)
        self.assertIn('owner', vault_data)
        self.assertIn('member_count', vault_data)
        self.assertIn('user_role', vault_data)

        # Verify vault name
        self.assertEqual(vault_data['name'], "AI Research Papers 2025")

        # Verify user is owner
        self.assertEqual(vault_data['user_role'], 'OWNER')
