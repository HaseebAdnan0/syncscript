# PRD: Real-Time WebSocket Collaboration Infrastructure

## 1. Overview

### 1.1 Purpose
Implement real-time collaboration infrastructure for SyncScript using Django Channels and WebSockets. Enable live updates when researchers add sources, create annotations, or modify vault content—ensuring all collaborators see changes instantly without page refreshes.

### 1.2 Success Metrics
- **Latency**: < 200ms from server event to client UI update (p95)
- **Reliability**: 99.5% message delivery success rate
- **Concurrency**: Support 50+ simultaneous connections per vault
- **Reconnection**: Automatic recovery with event replay within 5 seconds
- **Developer Experience**: Clear event contracts, easy to add new event types

### 1.3 Timeline
- **Phase 1 (Week 1)**: Core infrastructure (Channels, Redis, ASGI, auth)
- **Phase 2 (Week 2)**: Event broadcasting (signals, consumers, room management)
- **Phase 3 (Week 3)**: Presence tracking, sequence numbers, error handling
- **Phase 4 (Week 4)**: Testing, documentation, scaling guide

---

## 2. Technical Architecture

### 2.1 Tech Stack
- **Django Channels 4.3+**: WebSocket protocol handling
- **Daphne**: ASGI server for async request handling
- **channels-redis 4.2+**: Redis-backed channel layer
- **Redis 7.0+**: In-memory message broker and presence store
- **Celery 5.6+**: Async task queue for signal handlers

### 2.2 File Structure
```
backend/
├── config/
│   ├── asgi.py                    # ASGI application entry point
│   ├── settings.py                # Channel layer config
│   └── urls.py                    # HTTP routing (unchanged)
├── apps/vaults/
│   ├── consumers.py               # VaultConsumer WebSocket handler
│   ├── routing.py                 # WebSocket URL routing
│   ├── signals.py                 # Post-save signal handlers
│   ├── tasks.py                   # Celery tasks for broadcasts
│   ├── middleware.py              # JWT WebSocket auth middleware
│   └── tests/
│       ├── test_consumers.py      # Consumer unit tests
│       └── test_websocket_e2e.py  # E2E WebSocket tests
├── apps/sources/
│   └── signals.py                 # Source change signals
├── apps/annotations/
│   └── signals.py                 # Annotation change signals
└── core/
    └── websocket_utils.py         # Shared broadcast helpers
```

### 2.3 System Diagram
```
┌─────────────────┐
│  Django Channels│
│  (Daphne ASGI)  │
└────────┬────────┘
         │
         ├─── WebSocket: /ws/vault/{vault_id}/
         │    ├─── JWT Auth Middleware
         │    └─── VaultConsumer
         │
         ├─── HTTP: /api/v1/...
         │    └─── Django REST Framework
         │
         v
┌─────────────────┐       ┌──────────────┐
│  Redis Channel  │<──────│   Celery     │
│     Layer       │       │  (async sig) │
└────────┬────────┘       └──────────────┘
         │
         └─── Rooms: vault_{id}
              ├─── Presence set: vault_{id}:presence
              └─── Sequence counter: vault_{id}:seq
```

---

## 3. Core Features

### 3.1 WebSocket Connection Flow

#### 3.1.1 Client Connection
**Endpoint**: `ws://localhost:8000/ws/vault/{vault_id}/?token={jwt_access_token}`

**Flow**:
1. Client initiates WebSocket with JWT in query parameter
2. `JWTAuthMiddleware` extracts token, validates signature, sets `scope["user"]`
3. `VaultConsumer.connect()` checks:
   - User is authenticated
   - User has vault membership (any role: owner/contributor/viewer)
4. On success:
   - Add connection to `vault_{vault_id}` room
   - Add user to presence set with timestamp
   - Broadcast `presence.update` to room with current user list
   - Send `connection.success` message with `seq` (current sequence number)
