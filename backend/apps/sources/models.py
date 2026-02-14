from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SourceType(models.TextChoices):
    URL = 'URL', 'URL'
    PDF = 'PDF', 'PDF'
    BOOK = 'BOOK', 'Book'
    JOURNAL = 'JOURNAL', 'Journal'
    DATASET = 'DATASET', 'Dataset'


class Source(models.Model):
    vault = models.ForeignKey(
        'vaults.Vault',
        on_delete=models.CASCADE,
        related_name='sources'
    )
    url = models.URLField(max_length=2048)
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True)
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.URL
    )
    metadata = models.JSONField(default=dict)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_sources'
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vault', 'is_deleted']),
            models.Index(fields=['source_type']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['vault', 'url'],
                condition=models.Q(is_deleted=False),
                name='unique_active_source_per_vault'
            )
        ]

    def __str__(self):
        return f"{self.title} ({self.source_type})"
