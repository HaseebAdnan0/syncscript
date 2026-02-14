"""
Celery tasks for AI citation generation.

This module contains background tasks for generating citations using Claude AI.
"""
import logging
from typing import Any
from datetime import timedelta

from celery import shared_task
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.sources.models import Source  # type: ignore[import-untyped]
from apps.citations.models import CitationFormat  # type: ignore[import-untyped]
from apps.citations.services.ai_citation import generate_ai_citation  # type: ignore[import-untyped]
from apps.citations.utils import log_ai_citation_usage  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30, time_limit=30)
def generate_ai_citation_task(self, source_id: int, citation_format: str, user_id: int) -> dict[str, Any]:
    """
    Generate AI citation for a source asynchronously.

    This task generates a citation using Claude AI and caches the result
    in the source metadata.

    Args:
        self: Celery task instance (bound task)
        source_id: ID of the Source to generate citation for
        citation_format: Citation format string (apa7, mla9, etc.)
        user_id: ID of the User who requested the citation

    Returns:
        dict with generation results:
            - source_id: ID of the source
            - format: Citation format used
            - citation: Plain text citation
            - citation_html: HTML-formatted citation
            - cached: Always False for new generations

    Raises:
        Exception: On task failure (will retry up to max_retries)
    """
    try:
        # Get source
        source = get_object_or_404(Source, id=source_id, is_deleted=False)

        # Get user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = get_object_or_404(User, id=user_id)

        # Prepare metadata
        metadata = source.metadata.copy() if source.metadata else {}
        metadata['title'] = source.title
        metadata['url'] = source.url

        # Convert format string to enum
        format_enum = CitationFormat(citation_format)

        # Generate AI citation
        logger.info(f"Generating AI citation for source {source_id} in format {citation_format}")
        citation_text, citation_html, usage_data = generate_ai_citation(metadata, format_enum)

        # Cache the generated citation
        _cache_citation(source, citation_format, citation_text, citation_html, 'ai')

        # Log AI usage in audit log
        vault = source.vault
        log_ai_citation_usage(user, vault, source, citation_format, usage_data)

        logger.info(f"Successfully generated AI citation for source {source_id}")

        return {
            'source_id': source_id,
            'format': citation_format,
            'citation': citation_text,
            'citation_html': citation_html,
            'cached': False,
        }

    except Exception as exc:
        logger.error(f"Failed to generate AI citation for source {source_id}: {str(exc)}")
        # Retry the task with exponential backoff
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=0, time_limit=600)
def export_vault_citations_task(self, vault_id: str, citation_format: str, user_id: int) -> dict[str, Any]:  # noqa: ARG001
    """
    Export all citations from a vault asynchronously (for large vaults).

    This task generates citations for all sources in a vault and stores the
    export file temporarily for download.

    Args:
        self: Celery task instance (bound task)
        vault_id: UUID of the Vault to export citations from
        citation_format: Citation format string (apa7, mla9, etc.)
        user_id: ID of the User who requested the export

    Returns:
        dict with export results:
            - vault_id: UUID of the vault
            - format: Citation format used
            - file_path: Path to temporary export file
            - citation_count: Number of citations exported
            - expires_at: ISO timestamp when file expires (24h)

    Raises:
        Exception: On task failure
    """
    from django.core.cache import cache
    from apps.vaults.models import Vault  # type: ignore[import-untyped]
    from apps.citations.models import CitationFormat  # type: ignore[import-untyped]
    from apps.citations.services.structured_citation import has_complete_metadata, generate_structured_citation  # type: ignore[import-untyped]
    from apps.citations.services.ai_citation import generate_ai_citation  # type: ignore[import-untyped]

    try:
        logger.info(f"Starting batch export for vault {vault_id} in format {citation_format}")

        # Get vault
        vault = get_object_or_404(Vault, id=vault_id)

        # Get all sources from vault
        sources = Source.objects.filter(vault=vault, is_deleted=False).order_by('created_at')

        # Convert format string to enum
        format_enum = CitationFormat(citation_format)

        # Generate citations for all sources
        citations = []
        for source in sources:
            # Check cache first
            cached_citation = _get_cached_citation(source, citation_format)
            if cached_citation:
                citation_text = cached_citation['text']
            else:
                # Prepare metadata
                metadata = source.metadata.copy() if source.metadata else {}
                metadata['title'] = source.title
                metadata['url'] = source.url

                # Generate citation
                if has_complete_metadata(metadata):
                    citation_text = generate_structured_citation(metadata, format_enum)
                    citation_html = citation_text
                    generation_source = 'structured'
                else:
                    # Use AI citation
                    citation_text, citation_html, _ = generate_ai_citation(metadata, format_enum)
                    generation_source = 'ai'

                # Cache the generated citation
                _cache_citation(source, citation_format, citation_text, citation_html, generation_source)

            citations.append(citation_text)

        # Generate export file content
        if format_enum == CitationFormat.BIBTEX:
            content = '\n\n'.join(citations)
            file_ext = 'bib'
        else:
            content = '\n\n'.join(citations)
            file_ext = 'txt'

        # Store file in temporary directory (managed by Django cache)
        cache_key = f'export_file:{vault_id}:{citation_format}:{user_id}'
        expires_at = timezone.now() + timedelta(hours=24)

        # Store content in cache (24h expiry)
        cache.set(cache_key, {
            'content': content,
            'filename': f'{vault.name}-citations.{file_ext}',
            'content_type': 'application/x-bibtex' if format_enum == CitationFormat.BIBTEX else 'text/plain',
            'expires_at': expires_at.isoformat(),
        }, timeout=86400)  # 24 hours

        logger.info(f"Successfully exported {len(citations)} citations for vault {vault_id}")

        return {
            'vault_id': str(vault_id),
            'format': citation_format,
            'cache_key': cache_key,
            'citation_count': len(citations),
            'expires_at': expires_at.isoformat(),
        }

    except Exception as exc:
        logger.error(f"Failed to export citations for vault {vault_id}: {str(exc)}")
        raise exc


def _get_cached_citation(source: Any, citation_format: str) -> dict[str, Any] | None:
    """Get cached citation from source metadata if available."""
    if not source.metadata:
        return None
    citations_cache = source.metadata.get('citations', {})
    return citations_cache.get(citation_format)


def _cache_citation(source: Any, citation_format: str, text: str, html: str, generation_source: str) -> None:
    """
    Cache generated citation in source metadata.

    Args:
        source: Source instance
        citation_format: Citation format string
        text: Plain text citation
        html: HTML citation
        generation_source: 'structured' or 'ai'
    """
    # Initialize citations cache if not exists
    if not source.metadata:
        source.metadata = {}

    if 'citations' not in source.metadata:
        source.metadata['citations'] = {}

    # Store citation
    source.metadata['citations'][citation_format] = {
        'text': text,
        'html': html,
        'generated_at': timezone.now().isoformat(),
        'source': generation_source
    }

    source.save()
