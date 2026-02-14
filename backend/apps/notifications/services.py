"""Notification creation service with preference and mute checking."""

import os
from typing import Any, Dict, Optional

import pusher  # type: ignore[import-untyped]

from apps.notifications.models import MutedVault, Notification, NotificationPreferences


# Pusher client (lazy-loaded)
_pusher_client: Optional[pusher.Pusher] = None  # type: ignore[name-defined]


def get_pusher_client() -> Optional[pusher.Pusher]:  # type: ignore[name-defined]
    """Get or create Pusher client instance."""
    global _pusher_client

    # Skip if not configured
    if not os.getenv('PUSHER_APP_ID'):
        return None

    # Create client if not exists
    if _pusher_client is None:
        _pusher_client = pusher.Pusher(
            app_id=os.getenv('PUSHER_APP_ID', ''),
            key=os.getenv('PUSHER_KEY', ''),
            secret=os.getenv('PUSHER_SECRET', ''),
            cluster=os.getenv('PUSHER_CLUSTER', 'us2'),
            ssl=True,
        )

    return _pusher_client


def create_notification(
    user: Any,  # User model
    notification_type: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> Optional[Notification]:
    """
    Create a notification for a user if preferences allow.

    Checks:
    - If vault is muted (skip if muted)
    - User preferences for the notification type

    Args:
        user: User to notify
        notification_type: Type from Notification.TYPE_CHOICES
        title: Notification title
        body: Notification body
        data: Optional JSON data (must include vault_id for mute checking)

    Returns:
        Created Notification or None if skipped
    """
    # Check if vault is muted (if vault_id is provided in data)
    if data and "vault_id" in data:
        vault_id = data["vault_id"]
        is_muted = MutedVault.objects.filter(user=user, vault_id=vault_id).exists()
        if is_muted:
            return None

    # Get user preferences (auto-create if missing)
    preferences, _ = NotificationPreferences.objects.get_or_create(user=user)

    # Check preferences based on notification type
    should_skip = False

    if notification_type == "vault_invite":
        # Vault invites always sent (no preference to disable)
        pass
    elif notification_type == "member_joined":
        # Check email_vault_activity preference
        if not preferences.email_vault_activity:
            should_skip = True
    elif notification_type == "source_added":
        # Check email_vault_activity preference
        if not preferences.email_vault_activity:
            should_skip = True
    elif notification_type in ["annotation_reply", "mention"]:
        # Check email_mentions preference
        if not preferences.email_mentions:
            should_skip = True

    if should_skip:
        return None

    # Create the notification
    notification = Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        body=body,
        data=data or {},
    )

    # Send real-time notification via Pusher
    _send_pusher_notification(user, notification)

    # Queue immediate email notification if user preference is set
    from apps.notifications.tasks import send_immediate_notification_email
    send_immediate_notification_email.delay(notification.id)  # type: ignore[attr-defined]

    return notification


def _send_pusher_notification(user: Any, notification: Notification) -> None:
    """
    Send real-time notification via Pusher to user's private channel.

    Args:
        user: User to notify
        notification: Created notification object
    """
    from apps.notifications.serializers import NotificationSerializer

    # Get Pusher client (returns None if not configured)
    client = get_pusher_client()
    if client is None:
        return

    try:
        # Serialize notification data
        serializer = NotificationSerializer(notification)

        # Send to private user channel
        channel_name = f"private-user-{user.id}"
        client.trigger(channel_name, "notification", serializer.data)

        # Also send badge update with new unread count
        unread_count = Notification.objects.filter(user=user, read_at__isnull=True).count()
        client.trigger(channel_name, "badge_update", {"count": unread_count})

    except Exception:  # type: ignore[misc]
        # Silently fail if Pusher is unavailable
        # Don't block notification creation
        pass