5. On failure:
   - Send `{"error": {"code": "AUTH_FAILED", "message": "Invalid token or insufficient permissions"}}`
   - Close connection with code `1008` (Policy Violation) after 2 seconds

#### 3.1.2 Authentication Middleware
```python
# apps/vaults/middleware.py
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Extract token from query string: ?token=xxx
        # Validate JWT, decode payload
        # Fetch user from DB (async)
        # Set scope["user"] or AnonymousUser
        # Call next middleware
```

**Error Handling**:
- Invalid token → `scope["user"] = AnonymousUser`
- Expired token → Same (consumer will reject in `connect()`)
- Missing token → Same

### 3.2 Room Management

#### 3.2.1 Joining Vault Room
**Trigger**: On `connect()` after auth check passes

**Actions**:
1. `await self.channel_layer.group_add(f"vault_{vault_id}", self.channel_name)`
2. Store presence in Redis:
   ```python
   await redis_client.zadd(
       f"vault_{vault_id}:presence",
       {user_id: timestamp}
   )
   ```
3. Broadcast to room:
   ```json
   {
     "type": "presence.update",
     "payload": {
       "active_users": [
         {"user_id": 1, "username": "alice", "joined_at": "2026-02-14T10:30:00Z", "status": "active"},
         {"user_id": 2, "username": "bob", "joined_at": "2026-02-14T10:32:15Z", "status": "active"}
       ]
     },
     "metadata": {"vault_id": 123, "timestamp": "2026-02-14T10:32:20Z"}
   }
   ```

#### 3.2.2 Leaving Vault Room
**Trigger**: On `disconnect()` or connection timeout

**Actions**:
1. `await self.channel_layer.group_discard(f"vault_{vault_id}", self.channel_name)`
2. Remove from presence:
   ```python
   await redis_client.zrem(f"vault_{vault_id}:presence", user_id)
   ```
3. Broadcast updated presence list to room

#### 3.2.3 Presence Tracking Data Structure
**Redis Sorted Set**: `vault_{vault_id}:presence`
- **Member**: `user_id` (int)
- **Score**: Unix timestamp of join

**Enrichment on Read**:
- Fetch user details from DB (username, avatar)
- Calculate `status`:
  - `active`: Last heartbeat < 60 seconds ago
  - `idle`: Last heartbeat 60-300 seconds ago
  - Remove if > 300 seconds (handled by periodic cleanup task)

**Heartbeat**: Client sends `{"type": "heartbeat"}` every 30 seconds
- Consumer updates timestamp in sorted set
- No broadcast (internal tracking only)

### 3.3 Event Types & Payloads

#### 3.3.1 Message Envelope Structure
All WebSocket messages follow this envelope:

```json
{
  "type": "event",
  "seq": 42,
  "event": "source.created",
  "payload": { /* event-specific data */ },
  "metadata": {
    "vault_id": 123,
    "user": {"id": 1, "username": "alice"},
    "timestamp": "2026-02-14T10:35:00Z"
  }
}
```

**Fields**:
- `type`: Always `"event"` (future: `"error"`, `"ack"`)
- `seq`: Incrementing sequence number per vault (for replay on reconnect)
- `event`: Event name (dot-separated namespace)
- `payload`: Event-specific data
- `metadata`: Context (vault, user, timestamp)

#### 3.3.2 Event Catalog

**source.created**
```json
{
  "event": "source.created",
  "payload": {
    "source": {
      "id": 456,
      "url": "https://example.com/paper.pdf",
      "title": "Machine Learning Survey",
      "created_at": "2026-02-14T10:35:00Z",
      "created_by": {"id": 1, "username": "alice"}
    }
  }
}
```

**source.updated**
```json
{
  "event": "source.updated",
  "payload": {
    "source_id": 456,
    "changes": {
      "title": "ML Survey 2026 (Updated)"
    },
    "updated_by": {"id": 2, "username": "bob"}
  }
}
```

