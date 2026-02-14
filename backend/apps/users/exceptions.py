"""
Custom exception handlers for users app.
"""
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
from django_ratelimit.exceptions import Ratelimited


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that handles rate limiting and email verification.

    Returns 429 status code with Retry-After header when rate limit is exceeded.
    Returns 403 with email_verification_required flag for unverified users.
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

    # Check if exception has email_verification_required attribute
    if response is not None and hasattr(exc, 'email_verification_required'):
        # Add email_verification_required to response data
        response.data['email_verification_required'] = exc.email_verification_required  # type: ignore

    return response
