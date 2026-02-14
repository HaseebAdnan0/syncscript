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


@shared_task
def send_daily_digest() -> int:
    """
    Send daily email digests to users who have daily preference.

    Queries all users with email_digest_frequency='daily' and un-emailed notifications.
    Batches all un-emailed notifications per user into a single digest email.
    Marks all notifications as emailed after successful send.

    Returns:
        Number of users who received digest emails
    """
    from django.contrib.auth import get_user_model
    from apps.notifications.models import NotificationPreferences

    User = get_user_model()
    sent_count = 0

    # Get all users with daily preference
    users_with_daily = NotificationPreferences.objects.filter(
        email_digest_frequency='daily'
    ).select_related('user')

    for pref in users_with_daily:
        user = pref.user

        # Get un-emailed notifications for this user
        notifications = Notification.objects.filter(
            user=user,
            emailed_at__isnull=True
        ).order_by('-created_at')

        if not notifications.exists():
            continue

        # Send digest email
        success = send_notification_email(user, list(notifications))  # type: ignore[arg-type]

        if success:
            # Mark all as emailed
            notification_ids = [n.id for n in notifications]  # type: ignore[attr-defined]
            Notification.objects.filter(id__in=notification_ids).update(
                emailed_at=timezone.now()
            )
            sent_count += 1
            print(f"Sent daily digest to {user.username} with {len(notification_ids)} notifications")

    print(f"Daily digest: sent to {sent_count} users")
    return sent_count


@shared_task
def send_weekly_digest() -> int:
    """
    Send weekly email digests to users who have weekly preference.

    Queries all users with email_digest_frequency='weekly' and un-emailed notifications.
    Batches all un-emailed notifications per user into a single digest email.
    Marks all notifications as emailed after successful send.

    Returns:
        Number of users who received digest emails
    """
    from django.contrib.auth import get_user_model
    from apps.notifications.models import NotificationPreferences

    User = get_user_model()
    sent_count = 0

    # Get all users with weekly preference
    users_with_weekly = NotificationPreferences.objects.filter(
        email_digest_frequency='weekly'
    ).select_related('user')

    for pref in users_with_weekly:
        user = pref.user

        # Get un-emailed notifications for this user
        notifications = Notification.objects.filter(
            user=user,
            emailed_at__isnull=True
        ).order_by('-created_at')

        if not notifications.exists():
            continue

        # Send digest email
        success = send_notification_email(user, list(notifications))  # type: ignore[arg-type]

        if success:
            # Mark all as emailed
            notification_ids = [n.id for n in notifications]  # type: ignore[attr-defined]
            Notification.objects.filter(id__in=notification_ids).update(
                emailed_at=timezone.now()
            )
            sent_count += 1
            print(f"Sent weekly digest to {user.username} with {len(notification_ids)} notifications")

    print(f"Weekly digest: sent to {sent_count} users")
    return sent_count