**source.deleted**
```json
{
  "event": "source.deleted",
  "payload": {
    "source_id": 456,
    "deleted_by": {"id": 1, "username": "alice"}
  }
}
```

**annotation.created**
```json
{
  "event": "annotation.created",
  "payload": {
    "annotation": {
      "id": 789,
      "source_id": 456,
      "text": "Key finding on page 5",
      "page_number": 5,
      "created_by": {"id": 3, "username": "charlie"}
    }
  }
}
```

**member.added**
```json
{
  "event": "member.added",
  "payload": {
    "member": {
      "user_id": 4,
      "username": "dana",
      "role": "CONTRIBUTOR"
    },
    "added_by": {"id": 1, "username": "alice"}
  }
}
```

**presence.update**
```json
{
  "event": "presence.update",
  "payload": {
    "active_users": [
      {"user_id": 1, "username": "alice", "joined_at": "...", "status": "active"},
      {"user_id": 2, "username": "bob", "joined_at": "...", "status": "idle"}
    ]
  }
}
```

### 3.4 Signal-Based Broadcasting

#### 3.4.1 Signal Handler Pattern
**Location**: `apps/sources/signals.py`, `apps/annotations/signals.py`, `apps/vaults/signals.py`

**Flow**:
1. Django model saved (e.g., `Source.objects.create(...)`)
2. `post_save` signal fires
3. Signal handler enqueues Celery task (async, non-blocking)
4. Celery worker:
   - Serializes model instance
   - Gets vault_id
   - Increments sequence number in Redis
   - Broadcasts to channel layer

**Example**:
```python
# apps/sources/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Source
from .tasks import broadcast_source_created

@receiver(post_save, sender=Source)
def on_source_saved(sender, instance, created, **kwargs):
    if created:
        broadcast_source_created.delay(instance.id)
```

```python
# apps/sources/tasks.py
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@shared_task
def broadcast_source_created(source_id):
    source = Source.objects.select_related('vault', 'created_by').get(id=source_id)
    vault_id = source.vault_id
    
    # Increment sequence
    seq = redis_client.incr(f"vault_{vault_id}:seq")
    
    # Build message
    message = {
        "type": "vault.event",  # Consumer method name
        "seq": seq,
        "event": "source.created",
        "payload": {
            "source": {
                "id": source.id,
                "url": source.url,
                "title": source.title,
                # ... full serialization
            }
        },
        "metadata": {
            "vault_id": vault_id,
            "user": {"id": source.created_by.id, "username": source.created_by.username},
            "timestamp": source.created_at.isoformat()
        }
    }
    
    # Broadcast to room
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"vault_{vault_id}",
        message
    )
```

#### 3.4.2 Signal Coverage
- `Source`: `post_save` (created=True → `source.created`, created=False → `source.updated`)
- `Source`: `post_delete` → `source.deleted`
- `Annotation`: `post_save` (created=True → `annotation.created`)
- `VaultMembership`: `post_save` (created=True → `member.added`)

### 3.5 Sequence Numbers & Event Replay

#### 3.5.1 Sequence Number Management
**Redis Key**: `vault_{vault_id}:seq` (integer counter)

**Increment**: On every broadcast (in Celery task before `group_send`)

**Client Usage**:
1. On initial connect, receive `{"seq": 42}` in `connection.success` message
2. Store `lastSeq = 42` in client state
3. On disconnect, persist `lastSeq` to localStorage
4. On reconnect:
   - Send `{"type": "replay_request", "since_seq": 42}`
   - Server responds with buffered events (if available)

#### 3.5.2 Event Buffering (Optional, Phase 2+)
**Redis List**: `vault_{vault_id}:events` (capped at last 100 events)

**Structure**:
```python
await redis_client.lpush(
    f"vault_{vault_id}:events",
    json.dumps(message)
)
await redis_client.ltrim(f"vault_{vault_id}:events", 0, 99)  # Keep last 100
await redis_client.expire(f"vault_{vault_id}:events", 3600)  # 1 hour TTL
```

