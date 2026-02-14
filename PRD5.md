# PRD: Real-Time WebSocket Collaboration Infrastructure

## Introduction

Implement real-time collaboration infrastructure for SyncScript using Django Channels and WebSockets. Enable live updates when researchers add sources, create annotations, or modify vault content—ensuring all collaborators see changes instantly without page refreshes.

This PRD covers the full implementation: core infrastructure, event broadcasting, presence tracking, sequence numbers with replay, rate limiting, testing, and minimal documentation.

## Goals

- Achieve < 200ms latency from server event to client UI update (p95)
- Support 50+ simultaneous connections per vault
- 99.5% message delivery success rate
- Automatic reconnection with event replay within 5 seconds
- Full 4-layer rate limiting and abuse prevention
- Comprehensive test coverage (E2E + unit + signal tests)

## User Stories

---

### US-001: Add WebSocket dependencies to requirements.txt
**Description:** As a developer, I need the required packages installed so Django Channels and Redis integration work.

**Acceptance Criteria:**
- [x] Add `channels[daphne]>=4.3.1` to requirements.txt
- [x] Add `channels-redis>=4.2.0` to requirements.txt
- [x] Add `redis>=5.0.1` to requirements.txt
- [x] Add `hiredis>=2.3.2` to requirements.txt
- [x] Packages install successfully with `pip install -r requirements.txt`
- [x] Typecheck passes

---

### US-002: Configure CHANNEL_LAYERS in Django settings
**Description:** As a developer, I need the channel layer configured so WebSocket messages route through Redis.

**Acceptance Criteria:**
- [x] Add `CHANNEL_LAYERS` dict to `config/settings.py`
- [x] Backend set to `channels_redis.core.RedisChannelLayer`
- [x] Hosts configured from `REDIS_URL` environment variable
- [x] Capacity set to 1500, expiry set to 10 seconds
- [x] Add `channels` and `daphne` to `INSTALLED_APPS`
- [x] Typecheck passes

---

### US-003: Create ASGI application entry point
**Description:** As a developer, I need the ASGI configuration so Daphne can serve both HTTP and WebSocket protocols.

**Acceptance Criteria:**
- [x] Create/update `config/asgi.py` with `ProtocolTypeRouter`
- [x] HTTP requests route to `get_asgi_application()`
- [x] WebSocket requests route through `AllowedHostsOriginValidator`
- [x] Import placeholder for `JWTAuthMiddleware` and `websocket_urlpatterns`
- [x] Typecheck passes

---

### US-004: Create WebSocket URL routing
**Description:** As a developer, I need WebSocket routes defined so clients can connect to vault rooms.

**Acceptance Criteria:**
- [x] Create `apps/vaults/routing.py`
- [x] Define route: `ws/vault/<int:vault_id>/` -> `VaultConsumer`
- [x] Export `websocket_urlpatterns` list
- [x] Typecheck passes

---

### US-005: Implement JWT authentication middleware for WebSockets
**Description:** As a developer, I need JWT validation on WebSocket connections so only authenticated users can connect.

**Acceptance Criteria:**
- [x] Create `apps/vaults/middleware.py`
- [x] Implement `JWTAuthMiddleware` extending `BaseMiddleware`
- [x] Extract token from query string (`?token=xxx`)
- [x] Validate JWT using `rest_framework_simplejwt.tokens.AccessToken`
- [x] Set `scope["user"]` to authenticated user or `AnonymousUser`
- [x] Handle invalid/expired/missing tokens gracefully
- [x] Typecheck passes

---

### US-006: Create basic VaultConsumer with connect/disconnect
**Description:** As a developer, I need the WebSocket consumer skeleton so clients can establish connections.

**Acceptance Criteria:**
- [x] Create `apps/vaults/consumers.py`
- [x] Implement `VaultConsumer` extending `AsyncWebsocketConsumer`
- [x] `connect()` extracts `vault_id` from URL kwargs
- [x] `connect()` checks user is authenticated (not AnonymousUser)
- [x] `connect()` verifies user has vault membership (any role)
- [x] On success: accept connection
- [x] On failure: send error JSON and close with code 1008
- [x] `disconnect()` handles cleanup
- [x] Typecheck passes

