from rest_framework.permissions import BasePermission
from .models import VaultMembership, RoleChoices


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