**Replay Handler** (in `VaultConsumer`):
```python
async def replay_request(self, data):
    since_seq = data.get("since_seq", 0)
    events = await redis_client.lrange(f"vault_{self.vault_id}:events", 0, -1)
    
    # Filter events with seq > since_seq
    missed = [e for e in events if json.loads(e)["seq"] > since_seq]
    
    for event in reversed(missed):  # Chronological order
        await self.send(text_data=event)
```

---

## 4. Configuration & Setup

### 4.1 ASGI Configuration
**File**: `config/asgi.py`

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from apps.vaults.middleware import JWTAuthMiddleware
from apps.vaults.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

### 4.2 Channel Layer Settings
**File**: `config/settings.py`

**Development (Single Redis)**:
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL", "redis://localhost:6379/0")],
            "capacity": 1500,  # Max messages per channel
            "expiry": 10,      # Message expiry (seconds)
        },
    },
}
```

**Production Scaling Notes** (document in README):
- **Redis Sentinel**: High availability with automatic failover
- **Separate Redis instances**: Cache (DB 0) vs Channels (DB 1)
- **Redis Cluster**: Sharding for > 10k connections
- **Connection pooling**: `channels_redis` handles this automatically

### 4.3 WebSocket Routing
**File**: `apps/vaults/routing.py`

```python
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/vault/<int:vault_id>/", consumers.VaultConsumer.as_asgi()),
]
```

### 4.4 Dependencies
**Add to `requirements.txt`**:
```
channels[daphne]>=4.3.1
channels-redis>=4.2.0
redis>=5.0.1
hiredis>=2.3.2  # C parser for Redis (performance)
```

### 4.5 Environment Variables
**Add to `.env`**:
```bash
# Redis (shared for cache + channels)
REDIS_URL=redis://localhost:6379/0

# Celery (for async signal handlers)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

---

## 5. Rate Limiting & Abuse Prevention

### 5.1 Multi-Layer Protection

**Layer 1: Connection Limit (Global per User)**
- **Rule**: Max 5 WebSocket connections per user across all vaults
- **Implementation**: Redis set `user_{user_id}:connections` tracking `channel_name`
- **Action on violation**: Close oldest connection with code `1008`

**Layer 2: Room Limit (Per Vault)**
- **Rule**: Max 100 connections per vault room
- **Implementation**: Count members in `vault_{vault_id}` group
- **Action on violation**: Reject new connection with error message + close

**Layer 3: Message Throttling (Per Connection)**
- **Rule**: Max 60 messages per minute per connection
- **Implementation**: Redis sorted set `conn_{channel_name}:messages` (score = timestamp)
- **Action on violation**: 
  - First offense: Send warning message
  - Second offense: Disconnect with code `1008`
  - Third offense (within 1 hour): Temporary ban (store in `user_{user_id}:banned` with TTL)

**Layer 4: Heartbeat Enforcement**
- **Rule**: Must send heartbeat every 30-60 seconds
- **Implementation**: Track last heartbeat in presence sorted set
- **Action on violation**: Remove from presence, close connection after 5 minutes silence

### 5.2 Rate Limit Configuration
**File**: `apps/vaults/consumers.py`

```python
class VaultConsumer(AsyncWebsocketConsumer):
    MAX_CONNECTIONS_PER_USER = 5
    MAX_CONNECTIONS_PER_VAULT = 100
    MAX_MESSAGES_PER_MINUTE = 60
    HEARTBEAT_TIMEOUT = 300  # 5 minutes
```

---

## 6. Error Handling

### 6.1 Error Message Format
```json
{
  "type": "error",
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "You do not have access to this vault",
    "details": {"vault_id": 123}
  },
  "metadata": {"timestamp": "2026-02-14T10:40:00Z"}
}
```

