"""
User models for SyncScript.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string
import uuid


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Adds email verification and profile fields for researchers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)

    # Email verification
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)

    # Profile fields
    bio = models.TextField(blank=True, max_length=500)
    institution = models.CharField(max_length=255, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_email_verified']),
            models.Index(fields=['email_verification_token']),
        ]

    def __str__(self):
        return self.email

    def generate_verification_token(self):
        """Generate a unique verification token."""
        self.email_verification_token = get_random_string(64)
        return self.email_verification_token

    def verify_email(self):
        """Mark email as verified and clear the token."""
        self.is_email_verified = True
        self.email_verification_token = None
        self.save(update_fields=['is_email_verified', 'email_verification_token'])
