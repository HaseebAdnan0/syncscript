"""
Tests for Source audit logging.
US-040: Write audit log signal tests
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.vaults.models import Vault, VaultMembership, AuditLog, RoleChoices
from apps.sources.models import Source, SourceType

User = get_user_model()


class SourceAuditLogSignalTest(TestCase):
    """Tests for Source audit log signals."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com',
            username='owner',
            password='testpass123'
        )
        self.owner.email_verified = True
        self.owner.save()

        self.vault = Vault.objects.create(name='Test Vault', owner=self.owner)

    def test_source_create_generates_source_created_log(self):
        """Test Source create generates source.created log."""
        # Clear existing logs from vault creation
        AuditLog.objects.filter(vault=self.vault).delete()

        # Create a source
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/article',
            title='Test Article',
            source_type=SourceType.URL,
            created_by=self.owner
        )

        # Check for source.created audit log
        log = AuditLog.objects.filter(vault=self.vault, action='source.created').first()
        self.assertIsNotNone(log, "source.created audit log should be created")
        if log:
            self.assertEqual(log.actor, self.owner)
            self.assertIn('source_id', log.metadata)
            self.assertEqual(log.metadata.get('title'), 'Test Article')
            self.assertEqual(log.metadata.get('url'), 'https://example.com/article')

    def test_source_update_generates_source_updated_log(self):
        """Test Source update generates source.updated log with changes."""
        # Create a source
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/article',
            title='Original Title',
            description='Original Description',
            source_type=SourceType.URL,
            created_by=self.owner
        )

        # Clear existing logs
        AuditLog.objects.filter(vault=self.vault).delete()

        # Update the source
        source.title = 'Updated Title'
        source.description = 'Updated Description'
        source.save()

        # Check for source.updated audit log
        log = AuditLog.objects.filter(vault=self.vault, action='source.updated').first()
        self.assertIsNotNone(log, "source.updated audit log should be created")
        if log:
            self.assertEqual(log.actor, self.owner)
            self.assertIn('source_id', log.metadata)
            # Check changes contain dirty fields
            changes = log.metadata.get('changes', {})
            self.assertIn('title', changes)
            self.assertIn('description', changes)

    def test_source_soft_delete_generates_source_soft_deleted_log(self):
        """Test Source soft delete generates source.soft_deleted log."""
        client = APIClient()
        client.force_authenticate(user=self.owner)

        # Create a source
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/article',
            title='Test Article',
            source_type=SourceType.URL,
            created_by=self.owner
        )

        # Clear existing logs
        AuditLog.objects.filter(vault=self.vault).delete()

        # Soft delete via API (DELETE request)
        response = client.delete(f'/api/v1/sources/{source.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check for source.soft_deleted audit log
        log = AuditLog.objects.filter(vault=self.vault, action='source.soft_deleted').first()
        self.assertIsNotNone(log, "source.soft_deleted audit log should be created")
        if log:
            self.assertEqual(log.actor, self.owner)
            self.assertIn('source_id', log.metadata)
            self.assertIn('vault_id', log.metadata)

    def test_source_restore_generates_source_restored_log(self):
        """Test Source restore generates source.restored log."""
        client = APIClient()
        client.force_authenticate(user=self.owner)

        # Create and soft-delete a source
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/article',
            title='Test Article',
            source_type=SourceType.URL,
            created_by=self.owner,
            is_deleted=True
        )

        # Clear existing logs
        AuditLog.objects.filter(vault=self.vault).delete()

        # Restore via API (POST to restore endpoint)
        response = client.post(f'/api/v1/sources/{source.id}/restore/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check for source.restored audit log
        log = AuditLog.objects.filter(vault=self.vault, action='source.restored').first()
        self.assertIsNotNone(log, "source.restored audit log should be created")
        if log:
            self.assertEqual(log.actor, self.owner)
            self.assertIn('source_id', log.metadata)
            self.assertIn('vault_id', log.metadata)
