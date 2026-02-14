from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from .models import Vault
from .permissions import IsVaultOwner
from .serializers import VaultSerializer


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
                vaultmembership__user=user,
                vaultmembership__role=role
            ).distinct()

        return queryset

    def perform_create(self, serializer):
        """Set the vault owner to the current user."""
        serializer.save(owner=self.request.user)
