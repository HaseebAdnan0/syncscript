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