---

### US-007: Implement room join/leave with channel layer
**Description:** As a developer, I need users to join vault rooms so broadcasts reach all collaborators.

**Acceptance Criteria:**
- [x] On successful connect, call `group_add(f"vault_{vault_id}", channel_name)`
- [x] On disconnect, call `group_discard(f"vault_{vault_id}", channel_name)`
- [x] Send `connection.success` message with current sequence number
- [x] Implement `vault_event` method to receive group messages and forward to client
- [x] Typecheck passes

---

### US-008: Implement presence tracking with Redis sorted set
**Description:** As a developer, I need to track active users per vault so clients can display who's online.

**Acceptance Criteria:**
- [x] On connect, add user to Redis sorted set `vault_{id}:presence` with timestamp score
- [x] On disconnect, remove user from sorted set
- [x] Create helper function to fetch presence list with user details
- [x] Enrich presence data with username from database
- [x] Calculate status: `active` (<60s), `idle` (60-300s)
- [x] Typecheck passes

---

### US-009: Broadcast presence updates on join/leave
**Description:** As a user, I want to see when collaborators join or leave so I know who's working on the vault.

**Acceptance Criteria:**
- [x] After joining room, broadcast `presence.update` event to all room members
- [x] After leaving room, broadcast updated `presence.update` to remaining members
- [x] Payload includes `active_users` array with user_id, username, joined_at, status
- [x] Typecheck passes

---

### US-010: Implement heartbeat handling
**Description:** As a developer, I need heartbeat messages to detect stale connections and maintain accurate presence.

**Acceptance Criteria:**
- [x] Handle incoming `{"type": "heartbeat"}` messages from client
- [x] Update user's timestamp in presence sorted set on heartbeat
- [x] No broadcast on heartbeat (internal tracking only)
- [x] Typecheck passes

---

### US-011: Create websocket_utils with broadcast helper
**Description:** As a developer, I need shared utilities for broadcasting so signal handlers can send events consistently.

**Acceptance Criteria:**
- [x] Create `core/websocket_utils.py`
- [x] Implement `broadcast_to_vault(vault_id, event_type, payload, user)` function
- [x] Function increments sequence number in Redis (`vault_{id}:seq`)
- [x] Function builds message envelope with type, seq, event, payload, metadata
- [x] Function sends via `channel_layer.group_send`
- [x] Typecheck passes

---

### US-012: Implement Source signal handlers
**Description:** As a developer, I need Source model changes to trigger broadcasts so collaborators see new sources instantly.

**Acceptance Criteria:**
- [x] Create/update `apps/sources/signals.py`
- [x] Connect `post_save` signal for Source model
- [x] On created=True, enqueue `broadcast_source_created` Celery task
- [x] On created=False, enqueue `broadcast_source_updated` Celery task
- [x] Connect `post_delete` signal, enqueue `broadcast_source_deleted` task
- [x] Register signals in `apps/sources/apps.py` ready()
- [x] Typecheck passes

---

### US-013: Implement Source broadcast Celery tasks
**Description:** As a developer, I need Celery tasks to broadcast Source events asynchronously without blocking HTTP requests.

**Acceptance Criteria:**
- [x] Create `apps/sources/tasks.py`
- [x] Implement `broadcast_source_created(source_id)` task
- [x] Implement `broadcast_source_updated(source_id, changed_fields)` task
- [x] Implement `broadcast_source_deleted(source_id, vault_id, deleted_by_id)` task
- [x] Tasks use `broadcast_to_vault` helper
- [x] Payloads match event catalog (source object with id, url, title, created_by)
- [x] Typecheck passes

---

### US-014: Implement Annotation signal handlers and tasks
**Description:** As a developer, I need Annotation changes to broadcast so collaborators see new annotations instantly.

**Acceptance Criteria:**
- [x] Create/update `apps/annotations/signals.py`
- [x] Connect `post_save` signal for Annotation model (created=True only)
- [x] Enqueue `broadcast_annotation_created` Celery task
- [x] Create `apps/annotations/tasks.py` with broadcast task
- [x] Payload includes annotation id, source_id, text, page_number, created_by
- [x] Register signals in apps.py
- [x] Typecheck passes

