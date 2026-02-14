# PRD: Real-time Updates & Notifications Integration

## Introduction

Integrate SyncScript's frontend with the existing backend WebSocket system and notifications API to enable real-time collaboration features. This includes live updates for vault content, presence indicators showing active collaborators, toast notifications for vault events, browser push notifications via Pusher for high-priority events, and a notification management system with user preferences.

## Goals

- Establish reliable WebSocket connection to vault rooms with automatic reconnection
- Display real-time source/annotation updates with optimistic UI and server reconciliation
- Show active collaborators in vault with animate-ping presence indicators
- Provide toast notifications for vault events (source added, member joined, etc.)
- Integrate Pusher for browser push notifications on high-priority events (new member, @mentions)
- Allow users to manage notification preferences (enable/disable, sound toggle)
- Display unread notification count badge in header
- Provide notification history panel with mark-as-read functionality

## User Stories

### US-001: Create useVaultSocket hook for WebSocket connection management
**Description:** As a developer, I need a reusable hook to manage WebSocket connections to vault rooms so that components can subscribe to real-time events.

**Acceptance Criteria:**
- [x] Create `frontend/src/hooks/useVaultSocket.ts`
- [x] Hook accepts `vaultId` parameter and returns connection state, send function, and event handlers
- [x] Manages connection lifecycle (connect on mount, disconnect on unmount)
- [x] Implements automatic reconnection with exponential backoff (1s, 2s, 4s, max 30s)
- [x] Exposes connection status: 'connecting' | 'connected' | 'disconnected' | 'reconnecting'
- [x] Uses `NEXT_PUBLIC_WS_URL` environment variable for WebSocket endpoint
- [x] Typecheck passes

### US-002: Create ConnectionStatus indicator component
**Description:** As a user, I want to see my connection status so I know if real-time updates are working.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/notifications/ConnectionStatus.tsx`
- [x] Displays colored dot: green (connected), yellow (reconnecting), red (disconnected)
- [x] Shows tooltip with status text on hover
- [x] Uses Bitcoin DeFi design tokens (primary orange for reconnecting state)
- [x] Compact design suitable for header placement
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-003: Create useRealtimeUpdates hook for optimistic updates with reconciliation
**Description:** As a developer, I need a hook that handles optimistic UI updates and reconciles with server state so that the UI feels instant while staying consistent.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/useRealtimeUpdates.ts`
- [ ] Accepts React Query mutation and query key parameters
- [ ] Provides `optimisticUpdate` function that immediately updates cache
- [ ] Listens for WebSocket confirmation events and reconciles state
- [ ] Rolls back optimistic update on WebSocket error event
- [ ] Integrates with TanStack Query cache invalidation
- [ ] Typecheck passes

### US-004: Integrate real-time source updates in vault detail page
**Description:** As a user, I want to see new sources appear instantly when collaborators add them so I stay in sync with my team.

**Acceptance Criteria:**
- [ ] Connect useVaultSocket in vault detail page component
- [ ] Listen for `source.created`, `source.updated`, `source.deleted` events
- [ ] Update sources list in real-time without full page refresh
- [ ] Show subtle animation when new source appears (fade-in)
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-005: Integrate real-time annotation updates
**Description:** As a user, I want to see new annotations appear instantly when collaborators add them.

**Acceptance Criteria:**
- [ ] Listen for `annotation.created`, `annotation.updated`, `annotation.deleted` events
- [ ] Update annotations list/panel in real-time
- [ ] Show annotation author avatar with new annotations
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-006: Create usePresence hook for tracking active vault members
**Description:** As a developer, I need a hook to track which members are currently active in a vault.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/usePresence.ts`
- [ ] Sends presence heartbeat every 30 seconds via WebSocket
- [ ] Receives and tracks `presence.join`, `presence.leave`, `presence.heartbeat` events
- [ ] Returns list of active member IDs with last activity timestamp
- [ ] Marks members as inactive after 60 seconds without heartbeat
- [ ] Typecheck passes

### US-007: Create PresenceIndicator component with animate-ping effect
**Description:** As a user, I want to see which collaborators are currently active in the vault so I know who I'm working with.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/notifications/PresenceIndicator.tsx`
- [ ] Displays row of member avatars (max 5, +N overflow indicator)
- [ ] Active members have green dot with `animate-ping` effect per DESIGN_RULES.md
- [ ] Shows member name on avatar hover
- [ ] Uses glass morphism container: `backdrop-blur-lg bg-white/5 border border-white/10`
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-008: Create notification API client and useNotifications hook
**Description:** As a developer, I need to fetch and manage notifications from the backend API.

**Acceptance Criteria:**
- [ ] Create `frontend/src/lib/api/notifications.ts` with API functions
- [ ] Implement: `getNotifications()`, `markAsRead(id)`, `markAllAsRead()`, `getUnreadCount()`
- [ ] Create `frontend/src/hooks/useNotifications.ts` using TanStack Query
- [ ] Hook returns notifications list, unread count, and mutation functions
- [ ] Polling every 60 seconds for unread count (when tab visible)
- [ ] Typecheck passes

