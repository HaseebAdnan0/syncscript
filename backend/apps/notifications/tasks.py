"""Celery tasks for notification email delivery"""
from __future__ import annotations

from typing import TYPE_CHECKING
from celery import shared_task  # type: ignore[import-untyped]
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from apps.notifications.models import Notification

from apps.notifications.models import Notification
from apps.notifications.email import send_notification_email


@shared_task
def send_immediate_notification_email(notification_id: int) -> bool:
    """
    Send an immediate email for a single notification.

    Only sends if user's email preference is set to 'immediate'.
    Marks notification as emailed after successful send.

    Args:
        notification_id: ID of the notification to email

    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        notification = Notification.objects.select_related(
            'user', 'user__notification_preferences'
        ).get(id=notification_id)
    except Notification.DoesNotExist:
        print(f"Notification {notification_id} not found")
        return False

    # Check if user preference is immediate
    try:
        preferences = notification.user.notification_preferences  # type: ignore[attr-defined]
        if preferences.email_digest_frequency != 'immediate':
            # User doesn't want immediate emails
            return False
    except Exception:
        # No preferences found, don't send
        return False

    # Send the email
    success = send_notification_email(notification.user, [notification])  # type: ignore[arg-type]

    # Mark as emailed if successful
    if success:
        notification.emailed_at = timezone.now()
        notification.save(update_fields=['emailed_at'])

    return success
