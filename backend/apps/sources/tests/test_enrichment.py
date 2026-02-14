"""
Unit tests for source metadata enrichment task (US-022).

Tests verify the enrich_source_metadata Celery task correctly fetches and merges
metadata from DOI (CrossRef) and ISBN (OpenLibrary) sources.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.vaults.models import Vault, AuditLog  # type: ignore[import-not-found]
from apps.sources.models import Source  # type: ignore[import-not-found]
from apps.sources.tasks import enrich_source_metadata  # type: ignore[import-not-found]

User = get_user_model()


class MetadataEnrichmentTests(TestCase):
    """
    Unit tests for source metadata enrichment via DOI/ISBN lookup.

    Tests verify the enrich_source_metadata task correctly:
    - Detects DOI in source URL
    - Detects ISBN in source metadata
    - Fetches metadata from CrossRef/OpenLibrary
    - Merges fetched metadata without overwriting user entries
    - Updates title if fetched title is better
    - Creates audit log entries
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
            description='Test vault for enrichment tests',
            owner=self.user
        )

    @patch('apps.citations.services.doi_lookup.fetch_doi_metadata')
    @patch('apps.citations.services.doi_lookup.normalize_doi')
    def test_enrich_source_with_doi_url(
        self,
        mock_normalize_doi: MagicMock,
        mock_fetch_doi: MagicMock
    ) -> None:
        """
        Test: Enrichment detects DOI in URL and fetches metadata from CrossRef.

        Verifies:
        - DOI detected in source URL
        - CrossRef API called with normalized DOI
        - Fetched metadata merged into source.metadata
        - Audit log created
        """
        # Create source with DOI URL
        source = Source.objects.create(
            vault=self.vault,
            url='https://doi.org/10.1234/example',
            title='Short Title',
            description='Test description',
            source_type='URL',
            created_by=self.user
        )

        # Mock DOI normalization and metadata fetch
        mock_normalize_doi.return_value = '10.1234/example'
        mock_fetch_doi.return_value = {
            'title': 'Complete Research Paper Title With More Detail',
            'authors': ['Smith, John', 'Doe, Jane'],
            'publication_date': '2024-01-15',
            'journal': 'Nature',
            'volume': '123',
            'pages': '45-67',
            'doi': '10.1234/example',
        }

        # Run enrichment task
        result = enrich_source_metadata(source.id)

        # Verify DOI was normalized
        mock_normalize_doi.assert_called_once_with(source.url)

        # Verify metadata was fetched
        mock_fetch_doi.assert_called_once_with('10.1234/example')

        # Verify task result
        self.assertTrue(result['enriched'])
        self.assertEqual(result['method'], 'doi')
        self.assertIn('authors', result['fetched_fields'])
        self.assertIn('publication_date', result['fetched_fields'])

        # Refresh source from database
        source.refresh_from_db()

        # Verify metadata was merged
        self.assertEqual(source.metadata['authors'], ['Smith, John', 'Doe, Jane'])
        self.assertEqual(source.metadata['journal'], 'Nature')
        self.assertEqual(source.metadata['doi'], '10.1234/example')

        # Verify title was updated (fetched title is longer)
        self.assertEqual(source.title, 'Complete Research Paper Title With More Detail')

        # Verify audit log was created
        audit_logs = AuditLog.objects.filter(
            vault=self.vault,
            action='source.metadata_enriched'
        )
        self.assertEqual(audit_logs.count(), 1)
        audit_log = audit_logs.first()
        self.assertEqual(audit_log.metadata['source_id'], source.id)  # type: ignore[index]
        self.assertEqual(audit_log.metadata['method'], 'doi')  # type: ignore[index]

    @patch('apps.citations.services.isbn_lookup.fetch_isbn_metadata')
    @patch('apps.citations.services.isbn_lookup.normalize_isbn')
    @patch('apps.citations.services.doi_lookup.normalize_doi')
    def test_enrich_source_with_isbn_metadata(
        self,
        mock_normalize_doi: MagicMock,
        mock_normalize_isbn: MagicMock,
        mock_fetch_isbn: MagicMock
    ) -> None:
        """
        Test: Enrichment detects ISBN in metadata and fetches from OpenLibrary.

        Verifies:
        - ISBN detected in source.metadata
        - OpenLibrary API called with normalized ISBN
        - Fetched metadata merged into source.metadata
        """
        # Create source with ISBN in metadata
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/book',
            title='Book Title',
            description='Test book',
            source_type='BOOK',
            created_by=self.user,
            metadata={'isbn': '978-0-123456-78-9'}
        )

        # Mock DOI normalization (returns None - no DOI)
        mock_normalize_doi.return_value = None

        # Mock ISBN normalization and metadata fetch
        mock_normalize_isbn.return_value = '9780123456789'
        mock_fetch_isbn.return_value = {
            'title': 'Complete Book Title',
            'authors': ['Author Name'],
            'publication_date': '2023',
            'publisher': 'Example Publisher',
            'isbn-13': '9780123456789',
        }

        # Run enrichment task
        result = enrich_source_metadata(source.id)

        # Verify ISBN was normalized
        mock_normalize_isbn.assert_called_once_with('978-0-123456-78-9')

        # Verify metadata was fetched
        mock_fetch_isbn.assert_called_once_with('9780123456789')

        # Verify task result
        self.assertTrue(result['enriched'])
        self.assertEqual(result['method'], 'isbn')
        self.assertIn('authors', result['fetched_fields'])

        # Refresh source from database
        source.refresh_from_db()

        # Verify metadata was merged
        self.assertEqual(source.metadata['authors'], ['Author Name'])
        self.assertEqual(source.metadata['publisher'], 'Example Publisher')

    @patch('apps.citations.services.doi_lookup.fetch_doi_metadata')
    @patch('apps.citations.services.doi_lookup.normalize_doi')
    def test_enrich_does_not_overwrite_existing_metadata(
        self,
        mock_normalize_doi: MagicMock,
        mock_fetch_doi: MagicMock
    ) -> None:
        """
        Test: Enrichment does not overwrite existing user-provided metadata.

        Verifies:
        - Existing metadata fields are preserved
        - Only missing fields are added
        """
        # Create source with some existing metadata
        source = Source.objects.create(
            vault=self.vault,
            url='https://doi.org/10.1234/example',
            title='User Title',
            description='Test description',
            source_type='URL',
            created_by=self.user,
            metadata={
                'authors': ['User Author'],  # User-provided author
                'custom_field': 'User Data',
            }
        )

        # Mock DOI normalization and metadata fetch
        mock_normalize_doi.return_value = '10.1234/example'
        mock_fetch_doi.return_value = {
            'title': 'Fetched Title',
            'authors': ['Fetched Author'],  # Should NOT overwrite user author
            'journal': 'Nature',  # Should be added (missing field)
            'doi': '10.1234/example',
        }

        # Run enrichment task
        result = enrich_source_metadata(source.id)

        # Refresh source from database
        source.refresh_from_db()

        # Verify user-provided metadata was NOT overwritten
        self.assertEqual(source.metadata['authors'], ['User Author'])
        self.assertEqual(source.metadata['custom_field'], 'User Data')

        # Verify missing fields were added
        self.assertEqual(source.metadata['journal'], 'Nature')
        self.assertEqual(source.metadata['doi'], '10.1234/example')

        # Verify fetched_fields does not include 'authors' (already existed)
        self.assertNotIn('authors', result['fetched_fields'])
        self.assertIn('journal', result['fetched_fields'])

    @patch('apps.citations.services.doi_lookup.normalize_doi')
    def test_enrich_no_doi_or_isbn_returns_not_enriched(
        self,
        mock_normalize_doi: MagicMock
    ) -> None:
        """
        Test: Enrichment returns enriched=False when no DOI or ISBN found.

        Verifies:
        - Task completes successfully even with no identifier
        - Source metadata unchanged
        """
        # Create source without DOI or ISBN
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/article',
            title='Article Title',
            description='Test article',
            source_type='URL',
            created_by=self.user
        )

        # Mock DOI normalization (returns None)
        mock_normalize_doi.return_value = None

        # Run enrichment task
        result = enrich_source_metadata(source.id)

        # Verify task completed but did not enrich
        self.assertFalse(result['enriched'])
        self.assertIsNone(result['method'])
        self.assertEqual(result['fetched_fields'], [])

    @patch('apps.citations.services.doi_lookup.fetch_doi_metadata')
    @patch('apps.citations.services.doi_lookup.normalize_doi')
    def test_enrich_updates_title_if_fetched_title_longer(
        self,
        mock_normalize_doi: MagicMock,
        mock_fetch_doi: MagicMock
    ) -> None:
        """
        Test: Enrichment updates title if fetched title is longer/more complete.

        Verifies:
        - Short title replaced by longer fetched title
        - Title update logged in fetched_fields
        """
        # Create source with short title
        source = Source.objects.create(
            vault=self.vault,
            url='https://doi.org/10.1234/example',
            title='Short',
            description='Test description',
            source_type='URL',
            created_by=self.user
        )

        # Mock DOI normalization and metadata fetch
        mock_normalize_doi.return_value = '10.1234/example'
        mock_fetch_doi.return_value = {
            'title': 'Much Longer and More Descriptive Research Paper Title',
            'authors': ['Author Name'],
        }

        # Run enrichment task
        result = enrich_source_metadata(source.id)

        # Refresh source from database
        source.refresh_from_db()

        # Verify title was updated
        self.assertEqual(source.title, 'Much Longer and More Descriptive Research Paper Title')

        # Verify fetched_fields includes title update
        self.assertIn('title (updated)', result['fetched_fields'])

    @patch('apps.citations.services.doi_lookup.fetch_doi_metadata')
    @patch('apps.citations.services.doi_lookup.normalize_doi')
    def test_enrich_does_not_update_title_if_existing_longer(
        self,
        mock_normalize_doi: MagicMock,
        mock_fetch_doi: MagicMock
    ) -> None:
        """
        Test: Enrichment does NOT update title if existing title is longer.

        Verifies:
        - Longer existing title preserved
        - Title not in fetched_fields
        """
        # Create source with long title
        source = Source.objects.create(
            vault=self.vault,
            url='https://doi.org/10.1234/example',
            title='Very Long User-Provided Research Paper Title With Detail',
            description='Test description',
            source_type='URL',
            created_by=self.user
        )

        # Mock DOI normalization and metadata fetch
        mock_normalize_doi.return_value = '10.1234/example'
        mock_fetch_doi.return_value = {
            'title': 'Short',
            'authors': ['Author Name'],
        }

        # Run enrichment task
        result = enrich_source_metadata(source.id)

        # Refresh source from database
        source.refresh_from_db()

        # Verify title was NOT updated
        self.assertEqual(source.title, 'Very Long User-Provided Research Paper Title With Detail')

        # Verify fetched_fields does not include title
        title_fields = [f for f in result['fetched_fields'] if 'title' in f]
        self.assertEqual(len(title_fields), 0)

    def test_enrich_source_not_found_returns_error(self) -> None:
        """
        Test: Enrichment handles missing source gracefully.

        Verifies:
        - Task returns error when source_id not found
        - No exception raised
        """
        # Run enrichment task with non-existent source ID
        result = enrich_source_metadata(99999)

        # Verify error returned
        self.assertFalse(result['enriched'])
        self.assertEqual(result['error'], 'Source not found')

    @patch('apps.citations.services.doi_lookup.fetch_doi_metadata')
    @patch('apps.citations.services.doi_lookup.normalize_doi')
    def test_enrich_handles_api_failure_gracefully(
        self,
        mock_normalize_doi: MagicMock,
        mock_fetch_doi: MagicMock
    ) -> None:
        """
        Test: Enrichment handles API failures gracefully.

        Verifies:
        - Task completes when API returns None
        - Source unchanged
        - No exception raised
        """
        # Create source with DOI
        source = Source.objects.create(
            vault=self.vault,
            url='https://doi.org/10.1234/example',
            title='Test Title',
            description='Test description',
            source_type='URL',
            created_by=self.user
        )

        # Mock DOI normalization but API failure (returns None)
        mock_normalize_doi.return_value = '10.1234/example'
        mock_fetch_doi.return_value = None

        # Run enrichment task
        result = enrich_source_metadata(source.id)

        # Verify task completed but did not enrich
        self.assertFalse(result['enriched'])

        # Refresh source from database
        source.refresh_from_db()

        # Verify source unchanged
        self.assertEqual(source.title, 'Test Title')
        self.assertEqual(source.metadata, {})