---

### US-015: Implement VaultMembership signal handlers and tasks
**Description:** As a developer, I need member additions to broadcast so collaborators see new team members.

**Acceptance Criteria:**
- [x] Update `apps/vaults/signals.py`
- [x] Connect `post_save` signal for VaultMembership model (created=True only)
- [x] Create `apps/vaults/tasks.py` with `broadcast_member_added` task
- [x] Payload includes member user_id, username, role, added_by
- [x] Typecheck passes

---

### US-016: Implement event buffering in Redis
**Description:** As a developer, I need events stored in Redis so clients can replay missed events after reconnection.

**Acceptance Criteria:**
- [x] Update `broadcast_to_vault` to also push event to Redis list `vault_{id}:events`
- [x] Use `lpush` to add event JSON to list
- [x] Use `ltrim` to keep only last 100 events
- [x] Set 1-hour TTL on events list with `expire`
- [x] Typecheck passes

---

### US-017: Implement replay request handler in consumer
**Description:** As a user, I want missed events replayed after reconnection so I don't miss collaborator changes.

**Acceptance Criteria:**
- [x] Handle incoming `{"type": "replay_request", "since_seq": N}` messages
- [x] Fetch events from Redis list `vault_{id}:events`
- [x] Filter events where `seq > since_seq`
- [x] Send filtered events to client in chronological order
- [x] Typecheck passes

---

### US-018: Implement connection limit per user (Layer 1)
**Description:** As a developer, I need to limit connections per user to prevent resource abuse.

**Acceptance Criteria:**
- [x] Track active connections in Redis set `user_{id}:connections`
- [x] On connect, check if user has >= 5 connections
- [x] If limit exceeded, close oldest connection with code 1008
- [x] On disconnect, remove channel from user's connection set
- [x] Typecheck passes

---

### US-019: Implement room limit per vault (Layer 2)
**Description:** As a developer, I need to limit connections per vault to prevent overload.

**Acceptance Criteria:**
- [x] On connect, count members in `vault_{id}` group (via presence set)
- [x] If >= 100 connections, reject with error message and close
- [x] Error code: `ROOM_FULL`
- [x] Typecheck passes

---

### US-020: Implement message throttling (Layer 3)
**Description:** As a developer, I need to throttle client messages to prevent spam.

**Acceptance Criteria:**
- [x] Track message timestamps in Redis sorted set `conn_{channel}:messages`
- [x] On each message, check if > 60 messages in last 60 seconds
- [x] First offense: send warning message
- [x] Second offense: disconnect with code 1008
- [x] Third offense within 1 hour: set temporary ban in `user_{id}:banned`
- [x] Check ban status on connect, reject banned users
- [x] Typecheck passes

---

### US-021: Implement heartbeat timeout enforcement (Layer 4)
**Description:** As a developer, I need to disconnect idle connections to free resources.

**Acceptance Criteria:**
- [x] Create Celery periodic task to check presence timestamps
- [x] Remove users from presence if last heartbeat > 300 seconds ago
- [x] Send disconnect to stale connections
- [x] Run cleanup task every 60 seconds
- [x] Typecheck passes

---

### US-022: Implement error message format and close handling
**Description:** As a developer, I need consistent error responses so clients can handle failures gracefully.

**Acceptance Criteria:**
- [ ] Create `send_error(code, message, details=None)` helper method in consumer
- [ ] Error format: `{"type": "error", "error": {"code": X, "message": Y, "details": Z}, "metadata": {"timestamp": ...}}`
- [ ] Implement error codes: AUTH_FAILED, PERMISSION_DENIED, RATE_LIMIT_EXCEEDED, VAULT_NOT_FOUND, INTERNAL_ERROR
- [ ] Wait 2 seconds after sending error before closing connection
- [ ] Log errors to Django logger `channels.vault.consumer`
- [ ] Typecheck passes

---

### US-023: Create consumer unit tests
**Description:** As a developer, I need unit tests for the VaultConsumer to verify core logic.

