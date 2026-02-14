"""
JWT authentication middleware for WebSocket connections.

Validates JWT tokens from query parameters and attaches authenticated
user to the connection scope.
"""
from typing import Any, Callable
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken  # type: ignore[import-untyped]
from rest_framework_simplejwt.exceptions import TokenError  # type: ignore[import-untyped]

from apps.users.models import User  # type: ignore[import-not-found]


class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT authentication middleware for WebSocket connections.

    Extracts token from query string (?token=xxx), validates it,
    and sets scope["user"] to authenticated user or AnonymousUser.

    Usage:
        application = JWTAuthMiddleware(URLRouter(...))
    """

    async def __call__(self, scope: dict[str, Any], receive: Callable, send: Callable) -> Callable:  # type: ignore[override]
        """
        Process WebSocket connection and authenticate user via JWT.

        Args:
            scope: ASGI connection scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Extract token from query string
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        token_list = query_params.get("token", [])

        if token_list:
            token_str = token_list[0]
            user = await self._get_user_from_token(token_str)
        else:
            user = AnonymousUser()

        # Attach user to scope
        scope["user"] = user

        # Continue processing
        return await super().__call__(scope, receive, send)  # type: ignore[arg-type]

    async def _get_user_from_token(self, token_str: str) -> User | AnonymousUser:
        """
        Validate JWT token and retrieve user.

        Args:
            token_str: JWT token string

        Returns:
            Authenticated User or AnonymousUser if invalid/expired
        """
        try:
            # Validate token using simplejwt
            access_token = AccessToken(token_str)  # type: ignore[arg-type]
            user_id = access_token.get("user_id")

            if user_id is None:
                return AnonymousUser()

            # Fetch user from database (async)
            user = await self._get_user(user_id)
            return user if user else AnonymousUser()

        except TokenError:
            # Invalid, expired, or malformed token
            return AnonymousUser()
        except Exception:
            # Any other error (database, etc.)
            return AnonymousUser()

    @database_sync_to_async
    def _get_user(self, user_id: int) -> User | None:
        """
        Fetch user from database by ID.

        Args:
            user_id: User primary key

        Returns:
            User instance or None if not found
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
