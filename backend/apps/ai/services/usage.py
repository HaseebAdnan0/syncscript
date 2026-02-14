"""AI usage tracking service for monitoring token consumption and rate limiting."""

from datetime import datetime
from typing import TypedDict
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Sum, Count
from apps.ai.models import AIUsageLog

User = get_user_model()


class DailyUsage(TypedDict):
    """Return type for daily usage statistics."""
    tokens_used: int
    request_count: int


def log_usage(user: User, request_type: str, tokens_used: int) -> AIUsageLog:
    """
    Log an AI API usage event.

    Args:
        user: The user making the request
        request_type: Type of request ('summary', 'insights', 'question')
        tokens_used: Number of tokens consumed

    Returns:
        The created AIUsageLog instance
    """
    return AIUsageLog.objects.create(
        user=user,
        request_type=request_type,
        tokens_used=tokens_used
    )


def get_daily_usage(user: User) -> DailyUsage:
    """
    Get total tokens and request count for the current day (UTC).

    Args:
        user: The user to check usage for

    Returns:
        Dictionary with tokens_used and request_count
    """
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    usage_stats = AIUsageLog.objects.filter(
        user=user,
        created_at__gte=today_start
    ).aggregate(
        total_tokens=Sum('tokens_used'),
        total_requests=Count('id')
    )

    return DailyUsage(
        tokens_used=usage_stats['total_tokens'] or 0,
        request_count=usage_stats['total_requests'] or 0
    )


def get_remaining_requests(user: User) -> int:
    """
    Get the number of AI requests remaining for today.

    Args:
        user: The user to check remaining requests for

    Returns:
        Number of requests remaining (0 if limit exceeded)
    """
    daily_limit = getattr(settings, 'AI_DAILY_LIMIT', 20)
    usage = get_daily_usage(user)
    remaining = daily_limit - usage['request_count']
    return max(0, remaining)