### 6.2 Error Codes
| Code | Meaning | Action |
|------|---------|--------|
| `AUTH_FAILED` | Invalid/expired JWT | Send error → close (1008) after 2s |
| `PERMISSION_DENIED` | User not vault member | Send error → close (1008) after 2s |
| `RATE_LIMIT_EXCEEDED` | Too many messages | Send error → close (1008) on repeat |
| `VAULT_NOT_FOUND` | Invalid vault_id | Send error → close (1011) after 2s |
| `INTERNAL_ERROR` | Server exception | Send error → close (1011) after 2s |

### 6.3 Connection Close Codes
- `1000`: Normal closure (client disconnect)
- `1008`: Policy violation (auth/permission fail)
- `1011`: Internal server error
- `4000` (custom): Rate limit ban

### 6.4 Error Response Flow
1. Consumer detects error condition
2. Send error message to client (JSON)
3. Wait 2 seconds (client can display error)
4. Close connection with appropriate code
5. Log error to Django logger (`channels.vault.consumer`)

---

## 7. Testing Strategy

### 7.1 End-to-End WebSocket Tests
**File**: `apps/vaults/tests/test_websocket_e2e.py`

**Test Cases**:
1. **Connection Success**: Valid JWT + vault membership → connected
2. **Connection Rejected**: Invalid JWT → error + close (1008)
3. **Connection Rejected**: No vault membership → error + close (1008)
4. **Room Broadcast**: User A creates source → User B receives `source.created` event
5. **Presence Tracking**: User joins → all users receive `presence.update`
6. **Presence Tracking**: User leaves → all users receive updated presence
7. **Sequence Replay**: Disconnect during events → reconnect and replay missed events
8. **Rate Limiting**: Send 61 messages in 60s → receive warning, then disconnect
9. **Heartbeat Timeout**: No heartbeat for 5 min → connection closed
10. **Concurrent Users**: 10 users in same vault → all receive broadcasts

**Test Utilities**:
```python
from channels.testing import WebsocketCommunicator
from config.asgi import application

class WebSocketTestCase(TestCase):
    async def test_connection_success(self):
        user = User.objects.create_user(username="alice")
        vault = Vault.objects.create(name="Test", owner=user)
        VaultMembership.objects.create(vault=vault, user=user, role="OWNER")
        
        token = str(AccessToken.for_user(user))
        communicator = WebsocketCommunicator(
            application,
            f"/ws/vault/{vault.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "connection.success")
        self.assertIn("seq", response)
        
        await communicator.disconnect()
```

### 7.2 Consumer Unit Tests
**File**: `apps/vaults/tests/test_consumers.py`

**Mock Channel Layer**: Use `channels.testing.ChannelLive` to test without Redis

**Test Cases**:
1. `test_connect_sets_vault_id_in_scope`
2. `test_disconnect_removes_from_presence`
3. `test_vault_event_sends_to_websocket`
4. `test_heartbeat_updates_presence_timestamp`
5. `test_replay_request_returns_filtered_events`

### 7.3 Signal Handler Tests
**File**: `apps/sources/tests/test_signals.py`

**Test Cases**:
1. `test_source_created_triggers_celery_task`
2. `test_source_updated_broadcasts_to_vault`
3. `test_source_deleted_broadcasts_to_vault`

**Mock Celery**: Use `@override_settings(CELERY_TASK_ALWAYS_EAGER=True)` for synchronous execution

---

## 8. Deployment & Operations

### 8.1 Running Daphne (ASGI Server)
**Development**:
```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

**Production** (systemd service):
```ini
[Unit]
Description=SyncScript Daphne ASGI
After=network.target redis.service

[Service]
User=www-data
WorkingDirectory=/var/www/syncscript/backend
ExecStart=/var/www/syncscript/venv/bin/daphne -u /run/daphne.sock config.asgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

