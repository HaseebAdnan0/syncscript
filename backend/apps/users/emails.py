"""Email helper functions for user authentication."""
import secrets
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def get_unsubscribe_token(user):
    """
    Get or create unsubscribe token for user's EmailPreference.

    Args:
        user: User instance

    Returns:
        Unsubscribe token string
    """
    # Import here to avoid circular dependency
    from apps.users.models import EmailPreference

    # Get or create EmailPreference (should be created by signal, but ensure it exists)
    email_pref, created = EmailPreference.objects.get_or_create(
        user=user,
        defaults={'unsubscribe_token': secrets.token_urlsafe(32)}
    )

    # Generate token if missing (for old records)
    if not email_pref.unsubscribe_token:
        email_pref.unsubscribe_token = secrets.token_urlsafe(32)
        email_pref.save(update_fields=['unsubscribe_token'])

    return email_pref.unsubscribe_token


def send_verification_email(user, token):
    """
    Send email verification email to user.

    Args:
        user: User instance
        token: Verification token string
    """
    # Build verification URL
    verification_url = f"{settings.SITE_URL}/auth/verify-email?token={token}"

    # Render HTML email template
    html_message = render_to_string(
        'emails/verification.html',
        {
            'user': user,
            'verification_url': verification_url,
        }
    )

    # Generate plain text fallback by stripping HTML tags
    plain_message = strip_tags(html_message)

    # Send email
    send_mail(
        subject='Verify Your Email - SyncScript',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_reset_email(user, uid, token, request_ip=None, request_time=None):
    """
    Send password reset email to user.

    Args:
        user: User instance
        uid: Base64-encoded user ID
        token: Password reset token
        request_ip: IP address of reset request (optional)
        request_time: Timestamp of reset request (optional)
    """
    # Build password reset URL
    reset_url = f"{settings.SITE_URL}/auth/reset-password?uid={uid}&token={token}"

    # Render HTML email template
    html_message = render_to_string(
        'emails/password_reset.html',
        {
            'user': user,
            'reset_url': reset_url,
            'request_ip': request_ip,
            'request_time': request_time,
        }
    )

    # Generate plain text fallback by stripping HTML tags
    plain_message = strip_tags(html_message)

    # Send email
    send_mail(
        subject='Reset Your Password - SyncScript',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_welcome_email(user):
    """
    Send welcome email to user after email verification.

    Args:
        user: User instance
    """
    # Build dashboard URL
    dashboard_url = f"{settings.SITE_URL}/dashboard"

    # Render HTML email template
    html_message = render_to_string(
        'emails/welcome.html',
        {
            'user': user,
            'dashboard_url': dashboard_url,
        }
    )

    # Generate plain text fallback
    plain_message = strip_tags(html_message)

    # Send email
    send_mail(
        subject='Welcome to SyncScript!',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_vault_invite_email(invite):
    """
    Send vault invitation email to invited user.

    Args:
        invite: VaultMembership instance with PENDING status
    """
    # Build invitation acceptance URL
    invite_url = f"{settings.SITE_URL}/vaults/{invite.vault.id}/accept-invite?token={invite.id}"

    # Render HTML email template
    html_message = render_to_string(
        'emails/vault_invite.html',
        {
            'invite': invite,
            'inviter': invite.invited_by,
            'vault': invite.vault,
            'role': invite.get_role_display(),
            'invite_url': invite_url,
        }
    )

    # Generate plain text fallback
    plain_message = strip_tags(html_message)

    # Send email
    send_mail(
        subject=f'You\'re invited to collaborate on {invite.vault.name}',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invite.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_collaboration_notification(user, notification_data):
    """
    Send collaboration notification email about vault activity.

    Args:
        user: User instance receiving the notification
        notification_data: Dict with keys:
            - notification_type: str (source_added, annotation_created, member_joined)
            - actor: User instance who performed the action
            - vault: Vault instance
            - target: Optional related object (source, annotation, etc.)
            - action_url: URL to view the activity
    """
    # Import here to avoid circular dependency
    from apps.users.models import EmailPreference

    # Check if user has notifications enabled
    try:
        email_pref = EmailPreference.objects.get(user=user)
        if not email_pref.collaboration_notifications:
            return  # User has unsubscribed from notifications
    except EmailPreference.DoesNotExist:
        pass  # No preference record, send notification (default behavior)

    # Get unsubscribe token
    unsubscribe_token = get_unsubscribe_token(user)
    unsubscribe_url = f"{settings.SITE_URL}/api/v1/auth/unsubscribe/{unsubscribe_token}/"

    # Render HTML email template
    html_message = render_to_string(
        'emails/collaboration_notification.html',
        {
            'user': user,
            'notification_data': notification_data,
            'unsubscribe_url': unsubscribe_url,
        }
    )

    # Generate plain text fallback
    plain_message = strip_tags(html_message)

    # Build subject based on notification type
    vault_name = notification_data.get('vault').name
    subject = f'New activity in {vault_name} - SyncScript'

    # Send email
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
