"""
WebSocket URL routing for vault rooms.

This module defines the WebSocket URL patterns for real-time collaboration
within knowledge vaults. Clients connect to vault-specific rooms to receive
live updates for sources, annotations, and member changes.
"""

from django.urls import re_path
from apps.vaults.consumers import VaultConsumer

# WebSocket URL patterns
websocket_urlpatterns = [
    re_path(r"ws/vault/(?P<vault_id>\d+)/$", VaultConsumer.as_asgi()),
]
