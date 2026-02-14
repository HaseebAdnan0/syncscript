from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.models import User
from apps.vaults.models import Vault, VaultMembership, RoleChoices
from apps.sources.models import Source
from apps.annotations.models import Annotation
from django.contrib.postgres.search import SearchVector


class SearchViewTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

        # Create vaults
        self.vault1 = Vault.objects.create(
            name='Research Vault',
            description='Test vault for research',
            owner=self.user1
        )
        self.vault2 = Vault.objects.create(
            name='Private Vault',
            description='Another vault',
            owner=self.user2
        )

        # Add user1 as contributor to vault1
        VaultMembership.objects.create(
            vault=self.vault1,
            user=self.user1,
            role=RoleChoices.CONTRIBUTOR,
            added_by=self.user1
        )

        # Create sources
        self.source1 = Source.objects.create(
            vault=self.vault1,
            url='https://example.com/paper1',
            title='Machine Learning Research',
            description='A study on deep learning algorithms',
            created_by=self.user1
        )
        self.source2 = Source.objects.create(
            vault=self.vault1,
            url='https://example.com/paper2',
            title='Python Programming Guide',
            description='Comprehensive guide to Python',
            created_by=self.user1
        )
        self.source3 = Source.objects.create(
            vault=self.vault2,
            url='https://example.com/paper3',
            title='Private Research',
            description='Secret study',
            created_by=self.user2
        )

        # Update search vectors manually
        self.source1.search_vector = (
            SearchVector('title', weight='A', config='english') +
            SearchVector('description', weight='B', config='english')
        )
        self.source1.save(update_fields=['search_vector'])

        self.source2.search_vector = (
            SearchVector('title', weight='A', config='english') +
            SearchVector('description', weight='B', config='english')
        )
        self.source2.save(update_fields=['search_vector'])

        self.source3.search_vector = (
            SearchVector('title', weight='A', config='english') +
            SearchVector('description', weight='B', config='english')
        )
        self.source3.save(update_fields=['search_vector'])

        # Create annotations
        self.annotation1 = Annotation.objects.create(
            source=self.source1,
            user=self.user1,
            content='This is a great paper on machine learning'
        )
        self.annotation1.search_vector = SearchVector('content', weight='A', config='english')
        self.annotation1.save(update_fields=['search_vector'])

        self.url = reverse('search:search')

    def test_search_requires_authentication(self):
        """Test that search endpoint requires authentication"""
        response = self.client.get(self.url, {'q': 'machine'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_minimum_query_length(self):
        """Test that queries must be at least 2 characters"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {'q': 'a'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_search_sources_success(self):
        """Test successful search across sources"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {'q': 'machine learning'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sources', response.data)
        self.assertIn('annotations', response.data)
        self.assertIn('vaults', response.data)
        self.assertGreater(len(response.data['sources']), 0)

    def test_search_respects_vault_permissions(self):
        """Test that users can only search their accessible vaults"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {'q': 'private'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should not see results from vault2 (owned by user2)
        for source in response.data['sources']:
            self.assertNotEqual(source['vault_id'], str(self.vault2.id))

    def test_search_with_type_filter(self):
        """Test filtering by type"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {'q': 'machine', 'type': 'sources'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['sources']), 0)
        # Annotations should be empty when filtering to sources only
        self.assertEqual(len(response.data['annotations']), 0)

    def test_search_with_vault_filter(self):
        """Test filtering by vault_id"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {
            'q': 'research',
            'vault_id': str(self.vault1.id)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_vault_filter_permission_check(self):
        """Test that vault filter respects permissions"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {
            'q': 'research',
            'vault_id': str(self.vault2.id)  # user1 doesn't have access
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_annotations(self):
        """Test searching annotations"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {'q': 'great paper'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['annotations']), 0)

    def test_search_result_structure(self):
        """Test that search results have expected structure"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {'q': 'machine'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if len(response.data['sources']) > 0:
            source_result = response.data['sources'][0]
            self.assertIn('id', source_result)
            self.assertIn('type', source_result)
            self.assertIn('title', source_result)
            self.assertIn('snippet', source_result)
            self.assertIn('highlight', source_result)
            self.assertIn('relevance', source_result)
            self.assertIn('vault_id', source_result)
            self.assertIn('vault_name', source_result)
            self.assertIn('breadcrumb', source_result)

    def test_search_limit_parameter(self):
        """Test that limit parameter works"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {'q': 'research', 'limit': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Total results should not exceed limit per type
        self.assertLessEqual(len(response.data['sources']), 1)
