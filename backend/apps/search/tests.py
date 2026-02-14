"""
Tests for the search app.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.annotations.models import Annotation
from apps.sources.models import Source
from apps.vaults.models import Vault

User = get_user_model()


class SearchSignalsTest(TestCase):
    """Test that signals correctly trigger search vector update tasks."""

    def setUp(self):
        """Create test user and vault."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test description',
            owner=self.user
        )

    @patch('apps.search.tasks.update_source_search_vector.delay')
    def test_source_create_triggers_signal(self, mock_task):
        """Creating a Source should trigger search vector update."""
        source = Source.objects.create(
            vault=self.vault,
            title='Test Source',
            description='Test description',
            source_type='url',
            url='https://example.com'
        )

        # Verify task was called with source ID
        mock_task.assert_called_once_with(source.id)

    @patch('apps.search.tasks.update_source_search_vector.delay')
    def test_source_update_relevant_field_triggers_signal(self, mock_task):
        """Updating relevant fields (title, description) should trigger update."""
        source = Source.objects.create(
            vault=self.vault,
            title='Test Source',
            description='Test description',
            source_type='url',
            url='https://example.com'
        )

        # Reset mock to clear the create call
        mock_task.reset_mock()

        # Update title
        source.title = 'Updated Title'
        source.save(update_fields=['title'])

        # Verify task was called
        mock_task.assert_called_once_with(source.id)

    @patch('apps.search.tasks.update_source_search_vector.delay')
    def test_source_update_irrelevant_field_skips_signal(self, mock_task):
        """Updating non-relevant fields should not trigger update."""
        source = Source.objects.create(
            vault=self.vault,
            title='Test Source',
            description='Test description',
            source_type='url',
            url='https://example.com'
        )

        # Reset mock to clear the create call
        mock_task.reset_mock()

        # Update URL only (not indexed)
        source.url = 'https://newurl.com'
        source.save(update_fields=['url'])

        # Verify task was NOT called
        mock_task.assert_not_called()

    @patch('apps.search.tasks.update_annotation_search_vector.delay')
    def test_annotation_create_triggers_signal(self, mock_task):
        """Creating an Annotation should trigger search vector update."""
        source = Source.objects.create(
            vault=self.vault,
            title='Test Source',
            description='Test description',
            source_type='url',
            url='https://example.com'
        )

        annotation = Annotation.objects.create(
            source=source,
            user=self.user,
            content='Test annotation content',
            page_number=1
        )

        # Verify task was called with annotation ID
        mock_task.assert_called_once_with(annotation.id)

    @patch('apps.search.tasks.update_annotation_search_vector.delay')
    def test_annotation_update_content_triggers_signal(self, mock_task):
        """Updating content field should trigger update."""
        source = Source.objects.create(
            vault=self.vault,
            title='Test Source',
            description='Test description',
            source_type='url',
            url='https://example.com'
        )

        annotation = Annotation.objects.create(
            source=source,
            user=self.user,
            content='Test annotation content',
            page_number=1
        )

        # Reset mock to clear the create call
        mock_task.reset_mock()

        # Update content
        annotation.content = 'Updated content'
        annotation.save(update_fields=['content'])

        # Verify task was called
        mock_task.assert_called_once_with(annotation.id)

    @patch('apps.search.tasks.update_annotation_search_vector.delay')
    def test_annotation_update_irrelevant_field_skips_signal(self, mock_task):
        """Updating non-relevant fields should not trigger update."""
        source = Source.objects.create(
            vault=self.vault,
            title='Test Source',
            description='Test description',
            source_type='url',
            url='https://example.com'
        )

        annotation = Annotation.objects.create(
            source=source,
            user=self.user,
            content='Test annotation content',
            page_number=1
        )

        # Reset mock to clear the create call
        mock_task.reset_mock()

        # Update page_number only (not indexed)
        annotation.page_number = 2
        annotation.save(update_fields=['page_number'])

        # Verify task was NOT called
        mock_task.assert_not_called()
