"""
ViewSet for notifications API endpoints.
"""
from typing import Any
from django.db.models import F
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

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
