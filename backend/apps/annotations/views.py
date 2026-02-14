"""Views for annotations app"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from apps.annotations.models import Annotation
from apps.annotations.serializers import AnnotationSerializer
from apps.annotations.permissions import IsAuthorOrReadOnly
from apps.vaults.models import Vault, VaultMembership


class AnnotationPagination(PageNumberPagination):
    """
    Custom pagination for annotations (US-030).
    50 top-level annotations per page.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class AnnotationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Annotation CRUD operations (US-029).
    Provides list, retrieve, create, update, delete functionality for annotations.
    """
    queryset = Annotation.objects.all()
    serializer_class = AnnotationSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]
    pagination_class = AnnotationPagination

    def perform_create(self, serializer):
        """
        Override perform_create to set user from request.user automatically (US-029).
        For nested routes, also sets source from URL source_pk (US-031).
        """
        # Check if this is a nested route (sources/{source_pk}/annotations/)
        source_pk = self.kwargs.get('source_pk')
        if source_pk:
            serializer.save(user=self.request.user, source_id=source_pk)
        else:
            serializer.save(user=self.request.user)

    def get_queryset(self):
        """
        Override get_queryset to filter by sources in user's vaults (US-029).
        For nested routes, also filters by source_pk and parent=None (US-030).
        Returns only annotations from sources in vaults where user is owner or member.
        """
        user = self.request.user

        # Get vaults where user is owner
        owned_vault_ids = Vault.objects.filter(owner=user).values_list('id', flat=True)

        # Get vaults where user is a member
        member_vault_ids = VaultMembership.objects.filter(user=user).values_list('vault_id', flat=True)

        # Combine both sets of vault IDs
        accessible_vault_ids = list(owned_vault_ids) + list(member_vault_ids)

        # Base queryset: annotations from accessible vaults
        queryset = Annotation.objects.filter(
            source__vault_id__in=accessible_vault_ids
        )

        # If this is a nested route (sources/{source_pk}/annotations/), filter by source and parent=None
        source_pk = self.kwargs.get('source_pk')
        if source_pk:
            # For nested routes, return only top-level annotations (parent=None) for this source
            queryset = queryset.filter(source_id=source_pk, parent=None)
            # Add prefetch_related for performance (US-030)
            queryset = queryset.prefetch_related('replies')

        return queryset
