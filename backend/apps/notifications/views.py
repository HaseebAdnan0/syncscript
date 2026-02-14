"""
ViewSet for notifications API endpoints.
"""
from typing import Any
from django.db.models import F
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationPagination(PageNumberPagination):
    """Custom pagination for notifications with 20 items per page."""
    page_size = 20


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing notifications.

    Provides list and retrieve endpoints with filtering.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get_queryset(self) -> Any:
        """
        Return notifications for the authenticated user.

        Orders by unread first, then by created_at descending.
        Supports ?unread_only=true query param to filter unread notifications.
        """
        user = self.request.user
        queryset = Notification.objects.filter(user=user)

        # Filter to unread only if requested
        if self.request.query_params.get('unread_only') == 'true':
            queryset = queryset.filter(read_at__isnull=True)

        # Order by unread first (NULL read_at comes first with nulls_first), then newest first
        queryset = queryset.order_by(F('read_at').asc(nulls_first=True), '-created_at')

        return queryset

    @action(detail=True, methods=['patch', 'post'], url_path='mark-read')
    def mark_read(self, request, pk=None) -> Response:  # type: ignore[no-untyped-def]
        """
        Mark a notification as read.

        POST/PATCH /api/v1/notifications/{id}/mark-read/

        Idempotent: re-marking doesn't change timestamp.
        Only allows marking own notifications.
        """
        notification = self.get_object()

        # Ensure user owns this notification
        if notification.user != request.user:
            return Response(
                {'detail': 'You do not have permission to mark this notification as read.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Mark as read (idempotent - only sets timestamp if not already read)
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=['read_at'])

        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request) -> Response:  # type: ignore[no-untyped-def]
        """
        Get count of unread notifications for current user.

        GET /api/v1/notifications/unread-count/

        Returns: { "count": N }
        """
        count = Notification.objects.filter(
            user=request.user,
            read_at__isnull=True
        ).count()
        return Response({'count': count})

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request) -> Response:  # type: ignore[no-untyped-def]
        """
        Mark all notifications as read for current user.

        POST /api/v1/notifications/mark-all-read/

        Returns: { "updated": N }
        """
        updated_count = Notification.objects.filter(
            user=request.user,
            read_at__isnull=True
        ).update(read_at=timezone.now())

        return Response({'updated': updated_count})
