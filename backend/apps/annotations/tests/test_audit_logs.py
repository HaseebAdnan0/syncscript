"""
Tests for Annotation audit logging.
US-040: Write audit log signal tests
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.vaults.models import Vault, VaultMembership, AuditLog, RoleChoices
from apps.sources.models import Source, SourceType
from apps.annotations.models import Annotation

User = get_user_model()


class AnnotationAuditLogSignalTest(TestCase):
    """Tests for Annotation audit log signals."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com',
            username='owner',
            password='testpass123'
        )
        self.owner.email_verified = True
        self.owner.save()

        self.contributor = User.objects.create_user(
            email='contributor@example.com',
            username='contributor',
            password='testpass123'
        )
        self.contributor.email_verified = True
        self.contributor.save()

        self.vault = Vault.objects.create(name='Test Vault', owner=self.owner)

        # Add contributor to vault
        VaultMembership.objects.create(
            vault=self.vault,
            user=self.contributor,
            role=RoleChoices.CONTRIBUTOR,
            added_by=self.owner
        )

        # Create a source for annotations
        self.source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/article',
            title='Test Article',
            source_type=SourceType.PDF,
            created_by=self.owner
        )

    def test_annotation_create_generates_annotation_created_log(self):
        """Test Annotation create generates annotation.created log."""
        # Clear existing logs
        AuditLog.objects.filter(vault=self.vault).delete()

        # Create a top-level annotation
        annotation = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='This is a test annotation',
            page_number=1,
            position={'x': 100, 'y': 200}
        )

        # Check for annotation.created audit log
        log = AuditLog.objects.filter(vault=self.vault, action='annotation.created').first()
        self.assertIsNotNone(log, "annotation.created audit log should be created")
        if log:
            self.assertEqual(log.actor, self.owner)
            self.assertIn('annotation_id', log.metadata)
            self.assertIn('source_id', log.metadata)
            self.assertIn('content_preview', log.metadata)

    def test_annotation_reply_generates_annotation_replied_log(self):
        """Test Annotation reply generates annotation.replied log."""
        # Create a top-level annotation
        top_level = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Original annotation',
            page_number=1
        )

        # Clear existing logs
        AuditLog.objects.filter(vault=self.vault).delete()

        # Create a reply
        reply = Annotation.objects.create(
            source=self.source,
            user=self.contributor,
            content='Reply to annotation',
            parent=top_level
        )

        # Check for annotation.replied audit log
        log = AuditLog.objects.filter(vault=self.vault, action='annotation.replied').first()
        self.assertIsNotNone(log, "annotation.replied audit log should be created")
        if log:
            self.assertEqual(log.actor, self.contributor)
            self.assertIn('annotation_id', log.metadata)
            self.assertIn('source_id', log.metadata)
            self.assertIn('parent_id', log.metadata)
            self.assertEqual(log.metadata.get('parent_id'), str(top_level.id))

    def test_annotation_update_generates_annotation_updated_log(self):
        """Test Annotation update generates annotation.updated log."""
        # Create an annotation
        annotation = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Original content',
            page_number=1
        )

        # Clear existing logs
        AuditLog.objects.filter(vault=self.vault).delete()

        # Update the annotation
        annotation.content = 'Updated content'
        annotation.save()

        # Check for annotation.updated audit log
        log = AuditLog.objects.filter(vault=self.vault, action='annotation.updated').first()
        self.assertIsNotNone(log, "annotation.updated audit log should be created")
        if log:
            self.assertEqual(log.actor, self.owner)
            self.assertIn('annotation_id', log.metadata)
            # Check changes contain dirty fields
            changes = log.metadata.get('changes', {})
            self.assertIn('content', changes)

    def test_annotation_delete_generates_annotation_deleted_log(self):
        """Test Annotation delete generates annotation.deleted log."""
        # Create an annotation
        annotation = Annotation.objects.create(
            source=self.source,
            user=self.owner,
            content='Annotation to delete',
            page_number=1
        )

        annotation_id = annotation.id

        # Clear existing logs
        AuditLog.objects.filter(vault=self.vault).delete()

        # Delete the annotation
        annotation.delete()

        # Check for annotation.deleted audit log
        log = AuditLog.objects.filter(vault=self.vault, action='annotation.deleted').first()
        self.assertIsNotNone(log, "annotation.deleted audit log should be created")
        if log:
            self.assertEqual(log.actor, self.owner)
            self.assertIn('annotation_id', log.metadata)
            self.assertIn('source_id', log.metadata)
            self.assertEqual(log.metadata.get('annotation_id'), str(annotation_id))
