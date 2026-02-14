from rest_framework.permissions import BasePermission
from .models import Vault, VaultMembership, RoleChoices, ROLE_WEIGHTS


def _get_vault_from_view(view):
    """Get vault from URL kwargs (for nested routes)."""
    vault_pk = view.kwargs.get('vault_pk')
    if vault_pk:
        try:
            return Vault.objects.get(pk=vault_pk)
        except Vault.DoesNotExist:
            return None
    return None


class IsVaultOwner(BasePermission):
    """
    Permission that checks if the user has OWNER role in the vault.
    Handles both Vault objects and objects with `.vault` attribute (like VaultMembership).
    """
    def has_permission(self, request, view):
        """Check permission for create/list on nested routes."""
        vault = _get_vault_from_view(view)
        if vault is None:
            return True  # Let object permission handle it
        return VaultMembership.objects.filter(
            vault=vault,
            user=request.user,
            role=RoleChoices.OWNER
        ).exists()

    def has_object_permission(self, request, view, obj):
        # Get the vault - either the object itself or via .vault attribute
        vault = obj if hasattr(obj, 'members') else getattr(obj, 'vault', None)

        if vault is None:
            return False

        # Check if user has OWNER role membership
        return VaultMembership.objects.filter(
            vault=vault,
            user=request.user,
            role=RoleChoices.OWNER
        ).exists()


class IsVaultContributor(BasePermission):
    """
    Permission that checks if the user has CONTRIBUTOR role or higher (OWNER, CONTRIBUTOR).
    Used for write operations that contributors can perform.
    """
    def has_object_permission(self, request, view, obj):
        # Get the vault - either the object itself or via .vault attribute
        vault = obj if hasattr(obj, 'members') else getattr(obj, 'vault', None)

        if vault is None:
            return False

        # Get user's membership
        try:
            membership = VaultMembership.objects.get(
                vault=vault,
                user=request.user
            )
            # Check if role weight >= CONTRIBUTOR weight (2)
            return ROLE_WEIGHTS.get(membership.role, 0) >= ROLE_WEIGHTS[RoleChoices.CONTRIBUTOR]
        except VaultMembership.DoesNotExist:
            return False


class IsVaultMember(BasePermission):
    """
    Permission that checks if the user has any membership in the vault.
    Used for read access to vault resources.
    """
    def has_permission(self, request, view):
        """Check permission for list views on nested routes."""
        vault = _get_vault_from_view(view)
        if vault is None:
            return True  # Let object permission handle it
        return VaultMembership.objects.filter(
            vault=vault,
            user=request.user
        ).exists()

    def has_object_permission(self, request, view, obj):
        # Get the vault - either the object itself or via .vault attribute
        vault = obj if hasattr(obj, 'members') else getattr(obj, 'vault', None)

        if vault is None:
            return False

        # Check if any membership exists for this user
        return VaultMembership.objects.filter(
            vault=vault,
            user=request.user
        ).exists()
