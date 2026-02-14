from rest_framework import permissions
from rest_framework.permissions import BasePermission
from apps.vaults.models import VaultMembership, RoleChoices, ROLE_WEIGHTS


class VaultSourcePermission(BasePermission):
    """
    Permission for Source objects that enforces vault membership and role requirements.

    - list/retrieve: requires any vault membership (OWNER, CONTRIBUTOR, or VIEWER)
    - create/update: requires OWNER or CONTRIBUTOR role
    - delete: requires OWNER role only
    """

    def has_permission(self, request, view):
        """
        Check if user is authenticated for all operations.
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check if user has appropriate vault membership and role for the action.

        Args:
            obj: Source instance with .vault attribute
        """
        # Get the vault from the source
        vault = getattr(obj, 'vault', None)

        if vault is None:
            return False

        # Check if user has membership in the vault
        try:
            membership = VaultMembership.objects.get(
                vault=vault,
                user=request.user
            )
        except VaultMembership.DoesNotExist:
            return False

        # Safe methods (GET, HEAD, OPTIONS) - any member can view
        if request.method in permissions.SAFE_METHODS:
            return True

        # DELETE - only OWNER
        if request.method == 'DELETE':
            return membership.role == RoleChoices.OWNER

        # Create/Update (POST, PUT, PATCH) - OWNER or CONTRIBUTOR
        # Check if role weight >= CONTRIBUTOR weight (2)
        return ROLE_WEIGHTS.get(membership.role, 0) >= ROLE_WEIGHTS[RoleChoices.CONTRIBUTOR]
