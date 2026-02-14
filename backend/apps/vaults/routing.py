"""
WebSocket URL routing for vault rooms.

This module defines the WebSocket URL patterns for real-time collaboration
within knowledge vaults. Clients connect to vault-specific rooms to receive
live updates for sources, annotations, and member changes.
"""

from django.urls import re_path
from apps.vaults.consumers import VaultConsumer

# WebSocket URL patterns
# Note: pyright may flag this as a type error, but it's valid for Channels URLRouter
websocket_urlpatterns = [
    # UUID pattern: 8-4-4-4-12 hexadecimal characters
    re_path(r"ws/vault/(?P<vault_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$", VaultConsumer.as_asgi()),  # type: ignore[arg-type]
]
