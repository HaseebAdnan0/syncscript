"""
AI rate limiting decorators for API endpoints.
"""
from functools import wraps
from datetime import timedelta
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status

from apps.ai.services.usage import get_remaining_requests


def ai_rate_limit(view_func):
    """
    Decorator to enforce AI request rate limits on API endpoints.

    Checks remaining requests before allowing the view to execute.
    Returns 429 Too Many Requests if limit is exceeded.

    Response on rate limit:
    {
        "error": "AI request limit reached",
        "resets_at": "<ISO timestamp>",
        "cached_available": true
    }
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Get remaining requests for the authenticated user
        remaining = get_remaining_requests(request.user)

        if remaining <= 0:
            # Calculate reset time (midnight UTC tomorrow)
            now = timezone.now()
            tomorrow = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            return Response(
                {
                    "error": "AI request limit reached",
                    "resets_at": tomorrow.isoformat(),
                    "cached_available": True
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Allow request to proceed
        return view_func(request, *args, **kwargs)

    return wrapper
