from django.contrib.postgres.search import SearchQuery, SearchRank, SearchHeadline
from django.db.models import Q, F, Value, Count
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.sources.models import Source
from apps.annotations.models import Annotation
from apps.vaults.models import Vault
from .models import SearchHistory
from .serializers import SearchHistorySerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_view(request):
    """
    Search across vaults, sources, and annotations.

    Query params:
    - q (required): Search query string (min 2 chars)
    - type (optional): Filter by type - sources, annotations, vaults (comma-separated)
    - vault_id (optional): Filter to specific vault
    - limit (optional): Max results per type (default 20, max 100)
    """
    query_string = request.GET.get('q', '').strip()

    # Validate query length
    if len(query_string) < 2:
        return Response(
            {'error': 'Search query must be at least 2 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Parse filters
    type_filter = request.GET.get('type', '').strip()
    vault_id = request.GET.get('vault_id', '').strip()
    limit = min(int(request.GET.get('limit', 20)), 100)

    # Parse type filter
    search_types = set()
    if type_filter:
        search_types = set(t.strip() for t in type_filter.split(','))
    else:
        search_types = {'sources', 'annotations', 'vaults'}

    # Get user's accessible vaults (Owner, Contributor, or Viewer)
    accessible_vault_ids = list(
        request.user.vault_memberships.values_list('vault_id', flat=True)
    )

    # Add vaults where user is the owner
    owned_vault_ids = list(
        Vault.objects.filter(owner=request.user).values_list('id', flat=True)
    )
    accessible_vault_ids.extend(owned_vault_ids)
    accessible_vault_ids = list(set(accessible_vault_ids))  # Remove duplicates

    # Apply vault filter if specified
    if vault_id:
        if vault_id not in [str(vid) for vid in accessible_vault_ids]:
            return Response(
                {'error': 'Vault not found or access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        accessible_vault_ids = [vault_id]

    # Create search query
    search_query = SearchQuery(query_string, config='english')

    results = {
        'query': query_string,
        'sources': [],
        'annotations': [],
        'vaults': [],
        'total_count': 0
    }

    # Search Sources
    if 'sources' in search_types:
        source_results = (
            Source.objects
            .filter(vault_id__in=accessible_vault_ids, is_deleted=False)
            .filter(search_vector=search_query)
            .annotate(
                relevance=SearchRank(F('search_vector'), search_query),
                highlighted_title=SearchHeadline(
                    'title',
                    search_query,
                    config='english',
                    start_sel='<mark>',
                    stop_sel='</mark>',
                    max_words=10,
                    min_words=5
                ),
                highlighted_description=SearchHeadline(
                    Coalesce('description', Value('')),
                    search_query,
                    config='english',
                    start_sel='<mark>',
                    stop_sel='</mark>',
                    max_words=30,
                    min_words=10
                )
            )
            .select_related('vault', 'created_by')
            .order_by('-relevance')[:limit]
        )

        for source in source_results:
            results['sources'].append({
                'id': source.id,
                'type': 'source',
                'title': source.title,
                'snippet': source.description[:200] if source.description else '',
                'highlight': source.highlighted_description if source.description else source.highlighted_title,
                'relevance': float(source.relevance),
                'vault_id': str(source.vault.id),
                'vault_name': source.vault.name,
                'breadcrumb': f"{source.vault.name}"
            })

    # Search Annotations
    if 'annotations' in search_types:
        annotation_results = (
            Annotation.objects
            .filter(source__vault_id__in=accessible_vault_ids, source__is_deleted=False)
            .filter(search_vector=search_query)
            .annotate(
                relevance=SearchRank(F('search_vector'), search_query),
                highlighted_content=SearchHeadline(
                    'content',
                    search_query,
                    config='english',
                    start_sel='<mark>',
                    stop_sel='</mark>',
                    max_words=30,
                    min_words=10
                )
            )
            .select_related('source', 'source__vault', 'user')
            .order_by('-relevance')[:limit]
        )

        for annotation in annotation_results:
            results['annotations'].append({
                'id': annotation.id,
                'type': 'annotation',
                'title': f"Annotation by {annotation.user.username}",
                'snippet': annotation.content[:200],
                'highlight': annotation.highlighted_content,
                'relevance': float(annotation.relevance),
                'vault_id': str(annotation.source.vault.id),
                'vault_name': annotation.source.vault.name,
                'breadcrumb': f"{annotation.source.vault.name} > {annotation.source.title}"
            })

    # Search Vaults (basic name/description search, no tsvector)
    if 'vaults' in search_types:
        vault_results = (
            Vault.objects
            .filter(id__in=accessible_vault_ids)
            .filter(Q(name__icontains=query_string) | Q(description__icontains=query_string))
            .order_by('name')[:limit]
        )

        for vault in vault_results:
            # Simple relevance based on name match vs description match
            relevance = 1.0 if query_string.lower() in vault.name.lower() else 0.5
            results['vaults'].append({
                'id': str(vault.id),
                'type': 'vault',
                'title': vault.name,
                'snippet': vault.description[:200] if vault.description else '',
                'highlight': vault.name,  # No highlighting for vaults
                'relevance': relevance,
                'vault_id': str(vault.id),
                'vault_name': vault.name,
                'breadcrumb': vault.name
            })

    results['total_count'] = (
        len(results['sources']) +
        len(results['annotations']) +
        len(results['vaults'])
    )

    return Response(results)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def suggestions_view(request):
    """
    Get search suggestions for typeahead.

    Query params:
    - q (required): Search query string (min 2 chars)

    Returns top 5 suggestions based on Source titles and Annotation content.
    """
    query_string = request.GET.get('q', '').strip()

    # Validate query length
    if len(query_string) < 2:
        return Response(
            {'error': 'Search query must be at least 2 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get user's accessible vaults
    accessible_vault_ids = list(
        request.user.vault_memberships.values_list('vault_id', flat=True)
    )
    owned_vault_ids = list(
        Vault.objects.filter(owner=request.user).values_list('id', flat=True)
    )
    accessible_vault_ids.extend(owned_vault_ids)
    accessible_vault_ids = list(set(accessible_vault_ids))

    suggestions = []

    # Get suggestions from Source titles (case-insensitive prefix matching)
    source_suggestions = (
        Source.objects
        .filter(vault_id__in=accessible_vault_ids, is_deleted=False)
        .filter(title__icontains=query_string)
        .values('title')
        .annotate(count=Count('id'))
        .order_by('-count', 'title')[:3]
    )

    for suggestion in source_suggestions:
        suggestions.append({
            'text': suggestion['title'],
            'type': 'source',
            'count': suggestion['count']
        })

    # Get suggestions from Annotation content (first 100 chars, prefix matching)
    # Limited to reduce response time
    if len(suggestions) < 5:
        annotation_suggestions = (
            Annotation.objects
            .filter(source__vault_id__in=accessible_vault_ids, source__is_deleted=False)
            .filter(content__icontains=query_string)
            .values('content')
            .order_by('-created_at')[:2]
        )

        for suggestion in annotation_suggestions:
            # Extract first sentence or 50 chars as suggestion text
            content = suggestion['content']
            snippet = content[:50] + '...' if len(content) > 50 else content
            suggestions.append({
                'text': snippet,
                'type': 'annotation',
                'count': 1
            })

    # Limit to 5 total suggestions
    suggestions = suggestions[:5]

    return Response({'suggestions': suggestions})


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def recent_searches_view(request):
    """
    Get or clear recent search history.

    GET: Return last 10 searches for authenticated user.
    DELETE: Clear all search history for authenticated user.
    """
    if request.method == 'GET':
        # Get last 10 searches ordered by most recent
        recent_searches = SearchHistory.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]

        serializer = SearchHistorySerializer(recent_searches, many=True)
        return Response({'recent_searches': serializer.data})

    elif request.method == 'DELETE':
        # Clear all search history for this user
        deleted_count, _ = SearchHistory.objects.filter(user=request.user).delete()
        return Response({
            'message': f'Deleted {deleted_count} search history entries',
            'deleted_count': deleted_count
        }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_recent_search_view(request, search_id):
    """
    Delete a single search history entry.

    DELETE /api/v1/search/recent/{id}/
    """
    try:
        search_entry = SearchHistory.objects.get(id=search_id, user=request.user)
        search_entry.delete()
        return Response({
            'message': 'Search history entry deleted'
        }, status=status.HTTP_200_OK)
    except SearchHistory.DoesNotExist:
        return Response({
            'error': 'Search history entry not found or access denied'
        }, status=status.HTTP_404_NOT_FOUND)
