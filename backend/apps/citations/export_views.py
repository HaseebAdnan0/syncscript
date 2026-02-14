"""
Batch citation export view for vaults.
Separated into its own module to avoid ViewSet routing issues.
"""
from datetime import datetime
from django.http import HttpResponse
from django.db.models import Q
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from celery.result import AsyncResult
from apps.vaults.models import Vault  # type: ignore[import-untyped]
from apps.sources.models import Source  # type: ignore[import-untyped]
from apps.citations.models import CitationFormat  # type: ignore[import-untyped]
from apps.citations.services.structured_citation import has_complete_metadata, generate_structured_citation  # type: ignore[import-untyped]
from apps.citations.services.ai_citation import generate_ai_citation  # type: ignore[import-untyped]
from apps.citations.tasks import export_vault_citations_task  # type: ignore[import-untyped]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_vault_citations(request, vault_id):
    """
    GET /api/v1/citations/vaults/{vault_id}/export/?format=<format>

    Export all citations from a vault in the specified format.
    Uses progressive strategy based on vault size:
    - Small (≤50 sources): Synchronous, immediate download
    - Medium (51-200 sources): Synchronous with cached citations
    - Large (>200 sources): Async background job, returns 202 with status URL

    Query params:
    - format (str): Citation format (apa7, mla9, chicago17, bibtex, ieee, harvard)

    Response:
    - Small/Medium: File download with appropriate content-type
    - Large: 202 Accepted with task_id and status_url

    Permission: User must have vault access (viewer+)
    """
    user = request.user

    # Get vault and check permission
    try:
        vault = Vault.objects.get(
            Q(id=vault_id) & (Q(owner=user) | Q(members=user))
        )
    except Vault.DoesNotExist:
        raise PermissionDenied('You do not have access to this vault')

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
    source_count = sources.count()

    if source_count == 0:
        raise ValidationError({'error': 'Vault has no sources to export'})

    # Progressive export strategy based on vault size
    if source_count > 200:
        # Large vault: Queue background job
        task = export_vault_citations_task.delay(  # type: ignore[misc]
            str(vault_id),
            citation_format_str,
            user.id
        )
        return Response({
            'status': 'pending',
            'task_id': task.id,
            'status_url': f'/api/v1/citations/export/status/{task.id}/',
            'message': 'Export started. You will be notified when ready.',
            'source_count': source_count,
        }, status=status.HTTP_202_ACCEPTED)

    # Small/Medium vaults: Generate synchronously
    citations = []
    for source in sources:
        # Check cache first
        cached_citation = _get_cached_citation(source, citation_format_str)
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
                # For batch export, use AI citation synchronously
                citation_text, citation_html, _ = generate_ai_citation(metadata, citation_format)
                generation_source = 'ai'

            # Cache the generated citation
            _cache_citation(source, citation_format_str, citation_text, citation_html, generation_source)

        citations.append(citation_text)

    # Generate export file content
    if citation_format == CitationFormat.BIBTEX:
        content = '\n\n'.join(citations)
        filename = f'{vault.name}-citations.bib'
        content_type = 'application/x-bibtex'
    else:
        content = '\n\n'.join(citations)
        filename = f'{vault.name}-citations.txt'
        content_type = 'text/plain'

    # Return file download
    response = HttpResponse(content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _get_cached_citation(source, citation_format):
    """Get cached citation from source metadata if available."""
    if not source.metadata:
        return None
    citations_cache = source.metadata.get('citations', {})
    return citations_cache.get(citation_format)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_status(request, task_id):
    """
    GET /api/v1/citations/export/status/{task_id}/

    Check status of background export task.

    Response:
    - Pending: {"status": "pending", "progress": null}
    - Completed: {"status": "completed", "result": {...}, "download_url": "..."}
    - Failed: {"status": "failed", "error": "..."}

    Permission: Authenticated users only
    """
    task_result = AsyncResult(task_id)

    if task_result.state == 'PENDING':
        return Response({
            'status': 'pending',
            'progress': None,
        })
    elif task_result.state == 'SUCCESS':
        result = task_result.result
        cache_key = result.get('cache_key')

        return Response({
            'status': 'completed',
            'result': {
                'vault_id': result.get('vault_id'),
                'format': result.get('format'),
                'citation_count': result.get('citation_count'),
                'expires_at': result.get('expires_at'),
            },
            'download_url': f'/api/v1/citations/export/download/{cache_key}/',
        })
    elif task_result.state == 'FAILURE':
        return Response({
            'status': 'failed',
            'error': str(task_result.info),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        # RETRY, STARTED, etc.
        return Response({
            'status': 'pending',
            'progress': task_result.state.lower(),
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_download(request, cache_key):
    """
    GET /api/v1/citations/export/download/{cache_key}/

    Download completed export file from cache.

    Response: File download

    Permission: Authenticated users only
    """
    # Get file from cache
    cached_file = cache.get(cache_key)

    if not cached_file:
        raise ValidationError({'error': 'Export file not found or expired'})

    # Return file download
    response = HttpResponse(
        cached_file['content'],
        content_type=cached_file['content_type']
    )
    response['Content-Disposition'] = f'attachment; filename="{cached_file["filename"]}"'
    return response


def _cache_citation(source, citation_format, text, html, generation_source):
    """Cache generated citation in source metadata."""
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
