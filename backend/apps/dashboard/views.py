from datetime import timedelta
from django.utils import timezone
from django.db.models import Q, F, Case, When, Count
from django.db.models.functions import TruncDate
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from apps.vaults.models import Vault, VaultMembership, AuditLog
from apps.sources.models import Source
from apps.annotations.models import Annotation
from apps.users.models import User
from .serializers import RecentVaultSerializer, ActivityFeedSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Returns aggregated dashboard statistics for the authenticated user.

    GET /api/v1/dashboard/stats/

    Returns:
        {
            "vaults_count": int,      # Total vaults user owns or is member of
            "sources_count": int,      # Total sources across all accessible vaults
            "annotations_this_week": int  # Annotations created by user in last 7 days
        }
    """
    user = request.user

    # Get vaults the user has access to (owned or member)
    accessible_vaults = Vault.objects.filter(
        Q(owner=user) | Q(members=user)
    ).distinct()

    vaults_count = accessible_vaults.count()

    # Count sources across all accessible vaults
    sources_count = Source.objects.filter(
        vault__in=accessible_vaults,
        is_deleted=False
    ).count()

    # Count annotations created by this user in the last 7 days
    seven_days_ago = timezone.now() - timedelta(days=7)
    annotations_this_week = Annotation.objects.filter(
        user=user,
        created_at__gte=seven_days_ago
    ).count()

    return Response({
        'vaults_count': vaults_count,
        'sources_count': sources_count,
        'annotations_this_week': annotations_this_week
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_vaults(request):
    """
    Returns the 3 most recently accessed vaults for the authenticated user.

    GET /api/v1/dashboard/recent-vaults/

    Returns array of vaults with fields:
        - id: vault UUID
        - name: vault name
        - description: vault description
        - last_accessed_at: timestamp of last access (or updated_at as fallback)
        - sources_count: count of non-deleted sources
        - role: user's role in the vault
    """
    user = request.user

    # Get all accessible vaults (owned or member)
    accessible_vaults = Vault.objects.filter(
        Q(owner=user) | Q(members=user)
    ).distinct()

    # Annotate with last_accessed_at from membership, use updated_at as fallback
    # Order by last_accessed_at (nulls last), then by updated_at
    vaults_with_access = accessible_vaults.annotate(
        membership_last_accessed=Case(
            When(
                memberships__user=user,
                memberships__last_accessed_at__isnull=False,
                then=F('memberships__last_accessed_at')
            ),
            default=None
        )
    ).order_by(
        F('membership_last_accessed').desc(nulls_last=True),
        '-updated_at'
    )[:3]

    serializer = RecentVaultSerializer(
        vaults_with_access,
        many=True,
        context={'request': request}
    )

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activity_feed(request):
    """
    Returns recent activity across all vaults the user has access to.

    GET /api/v1/dashboard/activity/
    Query params:
        - limit: Number of items to return (default 10, max 50)

    Returns array of activity items with fields:
        - id: audit log entry UUID
        - action: action name
        - description: human-readable description
        - actor: user info who performed the action
        - vault_id: vault UUID
        - vault_name: vault name
        - target_type: type of entity affected (source/annotation/member/vault)
        - target_id: ID of affected entity (if available)
        - created_at: timestamp
    """
    user = request.user

    # Get limit from query params, default 10, max 50
    limit = request.query_params.get('limit', 10)
    try:
        limit = int(limit)
        limit = max(1, min(limit, 50))  # Clamp between 1 and 50
    except (ValueError, TypeError):
        limit = 10

    # Get vaults the user has access to (owned or member)
    accessible_vaults = Vault.objects.filter(
        Q(owner=user) | Q(members=user)
    ).distinct()

    # Get recent audit logs for these vaults
    activity_logs = AuditLog.objects.filter(
        vault__in=accessible_vaults
    ).select_related('vault', 'actor').order_by('-created_at')[:limit]

    serializer = ActivityFeedSerializer(activity_logs, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sources_timeline(request):
    """
    Returns sources added per day over the last 30 days.

    GET /api/v1/dashboard/analytics/sources-timeline/

    Returns array of:
        [
            {"date": "2026-02-01", "count": 5},
            {"date": "2026-02-02", "count": 3},
            ...
        ]
    """
    user = request.user

    # Get vaults the user has access to (owned or member)
    accessible_vaults = Vault.objects.filter(
        Q(owner=user) | Q(members=user)
    ).distinct()

    # Calculate date 30 days ago
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Get sources grouped by date
    timeline_data = (
        Source.objects.filter(
            vault__in=accessible_vaults,
            is_deleted=False,
            created_at__gte=thirty_days_ago
        )
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Convert QuerySet to list of dicts with string dates
    result = [
        {
            'date': entry['date'].strftime('%Y-%m-%d'),
            'count': entry['count']
        }
        for entry in timeline_data
    ]

    return Response(result, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def source_types(request):
    """
    Returns breakdown of sources by type with counts and percentages.

    GET /api/v1/dashboard/analytics/source-types/

    Returns array of:
        [
            {"type": "PDF", "count": 15, "percentage": 45.5},
            {"type": "URL", "count": 10, "percentage": 30.3},
            ...
        ]
    """
    user = request.user

    # Get vaults the user has access to (owned or member)
    accessible_vaults = Vault.objects.filter(
        Q(owner=user) | Q(members=user)
    ).distinct()

    # Get total sources count
    total_sources = Source.objects.filter(
        vault__in=accessible_vaults,
        is_deleted=False
    ).count()

    # Get sources grouped by type
    type_data = (
        Source.objects.filter(
            vault__in=accessible_vaults,
            is_deleted=False
        )
        .values('source_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Calculate percentages
    result = [
        {
            'type': entry['source_type'],
            'count': entry['count'],
            'percentage': round((entry['count'] / total_sources * 100), 1) if total_sources > 0 else 0
        }
        for entry in type_data
    ]

    return Response(result, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def top_collaborators(request):
    """
    Returns top 5 collaborators by contribution count across all accessible vaults.

    GET /api/v1/dashboard/analytics/top-collaborators/

    Returns array of:
        [
            {
                "user_id": 123,
                "name": "John Doe",
                "avatar_url": "https://...",
                "contributions_count": 45
            },
            ...
        ]

    Contributions include: sources created, annotations created, audit log entries.
    """
    user = request.user

    # Get vaults the user has access to (owned or member)
    accessible_vaults = Vault.objects.filter(
        Q(owner=user) | Q(members=user)
    ).distinct()

    # Get all members of accessible vaults (excluding current user)
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Get unique collaborators from vault memberships
    collaborator_ids = VaultMembership.objects.filter(
        vault__in=accessible_vaults
    ).exclude(user=user).values_list('user_id', flat=True).distinct()

    # Count contributions for each collaborator
    collaborator_stats = []
    for collaborator_id in collaborator_ids:
        # Count sources created
        sources_count = Source.objects.filter(
            vault__in=accessible_vaults,
            created_by_id=collaborator_id,
            is_deleted=False
        ).count()

        # Count annotations created
        annotations_count = Annotation.objects.filter(
            source__vault__in=accessible_vaults,
            user_id=collaborator_id
        ).count()

        # Count audit log entries (actions performed)
        actions_count = AuditLog.objects.filter(
            vault__in=accessible_vaults,
            actor_id=collaborator_id
        ).count()

        total_contributions = sources_count + annotations_count + actions_count

        if total_contributions > 0:
            try:
                collaborator = User.objects.get(id=collaborator_id)
                collaborator_stats.append({
                    'user_id': collaborator.id,
                    'name': f"{collaborator.first_name} {collaborator.last_name}".strip() or collaborator.username,
                    'avatar_url': getattr(collaborator, 'avatar_url', '') or '',
                    'contributions_count': total_contributions
                })
            except User.DoesNotExist:
                pass

    # Sort by contributions and get top 5
    collaborator_stats.sort(key=lambda x: x['contributions_count'], reverse=True)
    top_5 = collaborator_stats[:5]

    return Response(top_5, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_platform_stats(request):
    """
    Returns public platform statistics for marketing pages.

    GET /api/v1/dashboard/public-stats/

    Returns:
        {
            "users_count": int,       # Total registered users
            "sources_count": int,     # Total sources across platform
            "citations_count": int    # Total citations generated (annotations)
        }

    Results are cached for 5 minutes to reduce database load.
    """
    cache_key = 'public_platform_stats'
    cached_stats = cache.get(cache_key)

    if cached_stats:
        return Response(cached_stats, status=status.HTTP_200_OK)

    # Count total users (verified emails only for accurate count)
    users_count = User.objects.filter(email_verified=True).count()

    # Count total sources (non-deleted)
    sources_count = Source.objects.filter(is_deleted=False).count()

    # Count total annotations (used as proxy for citations)
    citations_count = Annotation.objects.count()

    stats = {
        'users_count': users_count,
        'sources_count': sources_count,
        'citations_count': citations_count,
    }

    # Cache for 5 minutes
    cache.set(cache_key, stats, 60 * 5)

    return Response(stats, status=status.HTTP_200_OK)
