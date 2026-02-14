from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class RequestType(models.TextChoices):
    SUMMARY = 'summary', 'Summary'
    INSIGHTS = 'insights', 'Insights'
    QUESTION = 'question', 'Question'


class AIUsageLog(models.Model):
    """
    Tracks AI token usage per user for cost monitoring and rate limiting.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_usage_logs'
    )
    request_type = models.CharField(
        max_length=20,
        choices=RequestType.choices
    )
    tokens_used = models.IntegerField(help_text='Total tokens (prompt + completion)')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'ai_usage_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['request_type']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.request_type} ({self.tokens_used} tokens) at {self.created_at}"


class ChatRole(models.TextChoices):
    USER = 'user', 'User'
    ASSISTANT = 'assistant', 'Assistant'


class ChatConversation(models.Model):
    """
    Represents a Q&A conversation thread within a vault.
    """
    vault = models.ForeignKey(
        'vaults.Vault',
        on_delete=models.CASCADE,
        related_name='ai_conversations'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_chat_conversations'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['vault', '-updated_at']),
            models.Index(fields=['user', '-updated_at']),
        ]

    def __str__(self):
        return f"Conversation in {self.vault.name} by {self.user.username}"


class ChatMessage(models.Model):
    """
    Individual message in a chat conversation.
    """
    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(
        max_length=20,
        choices=ChatRole.choices
    )
    content = models.TextField()
    sources_cited = models.JSONField(
        default=list,
        help_text='List of source citations: [{source_id, source_title, excerpt}, ...]'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_chat_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
