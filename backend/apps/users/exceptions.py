"""
Custom exception handlers for users app.
"""
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
from django_ratelimit.exceptions import Ratelimited


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that handles rate limiting.

    Returns 429 status code with Retry-After header when rate limit is exceeded.
    """
    # Handle Ratelimited exception BEFORE calling DRF's exception handler
    # This is necessary because Ratelimited inherits from PermissionDenied,
    # and DRF's handler would convert it to a 403 response
    if isinstance(exc, Ratelimited):
        # Return 429 Too Many Requests with appropriate error message
        response = Response(
            {
                'error': 'Rate limit exceeded. Please try again later.',
                'detail': 'Too many requests. You have been rate limited.'
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

        # Add Retry-After header (60 seconds as a reasonable default)
        # django-ratelimit doesn't provide exact retry time, so we use a sensible default
        response['Retry-After'] = '60'
        return response

    # Call DRF's default exception handler for all other exceptions
    response = drf_exception_handler(exc, context)

    return response
