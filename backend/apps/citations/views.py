from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from celery.result import AsyncResult
from apps.sources.models import Source
from apps.vaults.models import VaultMembership, RoleChoices
from apps.citations.models import CitationFormat
from apps.citations.serializers import CitationRequestSerializer, CitationResponseSerializer
from apps.citations.services.structured_citation import has_complete_metadata, generate_structured_citation
from apps.citations.tasks import generate_ai_citation_task


class CitationViewSet(viewsets.ViewSet):
    """
    ViewSet for citation generation operations.
    Provides endpoint to generate citations for sources.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path=r'tasks/(?P<task_id>[a-f0-9\-]+)')
    def task_status(self, request, task_id=None):
        """
        GET /api/v1/citations/tasks/{task_id}/

        Poll the status of an async citation generation task.

        Response:
        - status (str): Task status ('pending', 'completed', 'failed')
        - result (dict): Task result (only if completed)
        """
        task = AsyncResult(task_id)

        if task.state == 'PENDING':
            return Response({
                'status': 'pending'
            }, status=status.HTTP_200_OK)
        elif task.state == 'SUCCESS':
            return Response({
                'status': 'completed',
                'result': task.result
            }, status=status.HTTP_200_OK)
        elif task.state == 'FAILURE':
            return Response({
                'status': 'failed',
                'error': str(task.info)
            }, status=status.HTTP_200_OK)
        else:
            # Other states: RETRY, STARTED, etc.
            return Response({
                'status': 'pending'
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path=r'sources/(?P<source_id>\d+)/citation')
    def generate_citation(self, request, source_id=None):
        """
        POST /api/v1/citations/sources/{source_id}/citation/

        Generate a citation for a source in the specified format.

        Request body:
        - format (str): Citation format (apa7, mla9, chicago17, bibtex, ieee, harvard)

        Response (structured citations):
        - citation (str): Plain text citation
        - citation_html (str): HTML-formatted citation with italics
        - format (str): Citation format used
        - source (str): Generation method ('structured' or 'ai')
        - cached (bool): Whether citation was served from cache

        Response (AI citations - async):
        - task_id (str): Celery task ID
        - status_url (str): URL to poll for task status

        Permission: User must have vault access (viewer+)
        """
        # Validate request data
        request_serializer = CitationRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        citation_format_str = request_serializer.validated_data['format']
        # Convert string to CitationFormat enum
        citation_format = CitationFormat(citation_format_str)

        # Get source and verify it exists
        source = get_object_or_404(Source, id=source_id, is_deleted=False)

        # Check user has permission to access vault
        self._check_vault_permission(source.vault, request.user)

        # Check if citation is cached
        cached_citation = self._get_cached_citation(source, citation_format_str)
        if cached_citation:
            response_data = {
                'citation': cached_citation['text'],
                'citation_html': cached_citation['html'],
                'format': citation_format_str,
                'source': cached_citation['source'],
                'cached': True
            }
            response_serializer = CitationResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        # Prepare metadata for citation generation
        metadata = source.metadata.copy() if source.metadata else {}
        metadata['title'] = source.title
        metadata['url'] = source.url

        # Determine generation method: structured or AI
        if has_complete_metadata(metadata):
            # Use structured citation (synchronous)
            citation_text = generate_structured_citation(metadata, citation_format)
            citation_html = citation_text  # For structured citations, HTML is same as text
            generation_source = 'structured'

            # Cache the generated citation
            self._cache_citation(source, citation_format_str, citation_text, citation_html, generation_source)

            # Prepare response
            response_data = {
                'citation': citation_text,
                'citation_html': citation_html,
                'format': citation_format_str,
                'source': generation_source,
                'cached': False
            }
            response_serializer = CitationResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)

            return Response(response_serializer.data, status=status.HTTP_200_OK)
        else:
            # Use AI citation (asynchronous via Celery)
            task = generate_ai_citation_task.delay(source.id, citation_format_str)

            # Return 202 Accepted with task ID and status URL
            return Response({
                'task_id': task.id,
                'status_url': f'/api/v1/citations/tasks/{task.id}/'
            }, status=status.HTTP_202_ACCEPTED)

    def _check_vault_permission(self, vault, user):
        """
        Check if user has permission to access vault (viewer+).

        Args:
            vault: Vault instance
            user: User instance

        Raises:
            PermissionDenied if user doesn't have permission
        """
        # Check if user is owner
        if vault.owner == user:
            return

        # Check if user has membership with any role (viewer, contributor, owner)
        membership = VaultMembership.objects.filter(
            vault=vault,
            user=user,
            role__in=[RoleChoices.VIEWER, RoleChoices.CONTRIBUTOR, RoleChoices.OWNER]
        ).first()

        if not membership:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to access this vault.")

    def _get_cached_citation(self, source, citation_format):
        """
        Get cached citation from source metadata if available.

        Args:
            source: Source instance
            citation_format: Citation format string

        Returns:
            Cached citation dict or None if not cached
        """
        if not source.metadata:
            return None

        citations_cache = source.metadata.get('citations', {})
        return citations_cache.get(citation_format)

    def _cache_citation(self, source, citation_format, text, html, generation_source):
        """
        Cache generated citation in source metadata.

        Args:
            source: Source instance
            citation_format: Citation format string
            text: Plain text citation
            html: HTML citation
            generation_source: 'structured' or 'ai'
        """
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
