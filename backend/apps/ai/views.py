from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from apps.sources.models import Source, PDFUpload
from apps.vaults.models import Vault, VaultMembership, RoleChoices
from .decorators import ai_rate_limit
from .services.claude_client import ClaudeClient
from .services.usage import log_usage, get_daily_usage
from .services.chunking import chunk_text, get_relevant_chunks
from .serializers import SummarizeRequestSerializer, AskQuestionSerializer
from .models import ChatConversation, ChatMessage
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@ai_rate_limit
def vault_insights(request, vault_id):
    """
    GET /api/v1/vaults/{id}/insights/

    Generate AI insights about a vault's research themes, gaps, and cross-references.

    Returns cached insights if ai_insights_updated_at < 24 hours old.

    Returns:
    - themes (list): [{name, weight, source_count}]
    - research_gaps (list): Identified gaps in the research
    - cross_references (list): [{sources, relationship}]
    - suggested_searches (list): Search terms to explore
    - generated_at (datetime): When insights were generated
    """
    # Get vault and verify permissions
    vault = get_object_or_404(Vault, id=vault_id, is_archived=False)

    # Check if user has read permission on vault
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
        raise PermissionDenied("You do not have permission to access this vault.")

    # Check for cached insights (valid for 24 hours)
    if vault.ai_insights_cache and vault.ai_insights_updated_at:
        cache_age = timezone.now() - vault.ai_insights_updated_at
        if cache_age < timedelta(hours=24):
            logger.info(f"Returning cached insights for vault {vault_id}")
            return Response(vault.ai_insights_cache, status=status.HTTP_200_OK)

    # Gather all source summaries or metadata
    sources = Source.objects.filter(vault=vault, is_deleted=False).select_related('vault')

    if sources.count() == 0:
        return Response(
            {"error": "Vault has no sources. Add sources to generate insights."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Build sources data for Claude
    sources_data = []
    for source in sources:
        source_info = {
            'id': source.id,
            'title': source.title,
            'source_type': source.source_type,
        }

        # Include AI summary if available
        if source.ai_summary:
            source_info['summary'] = source.ai_summary
        else:
            # Fallback to description or metadata
            source_info['description'] = source.description or ''
            if source.metadata:
                source_info['metadata'] = {
                    'authors': source.metadata.get('authors', []),
                    'abstract': source.metadata.get('abstract', ''),
                    'keywords': source.metadata.get('keywords', []),
                }

        sources_data.append(source_info)

    # Call Claude to analyze sources
    try:
        claude_client = ClaudeClient()
        result = claude_client.analyze_sources(sources_data)

        # Check for errors
        if 'error' in result:
            logger.error(f"Claude API error for vault {vault_id}: {result['error']}")
            return Response(
                {"error": f"AI analysis failed: {result['error']}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Extract tokens used
        tokens_used = result.pop('tokens_used', 0)

        # Add generated_at timestamp
        result['generated_at'] = timezone.now().isoformat()

        # Cache insights in vault
        vault.ai_insights_cache = result
        vault.ai_insights_updated_at = timezone.now()
        vault.save(update_fields=['ai_insights_cache', 'ai_insights_updated_at'])

        # Log token usage
        log_usage(request.user, 'insights', tokens_used)

        logger.info(f"Generated AI insights for vault {vault_id}, tokens: {tokens_used}")

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error generating insights for vault {vault_id}: {e}", exc_info=True)
        return Response(
            {"error": "An unexpected error occurred during analysis."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ai_rate_limit
def ask_question(request, vault_id):
    """
    POST /api/v1/vaults/{id}/ask/

    Ask a question about vault contents and get cited answers.

    Request body:
    - question (str): The question to ask
    - conversation_id (uuid, optional): Existing conversation to continue

    Returns:
    - answer (str): AI-generated answer
    - citations (list): [{source_id, source_title, excerpt}]
    - conversation_id (uuid): Conversation ID for follow-up questions
    """
    # Validate request
    serializer = AskQuestionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    question = serializer.validated_data['question']
    conversation_id = serializer.validated_data.get('conversation_id')

    # Get vault and verify permissions
    vault = get_object_or_404(Vault, id=vault_id, is_archived=False)

    # Check if user has read permission on vault
    has_permission = False
    if vault.owner == request.user:
        has_permission = True
    else:
        membership = VaultMembership.objects.filter(
            vault=vault,
            user=request.user
        ).first()
        has_permission = membership is not None

    if not has_permission:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("You do not have permission to access this vault.")

    # Get or create conversation
    if conversation_id:
        conversation = get_object_or_404(
            ChatConversation,
            id=conversation_id,
            vault=vault,
            user=request.user
        )
    else:
        # Create new conversation
        conversation = ChatConversation.objects.create(
            vault=vault,
            user=request.user
        )

        # Enforce 10 conversation limit per vault
        vault_conversations = ChatConversation.objects.filter(
            vault=vault
        ).order_by('-updated_at')

        if vault_conversations.count() > 10:
            # Delete oldest conversations beyond limit
            to_delete = vault_conversations[10:]
            ChatConversation.objects.filter(
                id__in=[c.id for c in to_delete]
            ).delete()

    # Gather text from all sources in vault
    sources = Source.objects.filter(vault=vault, is_deleted=False).select_related('vault')

    if sources.count() == 0:
        return Response(
            {"error": "Vault has no sources. Add sources to ask questions."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Extract and chunk text from all sources
    all_chunks = []
    source_map = {}  # Map chunk indices to source info

    for source in sources:
        text_content = ""

        # Get source text
        if source.source_type == 'PDF':
            pdf_upload = PDFUpload.objects.filter(
                source=source,
                processing_status='completed',
                deleted_at__isnull=True
            ).first()
            if pdf_upload and pdf_upload.extracted_text:
                text_content = pdf_upload.extracted_text
        elif source.ai_summary:
            # Use AI summary if available
            summary = source.ai_summary
            text_content = f"{summary.get('abstract', '')} {' '.join(summary.get('key_findings', []))}"
        else:
            # Fallback to description or metadata
            text_content = source.description or ''
            if source.metadata:
                text_content += f" {source.metadata.get('abstract', '')}"

        # Skip sources with no content
        if not text_content.strip():
            continue

        # Chunk this source's text
        source_chunks = chunk_text(text_content, max_tokens=2000, overlap=200)

        # Track which source each chunk belongs to
        start_idx = len(all_chunks)
        for i, chunk in enumerate(source_chunks):
            chunk_idx = start_idx + i
            source_map[chunk_idx] = {
                'source_id': str(source.id),
                'source_title': source.title,
                'source_type': source.source_type
            }

        all_chunks.extend(source_chunks)

    if not all_chunks:
        return Response(
            {"error": "No content available in vault sources. Please process PDFs or add source descriptions."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get relevant chunks for the question
    relevant_chunks = get_relevant_chunks(question, all_chunks, max_chunks=5)

    # Build context for Claude
    context_chunks = []
    for chunk in relevant_chunks:
        chunk_info = source_map.get(chunk['chunk_id'], {})
        context_chunks.append({
            'text': chunk['text'],
            'source_id': chunk_info.get('source_id', ''),
            'source_title': chunk_info.get('source_title', 'Unknown'),
        })

    # Call Claude to answer question
    try:
        claude_client = ClaudeClient()
        result = claude_client.answer_question(question, context_chunks)

        # Check for errors
        if 'error' in result:
            logger.error(f"Claude API error for vault {vault_id} question: {result['error']}")
            return Response(
                {"error": f"AI answer failed: {result['error']}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Extract tokens used
        tokens_used = result.pop('tokens_used', 0)

        # Build citations from chunk indices
        citation_indices = result.get('citations', [])
        citations = []
        seen_sources = set()  # Avoid duplicate citations from same source

        for idx in citation_indices:
            if idx < len(relevant_chunks):
                chunk = relevant_chunks[idx]
                chunk_info = source_map.get(chunk['chunk_id'], {})
                source_id = chunk_info.get('source_id', '')

                # Skip if we already cited this source
                if source_id in seen_sources:
                    continue

                seen_sources.add(source_id)
                citations.append({
                    'source_id': source_id,
                    'source_title': chunk_info.get('source_title', 'Unknown'),
                    'excerpt': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text']
                })

        # Save user message
        ChatMessage.objects.create(
            conversation=conversation,
            role='user',
            content=question,
            sources_cited=[]
        )

        # Save assistant message with citations
        ChatMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=result.get('answer', ''),
            sources_cited=citations
        )

        # Update conversation timestamp
        conversation.save()  # Auto-updates updated_at

        # Log token usage
        log_usage(request.user, 'question', tokens_used)

        logger.info(f"Answered question for vault {vault_id}, tokens: {tokens_used}")

        return Response({
            'answer': result.get('answer', ''),
            'citations': citations,
            'conversation_id': str(conversation.id)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error answering question for vault {vault_id}: {e}", exc_info=True)
        return Response(
            {"error": "An unexpected error occurred while processing your question."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_conversations(request, vault_id):
    """
    GET /api/v1/vaults/{id}/conversations/

    List all conversations for a vault with message preview.

    Returns:
    - conversations: [{id, created_at, updated_at, message_count, preview}]
    """
    # Get vault and verify permissions
    vault = get_object_or_404(Vault, id=vault_id, is_archived=False)

    # Check if user has read permission on vault
    has_permission = False
    if vault.owner == request.user:
        has_permission = True
    else:
        membership = VaultMembership.objects.filter(
            vault=vault,
            user=request.user
        ).first()
        has_permission = membership is not None

    if not has_permission:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("You do not have permission to access this vault.")

    # Get all conversations for this vault and user
    conversations = ChatConversation.objects.filter(
        vault=vault,
        user=request.user
    ).order_by('-updated_at')

    # Build response with preview
    result = []
    for conv in conversations:
        messages = conv.messages.all()[:2]  # Get first 2 messages for preview
        message_count = conv.messages.count()

        preview = ""
        if messages:
            # Use first user message as preview
            first_user_msg = messages[0] if messages[0].role == 'user' else None
            if first_user_msg:
                preview = first_user_msg.content[:100]
                if len(first_user_msg.content) > 100:
                    preview += "..."

        result.append({
            'id': conv.id,
            'created_at': conv.created_at.isoformat(),
            'updated_at': conv.updated_at.isoformat(),
            'message_count': message_count,
            'preview': preview
        })

    return Response({'conversations': result}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation(request, vault_id, conversation_id):
    """
    GET /api/v1/vaults/{id}/conversations/{conv_id}/

    Get full message history for a conversation.

    Returns:
    - id: Conversation ID
    - created_at: When conversation started
    - updated_at: Last message time
    - messages: [{role, content, sources_cited, created_at}]
    """
    # Get vault and verify permissions
    vault = get_object_or_404(Vault, id=vault_id, is_archived=False)

    # Check if user has read permission on vault
    has_permission = False
    if vault.owner == request.user:
        has_permission = True
    else:
        membership = VaultMembership.objects.filter(
            vault=vault,
            user=request.user
        ).first()
        has_permission = membership is not None

    if not has_permission:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("You do not have permission to access this vault.")

    # Get conversation and verify ownership
    conversation = get_object_or_404(
        ChatConversation,
        id=conversation_id,
        vault=vault,
        user=request.user
    )

    # Get all messages
    messages = conversation.messages.all().order_by('created_at')

    # Build response
    message_list = []
    for msg in messages:
        message_list.append({
            'role': msg.role,
            'content': msg.content,
            'sources_cited': msg.sources_cited,
            'created_at': msg.created_at.isoformat()
        })

    return Response({
        'id': conversation.id,
        'created_at': conversation.created_at.isoformat(),
        'updated_at': conversation.updated_at.isoformat(),
        'messages': message_list
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ai_usage(request):
    """
    GET /api/v1/ai/usage/

    Get current AI usage stats for the authenticated user.

    Returns:
    - requests_today (int): Number of AI requests made today
    - requests_limit (int): Daily request limit
    - tokens_today (int): Total tokens consumed today
    - resets_at (str): ISO timestamp when usage resets (midnight UTC)
    """
    from django.conf import settings
    from datetime import timedelta

    # Get daily usage
    usage = get_daily_usage(request.user)

    # Get daily limit from settings
    requests_limit = getattr(settings, 'AI_DAILY_LIMIT', 20)

    # Calculate when usage resets (midnight UTC tomorrow)
    now = timezone.now()
    tomorrow_midnight = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    return Response({
        'requests_today': usage['request_count'],
        'requests_limit': requests_limit,
        'tokens_today': usage['tokens_used'],
        'resets_at': tomorrow_midnight.isoformat()
    }, status=status.HTTP_200_OK)
