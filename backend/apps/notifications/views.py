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

from .models import Notification, NotificationPreferences, MutedVault
from .serializers import NotificationSerializer, NotificationPreferencesSerializer, MutedVaultSerializer


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

    @action(detail=False, methods=['get', 'patch'], url_path='preferences')
    def preferences(self, request) -> Response:  # type: ignore[no-untyped-def]
        """
        View or update notification preferences for current user.

        GET /api/v1/notifications/preferences/
        PATCH /api/v1/notifications/preferences/

        Auto-creates preferences if missing on GET.
        """
        # Get or create preferences for this user
        prefs, created = NotificationPreferences.objects.get_or_create(user=request.user)

        if request.method == 'GET':
            serializer = NotificationPreferencesSerializer(prefs)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            serializer = NotificationPreferencesSerializer(
                prefs,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        return Response(
            {'detail': 'Method not allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=False, methods=['get', 'post'], url_path='muted-vaults')
    def muted_vaults(self, request) -> Response:  # type: ignore[no-untyped-def]
        """
        List or mute vaults for current user.

        GET /api/v1/notifications/muted-vaults/
        Returns list of muted vaults with vault details.

        POST /api/v1/notifications/muted-vaults/
        Mute a vault by providing { "vault_id": X }
        Validates user is member of vault before muting.
        """
        if request.method == 'GET':
            muted = MutedVault.objects.filter(user=request.user).select_related('vault')
            serializer = MutedVaultSerializer(muted, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            vault_id = request.data.get('vault_id')
            if not vault_id:
                return Response(
                    {'detail': 'vault_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Import here to avoid circular imports
            from apps.vaults.models import Vault, VaultMembership

            # Validate vault exists
            try:
                vault = Vault.objects.get(id=vault_id)
            except Vault.DoesNotExist:
                return Response(
                    {'detail': 'Vault not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Validate user is a member of this vault
            is_member = VaultMembership.objects.filter(
                vault=vault,
                user=request.user
            ).exists()

            if not is_member:
                return Response(
                    {'detail': 'You must be a member of this vault to mute it'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Create or get muted vault (idempotent)
            muted, created = MutedVault.objects.get_or_create(
                user=request.user,
                vault=vault
            )

            serializer = MutedVaultSerializer(muted)
            response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(serializer.data, status=response_status)

        return Response(
            {'detail': 'Method not allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=False, methods=['delete'], url_path='muted-vaults/(?P<vault_id>[^/.]+)')
    def unmute_vault(self, request, vault_id=None) -> Response:  # type: ignore[no-untyped-def]
        """
        Unmute a vault for current user.

        DELETE /api/v1/notifications/muted-vaults/{vault_id}/

        Idempotent: returns 204 even if vault wasn't muted.
        """
        try:
            muted = MutedVault.objects.get(
                user=request.user,
                vault_id=vault_id
            )
            muted.delete()
        except MutedVault.DoesNotExist:
            # Idempotent - no error if already unmuted
            pass

        return Response(status=status.HTTP_204_NO_CONTENT)
