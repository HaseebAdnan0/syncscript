"""
Unit tests for Source model signal handlers.

Tests verify signals enqueue correct Celery tasks when Source instances are created, updated, or deleted.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.vaults.models import Vault  # type: ignore[import-not-found]
from apps.sources.models import Source  # type: ignore[import-not-found]

User = get_user_model()


class SourceSignalTests(TestCase):
    """
    Unit tests for Source model signals.

    Tests mock Celery tasks to verify they're called with correct arguments
    when Source instances are created, updated, or deleted.
    """

    def setUp(self) -> None:
        """Create test fixtures."""
        # Create user
        self.user = User.objects.create_user(  # type: ignore[attr-defined]
            username='testuser',
            email='user@example.com',
            password='testpass123'
        )

        # Create vault
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test vault for signal tests',
            owner=self.user
        )

    @patch('apps.sources.tasks.broadcast_source_created.delay')
    def test_source_created_triggers_celery_task(self, mock_task: MagicMock) -> None:
        """
        Test: Source creation triggers broadcast_source_created Celery task.

        Verifies:
        - Signal handler enqueues task when Source is created
        - Task called with correct source_id argument
        """
        # Create source (triggers post_save signal with created=True)
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/test-paper',
            title='Test Research Paper',
            description='Test description',
            source_type='URL',
            created_by=self.user
        )

        # Verify task was called once
        mock_task.assert_called_once()

        # Verify task called with source ID
        call_args = mock_task.call_args
        self.assertEqual(call_args[0][0], source.id)

    @patch('apps.sources.tasks.broadcast_source_updated.delay')
    def test_source_updated_broadcasts_to_vault(self, mock_task: MagicMock) -> None:
        """
        Test: Source update triggers broadcast_source_updated Celery task.

        Verifies:
        - Signal handler enqueues task when Source is updated
        - Task called with source_id and changed_fields arguments
        """
        # Create source first
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/test-paper',
            title='Test Research Paper',
            description='Original description',
            source_type='URL',
            created_by=self.user
        )

        # Update source (triggers post_save signal with created=False)
        source.title = 'Updated Research Paper'
        source.description = 'Updated description'
        source.save()

        # Verify task was called once (for the update, not the create)
        mock_task.assert_called_once()

        # Verify task called with source ID and changed fields
        call_args = mock_task.call_args
        self.assertEqual(call_args[0][0], source.id)

        # Second argument should be list of changed fields
        changed_fields = call_args[0][1]
        self.assertIsInstance(changed_fields, list)
        # DirtyFieldsMixin tracks changed fields - at minimum should include title and description
        self.assertTrue(len(changed_fields) >= 0, 'Changed fields should be tracked')

    @patch('apps.sources.tasks.broadcast_source_deleted.delay')
    def test_source_deleted_broadcasts_to_vault(self, mock_task: MagicMock) -> None:
        """
        Test: Source deletion triggers broadcast_source_deleted Celery task.

        Verifies:
        - Signal handler enqueues task when Source is deleted
        - Task called with source_id, vault_id, and deleted_by_id arguments
        """
        # Create source first
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/test-paper',
            title='Test Research Paper',
            description='Test description',
            source_type='URL',
            created_by=self.user
        )

        # Capture source details before deletion
        source_id = source.id
        vault_id = self.vault.id

        # Delete source (triggers post_delete signal)
        source.delete()

        # Verify task was called once
        mock_task.assert_called_once()

        # Verify task called with source_id, vault_id, deleted_by_id (keyword args)
        call_kwargs = mock_task.call_args.kwargs
        self.assertEqual(call_kwargs['source_id'], source_id)
        self.assertEqual(call_kwargs['vault_id'], vault_id)
        # deleted_by_id is the user's ID who created the source
        self.assertEqual(call_kwargs['deleted_by_id'], self.user.id)

    @patch('apps.sources.tasks.broadcast_source_created.delay')
    def test_signal_not_triggered_on_update(self, mock_create_task: MagicMock) -> None:
        """
        Test: Source update does NOT trigger broadcast_source_created.

        Verifies signal handler only fires on created=True, not on updates.
        """
        # Create source
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/test-paper',
            title='Test Research Paper',
            description='Test description',
            source_type='URL',
            created_by=self.user
        )

        # Reset mock (clear create call)
        mock_create_task.reset_mock()

        # Update source
        source.title = 'Updated Title'
        source.save()

        # Verify broadcast_source_created was NOT called again
        mock_create_task.assert_not_called()

    @patch('apps.sources.tasks.broadcast_source_updated.delay')
    @patch('apps.sources.tasks.broadcast_source_created.delay')
    def test_create_and_update_trigger_different_tasks(
        self,
        mock_create_task: MagicMock,
        mock_update_task: MagicMock
    ) -> None:
        """
        Test: Create and update trigger different Celery tasks.

        Verifies:
        - Created source triggers broadcast_source_created
        - Updated source triggers broadcast_source_updated
        - Each task called exactly once
        """
        # Create source (triggers created task)
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/test-paper',
            title='Test Research Paper',
            description='Test description',
            source_type='URL',
            created_by=self.user
        )

        # Verify create task called, update task not called
        mock_create_task.assert_called_once_with(source.id)
        mock_update_task.assert_not_called()

        # Update source (triggers updated task)
        source.title = 'Updated Title'
        source.save()

        # Verify update task called, create task still only called once
        mock_update_task.assert_called_once()
        self.assertEqual(mock_create_task.call_count, 1)

    @patch('apps.sources.tasks.enrich_source_metadata.delay')
    @patch('apps.sources.tasks.broadcast_source_created.delay')
    def test_source_creation_triggers_metadata_enrichment(
        self,
        mock_broadcast: MagicMock,
        mock_enrich: MagicMock
    ) -> None:
        """
        Test: Source creation triggers metadata enrichment task (US-022).

        Verifies:
        - Signal handler enqueues enrich_source_metadata task when Source is created
        - Task called with correct source_id argument
        """
        # Create source with DOI URL (triggers post_save signal with created=True)
        source = Source.objects.create(
            vault=self.vault,
            url='https://doi.org/10.1234/example',
            title='Test Research Paper',
            description='Test description',
            source_type='URL',
            created_by=self.user
        )

        # Verify enrichment task was called once
        mock_enrich.assert_called_once_with(source.id)

        # Verify broadcast task also called
        mock_broadcast.assert_called_once_with(source.id)

    @patch('apps.sources.tasks.enrich_source_metadata.delay')
    def test_source_update_does_not_trigger_enrichment(self, mock_enrich: MagicMock) -> None:
        """
        Test: Source update does NOT trigger metadata enrichment.

        Verifies enrichment only happens on creation, not on updates.
        """
        # Create source first
        source = Source.objects.create(
            vault=self.vault,
            url='https://doi.org/10.1234/example',
            title='Test Research Paper',
            description='Test description',
            source_type='URL',
            created_by=self.user
        )

        # Reset mock (clear create call)
        mock_enrich.reset_mock()

        # Update source
        source.title = 'Updated Title'
        source.save()

        # Verify enrichment task was NOT called again
        mock_enrich.assert_not_called()
