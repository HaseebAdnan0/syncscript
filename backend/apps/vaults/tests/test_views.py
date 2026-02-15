"""
Tests for Vault API views.
US-036: Write vault API tests
US-037: Write membership API tests
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.vaults.models import Vault, VaultMembership, RoleChoices

User = get_user_model()


class VaultViewSetTest(TestCase):
    """Tests for VaultViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email='owner@example.com',
            username='owner',
            password='testpass123'
        )
        self.owner.email_verified = True
        self.owner.save()

        self.contributor = User.objects.create_user(
            email='contributor@example.com',
            username='contributor',
            password='testpass123'
        )
        self.contributor.email_verified = True
        self.contributor.save()

        self.viewer = User.objects.create_user(
            email='viewer@example.com',
            username='viewer',
            password='testpass123'
        )
        self.viewer.email_verified = True
        self.viewer.save()

        self.non_member = User.objects.create_user(
            email='nonmember@example.com',
            username='nonmember',
            password='testpass123'
        )
        self.non_member.email_verified = True
        self.non_member.save()

    def test_create_vault_assigns_owner_membership(self):
        """Test that creating a vault automatically assigns owner membership."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post('/api/v1/vaults/', {
            'name': 'New Vault',
            'description': 'Test description'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        vault = Vault.objects.get(id=response.data['id'])
        self.assertEqual(vault.owner, self.owner)
        # Verify owner membership was auto-created by signal
        self.assertTrue(
            VaultMembership.objects.filter(
                vault=vault, user=self.owner, role=RoleChoices.OWNER
            ).exists()
        )

    def test_list_vaults_shows_owned_vaults(self):
        """Test that list returns vaults owned by user."""
        vault = Vault.objects.create(name='Owner Vault', owner=self.owner)
        # Owner membership auto-created by signal

        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/v1/vaults/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_vaults_filter_by_archived(self):
        """Test filtering vaults by archived status."""
        Vault.objects.create(name='Active', owner=self.owner, is_archived=False)
        Vault.objects.create(name='Archived', owner=self.owner, is_archived=True)
        # Owner memberships auto-created by signal

        self.client.force_authenticate(user=self.owner)

        # Filter for archived vaults
        response = self.client.get('/api/v1/vaults/?is_archived=true')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Archived')

        # Filter for active vaults
        response = self.client.get('/api/v1/vaults/?is_archived=false')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Active')

    def test_list_vaults_filter_by_role(self):
        """Test filtering vaults by user role."""
        Vault.objects.create(name='Owned', owner=self.owner)
        # Owner membership auto-created by signal for vault1

        vault2 = Vault.objects.create(name='Contributed', owner=self.contributor)
        # Add self.owner as contributor to vault2
        VaultMembership.objects.create(vault=vault2, user=self.owner, role=RoleChoices.CONTRIBUTOR)

        self.client.force_authenticate(user=self.owner)

        # Filter for OWNER role
        response = self.client.get('/api/v1/vaults/?role=OWNER')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Owned')

    def test_non_owner_cannot_update_vault(self):
        """Test that non-owners get 403 on update."""
        vault = Vault.objects.create(name='Test', owner=self.owner)
        # Owner membership auto-created by signal
        VaultMembership.objects.create(vault=vault, user=self.contributor, role=RoleChoices.CONTRIBUTOR)

        self.client.force_authenticate(user=self.contributor)
        response = self.client.patch(f'/api/v1/vaults/{vault.id}/', {'name': 'Updated'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_owner_cannot_delete_vault(self):
        """Test that non-owners get 403 on delete."""
        vault = Vault.objects.create(name='Test', owner=self.owner)
        # Owner membership auto-created by signal
        VaultMembership.objects.create(vault=vault, user=self.contributor, role=RoleChoices.CONTRIBUTOR)

        self.client.force_authenticate(user=self.contributor)
        response = self.client.delete(f'/api/v1/vaults/{vault.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_archive_action(self):
        """Test archive action sets is_archived to True."""
        vault = Vault.objects.create(name='Test', owner=self.owner)
        # Owner membership auto-created by signal

        self.client.force_authenticate(user=self.owner)
        response = self.client.post(f'/api/v1/vaults/{vault.id}/archive/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'archived')

        vault.refresh_from_db()
        self.assertTrue(vault.is_archived)

    def test_restore_action(self):
        """Test restore action sets is_archived to False."""
        vault = Vault.objects.create(name='Test', owner=self.owner, is_archived=True)
        # Owner membership auto-created by signal

        self.client.force_authenticate(user=self.owner)
        response = self.client.post(f'/api/v1/vaults/{vault.id}/restore/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'restored')

        vault.refresh_from_db()
        self.assertFalse(vault.is_archived)

    def test_vault_citation_format_initially_null(self):
        """Test new vaults have no default citation format (US-014)."""
        vault = Vault.objects.create(name='Test', owner=self.owner)
        self.assertIsNone(vault.default_citation_format)

        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/v1/vaults/{vault.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['default_citation_format'])

    def test_owner_can_set_vault_citation_format(self):
        """Test owner can set vault's default citation format (US-014)."""
        vault = Vault.objects.create(name='Test', owner=self.owner)

        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f'/api/v1/vaults/{vault.id}/',
            {'default_citation_format': 'apa7'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['default_citation_format'], 'apa7')

        vault.refresh_from_db()
        self.assertEqual(vault.default_citation_format, 'apa7')

    def test_update_vault_citation_format_all_formats(self):
        """Test all 6 citation formats can be set (US-014)."""
        vault = Vault.objects.create(name='Test', owner=self.owner)
        self.client.force_authenticate(user=self.owner)

        formats = ['apa7', 'mla9', 'chicago17', 'bibtex', 'ieee', 'harvard']
        for fmt in formats:
            response = self.client.patch(
                f'/api/v1/vaults/{vault.id}/',
                {'default_citation_format': fmt}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['default_citation_format'], fmt)

    def test_clear_vault_citation_format(self):
        """Test vault citation format can be cleared by setting to null (US-014)."""
        vault = Vault.objects.create(name='Test', owner=self.owner, default_citation_format='apa7')

        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f'/api/v1/vaults/{vault.id}/',
            {'default_citation_format': None},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['default_citation_format'])

        vault.refresh_from_db()
        self.assertIsNone(vault.default_citation_format)

    def test_invalid_vault_citation_format_rejected(self):
        """Test invalid citation format is rejected (US-014)."""
        vault = Vault.objects.create(name='Test', owner=self.owner)

        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f'/api/v1/vaults/{vault.id}/',
            {'default_citation_format': 'invalid_format'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_contributor_cannot_set_vault_citation_format(self):
        """Test contributor cannot set vault's default citation format (US-014)."""
        vault = Vault.objects.create(name='Test', owner=self.owner)
        VaultMembership.objects.create(vault=vault, user=self.contributor, role=RoleChoices.CONTRIBUTOR)

        self.client.force_authenticate(user=self.contributor)
        response = self.client.patch(
            f'/api/v1/vaults/{vault.id}/',
            {'default_citation_format': 'apa7'}
        )
        # Contributors get 403 on vault updates (per existing permission structure)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class VaultMembershipViewSetTest(TestCase):
    """Tests for VaultMembershipViewSet (US-037)."""

    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email='owner@example.com',
            username='owner',
            password='testpass123'
        )
        self.owner.email_verified = True
        self.owner.save()

        self.member = User.objects.create_user(
            email='member@example.com',
            username='member',
            password='testpass123'
        )
        self.member.email_verified = True
        self.member.save()

        self.new_user = User.objects.create_user(
            email='newuser@example.com',
            username='newuser',
            password='testpass123'
        )
        self.new_user.email_verified = True
        self.new_user.save()

        self.vault = Vault.objects.create(name='Test Vault', owner=self.owner)
        # Owner membership auto-created by signal - get it for reference
        self.owner_membership = VaultMembership.objects.get(
            vault=self.vault,
            user=self.owner
        )

    def test_add_member_creates_membership(self):
        """Test adding a member creates VaultMembership."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f'/api/v1/vaults/{self.vault.id}/members/',
            {'user': self.new_user.id, 'role': 'CONTRIBUTOR'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            VaultMembership.objects.filter(vault=self.vault, user=self.new_user).exists()
        )

    def test_update_member_role(self):
        """Test updating a member's role."""
        membership = VaultMembership.objects.create(
            vault=self.vault,
            user=self.member,
            role=RoleChoices.CONTRIBUTOR
        )

        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f'/api/v1/vaults/{self.vault.id}/members/{membership.id}/',
            {'role': 'VIEWER'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        membership.refresh_from_db()
        self.assertEqual(membership.role, RoleChoices.VIEWER)

    def test_remove_member_deletes_membership(self):
        """Test removing a member deletes the membership."""
        membership = VaultMembership.objects.create(
            vault=self.vault,
            user=self.member,
            role=RoleChoices.CONTRIBUTOR
        )

        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(
            f'/api/v1/vaults/{self.vault.id}/members/{membership.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            VaultMembership.objects.filter(id=membership.id).exists()
        )

    def test_last_owner_deletion_returns_400(self):
        """Test deleting last owner returns 400 error."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(
            f'/api/v1/vaults/{self.vault.id}/members/{self.owner_membership.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_owner_cannot_add_member(self):
        """Test contributor cannot add members."""
        VaultMembership.objects.create(
            vault=self.vault,
            user=self.member,
            role=RoleChoices.CONTRIBUTOR
        )

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            f'/api/v1/vaults/{self.vault.id}/members/',
            {'user': self.new_user.id, 'role': 'VIEWER'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
