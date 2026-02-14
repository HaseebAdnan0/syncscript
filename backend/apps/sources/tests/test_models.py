from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from apps.vaults.models import Vault
from apps.sources.models import Source, SourceType

User = get_user_model()


class SourceModelTest(TestCase):
    """Test suite for Source model constraints and behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create(
            username='testuser',
            email='test@example.com'
        )
        self.user.set_password('testpass123')
        self.user.save()
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='A test vault',
            owner=self.user
        )

    def test_create_valid_source_with_all_fields(self):
        """Test creating a valid Source with all fields populated."""
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/article',
            title='Test Article',
            description='A test article description',
            source_type=SourceType.URL,
            metadata={'tags': ['ml', 'ai'], 'author': 'John Doe'},
            created_by=self.user,
            is_deleted=False
        )

        self.assertEqual(source.vault, self.vault)
        self.assertEqual(source.url, 'https://example.com/article')
        self.assertEqual(source.title, 'Test Article')
        self.assertEqual(source.description, 'A test article description')
        self.assertEqual(source.source_type, SourceType.URL)
        self.assertEqual(source.metadata, {'tags': ['ml', 'ai'], 'author': 'John Doe'})
        self.assertEqual(source.created_by, self.user)
        self.assertFalse(source.is_deleted)
        self.assertIsNotNone(source.created_at)
        self.assertIsNotNone(source.updated_at)

    def test_unique_constraint_prevents_duplicate_vault_url_for_active_sources(self):
        """Test unique constraint prevents duplicate vault+url for active sources."""
        Source.objects.create(
            vault=self.vault,
            url='https://example.com/unique',
            title='First Source',
            created_by=self.user
        )

        # Attempting to create another active source with same vault+url should fail
        with self.assertRaises(IntegrityError):
            Source.objects.create(
                vault=self.vault,
                url='https://example.com/unique',
                title='Second Source',
                created_by=self.user
            )

    def test_unique_constraint_allows_same_url_if_one_is_soft_deleted(self):
        """Test unique constraint allows same url if one is soft-deleted."""
        # Create and soft-delete first source
        source1 = Source.objects.create(
            vault=self.vault,
            url='https://example.com/soft-delete-test',
            title='First Source',
            created_by=self.user
        )
        source1.is_deleted = True
        source1.save()

        # Creating a new active source with same vault+url should succeed
        source2 = Source.objects.create(
            vault=self.vault,
            url='https://example.com/soft-delete-test',
            title='Second Source',
            created_by=self.user
        )

        self.assertIsNotNone(source2)
        self.assertEqual(source2.url, source1.url)
        self.assertEqual(source2.vault, source1.vault)
        self.assertFalse(source2.is_deleted)

    def test_source_type_enum_values_are_correct(self):
        """Test SourceType enum values are correct."""
        self.assertEqual(SourceType.URL, 'URL')
        self.assertEqual(SourceType.PDF, 'PDF')
        self.assertEqual(SourceType.BOOK, 'BOOK')
        self.assertEqual(SourceType.JOURNAL, 'JOURNAL')
        self.assertEqual(SourceType.DATASET, 'DATASET')

        # Verify all choices are accessible
        choices_dict = dict(SourceType.choices)
        self.assertEqual(len(choices_dict), 5)
        self.assertIn('URL', choices_dict)
        self.assertIn('PDF', choices_dict)
        self.assertIn('BOOK', choices_dict)
        self.assertIn('JOURNAL', choices_dict)
        self.assertIn('DATASET', choices_dict)

    def test_default_values(self):
        """Test default values (is_deleted=False, source_type=URL, metadata={})."""
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/defaults',
            title='Test Defaults',
            created_by=self.user
        )

        # Test default values
        self.assertFalse(source.is_deleted)
        self.assertEqual(source.source_type, SourceType.URL)
        self.assertEqual(source.metadata, {})
        self.assertEqual(source.description, '')
