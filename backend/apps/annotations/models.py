from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from dirtyfields import DirtyFieldsMixin
from apps.sources.models import Source
from apps.users.models import User


class Annotation(DirtyFieldsMixin, models.Model):
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='annotations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='annotations')
    content = models.TextField()
    page_number = models.IntegerField(null=True, blank=True)
    position = models.JSONField(default=dict)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    search_vector = SearchVectorField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['source', 'parent']),
            models.Index(fields=['user']),
            GinIndex(fields=['search_vector']),
        ]

    def __str__(self) -> str:
        return f"Annotation by {self.user.username} on {self.source.title[:50]}"

    def clean(self) -> None:
        """Validate maximum nesting level of 2 for threaded annotations."""
        super().clean()
        if self.parent is not None and self.parent.parent is not None:
            raise ValidationError("Maximum nesting level (2) exceeded. Cannot reply to a reply.")

    def save(self, *args, **kwargs) -> None:  # type: ignore
        """Override save to call full_clean() before saving."""
        self.full_clean()
        super().save(*args, **kwargs)
