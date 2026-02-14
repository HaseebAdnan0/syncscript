from django.db import models
from django.conf import settings


class SearchHistory(models.Model):
    """Records user search history for recent searches feature."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='search_history'
    )
    query = models.CharField(max_length=255)
    result_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'search_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name = 'Search History'
        verbose_name_plural = 'Search Histories'

    def __str__(self):
        return f"{self.user.email} searched '{self.query}' ({self.result_count} results)"
