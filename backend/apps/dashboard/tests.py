from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User
from apps.vaults.models import Vault, VaultMembership
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
        Annotation.objects.create(
            source=source1,
            user=self.user,
            content='Recent annotation'
        )
        old_annotation = Annotation.objects.create(
            source=source2,
            user=self.user,
            content='Old annotation'
        )
        # Manually set created_at to 10 days ago
        old_annotation.created_at = timezone.now() - timedelta(days=10)
        old_annotation.save()

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