**Nginx Reverse Proxy**:
```nginx
upstream daphne {
    server unix:/run/daphne.sock;
}

server {
    location /ws/ {
        proxy_pass http://daphne;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 8.2 Redis Configuration
**Development**: Default Redis (localhost:6379)

**Production**:
- **Persistence**: Enable RDB snapshots (backup channel layer state)
- **Maxmemory**: Set to 256MB-1GB depending on vault count
- **Eviction**: `allkeys-lru` (evict old events if memory full)
- **Monitoring**: Track memory usage, connection count

### 8.3 Celery Workers
**Start Worker**:
```bash
celery -A config worker -l info -Q websocket_events -c 4
```

**Queue Isolation**: Separate queue for WebSocket broadcasts (low latency priority)

### 8.4 Monitoring & Alerts
**Metrics to Track**:
- Active WebSocket connections (per vault, globally)
- Message throughput (events/second)
- Redis memory usage
- Celery task queue depth
- P95 latency (signal → client receive)

**Alerts**:
- Redis memory > 80%
- Celery queue depth > 1000
- WebSocket error rate > 1%

---

## 9. Documentation Requirements

### 9.1 Developer Docs
**File**: `docs/websockets.md`

**Sections**:
1. Architecture overview (diagram)
2. Adding new event types (step-by-step)
3. Local development setup (Redis, Daphne, Celery)
4. Testing WebSocket connections (wscat, browser console)
5. Debugging tips (channel layer inspection, Redis CLI)

### 9.2 API Docs
**File**: `docs/api/websockets.md`

**Sections**:
1. Connection endpoint (`/ws/vault/{id}/`)
2. Authentication (JWT query param)
3. Message envelope format
4. Event catalog (all event types with examples)
5. Error codes and close codes
6. Client libraries (JavaScript example with reconnect logic)

### 9.3 Frontend Integration Guide
**File**: `frontend/docs/websocket-client.md`

**Example Client**:
```typescript
// lib/websocket.ts
class VaultWebSocket {
  private ws: WebSocket | null = null;
  private lastSeq: number = 0;

