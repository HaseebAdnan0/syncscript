"""
Custom permissions for email verification enforcement.
"""
from rest_framework import permissions


class IsEmailVerified(permissions.BasePermission):
    """
    Permission class to enforce email verification.
    Unverified users cannot access protected endpoints.
    """
    message = 'Email verification required. Please verify your email before accessing this resource.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_email_verified
        )
