from rest_framework.permissions import BasePermission
from .models import VaultMembership, RoleChoices, ROLE_WEIGHTS


class IsVaultOwner(BasePermission):
    """
    Permission that checks if the user has OWNER role in the vault.
    Handles both Vault objects and objects with `.vault` attribute (like VaultMembership).
    """
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
