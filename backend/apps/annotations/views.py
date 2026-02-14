"""Views for annotations app"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.annotations.models import Annotation
from apps.annotations.serializers import AnnotationSerializer
from apps.annotations.permissions import IsAuthorOrReadOnly
from apps.vaults.models import Vault, VaultMembership


class AnnotationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Annotation CRUD operations (US-029).
    Provides list, retrieve, create, update, delete functionality for annotations.
    """
    queryset = Annotation.objects.all()
    serializer_class = AnnotationSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

    def perform_create(self, serializer):
        """
        Override perform_create to set user from request.user automatically (US-029).
        """
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """
        Override get_queryset to filter by sources in user's vaults (US-029).
        Returns only annotations from sources in vaults where user is owner or member.
        """
        user = self.request.user

        # Get vaults where user is owner
        owned_vault_ids = Vault.objects.filter(owner=user).values_list('id', flat=True)

        # Get vaults where user is a member
        member_vault_ids = VaultMembership.objects.filter(user=user).values_list('vault_id', flat=True)

        # Combine both sets of vault IDs
        accessible_vault_ids = list(owned_vault_ids) + list(member_vault_ids)

        # Filter annotations by sources in accessible vaults
        return Annotation.objects.filter(
            source__vault_id__in=accessible_vault_ids
        )
