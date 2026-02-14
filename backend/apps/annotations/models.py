from django.db import models
from apps.sources.models import Source
from apps.users.models import User


class Annotation(models.Model):
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='annotations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='annotations')
    content = models.TextField()
    page_number = models.IntegerField(null=True, blank=True)
    position = models.JSONField(default=dict)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['source', 'parent']),
            models.Index(fields=['user']),
        ]

    def __str__(self) -> str:
        return f"Annotation by {self.user.username} on {self.source.title[:50]}"
