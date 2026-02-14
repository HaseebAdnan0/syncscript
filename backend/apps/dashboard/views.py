from datetime import timedelta
from django.utils import timezone
from django.db.models import Q, F, Case, When
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.vaults.models import Vault, VaultMembership, AuditLog
from apps.sources.models import Source
from apps.annotations.models import Annotation
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
