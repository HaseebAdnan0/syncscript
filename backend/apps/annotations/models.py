from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Annotation(models.Model):
    """
    User annotations/notes on PDF sources.
    Links to Source and tracks text, page number, and creator.
    """
    source = models.ForeignKey(
        'sources.Source',
        on_delete=models.CASCADE,
        related_name='annotations'
    )
    text = models.TextField()
    page_number = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='annotations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['source', 'created_at']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"Annotation by {self.created_by} on {self.source}"
