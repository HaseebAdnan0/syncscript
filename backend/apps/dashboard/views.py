from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.vaults.models import Vault
from apps.sources.models import Source
from apps.annotations.models import Annotation


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