**Acceptance Criteria:**
- [ ] Create `apps/vaults/tests/test_consumers.py`
- [ ] Test: `test_connect_sets_vault_id_in_scope`
- [ ] Test: `test_disconnect_removes_from_presence`
- [ ] Test: `test_vault_event_sends_to_websocket`
- [ ] Test: `test_heartbeat_updates_presence_timestamp`
- [ ] Test: `test_replay_request_returns_filtered_events`
- [ ] All tests pass with `python manage.py test apps.vaults.tests.test_consumers`
- [ ] Typecheck passes

---

### US-024: Create E2E WebSocket tests (connection and auth)
**Description:** As a developer, I need E2E tests verifying WebSocket connections work end-to-end.

**Acceptance Criteria:**
- [ ] Create `apps/vaults/tests/test_websocket_e2e.py`
- [ ] Use `channels.testing.WebsocketCommunicator`
- [ ] Test: Connection success with valid JWT + vault membership
- [ ] Test: Connection rejected with invalid JWT (error + close 1008)
- [ ] Test: Connection rejected without vault membership (error + close 1008)
- [ ] All tests pass
- [ ] Typecheck passes

---

### US-025: Create E2E WebSocket tests (broadcasting)
**Description:** As a developer, I need E2E tests verifying events broadcast correctly between users.

**Acceptance Criteria:**
- [ ] Test: User A creates source -> User B receives `source.created` event
- [ ] Test: User joins -> all users receive `presence.update`
- [ ] Test: User leaves -> all users receive updated presence
- [ ] Test: 10 concurrent users in same vault all receive broadcasts
- [ ] Use `@override_settings(CELERY_TASK_ALWAYS_EAGER=True)` for sync execution
- [ ] All tests pass
- [ ] Typecheck passes

---

### US-026: Create E2E WebSocket tests (rate limiting and replay)
**Description:** As a developer, I need E2E tests verifying rate limiting and event replay work.

**Acceptance Criteria:**
- [ ] Test: Send 61 messages in 60s -> receive warning, then disconnect
- [ ] Test: No heartbeat for 5 min -> connection closed
- [ ] Test: Disconnect during events -> reconnect with replay_request gets missed events
- [ ] All tests pass
- [ ] Typecheck passes

---

### US-027: Create signal handler tests
**Description:** As a developer, I need tests verifying signals enqueue correct Celery tasks.

**Acceptance Criteria:**
- [ ] Create `apps/sources/tests/test_signals.py`
- [ ] Test: `test_source_created_triggers_celery_task`
- [ ] Test: `test_source_updated_broadcasts_to_vault`
- [ ] Test: `test_source_deleted_broadcasts_to_vault`
- [ ] Mock Celery tasks to verify they're called with correct arguments
- [ ] All tests pass
- [ ] Typecheck passes

---

### US-028: Update README with WebSocket documentation
**Description:** As a developer, I need minimal documentation so others can run and test the WebSocket system.

**Acceptance Criteria:**
- [ ] Add "Real-Time WebSocket" section to README.md
- [ ] Document connection endpoint: `ws://localhost:8000/ws/vault/{id}/?token={jwt}`
- [ ] List required services: Redis, Celery worker
- [ ] Add command to run Daphne: `daphne -b 0.0.0.0 -p 8000 config.asgi:application`
- [ ] Add command to run Celery: `celery -A config worker -l info -Q websocket_events`
- [ ] Brief list of event types: source.created, source.updated, source.deleted, annotation.created, member.added, presence.update
- [ ] Typecheck passes

---

## Non-Goals

- Typing indicators (`user.typing` event)
- Cursor tracking for collaborative editing
- Operational Transform / CRDT for conflict resolution
- Voice chat / WebRTC signaling
- Event compression (gzip/MessagePack)
- Horizontal scaling with Redis Cluster (document for future)
- Full API documentation (separate PRD)
- Frontend WebSocket client implementation (separate PRD)

## Technical Considerations

- **Existing models to use:** User, Vault, VaultMembership, Source, Annotation
- **Existing auth:** `rest_framework_simplejwt` already configured
- **Redis:** Already in stack for caching, reuse for channel layer
- **Celery:** Already configured, add new queue `websocket_events`
- **Test utilities:** Use `channels.testing.WebsocketCommunicator`
- **Async/sync bridge:** Use `asgiref.sync.async_to_sync` in Celery tasks
