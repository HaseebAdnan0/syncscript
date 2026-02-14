from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User
from apps.vaults.models import Vault, VaultMembership, AuditLog
from apps.sources.models import Source
from apps.annotations.models import Annotation


class DashboardStatsTests(TestCase):
    """Test suite for dashboard stats endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

    def test_dashboard_stats_requires_auth(self):
        """Test that stats endpoint requires authentication."""
        url = reverse('dashboard:dashboard_stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_stats_success(self):
        """Test successful retrieval of dashboard stats."""
        # Create test data
        vault1 = Vault.objects.create(name='Vault 1', owner=self.user)
        vault2 = Vault.objects.create(name='Vault 2', owner=self.other_user)
        VaultMembership.objects.create(vault=vault2, user=self.user, role='CONTRIBUTOR')

        source1 = Source.objects.create(
            vault=vault1,
            url='https://example.com/1',
            title='Source 1',
            created_by=self.user
        )
        source2 = Source.objects.create(
            vault=vault2,
            url='https://example.com/2',
            title='Source 2',
            created_by=self.other_user
        )

        # Create annotations - one from this week, one older
        # Use QuerySet.bulk_create to bypass the custom save() validation
        recent_annotation = Annotation(
            source=source1,
            user=self.user,
            content='Recent annotation',
            position={'x': 0, 'y': 0}
        )
        old_annotation = Annotation(
            source=source2,
            user=self.user,
            content='Old annotation',
            position={'x': 0, 'y': 0}
        )
        Annotation.objects.bulk_create([recent_annotation, old_annotation])

        # Update old annotation's created_at to 10 days ago (direct SQL update to bypass validation)
        Annotation.objects.filter(id=old_annotation.id).update(
            created_at=timezone.now() - timedelta(days=10)
        )

        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:dashboard_stats')
        response = self.client.get(url)

        # Assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['vaults_count'], 2)  # Owned + member
        self.assertEqual(response.data['sources_count'], 2)
        self.assertEqual(response.data['annotations_this_week'], 1)  # Only recent one

    def test_dashboard_stats_no_data(self):
        """Test stats with no data."""
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:dashboard_stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['vaults_count'], 0)
        self.assertEqual(response.data['sources_count'], 0)
        self.assertEqual(response.data['annotations_this_week'], 0)


class RecentVaultsTests(TestCase):
    """Test suite for recent vaults endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

    def test_recent_vaults_requires_auth(self):
        """Test that recent vaults endpoint requires authentication."""
        url = reverse('dashboard:recent_vaults')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_recent_vaults_with_last_accessed_at(self):
        """Test recent vaults ordered by last_accessed_at."""
        # Create 4 vaults
        vault1 = Vault.objects.create(name='Vault 1', owner=self.user)
        vault2 = Vault.objects.create(name='Vault 2', owner=self.user)
        vault3 = Vault.objects.create(name='Vault 3', owner=self.other_user)
        vault4 = Vault.objects.create(name='Vault 4', owner=self.user)

        # Add membership for vault3
        VaultMembership.objects.create(vault=vault3, user=self.user, role='CONTRIBUTOR')

        # Set last_accessed_at for some memberships
        # Vault 2 - most recent
        membership2 = VaultMembership.objects.filter(vault=vault2, user=self.user).first()
        membership2.last_accessed_at = timezone.now() - timedelta(hours=1)
        membership2.save()

        # Vault 3 - second most recent
        membership3 = VaultMembership.objects.filter(vault=vault3, user=self.user).first()
        membership3.last_accessed_at = timezone.now() - timedelta(hours=2)
        membership3.save()

        # Vault 1 and 4 have no last_accessed_at, will use updated_at

        # Create some sources
        Source.objects.create(
            vault=vault1,
            url='https://example.com/1',
            title='Source 1',
            created_by=self.user
        )
        Source.objects.create(
            vault=vault2,
            url='https://example.com/2',
            title='Source 2',
            created_by=self.user
        )

        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:recent_vaults')
        response = self.client.get(url)

        # Assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Only top 3 vaults

        # Check ordering - should be vault2, vault3, then one with latest updated_at
        self.assertEqual(response.data[0]['name'], 'Vault 2')
        self.assertEqual(response.data[1]['name'], 'Vault 3')

        # Check fields
        vault_data = response.data[0]
        self.assertIn('id', vault_data)
        self.assertIn('name', vault_data)
        self.assertIn('description', vault_data)
        self.assertIn('last_accessed_at', vault_data)
        self.assertIn('sources_count', vault_data)
        self.assertIn('role', vault_data)
        self.assertEqual(vault_data['sources_count'], 1)
        self.assertEqual(vault_data['role'], 'OWNER')

    def test_recent_vaults_fallback_to_updated_at(self):
        """Test that vaults without last_accessed_at use updated_at."""
        # Create 2 vaults without last_accessed_at
        vault1 = Vault.objects.create(name='Vault 1', owner=self.user)
        vault2 = Vault.objects.create(name='Vault 2', owner=self.user)

        # Update vault1's updated_at to be more recent
        Vault.objects.filter(id=vault1.id).update(
            updated_at=timezone.now()
        )
        Vault.objects.filter(id=vault2.id).update(
            updated_at=timezone.now() - timedelta(days=1)
        )

        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:recent_vaults')
        response = self.client.get(url)

        # Assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Should be ordered by updated_at
        self.assertEqual(response.data[0]['name'], 'Vault 1')
        self.assertEqual(response.data[1]['name'], 'Vault 2')

    def test_recent_vaults_empty(self):
        """Test recent vaults with no accessible vaults."""
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:recent_vaults')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class ActivityFeedTests(TestCase):
    """Test suite for activity feed endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        # Clear any existing audit logs from previous tests
        AuditLog.objects.all().delete()

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )

    def test_activity_feed_requires_auth(self):
        """Test that activity feed endpoint requires authentication."""
        url = reverse('dashboard:activity_feed')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_activity_feed_success(self):
        """Test successful retrieval of activity feed."""
        # Create vaults
        vault1 = Vault.objects.create(name='Vault 1', owner=self.user)
        vault2 = Vault.objects.create(name='Vault 2', owner=self.other_user)
        VaultMembership.objects.create(vault=vault2, user=self.user, role='CONTRIBUTOR')

        # Clear auto-generated audit logs from vault creation signals
        AuditLog.objects.all().delete()

        # Create audit logs for vault1
        log1 = AuditLog.objects.create(
            vault=vault1,
            actor=self.user,
            action='source_created',
            metadata={'title': 'Research Paper', 'source_id': 123}
        )
        log2 = AuditLog.objects.create(
            vault=vault1,
            actor=self.other_user,
            action='annotation_created',
            metadata={'title': 'Study Results'}
        )

        # Create audit logs for vault2
        log3 = AuditLog.objects.create(
            vault=vault2,
            actor=self.user,
            action='member_invited',
            metadata={'email': 'newuser@example.com'}
        )

        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:activity_feed')
        response = self.client.get(url)

        # Assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # All 3 logs from accessible vaults

        # Check ordering (most recent first)
        self.assertEqual(response.data[0]['action'], 'member_invited')
        self.assertEqual(response.data[1]['action'], 'annotation_created')
        self.assertEqual(response.data[2]['action'], 'source_created')

        # Check fields
        activity_item = response.data[0]
        self.assertIn('id', activity_item)
        self.assertIn('action', activity_item)
        self.assertIn('description', activity_item)
        self.assertIn('actor', activity_item)
        self.assertIn('vault_id', activity_item)
        self.assertIn('vault_name', activity_item)
        self.assertIn('target_type', activity_item)
        self.assertIn('target_id', activity_item)
        self.assertIn('created_at', activity_item)

        # Check actor information
        self.assertEqual(activity_item['actor']['username'], 'testuser')
        self.assertEqual(activity_item['actor']['first_name'], 'Test')

        # Check vault information
        self.assertEqual(activity_item['vault_name'], 'Vault 2')

        # Check description formatting
        self.assertEqual(activity_item['description'], "invited newuser@example.com to vault")

    def test_activity_feed_description_formatting(self):
        """Test human-readable description formatting for different action types."""
        vault = Vault.objects.create(name='Test Vault', owner=self.user)

        # Clear auto-generated audit logs from vault creation
        AuditLog.objects.all().delete()

        # Create logs with different actions
        AuditLog.objects.create(
            vault=vault,
            actor=self.user,
            action='source_added',
            metadata={'title': 'Research Paper'}
        )
        AuditLog.objects.create(
            vault=vault,
            actor=self.user,
            action='annotation_updated',
            metadata={'title': 'Study'}
        )
        AuditLog.objects.create(
            vault=vault,
            actor=self.user,
            action='member_removed',
            metadata={'email': 'old@example.com'}
        )
        AuditLog.objects.create(
            vault=vault,
            actor=self.user,
            action='vault_created',
            metadata={'name': 'New Vault'}
        )

        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:activity_feed')
        response = self.client.get(url)

        # Assert descriptions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

        descriptions = [item['description'] for item in response.data]
        self.assertIn("created vault 'New Vault'", descriptions)
        self.assertIn("removed old@example.com from vault", descriptions)
        self.assertIn("updated annotation on 'Study'", descriptions)
        self.assertIn("added source 'Research Paper'", descriptions)

    def test_activity_feed_limit_param(self):
        """Test limit query parameter."""
        vault = Vault.objects.create(name='Test Vault', owner=self.user)

        # Clear auto-generated audit logs from vault creation
        AuditLog.objects.all().delete()

        # Create 15 audit logs
        for i in range(15):
            AuditLog.objects.create(
                vault=vault,
                actor=self.user,
                action=f'action_{i}',
                metadata={'index': i}
            )

        # Authenticate
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:activity_feed')

        # Test default limit (10)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)

        # Test custom limit
        response = self.client.get(url, {'limit': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

        # Test max limit (50)
        response = self.client.get(url, {'limit': 100})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 15)  # Capped at actual count

        # Test invalid limit (should default to 10)
        response = self.client.get(url, {'limit': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)

    def test_activity_feed_empty(self):
        """Test activity feed with no accessible vaults."""
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:activity_feed')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_activity_feed_no_actor(self):
        """Test activity feed with null actor (system action)."""
        vault = Vault.objects.create(name='Test Vault', owner=self.user)

        # Clear auto-generated audit logs from vault creation
        AuditLog.objects.all().delete()

        AuditLog.objects.create(
            vault=vault,
            actor=None,  # System action
            action='system_cleanup',
            metadata={}
        )

        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:activity_feed')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIsNone(response.data[0]['actor'])

    def test_activity_feed_only_accessible_vaults(self):
        """Test that activity feed only shows logs from accessible vaults."""
        # Create vault user has no access to
        inaccessible_vault = Vault.objects.create(name='Private Vault', owner=self.other_user)

        # Create vault user has access to
        accessible_vault = Vault.objects.create(name='Accessible Vault', owner=self.user)

        # Clear auto-generated audit logs from vault creation
        AuditLog.objects.all().delete()

        AuditLog.objects.create(
            vault=inaccessible_vault,
            actor=self.other_user,
            action='private_action',
            metadata={}
        )

        AuditLog.objects.create(
            vault=accessible_vault,
            actor=self.user,
            action='accessible_action',
            metadata={}
        )

        # Authenticate and request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:activity_feed')
        response = self.client.get(url)

        # Should only see log from accessible vault
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['action'], 'accessible_action')


class AnalyticsTests(TestCase):
    """Test suite for analytics endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.other_user = User.objects.create_user(
            username='collaborator',
            email='collab@example.com',
            password='testpass123',
            first_name='Collab',
            last_name='User'
        )

    def test_sources_timeline_requires_auth(self):
        """Test that sources timeline endpoint requires authentication."""
        url = reverse('dashboard:sources_timeline')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sources_timeline_success(self):
        """Test successful retrieval of sources timeline."""
        # Create vault
        vault = Vault.objects.create(name='Test Vault', owner=self.user)

        # Create sources at different dates
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)

        # Create sources
        source1 = Source.objects.create(
            vault=vault,
            url='https://example.com/1',
            title='Source 1',
            created_by=self.user
        )
        source2 = Source.objects.create(
            vault=vault,
            url='https://example.com/2',
            title='Source 2',
            created_by=self.user
        )
        source3 = Source.objects.create(
            vault=vault,
            url='https://example.com/3',
            title='Source 3',
            created_by=self.user
        )

        # Update created_at to different dates (bypass validation)
        Source.objects.filter(id=source1.id).update(created_at=today)
        Source.objects.filter(id=source2.id).update(created_at=yesterday)
        Source.objects.filter(id=source3.id).update(created_at=two_days_ago)

        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:sources_timeline')
        response = self.client.get(url)

        # Assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 3)  # At least 3 date entries

        # Check data structure
        for item in response.data:
            self.assertIn('date', item)
            self.assertIn('count', item)
            self.assertIsInstance(item['date'], str)  # Date should be string
            self.assertIsInstance(item['count'], int)

        # Verify dates are in format YYYY-MM-DD
        import re
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        for item in response.data:
            self.assertTrue(date_pattern.match(item['date']))

    def test_sources_timeline_excludes_deleted(self):
        """Test that deleted sources are excluded from timeline."""
        vault = Vault.objects.create(name='Test Vault', owner=self.user)

        # Create active and deleted sources
        active_source = Source.objects.create(
            vault=vault,
            url='https://example.com/active',
            title='Active Source',
            created_by=self.user,
            is_deleted=False
        )
        deleted_source = Source.objects.create(
            vault=vault,
            url='https://example.com/deleted',
            title='Deleted Source',
            created_by=self.user,
            is_deleted=True
        )

        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:sources_timeline')
        response = self.client.get(url)

        # Assert response includes only active sources
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        total_count = sum(item['count'] for item in response.data)
        self.assertEqual(total_count, 1)  # Only active source counted

    def test_sources_timeline_only_last_30_days(self):
        """Test that timeline only includes sources from last 30 days."""
        vault = Vault.objects.create(name='Test Vault', owner=self.user)

        # Create recent and old sources
        recent_source = Source.objects.create(
            vault=vault,
            url='https://example.com/recent',
            title='Recent Source',
            created_by=self.user
        )
        old_source = Source.objects.create(
            vault=vault,
            url='https://example.com/old',
            title='Old Source',
            created_by=self.user
        )

        # Update old source to 40 days ago
        Source.objects.filter(id=old_source.id).update(
            created_at=timezone.now() - timedelta(days=40)
        )

        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:sources_timeline')
        response = self.client.get(url)

        # Assert response includes only recent sources
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        total_count = sum(item['count'] for item in response.data)
        self.assertEqual(total_count, 1)  # Only recent source counted

    def test_sources_timeline_empty(self):
        """Test timeline with no sources."""
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:sources_timeline')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_source_types_requires_auth(self):
        """Test that source types endpoint requires authentication."""
        url = reverse('dashboard:source_types')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_source_types_success(self):
        """Test successful retrieval of source type breakdown."""
        vault = Vault.objects.create(name='Test Vault', owner=self.user)

        # Create sources of different types
        Source.objects.create(
            vault=vault,
            url='https://example.com/1',
            title='PDF 1',
            source_type='PDF',
            created_by=self.user
        )
        Source.objects.create(
            vault=vault,
            url='https://example.com/2',
            title='PDF 2',
            source_type='PDF',
            created_by=self.user
        )
        Source.objects.create(
            vault=vault,
            url='https://example.com/3',
            title='URL 1',
            source_type='URL',
            created_by=self.user
        )
        Source.objects.create(
            vault=vault,
            url='https://example.com/4',
            title='Book 1',
            source_type='BOOK',
            created_by=self.user
        )

        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:source_types')
        response = self.client.get(url)

        # Assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 3)  # 3 different types

        # Check data structure
        for item in response.data:
            self.assertIn('type', item)
            self.assertIn('count', item)
            self.assertIn('percentage', item)

        # Verify percentages add up to 100 (with rounding tolerance)
        total_percentage = sum(item['percentage'] for item in response.data)
        self.assertAlmostEqual(total_percentage, 100.0, delta=0.5)

        # Check PDF type (should be highest count)
        pdf_item = next(item for item in response.data if item['type'] == 'PDF')
        self.assertEqual(pdf_item['count'], 2)
        self.assertEqual(pdf_item['percentage'], 50.0)

    def test_source_types_excludes_deleted(self):
        """Test that deleted sources are excluded from type breakdown."""
        vault = Vault.objects.create(name='Test Vault', owner=self.user)

        # Create active and deleted sources
        Source.objects.create(
            vault=vault,
            url='https://example.com/active',
            title='Active PDF',
            source_type='PDF',
            created_by=self.user,
            is_deleted=False
        )
        Source.objects.create(
            vault=vault,
            url='https://example.com/deleted',
            title='Deleted PDF',
            source_type='PDF',
            created_by=self.user,
            is_deleted=True
        )

        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:source_types')
        response = self.client.get(url)

        # Assert response includes only active sources
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        total_count = sum(item['count'] for item in response.data)
        self.assertEqual(total_count, 1)  # Only active source counted

    def test_source_types_empty(self):
        """Test source types with no sources."""
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:source_types')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_top_collaborators_requires_auth(self):
        """Test that top collaborators endpoint requires authentication."""
        url = reverse('dashboard:top_collaborators')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_top_collaborators_success(self):
        """Test successful retrieval of top collaborators."""
        # Create vault with collaborator
        vault = Vault.objects.create(name='Shared Vault', owner=self.user)
        VaultMembership.objects.create(vault=vault, user=self.other_user, role='CONTRIBUTOR')

        # Clear auto-generated audit logs
        AuditLog.objects.all().delete()

        # Create sources by collaborator
        Source.objects.create(
            vault=vault,
            url='https://example.com/1',
            title='Source 1',
            created_by=self.other_user
        )
        Source.objects.create(
            vault=vault,
            url='https://example.com/2',
            title='Source 2',
            created_by=self.other_user
        )

        # Create annotations by collaborator
        source1 = Source.objects.filter(created_by=self.other_user).first()
        annotation = Annotation(
            source=source1,
            user=self.other_user,
            content='Great insight',
            position={'x': 0, 'y': 0}
        )
        Annotation.objects.bulk_create([annotation])

        # Create audit log by collaborator
        AuditLog.objects.create(
            vault=vault,
            actor=self.other_user,
            action='vault_updated',
            metadata={}
        )

        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:top_collaborators')
        response = self.client.get(url)

        # Assert response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)  # One collaborator

        # Check data structure
        collaborator = response.data[0]
        self.assertIn('user_id', collaborator)
        self.assertIn('name', collaborator)
        self.assertIn('avatar_url', collaborator)
        self.assertIn('contributions_count', collaborator)

        # Verify collaborator data
        self.assertEqual(collaborator['user_id'], self.other_user.id)
        self.assertEqual(collaborator['name'], 'Collab User')
        self.assertEqual(collaborator['contributions_count'], 4)  # 2 sources + 1 annotation + 1 audit

    def test_top_collaborators_excludes_current_user(self):
        """Test that current user is excluded from collaborators list."""
        vault = Vault.objects.create(name='Test Vault', owner=self.user)

        # Create source by current user
        Source.objects.create(
            vault=vault,
            url='https://example.com/1',
            title='My Source',
            created_by=self.user
        )

        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:top_collaborators')
        response = self.client.get(url)

        # Assert current user is excluded
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_top_collaborators_returns_top_5(self):
        """Test that only top 5 collaborators are returned."""
        vault = Vault.objects.create(name='Test Vault', owner=self.user)

        # Create 7 collaborators
        collaborators = []
        for i in range(7):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123',
                first_name=f'User{i}',
                last_name='Test'
            )
            collaborators.append(user)
            VaultMembership.objects.create(vault=vault, user=user, role='CONTRIBUTOR')

            # Create varying numbers of sources (user0 has most)
            for j in range(7 - i):
                Source.objects.create(
                    vault=vault,
                    url=f'https://example.com/user{i}-{j}',
                    title=f'Source {i}-{j}',
                    created_by=user
                )

        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:top_collaborators')
        response = self.client.get(url)

        # Assert only top 5 returned
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

        # Verify ordering (user0 should be first with most contributions)
        self.assertEqual(response.data[0]['name'], 'User0 Test')
        self.assertGreater(
            response.data[0]['contributions_count'],
            response.data[1]['contributions_count']
        )

    def test_top_collaborators_empty(self):
        """Test top collaborators with no collaborators."""
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:top_collaborators')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_top_collaborators_only_accessible_vaults(self):
        """Test that collaborators are only from accessible vaults."""
        # Create accessible vault with collaborator
        accessible_vault = Vault.objects.create(name='Accessible', owner=self.user)
        VaultMembership.objects.create(vault=accessible_vault, user=self.other_user, role='CONTRIBUTOR')

        # Create inaccessible vault with different collaborator
        third_user = User.objects.create_user(
            username='thirduser',
            email='third@example.com',
            password='testpass123'
        )
        inaccessible_vault = Vault.objects.create(name='Inaccessible', owner=third_user)

        # Create sources
        Source.objects.create(
            vault=accessible_vault,
            url='https://example.com/1',
            title='Accessible Source',
            created_by=self.other_user
        )
        Source.objects.create(
            vault=inaccessible_vault,
            url='https://example.com/2',
            title='Inaccessible Source',
            created_by=third_user
        )

        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:top_collaborators')
        response = self.client.get(url)

        # Assert only collaborator from accessible vault is included
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user_id'], self.other_user.id)
