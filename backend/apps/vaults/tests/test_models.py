"""
Tests for Vault models.
US-035: Write model unit tests
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.vaults.models import Vault, VaultMembership, AuditLog, RoleChoices, ROLE_WEIGHTS

User = get_user_model()


class VaultModelTest(TestCase):
    """Tests for the Vault model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_vault_creation_with_required_fields(self):
        """Test creating a vault with all required fields."""
        vault = Vault.objects.create(
            name='Test Vault',
            description='A test vault for research',
            owner=self.user
        )
        self.assertEqual(vault.name, 'Test Vault')
        self.assertEqual(vault.description, 'A test vault for research')
        self.assertEqual(vault.owner, self.user)
        self.assertFalse(vault.is_archived)
        self.assertIsNotNone(vault.id)
        self.assertIsNotNone(vault.created_at)
        self.assertIsNotNone(vault.updated_at)

    def test_vault_str_representation(self):
        """Test vault string representation."""
        vault = Vault.objects.create(name='My Vault', owner=self.user)
        self.assertEqual(str(vault), 'My Vault')

    def test_vault_ordering(self):
        """Test vaults are ordered by created_at descending."""
        vault1 = Vault.objects.create(name='First', owner=self.user)
        vault2 = Vault.objects.create(name='Second', owner=self.user)
        vaults = list(Vault.objects.all())
        self.assertEqual(vaults[0], vault2)  # Most recent first
        self.assertEqual(vaults[1], vault1)


class VaultMembershipModelTest(TestCase):
    """Tests for the VaultMembership model."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com',
            username='owner',
            password='testpass123'
        )
        self.member = User.objects.create_user(
            email='member@example.com',
            username='member',
            password='testpass123'
        )
        self.vault = Vault.objects.create(name='Test Vault', owner=self.owner)

    def test_membership_creation(self):
        """Test creating a vault membership."""
        membership = VaultMembership.objects.create(
            vault=self.vault,
            user=self.member,
            role=RoleChoices.CONTRIBUTOR,
            added_by=self.owner
        )
        self.assertEqual(membership.vault, self.vault)
        self.assertEqual(membership.user, self.member)
        self.assertEqual(membership.role, RoleChoices.CONTRIBUTOR)
        self.assertEqual(membership.added_by, self.owner)
        self.assertIsNotNone(membership.added_at)

    def test_membership_unique_constraint(self):
        """Test that duplicate user membership in same vault is prevented."""
        VaultMembership.objects.create(
            vault=self.vault,
            user=self.member,
            role=RoleChoices.CONTRIBUTOR
        )
        with self.assertRaises(IntegrityError):
            VaultMembership.objects.create(
                vault=self.vault,
                user=self.member,
                role=RoleChoices.VIEWER
            )

    def test_role_weight_calculation(self):
        """Test role weight calculation for different roles."""
        # Owner membership is auto-created by signal when vault is created
        owner_membership = VaultMembership.objects.get(
            vault=self.vault,
            user=self.owner
        )
        contributor_membership = VaultMembership.objects.create(
            vault=self.vault,
            user=self.member,
            role=RoleChoices.CONTRIBUTOR
        )
        self.assertEqual(owner_membership.get_role_weight(), 3)
        self.assertEqual(contributor_membership.get_role_weight(), 2)

    def test_role_choices_values(self):
        """Test that RoleChoices has correct values."""
        self.assertEqual(RoleChoices.OWNER, 'OWNER')
        self.assertEqual(RoleChoices.CONTRIBUTOR, 'CONTRIBUTOR')
        self.assertEqual(RoleChoices.VIEWER, 'VIEWER')

    def test_role_weights_values(self):
        """Test that ROLE_WEIGHTS has correct values."""
        self.assertEqual(ROLE_WEIGHTS[RoleChoices.OWNER], 3)
        self.assertEqual(ROLE_WEIGHTS[RoleChoices.CONTRIBUTOR], 2)
        self.assertEqual(ROLE_WEIGHTS[RoleChoices.VIEWER], 1)

    def test_membership_str_representation(self):
        """Test membership string representation."""
        membership = VaultMembership.objects.create(
            vault=self.vault,
            user=self.member,
            role=RoleChoices.CONTRIBUTOR
        )
        expected = f"{self.member.username} - {self.vault.name} (CONTRIBUTOR)"
        self.assertEqual(str(membership), expected)


class AuditLogModelTest(TestCase):
    """Tests for the AuditLog model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.vault = Vault.objects.create(name='Test Vault', owner=self.user)

    def test_audit_log_creation(self):
        """Test creating an audit log entry."""
        log = AuditLog.objects.create(
            vault=self.vault,
            actor=self.user,
            action='vault.created',
            metadata={'name': 'Test Vault'}
        )
        self.assertEqual(log.vault, self.vault)
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.action, 'vault.created')
        self.assertEqual(log.metadata, {'name': 'Test Vault'})
        self.assertIsNotNone(log.created_at)

    def test_audit_log_with_null_actor(self):
        """Test audit log can have null actor (for system actions)."""
        log = AuditLog.objects.create(
            vault=self.vault,
            actor=None,
            action='vault.auto_archived',
            metadata={}
        )
        self.assertIsNone(log.actor)

    def test_audit_log_ordering(self):
        """Test audit logs are ordered by created_at descending."""
        log1 = AuditLog.objects.create(
            vault=self.vault,
            actor=self.user,
            action='action1'
        )
        log2 = AuditLog.objects.create(
            vault=self.vault,
            actor=self.user,
            action='action2'
        )
        logs = list(AuditLog.objects.all())
        self.assertEqual(logs[0], log2)  # Most recent first
        self.assertEqual(logs[1], log1)
