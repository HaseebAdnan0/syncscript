"""
User models for SyncScript.
"""
import secrets
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


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


class EmailPreference(models.Model):
    """
    User email notification preferences and unsubscribe tokens.
    Each user has one preference record created automatically on registration.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_preference')
    collaboration_notifications = models.BooleanField(default=True, help_text="Receive notifications about vault activity")
    marketing_emails = models.BooleanField(default=True, help_text="Receive product updates and newsletters")
    unsubscribe_token = models.CharField(max_length=64, unique=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'email_preferences'

    def __str__(self):
        return f"Email preferences for {self.user.email}"

    def save(self, *args, **kwargs):
        """Generate unique unsubscribe token if not set."""
        if not self.unsubscribe_token:
            self.unsubscribe_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_email_preference(sender, instance, created, **kwargs):
    """Create EmailPreference record when a new User is created."""
    if created:
        EmailPreference.objects.create(user=instance)
