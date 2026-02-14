# Permissions for annotations app
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from typing import Any


class IsAuthorOrReadOnly(BasePermission):
    """
    Permission class that allows:
    - Read access (GET, HEAD, OPTIONS) for all authenticated users
    - Write access (POST, PUT, PATCH, DELETE) only for the annotation author
    """

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """
        Check if user has permission to access the annotation object.

        Args:
            request: The incoming request
            view: The view being accessed (unused)
            obj: The annotation object being accessed

        Returns:
            True if permission granted, False otherwise
        """
        # Allow safe methods (GET, HEAD, OPTIONS) for all authenticated users
        if request.method in SAFE_METHODS:
            return True

        # For unsafe methods (POST, PUT, PATCH, DELETE), only allow the author
        return obj.user == request.user