  connect(vaultId: number, token: string) {
    this.ws = new WebSocket(
      `${WS_URL}/ws/vault/${vaultId}/?token=${token}`
    );

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "event") {
        this.lastSeq = msg.seq;
        this.handleEvent(msg.event, msg.payload);
      }
    };

    this.ws.onclose = () => {
      setTimeout(() => this.reconnect(vaultId, token), 5000);
    };
  }

  reconnect(vaultId: number, token: string) {
    this.connect(vaultId, token);
    this.ws?.send(JSON.stringify({
      type: "replay_request",
      since_seq: this.lastSeq
    }));
  }

  handleEvent(event: string, payload: any) {
    switch (event) {
      case "source.created":
        // Update React Query cache
        break;
      case "presence.update":
        // Update presence UI
        break;
    }
  }
}
```

---

## 10. Future Enhancements (Out of Scope)

### 10.1 Phase 2 Features
- **Typing Indicators**: `user.typing` event when user edits annotation
- **Cursor Tracking**: Broadcast cursor position for collaborative editing
- **Operational Transform**: Conflict-free annotation editing (CRDT/OT)
- **Voice Chat Integration**: WebRTC signaling over WebSocket

### 10.2 Scaling Optimizations
- **Event Compression**: gzip payloads for large source objects
- **Binary Protocol**: Use MessagePack instead of JSON
- **Edge Deployment**: Cloudflare Durable Objects for global low-latency
- **Horizontal Scaling**: Redis Cluster sharding by vault_id hash

---

## 11. Acceptance Criteria

### 11.1 Core Functionality
- [ ] Daphne ASGI server runs and accepts WebSocket connections
- [ ] JWT authentication middleware validates tokens and rejects invalid connections
- [ ] Users can join vault rooms (authenticated, vault membership verified)
- [ ] Source create/update/delete signals broadcast to all room members
- [ ] Annotation create signals broadcast to room
- [ ] Vault member add signals broadcast to room
- [ ] Presence tracking: active user list updates on join/leave
- [ ] Heartbeat mechanism prevents stale connections
- [ ] Sequence numbers increment on every event

### 11.2 Error Handling
- [ ] Invalid JWT → error message + close (1008)
- [ ] No vault access → error message + close (1008)
- [ ] Rate limit exceeded → warning + disconnect
- [ ] Internal errors logged and close gracefully (1011)

### 11.3 Performance
- [ ] < 200ms P95 latency from source creation to client UI update (local network)
- [ ] Support 50+ concurrent users in single vault
- [ ] No message loss under normal conditions (99.5% delivery)

### 11.4 Testing
- [ ] E2E WebSocket tests pass (10 test cases)
- [ ] Consumer unit tests pass (5 test cases)
- [ ] Signal handler tests verify Celery task enqueued

### 11.5 Documentation
- [ ] Developer docs explain architecture and how to add events
- [ ] API docs list all event types with examples
- [ ] Frontend integration guide with TypeScript client example
- [ ] Deployment guide covers Daphne + Nginx + Redis setup

---

## 12. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Redis memory overflow | Service outage | Set maxmemory + eviction policy; monitor usage |
| Celery task backlog | Delayed broadcasts | Separate queue for WS events; scale workers |
| WebSocket connection storms | Server overload | Rate limiting (connections per user/vault) |
| Token expiry during long session | Disconnection | Client refreshes token every 10 min, reconnects |
| Event replay inconsistency | Missed updates | Fallback: full state refresh on reconnect |

---

## 13. Dependencies & Prerequisites

### 13.1 Backend Services
- Redis 7.0+ running (localhost:6379 or remote)
- Celery worker running with `websocket_events` queue
- PostgreSQL (for user/vault/source data)

### 13.2 Configuration
- `CHANNEL_LAYERS` settings configured in `settings.py`
- `REDIS_URL` environment variable set
- ASGI application deployed with Daphne (not Django dev server)

### 13.3 External Services
- None (fully self-hosted with Redis)

---

## 14. Success Metrics (Post-Launch)

### 14.1 Week 1 (Alpha)
- 10 test users in 2 vaults
- 100+ WebSocket messages/hour
- 0 crashes or memory leaks
- < 5% error rate

### 14.2 Month 1 (Beta)
- 100 active users
- 50 vaults with real-time collaboration
- 99% uptime
- < 1% error rate
- User feedback: "feels instant" (qualitative)

### 14.3 Production (3 Months)
- 1000+ users
- 500+ vaults
- < 200ms P95 latency
- 99.5% uptime
- Support for 100 concurrent users per vault

---

## Appendix A: Redis Key Schema

| Key Pattern | Type | Purpose | TTL |
|-------------|------|---------|-----|
| `vault_{id}` | Channel Group | Room membership | N/A |
| `vault_{id}:seq` | Integer | Sequence counter | None |
| `vault_{id}:events` | List | Event buffer (last 100) | 1 hour |
| `vault_{id}:presence` | Sorted Set | Active users (score=timestamp) | None |
| `user_{id}:connections` | Set | Active channel names | None |
| `conn_{channel}:messages` | Sorted Set | Message timestamps (rate limit) | 1 min |
| `user_{id}:banned` | String | Temporary ban flag | 1 hour |

---

## Appendix B: WebSocket Close Codes Reference

| Code | Meaning | Use Case |
|------|---------|----------|
| 1000 | Normal Closure | Client intentionally disconnects |
| 1001 | Going Away | Server shutdown |
| 1008 | Policy Violation | Auth failure, permission denied |
| 1011 | Internal Error | Unhandled exception in consumer |
| 4000 | Rate Limit Ban | Custom: too many violations |
| 4001 | Heartbeat Timeout | Custom: no heartbeat for 5 min |