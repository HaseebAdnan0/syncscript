# WebSocket Real-Time Collaboration - Task Breakdown

**PRD**: Real-Time WebSocket Collaboration Infrastructure
**Created**: 2026-02-14
**Status**: Ready for Development

---

## Phase 1: Core Infrastructure (Week 1)

### Task 1.1: Install Dependencies & Configuration
- [ ] Add to `requirements.txt`: `channels[daphne]>=4.3.1`, `channels-redis>=4.2.0`, `redis>=5.0.1`, `hiredis>=2.3.2`
- [ ] Install packages: `pip install -r requirements.txt`
- [ ] Add environment variables to `.env`: `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- [ ] Configure `CHANNEL_LAYERS` in `config/settings.py` with Redis backend
- [ ] Verify Redis is running on localhost:6379

**Acceptance**: `python -m pip list | grep channels` shows installed packages

---

### Task 1.2: ASGI Application Setup
- [ ] Create/update `config/asgi.py` with `ProtocolTypeRouter` for HTTP + WebSocket
- [ ] Add `AllowedHostsOriginValidator` wrapper for CORS security
- [ ] Import routing from `apps/vaults/routing` (placeholder for now)
- [ ] Test ASGI app loads: `python -c "from config.asgi import application; print(application)"`

**File**: `config/asgi.py`

**Acceptance**: No import errors, application object created

---

### Task 1.3: JWT Authentication Middleware
- [ ] Create `apps/vaults/middleware.py`
- [ ] Implement `JWTAuthMiddleware(BaseMiddleware)`:
  - Extract token from query string `?token=xxx`
  - Validate JWT using `rest_framework_simplejwt.tokens.AccessToken`
  - Decode user ID, fetch user from DB (async: `database_sync_to_async`)
  - Set `scope["user"]` or `AnonymousUser`
- [ ] Handle errors gracefully (expired/invalid token → AnonymousUser, no exception)

**File**: `apps/vaults/middleware.py`

**Acceptance**: Middleware can decode valid JWT and set user in scope

---

### Task 1.4: WebSocket URL Routing
- [ ] Create `apps/vaults/routing.py`
- [ ] Define `websocket_urlpatterns` with path `ws/vault/<int:vault_id>/`
- [ ] Point to `consumers.VaultConsumer.as_asgi()` (create placeholder consumer)
- [ ] Import in `config/asgi.py` and wire into `URLRouter`

**Files**: `apps/vaults/routing.py`, `apps/vaults/consumers.py` (skeleton)

**Acceptance**: Routing configuration loads without errors

---

### Task 1.5: VaultConsumer Skeleton
- [ ] Create `apps/vaults/consumers.py`
- [ ] Implement `VaultConsumer(AsyncWebsocketConsumer)`:
  - `connect()`: Extract vault_id from URL kwargs, set `self.vault_id`
  - `connect()`: Check user is authenticated (`self.scope["user"].is_authenticated`)
  - `connect()`: Check user has vault membership (query `VaultMembership`)
  - On success: `await self.accept()`
  - On failure: `await self.send(...)` error JSON, then `await self.close(code=1008)`
  - `disconnect()`: Placeholder (just log for now)
  - `receive()`: Placeholder (just log incoming messages)

**File**: `apps/vaults/consumers.py`

**Acceptance**: Consumer accepts authenticated users with vault access, rejects others

---

### Task 1.6: Run Daphne Server
- [ ] Test running ASGI server: `daphne -b 0.0.0.0 -p 8000 config.asgi:application`
- [ ] Verify server starts without errors
- [ ] Test WebSocket connection with `wscat` or browser console:
  ```bash
  wscat -c "ws://localhost:8000/ws/vault/1/?token=<valid_jwt>"
  ```
- [ ] Verify connection accepted/rejected based on auth

**Acceptance**: Daphne runs, WebSocket connections work with JWT auth

---

## Phase 2: Room Management & Broadcasting (Week 2)

### Task 2.1: Room Join/Leave Logic
- [ ] In `VaultConsumer.connect()` after auth check:
  - `await self.channel_layer.group_add(f"vault_{self.vault_id}", self.channel_name)`
  - Send success message: `{"type": "connection.success", "seq": <current_seq>}`
- [ ] In `VaultConsumer.disconnect()`:
  - `await self.channel_layer.group_discard(f"vault_{self.vault_id}", self.channel_name)`
  - Log disconnect event

**File**: `apps/vaults/consumers.py`

**Acceptance**: Multiple clients can join same vault room, receive success message

---

### Task 2.2: Presence Tracking - Join
- [ ] Create utility function in `core/websocket_utils.py`: `add_user_to_presence(vault_id, user_id)`
  - Use `redis.zadd(f"vault_{vault_id}:presence", {user_id: timestamp})`
- [ ] Call in `VaultConsumer.connect()` after `group_add`
- [ ] Fetch active users: `get_active_users(vault_id)` → query sorted set, enrich with usernames
- [ ] Broadcast `presence.update` event to room with full user list

**Files**: `core/websocket_utils.py`, `apps/vaults/consumers.py`

**Acceptance**: When user joins, all clients in room receive `presence.update` event

---

### Task 2.3: Presence Tracking - Leave
- [ ] Create utility: `remove_user_from_presence(vault_id, user_id)`
  - Use `redis.zrem(f"vault_{vault_id}:presence", user_id)`
- [ ] Call in `VaultConsumer.disconnect()`
- [ ] Broadcast updated `presence.update` to room

**Files**: `core/websocket_utils.py`, `apps/vaults/consumers.py`

**Acceptance**: When user leaves, all remaining clients receive updated presence list

---

### Task 2.4: Heartbeat Mechanism
- [ ] In `VaultConsumer.receive()`, handle `{"type": "heartbeat"}` messages
- [ ] Update timestamp in presence sorted set: `redis.zadd(f"vault_{vault_id}:presence", {user_id: time.time()})`
- [ ] No broadcast (internal tracking only)
- [ ] Document: Clients should send heartbeat every 30 seconds

**File**: `apps/vaults/consumers.py`

**Acceptance**: Heartbeat messages update presence timestamp in Redis

---

### Task 2.5: Presence Cleanup Task (Celery)
- [ ] Create `apps/vaults/tasks.py`: `cleanup_stale_presence()`
- [ ] Use `redis.zremrangebyscore(f"vault_{vault_id}:presence", 0, time.time() - 300)` to remove users inactive > 5min
- [ ] Schedule as Celery beat task (every 1 minute)
- [ ] Broadcast `presence.update` if any users removed

**File**: `apps/vaults/tasks.py`

**Acceptance**: Stale presence entries removed automatically

---

### Task 2.6: Sequence Number Management
- [ ] Create utility: `get_next_seq(vault_id)` → `redis.incr(f"vault_{vault_id}:seq")`
- [ ] Create utility: `get_current_seq(vault_id)` → `redis.get(f"vault_{vault_id}:seq") or 0`
- [ ] In `VaultConsumer.connect()`, send current seq in `connection.success` message
- [ ] Document: Clients should store `lastSeq` for replay on reconnect

**File**: `core/websocket_utils.py`

**Acceptance**: Each vault has incrementing sequence number

---

### Task 2.7: Event Broadcasting Helper
- [ ] Create `broadcast_to_vault(vault_id, event_name, payload, user)` in `core/websocket_utils.py`:
  - Get next sequence number
  - Build message envelope: `{"type": "event", "seq": X, "event": event_name, "payload": {...}, "metadata": {...}}`
  - Use `channel_layer.group_send(f"vault_{vault_id}", message)`
- [ ] Add consumer method `async def vault_event(self, event)` to handle received messages
  - Send JSON to WebSocket: `await self.send(text_data=json.dumps(event))`

**Files**: `core/websocket_utils.py`, `apps/vaults/consumers.py`

**Acceptance**: Helper function broadcasts events to all room members

---

## Phase 3: Signal Handlers & Events (Week 2-3)

### Task 3.1: Celery Task for source.created
- [ ] Create `apps/sources/tasks.py`: `broadcast_source_created(source_id)`
- [ ] Fetch source with `select_related('vault', 'created_by')`
- [ ] Serialize source data (id, url, title, created_at, created_by)
- [ ] Call `broadcast_to_vault(vault_id, "source.created", payload, user)`

**File**: `apps/sources/tasks.py`

**Acceptance**: Task can broadcast source.created event to vault room

---

### Task 3.2: Signal Handler for Source Created
- [ ] Create `apps/sources/signals.py`
- [ ] Add `post_save` signal receiver for `Source` model:
  - If `created=True`, enqueue `broadcast_source_created.delay(instance.id)`
- [ ] Import signal in `apps/sources/apps.py` ready method

**File**: `apps/sources/signals.py`

**Acceptance**: Creating a source triggers Celery task (verify with logs)

---

### Task 3.3: Celery Task for source.updated
- [ ] Create `broadcast_source_updated(source_id, changes)` in `apps/sources/tasks.py`
- [ ] Build payload with source_id, changes dict, updated_by user
- [ ] Call `broadcast_to_vault(vault_id, "source.updated", payload, user)`

**File**: `apps/sources/tasks.py`

**Acceptance**: Task broadcasts source.updated event

---

### Task 3.4: Signal Handler for Source Updated
- [ ] In `apps/sources/signals.py`, update `post_save` receiver:
  - If `created=False`, detect changed fields (use `django-dirtyfields` or manual tracking)
  - Enqueue `broadcast_source_updated.delay(instance.id, changes)`

**File**: `apps/sources/signals.py`

**Acceptance**: Updating a source triggers broadcast with changed fields

---

### Task 3.5: Signal Handler for Source Deleted
- [ ] Add `post_delete` signal receiver for `Source` in `apps/sources/signals.py`
- [ ] Create `broadcast_source_deleted(source_id, vault_id, deleted_by_id)` task
- [ ] Broadcast `source.deleted` event with source_id and deleted_by user

**Files**: `apps/sources/signals.py`, `apps/sources/tasks.py`

**Acceptance**: Deleting a source broadcasts event to vault room

---

### Task 3.6: Signal Handler for annotation.created
- [ ] Create `apps/annotations/signals.py` with `post_save` receiver for `Annotation`
- [ ] Create `apps/annotations/tasks.py`: `broadcast_annotation_created(annotation_id)`
- [ ] Serialize annotation (id, source_id, text, page_number, created_by)
- [ ] Get vault_id from annotation.source.vault_id
- [ ] Broadcast `annotation.created` event

**Files**: `apps/annotations/signals.py`, `apps/annotations/tasks.py`

**Acceptance**: Creating annotation triggers broadcast to vault room

---

### Task 3.7: Signal Handler for member.added
- [ ] Create `apps/vaults/signals.py` with `post_save` receiver for `VaultMembership`
- [ ] Create `apps/vaults/tasks.py`: `broadcast_member_added(membership_id)`
- [ ] Serialize member (user_id, username, role) and added_by
- [ ] Broadcast `member.added` event to vault room

**Files**: `apps/vaults/signals.py`, `apps/vaults/tasks.py`

**Acceptance**: Adding vault member triggers broadcast

---

## Phase 4: Error Handling & Rate Limiting (Week 3)

### Task 4.1: Error Message Helper
- [ ] Create `send_error_and_close(self, code, message, details, close_code)` in `VaultConsumer`
- [ ] Build error JSON: `{"type": "error", "error": {"code": code, "message": message, "details": details}, "metadata": {...}}`
- [ ] Send to client, wait 2 seconds, then `await self.close(code=close_code)`

**File**: `apps/vaults/consumers.py`

**Acceptance**: Helper sends error and closes connection gracefully

---

### Task 4.2: Connection Limit - Per User
- [ ] In `VaultConsumer.connect()`, check user's active connections:
  - `redis.scard(f"user_{user_id}:connections")`
  - If >= 5, send error `RATE_LIMIT_EXCEEDED` and close
  - Else, add current channel: `redis.sadd(f"user_{user_id}:connections", self.channel_name)`
- [ ] In `disconnect()`, remove: `redis.srem(f"user_{user_id}:connections", self.channel_name)`

**File**: `apps/vaults/consumers.py`

**Acceptance**: User limited to 5 concurrent WebSocket connections

---

### Task 4.3: Connection Limit - Per Vault
- [ ] In `VaultConsumer.connect()`, count room members:
  - Use `channel_layer.group_size(f"vault_{vault_id}")` (if available) or track in Redis set
  - If >= 100, send error and close
- [ ] Document: Vault room limited to 100 concurrent users

**File**: `apps/vaults/consumers.py`

**Acceptance**: Vault room limited to 100 users (test with load script)

---

### Task 4.4: Message Rate Limiting
- [ ] In `VaultConsumer.receive()`, track messages per minute:
  - `redis.zadd(f"conn_{self.channel_name}:messages", {time.time(): time.time()})`
  - `redis.zremrangebyscore(...)` to remove entries older than 60s
  - Count entries: `redis.zcard(...)`
  - If > 60, increment violation counter
- [ ] First violation: Send warning message
- [ ] Second violation: Disconnect with code 4000
- [ ] Third violation (within 1 hour): Set `user_{user_id}:banned` with 1h TTL

**File**: `apps/vaults/consumers.py`

**Acceptance**: Clients sending >60 msg/min get throttled/banned

---

### Task 4.5: Heartbeat Timeout Enforcement
- [ ] Create Celery periodic task: `check_heartbeat_timeouts()`
- [ ] For each vault's presence set, check timestamps
- [ ] Remove users with timestamp > 300s old
- [ ] Close their WebSocket connections (track channel_name → user mapping)
- [ ] Broadcast `presence.update`

**File**: `apps/vaults/tasks.py`

**Acceptance**: Users not sending heartbeats for 5min get disconnected

---

## Phase 5: Event Replay & Reconnection (Week 3-4)

### Task 5.1: Event Buffering to Redis
- [ ] In `broadcast_to_vault()` helper, after `group_send()`:
  - `redis.lpush(f"vault_{vault_id}:events", json.dumps(message))`
  - `redis.ltrim(f"vault_{vault_id}:events", 0, 99)` (keep last 100)
  - `redis.expire(f"vault_{vault_id}:events", 3600)` (1 hour TTL)

**File**: `core/websocket_utils.py`

**Acceptance**: Last 100 events per vault stored in Redis

---

### Task 5.2: Replay Request Handler
- [ ] In `VaultConsumer.receive()`, handle `{"type": "replay_request", "since_seq": X}`:
  - Fetch buffered events: `redis.lrange(f"vault_{vault_id}:events", 0, -1)`
  - Parse JSON, filter events with `seq > since_seq`
  - Send each event to client in chronological order
- [ ] If no buffered events or seq too old, send error: `{"error": {"code": "REPLAY_UNAVAILABLE", ...}}`

**File**: `apps/vaults/consumers.py`

**Acceptance**: Client can request missed events after reconnect

---

### Task 5.3: Client Reconnection Logic (Frontend Docs)
- [ ] Create `frontend/docs/websocket-client.md`
- [ ] Document TypeScript WebSocket client class:
  - Store `lastSeq` in memory and localStorage
  - On disconnect, wait 5s and reconnect
  - On reconnect, send `{"type": "replay_request", "since_seq": lastSeq}`
  - Handle replayed events (merge into state, avoid duplicates)
- [ ] Provide full example code with React hooks integration

**File**: `frontend/docs/websocket-client.md`

**Acceptance**: Frontend docs include working reconnection example

---

## Phase 6: Testing (Week 4)

### Task 6.1: E2E Test - Connection Success
- [ ] Create `apps/vaults/tests/test_websocket_e2e.py`
- [ ] Test: Authenticated user with vault membership can connect
- [ ] Use `WebsocketCommunicator` from `channels.testing`
- [ ] Verify `connection.success` message received with `seq`

**File**: `apps/vaults/tests/test_websocket_e2e.py`

**Acceptance**: Test passes with green checkmark

---

### Task 6.2: E2E Test - Connection Rejected (No Auth)
- [ ] Test: Invalid JWT → connection rejected with error + close code 1008
- [ ] Test: No vault membership → connection rejected with `PERMISSION_DENIED`

**File**: `apps/vaults/tests/test_websocket_e2e.py`

**Acceptance**: Both tests pass

---

### Task 6.3: E2E Test - Room Broadcast
- [ ] Test: User A creates source → User B (in same vault) receives `source.created` event
- [ ] Use 2 WebSocket communicators, both connected to same vault
- [ ] Trigger source creation via Django ORM (signal fires)
- [ ] Assert User B receives event within 1 second

**File**: `apps/vaults/tests/test_websocket_e2e.py`

**Acceptance**: Event broadcast verified end-to-end

---

### Task 6.4: E2E Test - Presence Tracking
- [ ] Test: User joins → all users receive `presence.update`
- [ ] Test: User leaves → all users receive updated presence
- [ ] Verify presence list accuracy (usernames, timestamps)

**File**: `apps/vaults/tests/test_websocket_e2e.py`

**Acceptance**: Presence tracking works correctly

---

### Task 6.5: E2E Test - Sequence Replay
- [ ] Test:
  1. User A connects, receives `seq: 10`
  2. Disconnect User A
  3. Create 3 sources (seq 11, 12, 13)
  4. Reconnect User A, request replay `since_seq: 10`
  5. Verify User A receives 3 events
- [ ] Use event buffering in Redis

**File**: `apps/vaults/tests/test_websocket_e2e.py`

**Acceptance**: Replay mechanism works correctly

---

### Task 6.6: E2E Test - Rate Limiting
- [ ] Test: Send 61 messages in 60 seconds → receive warning, then disconnect
- [ ] Mock time or use fast Redis expiry for testing

**File**: `apps/vaults/tests/test_websocket_e2e.py`

**Acceptance**: Rate limiting enforced

---

### Task 6.7: Consumer Unit Tests
- [ ] Create `apps/vaults/tests/test_consumers.py`
- [ ] Test: `connect()` sets vault_id in scope
- [ ] Test: `disconnect()` removes from presence
- [ ] Test: `vault_event()` sends JSON to WebSocket
- [ ] Test: `heartbeat()` updates presence timestamp
- [ ] Use mock channel layer (`channels.testing.ChannelLive`)

**File**: `apps/vaults/tests/test_consumers.py`

**Acceptance**: 5 unit tests pass

---

### Task 6.8: Signal Handler Tests
- [ ] Create `apps/sources/tests/test_signals.py`
- [ ] Test: `Source.objects.create()` triggers `broadcast_source_created.delay()`
- [ ] Test: Updating source triggers `broadcast_source_updated.delay()`
- [ ] Test: Deleting source triggers `broadcast_source_deleted.delay()`
- [ ] Use `@override_settings(CELERY_TASK_ALWAYS_EAGER=True)` for synchronous Celery

**File**: `apps/sources/tests/test_signals.py`

**Acceptance**: 3 signal tests pass

---

## Phase 7: Documentation (Week 4)

### Task 7.1: Developer Documentation
- [ ] Create `docs/websockets.md`
- [ ] Sections:
  - Architecture diagram (ASCII or Mermaid)
  - How to add new event types (step-by-step guide)
  - Local development setup (Redis, Daphne, Celery commands)
  - Debugging tips (Redis CLI commands, channel layer inspection)

**File**: `docs/websockets.md`

**Acceptance**: Docs complete and reviewed by team

---

### Task 7.2: API Documentation
- [ ] Create `docs/api/websockets.md`
- [ ] Document:
  - Connection endpoint with auth
  - Message envelope format
  - All event types (source.created, source.updated, annotation.created, etc.) with JSON examples
  - Error codes and close codes reference table

**File**: `docs/api/websockets.md`

**Acceptance**: API docs cover all events and error cases

---

### Task 7.3: Frontend Integration Guide
- [ ] Already created in Task 5.3 (`frontend/docs/websocket-client.md`)
- [ ] Review and ensure it includes:
  - Full TypeScript client class
  - React hook example (`useVaultWebSocket`)
  - Reconnection logic
  - Event handling (updating React Query cache)

**File**: `frontend/docs/websocket-client.md`

**Acceptance**: Frontend team can integrate WebSocket client from docs alone

---

### Task 7.4: Deployment Guide
- [ ] Create `docs/deployment/websockets.md`
- [ ] Document:
  - Running Daphne (systemd service example)
  - Nginx reverse proxy config for WebSocket
  - Redis production setup (persistence, maxmemory)
  - Celery worker configuration
  - Monitoring metrics (Prometheus exporters)

**File**: `docs/deployment/websockets.md`

**Acceptance**: DevOps can deploy to production from this guide

---

## Phase 8: Manual Verification (Week 4)

### Task 8.1: Manual Test - Multi-User Collaboration
**Steps**:
1. Open 2 browser tabs, log in as different users in same vault
2. User A creates a source → verify User B sees it instantly (no refresh)
3. User B adds annotation → verify User A sees it
4. User A leaves → verify User B sees presence update

**Expected**: All events appear in real-time, < 1 second latency

**File**: Append to `.planning/MANUAL_VERIFICATION.md`

---

### Task 8.2: Manual Test - Reconnection Resilience
**Steps**:
1. Connect to vault, note current `seq`
2. Disable network (browser DevTools → Network → Offline)
3. Create 3 sources via Django admin
4. Re-enable network
5. Verify client reconnects and replays 3 missed events

**Expected**: All missed events delivered on reconnect

**File**: Append to `.planning/MANUAL_VERIFICATION.md`

---

### Task 8.3: Manual Test - Rate Limiting
**Steps**:
1. Connect to vault
2. Send 70 messages rapidly via browser console WebSocket
3. Verify warning message received after 60
4. Verify disconnection after continued spam

**Expected**: Rate limiting enforced, no server crash

**File**: Append to `.planning/MANUAL_VERIFICATION.md`

---

### Task 8.4: Manual Test - Cross-Browser Compatibility
**Steps**:
1. Test WebSocket connection in Chrome, Firefox, Safari, Edge
2. Verify events received in all browsers
3. Verify presence tracking works across browsers

**Expected**: All browsers work correctly

**File**: Append to `.planning/MANUAL_VERIFICATION.md`

---

## Phase 9: User Setup Requirements

### Task 9.1: User Setup - Redis Installation
- [ ] Append to `.planning/USER_SETUP.md`:
  - Install Redis 7.0+ (Ubuntu: `apt install redis`, macOS: `brew install redis`)
  - Start Redis: `redis-server` or `brew services start redis`
  - Test: `redis-cli ping` → should return `PONG`
  - Set environment variable: `REDIS_URL=redis://localhost:6379/0`

