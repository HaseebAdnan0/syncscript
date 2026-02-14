"""Notification creation service with preference and mute checking."""

from typing import Any, Dict, Optional

from apps.notifications.models import MutedVault, Notification, NotificationPreferences


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

    return notification
