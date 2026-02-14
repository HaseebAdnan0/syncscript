"""
Celery tasks for sending emails asynchronously.

All email tasks use exponential backoff retry strategy and log
success/failure for monitoring.
"""
import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from apps.users.emails import (
    send_verification_email,
    send_password_reset_email,
)

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,  # Exponential backoff
    retry_backoff_max=600,  # Max 10 minutes between retries
    max_retries=3,
)
def send_verification_email_task(self, user_id: int, token: str):
    """
    Send email verification email asynchronously.

    Args:
        user_id: ID of the user to send verification email to
        token: Verification token string

    Raises:
        ObjectDoesNotExist: If user doesn't exist (logged, not retried)
    """
    try:
        user = User.objects.get(id=user_id)
        send_verification_email(user, token)
        logger.info(f"Verification email sent successfully to {user.email}")
    except ObjectDoesNotExist:
        logger.error(f"User with ID {user_id} not found - cannot send verification email")
        raise
    except Exception as e:
        logger.error(f"Failed to send verification email to user {user_id}: {str(e)}")
        raise


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
)
def send_password_reset_email_task(self, user_id: int, uid: str, token: str, request_ip: str = None, request_time: str = None):
    """
    Send password reset email asynchronously.

    Args:
        user_id: ID of the user requesting password reset
        uid: Base64-encoded user ID
        token: Password reset token
        request_ip: IP address of reset request (optional)
        request_time: Timestamp of reset request (optional)

    Raises:
        ObjectDoesNotExist: If user doesn't exist (logged, not retried)
    """
    try:
        user = User.objects.get(id=user_id)
        send_password_reset_email(user, uid, token, request_ip, request_time)
        logger.info(f"Password reset email sent successfully to {user.email}")
    except ObjectDoesNotExist:
        logger.error(f"User with ID {user_id} not found - cannot send password reset email")
        raise
    except Exception as e:
        logger.error(f"Failed to send password reset email to user {user_id}: {str(e)}")
        raise


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
)
def send_welcome_email_task(self, user_id: int):
    """
    Send welcome email after successful email verification.

    Args:
        user_id: ID of the newly verified user

    Raises:
        ObjectDoesNotExist: If user doesn't exist (logged, not retried)
    """
    try:
        user = User.objects.get(id=user_id)
        # Import here to avoid circular imports when emails.py is updated
        from apps.users.emails import send_welcome_email
        send_welcome_email(user)
        logger.info(f"Welcome email sent successfully to {user.email}")
    except ObjectDoesNotExist:
        logger.error(f"User with ID {user_id} not found - cannot send welcome email")
        raise
    except Exception as e:
        logger.error(f"Failed to send welcome email to user {user_id}: {str(e)}")
        raise


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
)
def send_vault_invite_email_task(self, invite_id: str):
    """
    Send vault invitation email asynchronously.

    Args:
        invite_id: UUID of the VaultMembership instance

    Raises:
        ObjectDoesNotExist: If membership doesn't exist (logged, not retried)
    """
    try:
        from apps.vaults.models import VaultMembership
        invite = VaultMembership.objects.select_related('vault', 'user').get(id=invite_id)

        # Import here to avoid circular imports when emails.py is updated
        from apps.users.emails import send_vault_invite_email
        send_vault_invite_email(invite)
        logger.info(f"Vault invite email sent successfully to {invite.user.email}")
    except ObjectDoesNotExist:
        logger.error(f"VaultMembership with ID {invite_id} not found - cannot send invite email")
        raise
    except Exception as e:
        logger.error(f"Failed to send vault invite email for membership {invite_id}: {str(e)}")
        raise


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
)
def send_collaboration_notification_task(self, notification_data: dict):
    """
    Send collaboration notification email asynchronously.

    Args:
        notification_data: Dictionary containing:
            - user_id: ID of user to notify
            - vault_id: ID of vault where activity occurred
            - actor_username: Username of person who performed action
            - action: Type of action (source_added, annotation_created, member_joined)
            - target: Description of what was affected

    Raises:
        ObjectDoesNotExist: If user doesn't exist (logged, not retried)
    """
    try:
        user = User.objects.get(id=notification_data['user_id'])

        # Import here to avoid circular imports when emails.py is updated
        from apps.users.emails import send_collaboration_notification
        send_collaboration_notification(user, notification_data)
        logger.info(f"Collaboration notification sent successfully to {user.email}")
    except ObjectDoesNotExist:
        logger.error(f"User with ID {notification_data.get('user_id')} not found - cannot send notification")
        raise
    except Exception as e:
        logger.error(f"Failed to send collaboration notification to user {notification_data.get('user_id')}: {str(e)}")
        raise