**File**: `.planning/USER_SETUP.md`

---

### Task 9.2: User Setup - Celery Worker
- [ ] Append to `.planning/USER_SETUP.md`:
  - Start Celery worker: `celery -A config worker -l info -Q websocket_events`
  - Verify worker running: Check for "celery@hostname ready" in logs
  - Optional: Run Celery beat for periodic tasks: `celery -A config beat -l info`

**File**: `.planning/USER_SETUP.md`

---

### Task 9.3: User Setup - Daphne Server
- [ ] Append to `.planning/USER_SETUP.md`:
  - Run Daphne: `daphne -b 0.0.0.0 -p 8000 config.asgi:application`
  - Verify server running: Visit `http://localhost:8000` (should see Django API)
  - Test WebSocket: Use browser console or `wscat` tool

**File**: `.planning/USER_SETUP.md`

---

## Phase 10: Deployment & Optimization (Post-MVP)

### Task 10.1: Production Redis Configuration
- [ ] Enable RDB snapshots for persistence
- [ ] Set `maxmemory` (256MB-1GB)
- [ ] Set eviction policy: `allkeys-lru`
- [ ] Document in `docs/deployment/websockets.md`

**Acceptance**: Production-ready Redis config documented

---

### Task 10.2: Scaling Guide
- [ ] Document in `docs/deployment/websockets.md`:
  - Redis Sentinel for HA
  - Redis Cluster for horizontal scaling
  - Multiple Daphne workers behind Nginx
  - Celery worker pool sizing

