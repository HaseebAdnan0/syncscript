"""
User models for SyncScript.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Uses email as primary identifier and includes profile fields for researchers.
    """
    email = models.EmailField(unique=True, db_index=True)
    avatar_url = models.URLField(max_length=500, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    email_verified = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Onboarding fields
    onboarding_completed = models.BooleanField(default=False)
    onboarding_step = models.CharField(max_length=50, blank=True, null=True)
    onboarding_data = models.JSONField(default=dict)
    onboarding_path = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('guided', 'Guided'),
            ('demo', 'Demo'),
            ('skipped', 'Skipped'),
        ]
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email


class EmailVerificationToken(models.Model):
    """
    Email verification tokens for user account activation.
    Tokens expire after 24 hours.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'email_verification_tokens'

    def __str__(self):
        return f"Token for {self.user.email}"
