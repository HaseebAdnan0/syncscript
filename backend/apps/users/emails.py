"""Email helper functions for user authentication."""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


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
        'emails/verify_email.html',
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


def send_password_reset_email(user, uid, token):
    """
    Send password reset email to user.

    Args:
        user: User instance
        uid: Base64-encoded user ID
        token: Password reset token
    """
    # Build password reset URL
    reset_url = f"{settings.SITE_URL}/auth/reset-password?uid={uid}&token={token}"

    # Render HTML email template
    html_message = render_to_string(
        'emails/password_reset.html',
        {
            'user': user,
            'reset_url': reset_url,
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
