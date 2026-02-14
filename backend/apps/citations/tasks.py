"""
Celery tasks for AI citation generation.

This module contains background tasks for generating citations using Claude AI.
"""
import logging
from typing import Any

from celery import shared_task
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.sources.models import Source
from apps.citations.models import CitationFormat
from apps.citations.services.ai_citation import generate_ai_citation
from apps.citations.utils import log_ai_citation_usage

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30, time_limit=30)
def generate_ai_citation_task(self, source_id: int, citation_format: str) -> dict[str, Any]:
    """
    Generate AI citation for a source asynchronously.

    This task generates a citation using Claude AI and caches the result
    in the source metadata.

    Args:
        self: Celery task instance (bound task)
        source_id: ID of the Source to generate citation for
        citation_format: Citation format string (apa7, mla9, etc.)

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
        # Note: In Celery task context, we need to get the user from the source's vault
        # The user who triggered this task isn't directly available, so we use the vault owner
        vault = source.vault
        user = vault.owner  # Use vault owner as the actor for async tasks
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
