from django.db import models
from django.conf import settings
import hashlib


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


class SearchAnalytics(models.Model):
    """Tracks anonymized search query popularity for analytics."""

    query_hash = models.CharField(max_length=64, db_index=True)  # SHA-256 produces 64 hex chars
    query_normalized = models.CharField(max_length=255)
    search_count = models.IntegerField(default=1)
    last_searched = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'search_analytics'
        ordering = ['-search_count', '-last_searched']
        constraints = [
            models.UniqueConstraint(fields=['query_hash'], name='unique_query_hash')
        ]
        verbose_name = 'Search Analytics'
        verbose_name_plural = 'Search Analytics'

    def __str__(self):
        return f"'{self.query_normalized}' ({self.search_count} searches)"

    @staticmethod
    def hash_query(query: str) -> str:
        """Generate SHA-256 hash of normalized query for privacy."""
        normalized = query.strip().lower()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