**Acceptance**: Scaling guide complete

---

### Task 10.3: Monitoring Setup
- [ ] Set up Prometheus exporters for:
  - Redis (memory, connections)
  - Celery (queue depth, task latency)
  - Daphne (active WebSocket connections)
- [ ] Create Grafana dashboard with key metrics
- [ ] Document alert thresholds

**Acceptance**: Monitoring dashboard live

---

## Summary Checklist

**Phase 1 (Infrastructure)**: 6 tasks
**Phase 2 (Room Management)**: 7 tasks
**Phase 3 (Events)**: 7 tasks
**Phase 4 (Error Handling)**: 5 tasks
**Phase 5 (Replay)**: 3 tasks
**Phase 6 (Testing)**: 8 tasks
**Phase 7 (Documentation)**: 4 tasks
**Phase 8 (Manual Verification)**: 4 tasks
**Phase 9 (User Setup)**: 3 tasks
**Phase 10 (Deployment)**: 3 tasks

**Total**: 50 tasks

---

## Notes

- Tasks are ordered for sequential execution (dependencies respected)
- Each task has clear acceptance criteria
- Testing tasks should run in CI/CD pipeline
- Manual verification tasks require human testing
- User setup tasks are prerequisites for local development
- Phase 10 (Deployment) is optional for MVP but critical for production

**Estimated Total Time**: 3-4 weeks for full implementation and testing
