from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from apps.sources.models import Source, PDFUpload
from apps.vaults.models import VaultMembership, RoleChoices
from .decorators import ai_rate_limit
from .services.claude_client import ClaudeClient
from .services.usage import log_usage
from .serializers import SummarizeRequestSerializer
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ai_rate_limit
def summarize_source(request, source_id):
    """
    POST /api/v1/sources/{id}/summarize/

    Generate AI summary for a source (URL or PDF).

    Query params:
    - regenerate (bool): Force regeneration even if cached summary exists

    Returns:
    - abstract (str): Summary of the source
    - key_findings (list): Main findings
    - methodology (str): Research methodology
    - limitations (str): Study limitations
    - keywords (list): Key terms
    - language (str): Detected language code
    - quality_flags (list): Quality indicators (e.g., 'preprint', 'not_peer_reviewed')
    - generated_at (datetime): When summary was generated
    """
    # Validate request parameters
    request_serializer = SummarizeRequestSerializer(data=request.query_params)
    request_serializer.is_valid(raise_exception=True)
    regenerate = request_serializer.validated_data['regenerate']

    # Get source and verify permissions
    source = get_object_or_404(Source, id=source_id, is_deleted=False)

    # Check if user has read permission on vault
    vault = source.vault
    has_permission = False

    # Check if user is vault owner
    if vault.owner == request.user:
        has_permission = True
    else:
        # Check if user has membership (any role can read)
        membership = VaultMembership.objects.filter(
            vault=vault,
            user=request.user
        ).first()
        has_permission = membership is not None

    if not has_permission:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("You do not have permission to access this source.")

    # Return cached summary if exists and regenerate=false
    if source.ai_summary and not regenerate:
        return Response(source.ai_summary, status=status.HTTP_200_OK)

    # Extract text from source
    text_to_summarize = ""
    source_type = source.source_type

    if source_type == 'PDF':
        # Get PDF upload with extracted text
        pdf_upload = PDFUpload.objects.filter(
            source=source,
            processing_status='completed',
            deleted_at__isnull=True
        ).first()

        if pdf_upload and pdf_upload.extracted_text:
            text_to_summarize = pdf_upload.extracted_text
        else:
            return Response(
                {"error": "PDF text extraction not available. Please wait for processing to complete."},
                status=status.HTTP_400_BAD_REQUEST
            )

    elif source_type == 'URL':
        # For URLs, use metadata abstract or fetch content
        # For now, use the abstract from metadata if available
        metadata = source.metadata or {}
        text_to_summarize = metadata.get('abstract', '')

        # If no abstract, use description or return error
        if not text_to_summarize:
            text_to_summarize = source.description

        if not text_to_summarize:
            return Response(
                {"error": "No content available for summarization. Please add a description or upload the full text."},
                status=status.HTTP_400_BAD_REQUEST
            )

    else:
        # For other source types, use description
        text_to_summarize = source.description
        if not text_to_summarize:
            return Response(
                {"error": "No content available for summarization."},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Call Claude to generate summary
    try:
        claude_client = ClaudeClient()
        result = claude_client.summarize(text_to_summarize, source_type)

        # Check for errors
        if 'error' in result:
            logger.error(f"Claude API error for source {source_id}: {result['error']}")
            return Response(
                {"error": f"AI summarization failed: {result['error']}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Extract tokens used
        tokens_used = result.pop('tokens_used', 0)

        # Add generated_at timestamp
        result['generated_at'] = timezone.now().isoformat()

        # Save summary to source
        source.ai_summary = result
        source.save(update_fields=['ai_summary'])

        # Log token usage
        log_usage(request.user, 'summary', tokens_used)

        logger.info(f"Generated AI summary for source {source_id}, tokens: {tokens_used}")

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error generating summary for source {source_id}: {e}", exc_info=True)
        return Response(
            {"error": "An unexpected error occurred during summarization."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
