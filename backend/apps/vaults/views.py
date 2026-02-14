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

    @action(detail=True, methods=['get'], url_path='citations/export')
    def export_citations(self, request, pk=None):
        """
        GET /api/v1/vaults/{id}/citations/export/?format=<format>

        Export all citations from a vault in the specified format.

        Query params:
        - format (str): Citation format (apa7, mla9, chicago17, bibtex, ieee, harvard)

        Response: File download with appropriate content-type
        - BibTeX: .bib file with all sources
        - Other formats: .txt file with citations separated by blank lines

        Permission: User must have vault access (viewer+)
        """
        from django.http import HttpResponse
        from apps.sources.models import Source
        from apps.citations.models import CitationFormat
        from apps.citations.services.structured_citation import has_complete_metadata, generate_structured_citation
        from apps.citations.services.ai_citation import generate_ai_citation

        vault = self.get_object()

        # Get format from query params
        citation_format_str = request.query_params.get('format')
        if not citation_format_str:
            raise ValidationError({'format': 'Format query parameter is required'})

        # Validate format
        try:
            citation_format = CitationFormat(citation_format_str.lower())
        except ValueError:
            raise ValidationError({
                'format': f'Invalid format. Must be one of: {", ".join([f.value for f in CitationFormat])}'
            })

        # Get all sources from vault
        sources = Source.objects.filter(vault=vault, is_deleted=False).order_by('created_at')

        if not sources.exists():
            raise ValidationError({'error': 'Vault has no sources to export'})

        # Generate citations for all sources
        citations = []
        for source in sources:
            # Check cache first
            cached_citation = self._get_cached_citation(source, citation_format_str)
            if cached_citation:
                citation_text = cached_citation['text']
            else:
                # Prepare metadata
                metadata = source.metadata.copy() if source.metadata else {}
                metadata['title'] = source.title
                metadata['url'] = source.url

                # Generate citation
                if has_complete_metadata(metadata):
                    citation_text = generate_structured_citation(metadata, citation_format)
                    citation_html = citation_text
                    generation_source = 'structured'
                else:
                    # For batch export, use AI citation synchronously (no async)
                    citation_text, citation_html, _ = generate_ai_citation(metadata, citation_format)
                    generation_source = 'ai'

                # Cache the generated citation
                self._cache_citation(source, citation_format_str, citation_text, citation_html, generation_source)

            citations.append(citation_text)

        # Generate export file content
        if citation_format == CitationFormat.BIBTEX:
            # BibTeX: citations already include @entry format, just join with blank lines
            content = '\n\n'.join(citations)
            filename = f'{vault.name}-citations.bib'
            content_type = 'application/x-bibtex'
        else:
            # Other formats: join citations with blank lines
            content = '\n\n'.join(citations)
            filename = f'{vault.name}-citations.txt'
            content_type = 'text/plain'

        # Return file download
        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def _get_cached_citation(self, source, citation_format):
        """Get cached citation from source metadata if available."""
        if not source.metadata:
            return None
        citations_cache = source.metadata.get('citations', {})
        return citations_cache.get(citation_format)

    def _cache_citation(self, source, citation_format, text, html, generation_source):
        """Cache generated citation in source metadata."""
        from datetime import datetime

        # Initialize citations cache if not exists
        if not source.metadata:
            source.metadata = {}
        if 'citations' not in source.metadata:
            source.metadata['citations'] = {}

        # Store citation
        source.metadata['citations'][citation_format] = {
            'text': text,
            'html': html,
            'generated_at': datetime.now().isoformat(),
            'source': generation_source
        }
        source.save()


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
