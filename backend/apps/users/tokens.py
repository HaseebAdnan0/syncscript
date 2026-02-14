"""
Email verification token generation and validation.
"""
import secrets
from datetime import timedelta
from django.utils import timezone
from .models import EmailVerificationToken


def generate_verification_token(user):
    """
    Generate a secure email verification token for a user.

    Creates a 32-byte URL-safe token that expires in 24 hours.

    Args:
        user: User instance to create verification token for

    Returns:
        str: The generated token string
    """
    # Generate secure random token
    token = secrets.token_urlsafe(32)

    # Set expiration to 24 hours from now
    expires_at = timezone.now() + timedelta(hours=24)

    # Create token record in database
    EmailVerificationToken.objects.create(
        user=user,
        token=token,
        expires_at=expires_at
    )

    return token


def verify_token(token):
    """
    Validate an email verification token and return the associated user.

    Args:
        token: The token string to validate

    Returns:
        User instance if token is valid, None otherwise

    Side effects:
        - Deletes the token after successful verification
        - Expired or invalid tokens return None
    """
    try:
        # Fetch token from database
        verification_token = EmailVerificationToken.objects.get(token=token)

        # Check if token has expired
        if timezone.now() > verification_token.expires_at:
            # Delete expired token
            verification_token.delete()
            return None

        # Get user before deleting token
        user = verification_token.user

        # Delete token after successful verification
        verification_token.delete()

        return user

    except EmailVerificationToken.DoesNotExist:
        return None
