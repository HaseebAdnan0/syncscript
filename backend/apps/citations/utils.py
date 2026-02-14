"""
Utility functions for citation management.
"""
from typing import Dict, Any
from django.contrib.auth import get_user_model

from apps.sources.models import Source
from apps.vaults.models import Vault, AuditLog

User = get_user_model()


def invalidate_citation_cache(source: Source) -> None:
    """
    Invalidate all cached citations for a source.

    This removes the 'citations' key from source.metadata,
    forcing regeneration on next citation request.

    Args:
        source: Source instance to invalidate cache for

    Usage:
        invalidate_citation_cache(source)
    """
    # metadata is a JSONField with default=dict, so it should never be None
    # but we check anyway for safety
    if not source.metadata or not isinstance(source.metadata, dict):
        return

    if 'citations' in source.metadata:
        del source.metadata['citations']
        source.save(update_fields=['metadata'])


def log_ai_citation_usage(
    user: User,
    vault: Vault,
    source: Source,
    format: str,
    usage_data: Dict[str, Any]
) -> AuditLog:
    """
    Log AI citation generation usage in the audit log.

    This function creates an audit log entry for AI citation generation,
    tracking token usage, model used, and metadata for billing and analytics.

    Args:
        user: User who requested the citation
        vault: Vault containing the source
        source: Source being cited
        format: Citation format used (apa7, mla9, etc.)
        usage_data: Dictionary containing:
            - input_tokens: Number of input tokens
            - output_tokens: Number of output tokens
            - model: Model name used
            - total_tokens: Total tokens (input + output)

    Returns:
        Created AuditLog instance

    Usage:
        log_ai_citation_usage(user, vault, source, 'apa7', {
            'input_tokens': 150,
            'output_tokens': 50,
            'model': 'claude-3-5-sonnet-20241022',
            'total_tokens': 200
        })
    """
    return AuditLog.objects.create(
        vault=vault,
        actor=user,
        action='AI_CITATION_GENERATED',
        metadata={
            'source_id': source.id,
            'source_title': source.title,
            'format': format,
            'input_tokens': usage_data.get('input_tokens', 0),
            'output_tokens': usage_data.get('output_tokens', 0),
            'total_tokens': usage_data.get('total_tokens', 0),
            'model_used': usage_data.get('model', ''),
        }
    )
