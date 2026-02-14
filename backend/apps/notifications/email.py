"""Email notification service for sending notification digests."""
from typing import List, TYPE_CHECKING
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from apps.notifications.models import Notification
from django.contrib.auth import get_user_model

if TYPE_CHECKING:
    from django.contrib.auth.models import User
else:
    User = get_user_model()


def send_notification_email(user: "User", notifications: List[Notification]) -> bool:
    """
    Send a notification digest email to the user.

    Args:
        user: User to send email to
        notifications: List of Notification objects to include in digest

    Returns:
        True if email was sent successfully, False otherwise
    """
    if not notifications:
        return False

    # Prepare context for templates
    context = {
        'user': user,
        'notifications': notifications,
        'notification_count': len(notifications),
        'site_url': getattr(settings, 'SITE_URL', 'http://localhost:3000'),
    }

    # Generate HTML and plain text versions
    html_content = render_to_string('notifications/email_digest.html', context)
    text_content = render_to_string('notifications/email_digest.txt', context)

    # Determine subject based on count
    if len(notifications) == 1:
        subject = f"SyncScript: {notifications[0].title}"
    else:
        subject = f"SyncScript: You have {len(notifications)} new notifications"

    # Create email message
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],  # type: ignore[attr-defined]
    )
    email.attach_alternative(html_content, "text/html")

    try:
        email.send(fail_silently=False)
        return True
    except Exception as e:
        # Log error but don't raise (fail gracefully)
        print(f"Failed to send notification email to {user.email}: {e}")  # type: ignore[attr-defined]
        return False
