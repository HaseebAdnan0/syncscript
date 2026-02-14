from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.vaults.models import Vault, VaultMembership, RoleChoices
from apps.sources.models import Source, SourceType
from unittest.mock import patch

User = get_user_model()


class SourceCRUDTest(TestCase):
    """Test suite for Source API CRUD operations (US-018)."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()

        # Create test users
        self.owner_user = User.objects.create(
            username='owner',
            email='owner@example.com'
        )
        self.owner_user.set_password('testpass123')
        self.owner_user.save()

        self.contributor_user = User.objects.create(
            username='contributor',
            email='contributor@example.com'
        )
        self.contributor_user.set_password('testpass123')
        self.contributor_user.save()

        self.viewer_user = User.objects.create(
            username='viewer',
            email='viewer@example.com'
        )
        self.viewer_user.set_password('testpass123')
        self.viewer_user.save()

        self.other_user = User.objects.create(
            username='other',
            email='other@example.com'
        )
        self.other_user.set_password('testpass123')
        self.other_user.save()

        # Create test vault
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='A test vault',
            owner=self.owner_user
        )

        # Add vault memberships
        VaultMembership.objects.create(
            vault=self.vault,
            user=self.contributor_user,
            role=RoleChoices.CONTRIBUTOR
        )

        VaultMembership.objects.create(
            vault=self.vault,
            user=self.viewer_user,
            role=RoleChoices.VIEWER
        )

    @patch('apps.sources.serializers.extract_metadata')
    def test_post_creates_source_with_auto_extracted_metadata(self, mock_extract):
        """Test POST creates source with auto-extracted metadata."""
        # Mock metadata extraction
        mock_extract.return_value = {
            'title': 'Extracted Title',
            'authors': ['John Doe'],
            'publication_date': '2024-01-15',
            'abstract': 'This is an extracted abstract.'
        }

        self.client.force_authenticate(user=self.owner_user)

        url = f'/api/v1/vaults/{self.vault.id}/sources/'
        data = {
            'url': 'https://example.com/article',
            'source_type': SourceType.URL,
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['url'], 'https://example.com/article')
        self.assertEqual(response.data['title'], 'Extracted Title')
        self.assertIn('authors', response.data['metadata'])
        self.assertEqual(response.data['metadata']['authors'], ['John Doe'])
        self.assertEqual(response.data['created_by'], 'owner')

        # Verify source was created in database
        source = Source.objects.get(id=response.data['id'])
        self.assertEqual(source.vault, self.vault)
        self.assertEqual(source.created_by, self.owner_user)

    def test_get_list_returns_only_non_deleted_sources_in_users_vaults(self):
        """Test GET list returns only non-deleted sources in user's vaults."""
        # Create active and deleted sources in user's vault
        source1 = Source.objects.create(
            vault=self.vault,
            url='https://example.com/source1',
            title='Active Source 1',
            created_by=self.owner_user
        )

        source2 = Source.objects.create(
            vault=self.vault,
            url='https://example.com/source2',
            title='Active Source 2',
            created_by=self.owner_user
        )

        source_deleted = Source.objects.create(
            vault=self.vault,
            url='https://example.com/deleted',
            title='Deleted Source',
            created_by=self.owner_user,
            is_deleted=True
        )

        # Create another vault that user doesn't have access to
        other_vault = Vault.objects.create(
            name='Other Vault',
            description='Another vault',
            owner=self.other_user
        )

        source_other_vault = Source.objects.create(
            vault=other_vault,
            url='https://example.com/other-vault',
            title='Other Vault Source',
            created_by=self.other_user
        )

        # Test as owner
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get('/api/v1/sources/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        # Verify only active sources returned
        returned_ids = [item['id'] for item in response.data['results']]
        self.assertIn(str(source1.id), returned_ids)
        self.assertIn(str(source2.id), returned_ids)
        self.assertNotIn(str(source_deleted.id), returned_ids)
        self.assertNotIn(str(source_other_vault.id), returned_ids)

    def test_get_detail_returns_source_if_user_has_vault_access(self):
        """Test GET detail returns source if user has vault access."""
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/detail-test',
            title='Detail Test Source',
            description='This is a detailed description',
            source_type=SourceType.URL,
            metadata={'tags': ['test']},
            created_by=self.owner_user
        )

        # Test as contributor (has access)
        self.client.force_authenticate(user=self.contributor_user)
        response = self.client.get(f'/api/v1/sources/{source.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(source.id))
        self.assertEqual(response.data['title'], 'Detail Test Source')
        self.assertEqual(response.data['description'], 'This is a detailed description')
        self.assertEqual(response.data['url'], 'https://example.com/detail-test')

    def test_patch_updates_title_description_metadata_source_type(self):
        """Test PATCH updates title, description, metadata, source_type."""
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/patch-test',
            title='Original Title',
            description='Original description',
            source_type=SourceType.URL,
            metadata={'tags': ['old']},
            created_by=self.owner_user
        )

        self.client.force_authenticate(user=self.owner_user)

        url = f'/api/v1/sources/{source.id}/'
        data = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'source_type': SourceType.JOURNAL,
            'metadata': {'tags': ['new', 'updated']}
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')
        self.assertEqual(response.data['description'], 'Updated description')
        self.assertEqual(response.data['source_type'], SourceType.JOURNAL)
        self.assertEqual(response.data['metadata']['tags'], ['new', 'updated'])

        # Verify database was updated
        source.refresh_from_db()
        self.assertEqual(source.title, 'Updated Title')
        self.assertEqual(source.description, 'Updated description')
        self.assertEqual(source.source_type, SourceType.JOURNAL)

    def test_patch_cannot_change_url_vault_created_by(self):
        """Test PATCH cannot change url, vault, created_by."""
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/immutable-test',
            title='Test Source',
            created_by=self.owner_user
        )

        # Create another vault to attempt changing to
        other_vault = Vault.objects.create(
            name='Other Vault',
            description='Another vault',
            owner=self.owner_user
        )

        self.client.force_authenticate(user=self.owner_user)

        original_url = source.url
        original_vault_id = source.vault.id
        original_creator_id = source.created_by.id

        url = f'/api/v1/sources/{source.id}/'
        data = {
            'url': 'https://example.com/new-url',  # Attempt to change url
            'vault': str(other_vault.id),  # Attempt to change vault
            'title': 'Updated Title'  # This should work
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify immutable fields didn't change
        source.refresh_from_db()
        self.assertEqual(source.url, original_url)
        self.assertEqual(source.vault.id, original_vault_id)
        self.assertEqual(source.created_by.id, original_creator_id)

        # Verify mutable field did change
        self.assertEqual(source.title, 'Updated Title')

    def test_delete_soft_deletes_sets_is_deleted_true(self):
        """Test DELETE soft-deletes (sets is_deleted=True)."""
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/delete-test',
            title='To Be Deleted',
            created_by=self.owner_user
        )

        self.client.force_authenticate(user=self.owner_user)

        url = f'/api/v1/sources/{source.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify source still exists but is soft-deleted
        source.refresh_from_db()
        self.assertTrue(source.is_deleted)

        # Verify source no longer appears in list
        response = self.client.get('/api/v1/sources/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [item['id'] for item in response.data['results']]
        self.assertNotIn(str(source.id), returned_ids)

    def test_restore_action_sets_is_deleted_false(self):
        """Test restore action sets is_deleted=False."""
        source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/restore-test',
            title='To Be Restored',
            created_by=self.owner_user,
            is_deleted=True
        )

        self.client.force_authenticate(user=self.owner_user)

        url = f'/api/v1/sources/{source.id}/restore/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(source.id))

        # Verify source is restored
        source.refresh_from_db()
        self.assertFalse(source.is_deleted)

        # Verify source now appears in list
        response = self.client.get('/api/v1/sources/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [item['id'] for item in response.data['results']]
        self.assertIn(str(source.id), returned_ids)


class SourcePermissionTest(TestCase):
    """Test suite for Source API permission checks (US-019)."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()

        # Create test users
        self.owner_user = User.objects.create(
            username='owner',
            email='owner@example.com'
        )
        self.owner_user.set_password('testpass123')
        self.owner_user.save()

        self.contributor_user = User.objects.create(
            username='contributor',
            email='contributor@example.com'
        )
        self.contributor_user.set_password('testpass123')
        self.contributor_user.save()

        self.viewer_user = User.objects.create(
            username='viewer',
            email='viewer@example.com'
        )
        self.viewer_user.set_password('testpass123')
        self.viewer_user.save()

        self.non_member_user = User.objects.create(
            username='nonmember',
            email='nonmember@example.com'
        )
        self.non_member_user.set_password('testpass123')
        self.non_member_user.save()

        # Create test vault
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='A test vault',
            owner=self.owner_user
        )

        # Add vault memberships
        VaultMembership.objects.create(
            vault=self.vault,
            user=self.contributor_user,
            role=RoleChoices.CONTRIBUTOR
        )

        VaultMembership.objects.create(
            vault=self.vault,
            user=self.viewer_user,
            role=RoleChoices.VIEWER
        )

        # Create a test source
        self.source = Source.objects.create(
            vault=self.vault,
            url='https://example.com/test-source',
            title='Test Source',
            created_by=self.owner_user
        )

    def test_non_member_cannot_list_vault_sources(self):
        """Test non-member cannot list vault sources (403)."""
        self.client.force_authenticate(user=self.non_member_user)

        # Try to list sources in vault user is not member of
        response = self.client.get('/api/v1/sources/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Non-member should not see any sources from vault they're not part of
        self.assertEqual(len(response.data['results']), 0)

    def test_viewer_can_list_and_retrieve_but_not_create(self):
        """Test Viewer can list and retrieve but not create (403)."""
        self.client.force_authenticate(user=self.viewer_user)

        # Viewer can list sources
        response = self.client.get('/api/v1/sources/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Viewer can retrieve source detail
        response = self.client.get(f'/api/v1/sources/{self.source.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.source.id))

        # Viewer CANNOT create source
        url = f'/api/v1/vaults/{self.vault.id}/sources/'
        data = {
            'url': 'https://example.com/new-source',
            'title': 'New Source',
            'source_type': SourceType.URL,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_contributor_can_create_and_update(self):
        """Test Contributor can create and update."""
        self.client.force_authenticate(user=self.contributor_user)

        # Contributor can create source
        url = f'/api/v1/vaults/{self.vault.id}/sources/'
        data = {
            'url': 'https://example.com/contributor-source',
            'title': 'Contributor Created Source',
            'source_type': SourceType.URL,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_source_id = response.data['id']

        # Contributor can update source
        url = f'/api/v1/sources/{new_source_id}/'
        data = {
            'title': 'Updated by Contributor',
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated by Contributor')

    def test_contributor_cannot_delete(self):
        """Test Contributor cannot delete (403)."""
        self.client.force_authenticate(user=self.contributor_user)

        # Contributor CANNOT delete source
        url = f'/api/v1/sources/{self.source.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Verify source still exists and not deleted
        self.source.refresh_from_db()
        self.assertFalse(self.source.is_deleted)

    def test_owner_can_delete_and_restore(self):
        """Test Owner can delete and restore."""
        self.client.force_authenticate(user=self.owner_user)

        # Owner can delete source
        url = f'/api/v1/sources/{self.source.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify soft delete
        self.source.refresh_from_db()
        self.assertTrue(self.source.is_deleted)

        # Owner can restore source
        url = f'/api/v1/sources/{self.source.id}/restore/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify restore
        self.source.refresh_from_db()
        self.assertFalse(self.source.is_deleted)