### US-009: Create toast notification system for vault events
**Description:** As a user, I want to see toast notifications when vault events occur so I'm aware of collaborator activity.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/notifications/VaultToast.tsx`
- [ ] Integrates with existing Radix toast or creates new toast context
- [ ] Shows event-specific messages: "Alice added a new source", "Bob joined the vault"
- [ ] Toast appears bottom-right, auto-dismisses after 5 seconds
- [ ] Uses Bitcoin DeFi styling: dark background, orange accent border
- [ ] Includes dismiss button
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-010: Create UnreadBadge component for header
**Description:** As a user, I want to see my unread notification count in the header so I know when I have new notifications.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/notifications/UnreadBadge.tsx`
- [ ] Displays count in orange pill badge (Bitcoin primary color)
- [ ] Shows "9+" for counts > 9
- [ ] Hidden when count is 0
- [ ] Subtle pulse animation when count increases
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-011: Create NotificationPanel dropdown component
**Description:** As a user, I want to view my notification history in a dropdown panel so I can catch up on missed events.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/notifications/NotificationPanel.tsx`
- [ ] Dropdown panel triggered by bell icon click in header
- [ ] Lists notifications with icon, message, timestamp, read/unread state
- [ ] Unread notifications have left border accent (orange)
- [ ] "Mark all as read" button at top
- [ ] Click notification marks it as read
- [ ] Empty state message when no notifications
- [ ] Max height with scroll, shows last 20 notifications
- [ ] Uses glass morphism styling per design system
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-012: Create NotificationPreferences panel for user settings
**Description:** As a user, I want to configure my notification preferences so I control what alerts I receive.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/notifications/NotificationPreferences.tsx`
- [ ] Toggle for enabling/disabling all notifications
- [ ] Toggle for browser push notifications (with permission request)
- [ ] Toggle for sound notifications (global on/off)
- [ ] Saves preferences to backend API (`PATCH /api/v1/users/me/preferences/`)
- [ ] Persists sound preference in localStorage for immediate access
- [ ] Uses switch components with Bitcoin DeFi styling
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-013: Integrate Pusher for browser push notifications
**Description:** As a user, I want to receive browser push notifications for high-priority events even when the tab is not focused.

**Acceptance Criteria:**
- [ ] Create `frontend/src/lib/pusher.ts` for Pusher client setup
- [ ] Initialize Pusher with `NEXT_PUBLIC_PUSHER_KEY` and `NEXT_PUBLIC_PUSHER_CLUSTER`
- [ ] Subscribe to user's private notification channel on login
- [ ] Handle `member.joined` and `mention.created` events
- [ ] Request browser notification permission when user enables push
- [ ] Display native browser notification with event details
- [ ] Click notification focuses app tab
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-014: Implement sound notification with global toggle
**Description:** As a user, I want to hear a sound when notifications arrive so I don't miss important updates.

**Acceptance Criteria:**
- [ ] Add notification sound file to `frontend/public/sounds/notification.mp3`
- [ ] Create `frontend/src/lib/notificationSound.ts` utility
- [ ] Play sound on toast notification if sound enabled in preferences
- [ ] Respect user's sound toggle preference from localStorage
- [ ] No sound when tab is not visible (avoid annoying background sounds)
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-015: Integrate notification components into app header
**Description:** As a user, I want notification controls in the header so I can access them from any page.

**Acceptance Criteria:**
- [ ] Add bell icon with UnreadBadge to main app header
- [ ] Bell click opens NotificationPanel dropdown
- [ ] Add ConnectionStatus indicator to header (right side)
- [ ] Dropdown closes when clicking outside
- [ ] Keyboard accessible (Escape to close)
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-016: Integrate PresenceIndicator into vault detail page
**Description:** As a user, I want to see active collaborators when viewing a vault.

**Acceptance Criteria:**
- [ ] Add PresenceIndicator component to vault detail page header area
- [ ] Connect to usePresence hook with current vault ID
- [ ] Position near vault title or in toolbar area
- [ ] Responsive: collapses to count-only on mobile
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-017: Add notification preferences to user settings page
**Description:** As a user, I want to access notification settings from my profile/settings page.

**Acceptance Criteria:**
- [ ] Add "Notifications" section to user settings page
- [ ] Embed NotificationPreferences component
- [ ] Section header with bell icon
- [ ] Consistent styling with other settings sections
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-018: Handle WebSocket reconnection with state recovery
**Description:** As a user, I want the app to recover gracefully from connection interruptions so I don't lose sync with my team.

**Acceptance Criteria:**
- [ ] On reconnect, fetch latest vault state via API to reconcile
- [ ] Show toast: "Reconnected - syncing latest changes"
- [ ] Re-subscribe to all active rooms after reconnect
- [ ] Re-send presence heartbeat immediately after reconnect
- [ ] Typecheck passes
- [ ] Verify changes work in browser

## Non-Goals

- Backend WebSocket server implementation (already exists)
- Backend notifications API implementation (already exists)
- Cursor/selection sharing (Google Docs style collaboration)
- Detailed activity status beyond online/offline
- Different sounds per event type (single global sound only)
- Email notification preferences (out of scope)
- Mobile push notifications (web push only)
- Notification grouping/batching

## Technical Considerations

- **WebSocket URL:** Use `NEXT_PUBLIC_WS_URL` environment variable
- **Pusher Config:** Use `NEXT_PUBLIC_PUSHER_KEY` and `NEXT_PUBLIC_PUSHER_CLUSTER`
- **State Management:** Use Zustand for notification state, TanStack Query for API cache
- **Design System:** Follow Bitcoin DeFi aesthetic from CLAUDE.md
  - Primary orange: `#F7931A`
  - Glass morphism: `backdrop-blur-lg bg-white/5 border border-white/10`
  - Animate-ping for presence dots
- **Existing Components:** Reuse Radix UI toast, dropdown, and switch primitives
- **Sound File:** Keep under 50KB, use MP3 format for browser compatibility
- **Reconnection:** Exponential backoff prevents server overload during outages

## Dependencies

- Backend WebSocket system (assumed complete)
- Backend Vaults API (assumed complete)
- Backend Notifications API endpoints:
  - `GET /api/v1/notifications/`
  - `PATCH /api/v1/notifications/{id}/read/`
  - `POST /api/v1/notifications/mark-all-read/`
  - `GET /api/v1/notifications/unread-count/`
  - `PATCH /api/v1/users/me/preferences/`
