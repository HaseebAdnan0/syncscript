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

        # Add user1 as contributor to vault1 (only if not exists)
        VaultMembership.objects.get_or_create(
            vault=self.vault1,
            user=self.user1,
            defaults={
                'role': RoleChoices.CONTRIBUTOR,
                'added_by': self.user1
            }
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


class SuggestionsViewTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create vault
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test vault',
            owner=self.user
        )

        # Create sources with various titles
        self.source1 = Source.objects.create(
            vault=self.vault,
            url='https://example.com/1',
            title='Machine Learning Basics',
            created_by=self.user
        )
        self.source2 = Source.objects.create(
            vault=self.vault,
            url='https://example.com/2',
            title='Machine Learning Advanced',
            created_by=self.user
        )
        self.source3 = Source.objects.create(
            vault=self.vault,
            url='https://example.com/3',
            title='Python Programming',
            created_by=self.user
        )

        # Create annotation
        self.annotation = Annotation.objects.create(
            source=self.source1,
            user=self.user,
            content='This is a helpful annotation about neural networks'
        )

        self.url = reverse('search:suggestions')

    def test_suggestions_requires_authentication(self):
        """Test that suggestions endpoint requires authentication"""
        response = self.client.get(self.url, {'q': 'machine'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_suggestions_minimum_query_length(self):
        """Test that queries must be at least 2 characters"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {'q': 'a'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_suggestions_success(self):
        """Test successful suggestions response"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {'q': 'machine'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('suggestions', response.data)
        self.assertIsInstance(response.data['suggestions'], list)

    def test_suggestions_max_five_results(self):
        """Test that suggestions returns max 5 results"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {'q': 'machine'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data['suggestions']), 5)

    def test_suggestions_structure(self):
        """Test that suggestions have expected structure"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {'q': 'machine'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if len(response.data['suggestions']) > 0:
            suggestion = response.data['suggestions'][0]
            self.assertIn('text', suggestion)
            self.assertIn('type', suggestion)
            self.assertIn('count', suggestion)
            self.assertIn(suggestion['type'], ['source', 'annotation'])

    def test_suggestions_respects_permissions(self):
        """Test that suggestions only show accessible content"""
        # Create another user with different vault
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_vault = Vault.objects.create(
            name='Other Vault',
            description='Private vault',
            owner=other_user
        )
        Source.objects.create(
            vault=other_vault,
            url='https://example.com/private',
            title='Machine Learning Secret',
            created_by=other_user
        )

        # User should only see their own vault's suggestions
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {'q': 'machine'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that none of the suggestions are from the private vault
        for suggestion in response.data['suggestions']:
            self.assertNotIn('Secret', suggestion['text'])


class RecentSearchesViewTest(TestCase):
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

        # Import SearchHistory model
        from apps.search.models import SearchHistory

        # Create search history for user1
        self.search1 = SearchHistory.objects.create(
            user=self.user1,
            query='machine learning',
            result_count=5
        )
        self.search2 = SearchHistory.objects.create(
            user=self.user1,
            query='python programming',
            result_count=3
        )
        self.search3 = SearchHistory.objects.create(
            user=self.user1,
            query='data science',
            result_count=10
        )

        # Create search history for user2 (to test isolation)
        self.search_other = SearchHistory.objects.create(
            user=self.user2,
            query='private search',
            result_count=1
        )

        self.url = reverse('search:recent_searches')

    def test_recent_searches_requires_authentication(self):
        """Test that recent searches endpoint requires authentication"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_recent_searches_success(self):
        """Test GET recent searches returns user's history"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recent_searches', response.data)
        self.assertEqual(len(response.data['recent_searches']), 3)

    def test_recent_searches_ordered_by_date(self):
        """Test that recent searches are ordered by most recent first"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        searches = response.data['recent_searches']
        # Most recent should be first (data science was created last)
        self.assertEqual(searches[0]['query'], 'data science')

    def test_recent_searches_max_ten(self):
        """Test that only last 10 searches are returned"""
        from apps.search.models import SearchHistory

        # Create 15 total searches for user1
        for i in range(12):  # We already have 3
            SearchHistory.objects.create(
                user=self.user1,
                query=f'test query {i}',
                result_count=1
            )

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['recent_searches']), 10)

    def test_recent_searches_respects_user_isolation(self):
        """Test that users only see their own search history"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # User1 should not see user2's searches
        for search in response.data['recent_searches']:
            self.assertNotEqual(search['query'], 'private search')

    def test_recent_searches_structure(self):
        """Test that search history has expected structure"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        search = response.data['recent_searches'][0]
        self.assertIn('id', search)
        self.assertIn('query', search)
        self.assertIn('result_count', search)
        self.assertIn('created_at', search)

    def test_delete_all_recent_searches(self):
        """Test DELETE clears all search history for user"""
        self.client.force_authenticate(user=self.user1)

        # Delete all searches
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('deleted_count', response.data)
        self.assertEqual(response.data['deleted_count'], 3)

        # Verify searches are gone
        response = self.client.get(self.url)
        self.assertEqual(len(response.data['recent_searches']), 0)

        # Verify user2's searches are unaffected
        from apps.search.models import SearchHistory
        self.assertTrue(
            SearchHistory.objects.filter(user=self.user2).exists()
        )

    def test_delete_single_recent_search(self):
        """Test DELETE /recent/{id}/ removes single entry"""
        self.client.force_authenticate(user=self.user1)

        # Delete one search
        delete_url = reverse('search:delete_recent_search', kwargs={'search_id': self.search1.id})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify it's gone
        response = self.client.get(self.url)
        self.assertEqual(len(response.data['recent_searches']), 2)

        # Verify the correct search was deleted
        for search in response.data['recent_searches']:
            self.assertNotEqual(search['query'], 'machine learning')

    def test_delete_single_search_not_found(self):
        """Test DELETE single search returns 404 for non-existent ID"""
        self.client.force_authenticate(user=self.user1)

        # Try to delete non-existent search
        delete_url = reverse('search:delete_recent_search', kwargs={'search_id': 99999})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_single_search_permission_check(self):
        """Test users cannot delete other users' search history"""
        self.client.force_authenticate(user=self.user1)

        # Try to delete user2's search
        delete_url = reverse('search:delete_recent_search', kwargs={'search_id': self.search_other.id})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify user2's search still exists
        from apps.search.models import SearchHistory
        self.assertTrue(
            SearchHistory.objects.filter(id=self.search_other.id).exists()
        )
