from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import Vault, VaultMembership, AuditLog, RoleChoices
from .permissions import IsVaultOwner, IsVaultMember
from .serializers import VaultSerializer, VaultMembershipSerializer, AuditLogSerializer


class VaultViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing vaults with CRUD operations.

    Filters:
    - is_archived: Filter by archived status

    Ordering:
    - created_at, name: Order vaults by creation date or name
    """
    serializer_class = VaultSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_archived']
    ordering_fields = ['created_at', 'name']

    def get_permissions(self):
        """
        Return different permissions based on action.
        Mutations (update, partial_update, destroy) require owner permissions.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsVaultOwner()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Return vaults owned by or accessible to the current user."""
        user = self.request.user
        # User can see vaults they own or are a member of
        queryset = Vault.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct()

        # Filter by role if provided in query params
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(
                memberships__user=user,
                memberships__role=role
            ).distinct()

        return queryset

    def perform_create(self, serializer):
        """Set the vault owner to the current user."""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsVaultOwner])
    def archive(self, request, pk=None):
        """Archive a vault (owner only)."""
        vault = self.get_object()
        vault.is_archived = True
        vault.save()
        return Response({'status': 'archived'})

    @action(detail=True, methods=['post'], permission_classes=[IsVaultOwner])
    def restore(self, request, pk=None):
        """Restore an archived vault (owner only)."""
        vault = self.get_object()
        vault.is_archived = False
        vault.save()
        return Response({'status': 'restored'})


class VaultMembershipViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing vault members.

    Nested under /vaults/{vault_pk}/members/
    """
    serializer_class = VaultMembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Return different permissions based on action.
        Mutations (create, update, partial_update, destroy) require owner permissions.
        List/retrieve requires vault membership.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsVaultOwner()]
        return [IsVaultMember()]

    def get_queryset(self):
        """Filter memberships by vault from URL."""
        vault_pk = self.kwargs.get('vault_pk')
        return VaultMembership.objects.filter(vault_id=vault_pk)

    def perform_create(self, serializer):
        """Set vault and added_by when creating a membership."""
        vault_pk = self.kwargs.get('vault_pk')
        vault = Vault.objects.get(pk=vault_pk)
        serializer.save(vault=vault, added_by=self.request.user)

    def perform_destroy(self, instance):
        """
        Prevent deletion of the last owner (US-033).
        """
        # Check if this is the last owner being deleted
        if instance.role == RoleChoices.OWNER:
            owner_count = VaultMembership.objects.filter(
                vault=instance.vault,
                role=RoleChoices.OWNER
            ).count()

            if owner_count <= 1:
                raise ValidationError("Vault must have at least one owner")

        instance.delete()


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for audit logs.

    Nested under /vaults/{vault_pk}/audit-logs/
    Provides immutable audit trail for research integrity.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsVaultMember]

    def get_queryset(self):
        """Filter audit logs by vault from URL, ordered by newest first."""
        vault_pk = self.kwargs.get('vault_pk')
        return AuditLog.objects.filter(vault_id=vault_pk).order_by('-created_at')
