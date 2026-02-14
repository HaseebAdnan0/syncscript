"""
Batch citation export view for vaults.
Separated into its own module to avoid ViewSet routing issues.
"""
from django.http import HttpResponse
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied
from apps.vaults.models import Vault
from apps.sources.models import Source
from apps.citations.models import CitationFormat
from apps.citations.services.structured_citation import has_complete_metadata, generate_structured_citation
from apps.citations.services.ai_citation import generate_ai_citation
from datetime import datetime


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_vault_citations(request, vault_id):
    """
    GET /api/v1/vaults/{vault_id}/citations/export/?format=<format>

    Export all citations from a vault in the specified format.

    Query params:
    - format (str): Citation format (apa7, mla9, chicago17, bibtex, ieee, harvard)

    Response: File download with appropriate content-type
    - BibTeX: .bib file with all sources
    - Other formats: .txt file with citations separated by blank lines

    Permission: User must have vault access (viewer+)
    """
    # DEBUG: Print to confirm view is being called
    print(f'DEBUG: export_vault_citations called with vault_id={vault_id}')
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

    if not sources.exists():
        raise ValidationError({'error': 'Vault has no sources to export'})

    # Generate citations for all sources
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
                # For batch export, use AI citation synchronously (no async)
                citation_text, citation_html, _ = generate_ai_citation(metadata, citation_format)
                generation_source = 'ai'

            # Cache the generated citation
            _cache_citation(source, citation_format_str, citation_text, citation_html, generation_source)

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


def _get_cached_citation(source, citation_format):
    """Get cached citation from source metadata if available."""
    if not source.metadata:
        return None
    citations_cache = source.metadata.get('citations', {})
    return citations_cache.get(citation_format)


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
