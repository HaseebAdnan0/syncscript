# PRD 19: Notification System (Full Implementation)

## Introduction

SyncScript needs a complete notification system to keep researchers informed about activity in their Knowledge Vaults. This includes in-app notifications with real-time delivery via Pusher, email digests with configurable frequency, and browser push notifications. Users can customize their preferences globally and mute specific vaults.

## Goals

- Notify users of important vault activity (invites, new members, sources, annotations, mentions)
- Deliver notifications in real-time via Pusher with toast UI
- Batch email notifications into digests (immediate/daily/weekly/none)
- Allow granular user preferences with per-vault muting
- Auto-cleanup old notifications (read: 7 days, unread: 30 days)
- Support @mention detection in annotations with autocomplete UI

## User Stories

---

### US-001: Create Notification model and migration
**Description:** As a developer, I need a Notification model to store user notifications with type, content, and read status.

**Acceptance Criteria:**
- [x] Create `apps/notifications/models.py` with Notification model
- [x] Fields: `id`, `user` (FK), `type` (CharField with choices), `title`, `body`, `data` (JSONField), `read_at` (nullable DateTime), `created_at`
- [x] Type choices: `vault_invite`, `member_joined`, `source_added`, `annotation_reply`, `mention`
- [x] Add indexes on `user`, `read_at`, `created_at`
- [x] Generate and apply migration
- [x] Register in admin
- [x] Typecheck passes

---

### US-002: Create NotificationPreferences model
**Description:** As a developer, I need to store user notification preferences for email and push settings.

**Acceptance Criteria:**
- [x] Add NotificationPreferences model with OneToOne to User
- [x] Boolean fields: `email_vault_activity`, `email_mentions`, `push_enabled` (all default True)
- [x] `email_digest_frequency` CharField with choices: `immediate`, `daily`, `weekly`, `none` (default `daily`)
- [x] `push_sources`, `push_annotations` boolean fields (default True)
- [x] Auto-create preferences on user creation via signal
- [x] Generate and apply migration
- [x] Typecheck passes

---

### US-003: Create MutedVault model for per-vault muting
**Description:** As a developer, I need to track which vaults a user has muted to suppress notifications.

**Acceptance Criteria:**
- [ ] Add MutedVault model: `user` (FK), `vault` (FK), `created_at`
- [ ] Unique constraint on (user, vault)
- [ ] Generate and apply migration
- [ ] Register in admin
- [ ] Typecheck passes

---

### US-004: Create Notification serializers
**Description:** As a developer, I need serializers for notifications to power the API.

**Acceptance Criteria:**
- [ ] Create `apps/notifications/serializers.py`
- [ ] NotificationSerializer with all fields, `is_read` computed property
- [ ] NotificationPreferencesSerializer for user preferences
- [ ] MutedVaultSerializer with vault details (id, name)
- [ ] Typecheck passes

---

### US-005: Implement notification list endpoint
**Description:** As a user, I want to fetch my notifications so I can see recent activity.

**Acceptance Criteria:**
- [ ] GET `/api/v1/notifications/` returns paginated notifications
- [ ] Filter to authenticated user only
- [ ] Order by: unread first, then by created_at descending
- [ ] Support `?unread_only=true` query param
- [ ] Page size: 20
- [ ] Typecheck passes

---

### US-006: Implement mark notification as read endpoint
**Description:** As a user, I want to mark individual notifications as read.

**Acceptance Criteria:**
- [ ] PATCH `/api/v1/notifications/{id}/read/` sets `read_at` to current time
- [ ] Only allow marking own notifications
- [ ] Return updated notification
- [ ] Idempotent (re-marking doesn't change timestamp)
- [ ] Typecheck passes

---

### US-007: Implement mark all notifications as read endpoint
**Description:** As a user, I want to mark all my notifications as read at once.

**Acceptance Criteria:**
- [ ] POST `/api/v1/notifications/read-all/` marks all unread as read
- [ ] Only affects authenticated user's notifications
- [ ] Return count of notifications marked
- [ ] Typecheck passes

---

### US-008: Implement unread count endpoint
**Description:** As a user, I want to quickly fetch my unread notification count for the badge.

**Acceptance Criteria:**
- [ ] GET `/api/v1/notifications/unread-count/` returns `{ "count": N }`
- [ ] Only count authenticated user's notifications
- [ ] Efficient query (COUNT, not fetching all)
- [ ] Typecheck passes

---

### US-009: Implement notification preferences endpoints
**Description:** As a user, I want to view and update my notification preferences.

**Acceptance Criteria:**
- [ ] GET `/api/v1/notifications/preferences/` returns user's preferences
- [ ] PATCH `/api/v1/notifications/preferences/` updates preferences
- [ ] Auto-create preferences if missing on GET
- [ ] Validate email_digest_frequency choices
- [ ] Typecheck passes

---

### US-010: Implement muted vaults endpoints
**Description:** As a user, I want to mute/unmute specific vaults to control notifications.

**Acceptance Criteria:**
- [ ] GET `/api/v1/notifications/muted-vaults/` lists muted vaults
- [ ] POST `/api/v1/notifications/muted-vaults/` with `{ "vault_id": X }` mutes a vault
- [ ] DELETE `/api/v1/notifications/muted-vaults/{vault_id}/` unmutes
- [ ] Validate user is member of vault before muting
- [ ] Typecheck passes

---

### US-011: Create notification helper service
**Description:** As a developer, I need a service to create notifications with preference/mute checking.

**Acceptance Criteria:**
- [ ] Create `apps/notifications/services.py` with `create_notification()` function
- [ ] Parameters: `user`, `notification_type`, `title`, `body`, `data`
- [ ] Check if vault is muted (skip if muted)
- [ ] Check user preferences for the notification type
- [ ] Return created Notification or None if skipped
- [ ] Typecheck passes

---

### US-012: Signal handler for vault_invite notifications
**Description:** As a user, I want to be notified when I'm invited to a vault.

**Acceptance Criteria:**
- [ ] Create signal handler in `apps/notifications/signals.py`
- [ ] Listen for VaultMembership creation where user != owner
- [ ] Create notification with type `vault_invite`
- [ ] Data includes: `vault_id`, `vault_name`, `inviter_id`, `inviter_name`
- [ ] Connect signal in apps.py ready()
- [ ] Typecheck passes

---

### US-013: Signal handler for member_joined notifications
**Description:** As a vault owner, I want to be notified when someone joins my vault.

**Acceptance Criteria:**
- [ ] Listen for VaultMembership creation
- [ ] Notify vault owner (if different from new member)
- [ ] Create notification with type `member_joined`
- [ ] Data includes: `vault_id`, `vault_name`, `member_id`, `member_name`
- [ ] Typecheck passes

---

### US-014: Signal handler for source_added notifications
**Description:** As a vault member, I want to be notified when new sources are added.

**Acceptance Criteria:**
- [ ] Listen for Source creation
- [ ] Notify all vault members except the creator
- [ ] Create notification with type `source_added`
- [ ] Data includes: `vault_id`, `vault_name`, `source_id`, `source_title`, `creator_name`
- [ ] Respect muted vaults
- [ ] Typecheck passes

---

### US-015: Signal handler for annotation_reply notifications
**Description:** As a user, I want to be notified when someone replies to my annotation.

**Acceptance Criteria:**
- [ ] Listen for Annotation creation where `parent` is set
- [ ] Notify parent annotation author (if different from reply author)
- [ ] Create notification with type `annotation_reply`
- [ ] Data includes: `source_id`, `annotation_id`, `parent_id`, `replier_name`, `preview` (first 100 chars)
- [ ] Typecheck passes

---

### US-016: Create @mention detection utility
**Description:** As a developer, I need a utility to detect @mentions in annotation text.

**Acceptance Criteria:**
- [ ] Create `apps/notifications/mentions.py`
- [ ] Function `extract_mentions(text)` returns list of usernames from `@username` patterns
- [ ] Handle edge cases: start of text, after spaces, punctuation
- [ ] Function `resolve_mentions(usernames, vault_id)` returns User objects who are vault members
- [ ] Ignore invalid/non-member usernames
- [ ] Typecheck passes

---

### US-017: Signal handler for mention notifications
**Description:** As a user, I want to be notified when someone @mentions me in an annotation.

**Acceptance Criteria:**
- [ ] Extract mentions from annotation body on creation/update
- [ ] Create notification with type `mention` for each mentioned user
- [ ] Data includes: `source_id`, `annotation_id`, `mentioner_name`, `preview`
- [ ] Don't notify self-mentions
- [ ] Don't duplicate if also replying to same user
- [ ] Typecheck passes

---

### US-018: Integrate Pusher for real-time notification delivery
**Description:** As a user, I want to receive notifications in real-time without refreshing.

**Acceptance Criteria:**
- [ ] Add Pusher trigger in `create_notification()` service
- [ ] Send to private channel `private-user-{user_id}`
- [ ] Event name: `notification`
- [ ] Payload: serialized notification data
- [ ] Also send `badge_update` event with new unread count
- [ ] Typecheck passes

---

### US-019: Create Pusher authentication endpoint
**Description:** As a developer, I need an endpoint to authenticate Pusher private channels.

**Acceptance Criteria:**
- [ ] POST `/api/v1/notifications/pusher/auth/` authenticates channel subscription
- [ ] Validate channel name matches `private-user-{request.user.id}`
- [ ] Return Pusher auth signature
- [ ] Reject unauthorized channel access
- [ ] Typecheck passes

---

### US-020: Create email notification service
**Description:** As a developer, I need a service to send notification emails.

**Acceptance Criteria:**
- [ ] Create `apps/notifications/email.py`
- [ ] Function `send_notification_email(user, notifications)` sends digest
- [ ] Generate both HTML and plain text versions
- [ ] HTML template with notification list, icons, action links
- [ ] Plain text with simple list format
- [ ] Use Django email backend from settings
- [ ] Typecheck passes

---

### US-021: Create HTML email template for notifications
**Description:** As a user, I want notification emails to look professional and be easy to read.

**Acceptance Criteria:**
- [ ] Create `templates/notifications/email_digest.html`
- [ ] Header with SyncScript branding (Bitcoin DeFi aesthetic)
- [ ] List of notifications with icon, title, body preview, timestamp
- [ ] Action button linking to notification source
- [ ] Unsubscribe/preferences link in footer
- [ ] Mobile-responsive design
- [ ] Typecheck passes

---

### US-022: Celery task for immediate email notifications
**Description:** As a user with immediate email preference, I want emails sent right away.

**Acceptance Criteria:**
- [ ] Create `apps/notifications/tasks.py`
- [ ] Task `send_immediate_notification_email(notification_id)` sends single notification
- [ ] Only send if user preference is `immediate`
- [ ] Call from `create_notification()` service
- [ ] Mark notification as emailed (add `emailed_at` field to model)
- [ ] Typecheck passes

---

### US-023: Celery beat task for daily/weekly email digests
**Description:** As a user, I want to receive batched email digests based on my preference.

**Acceptance Criteria:**
- [ ] Task `send_daily_digest()` runs at 9 AM UTC
- [ ] Task `send_weekly_digest()` runs Monday 9 AM UTC
- [ ] Query users with matching preference and un-emailed notifications
- [ ] Batch notifications per user into single email
- [ ] Mark all as emailed after sending
- [ ] Add to Celery beat schedule in settings
- [ ] Typecheck passes

---

### US-024: Celery task for notification cleanup
**Description:** As a developer, I need to auto-delete old notifications to manage storage.

**Acceptance Criteria:**
- [ ] Task `cleanup_old_notifications()` runs daily
- [ ] Delete read notifications older than 7 days
- [ ] Delete unread notifications older than 30 days
- [ ] Log count of deleted notifications
- [ ] Add to Celery beat schedule
- [ ] Typecheck passes

---

### US-025: Add notification types and API client to frontend
**Description:** As a developer, I need TypeScript types and API functions for notifications.

**Acceptance Criteria:**
- [ ] Create `frontend/src/types/notifications.ts` with interfaces
- [ ] Types: Notification, NotificationPreferences, NotificationType enum
- [ ] Add to `frontend/src/lib/api.ts`: `getNotifications()`, `markAsRead()`, `markAllAsRead()`, `getUnreadCount()`, `getPreferences()`, `updatePreferences()`, `getMutedVaults()`, `muteVault()`, `unmuteVault()`
- [ ] Typecheck passes

---

### US-026: Create NotificationBell component with badge
**Description:** As a user, I want to see a notification bell icon with unread count in the header.

**Acceptance Criteria:**
- [ ] Create `components/features/notifications/NotificationBell.tsx`
- [ ] Bell icon (lucide-react)
- [ ] Red badge with unread count (hide if 0)
- [ ] Badge shows "9+" for counts > 9
- [ ] Click opens notification dropdown
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-027: Create NotificationItem component
**Description:** As a user, I want each notification to display clearly with icon, content, and time.

**Acceptance Criteria:**
- [ ] Create `components/features/notifications/NotificationItem.tsx`
- [ ] Icon based on notification type (different icons for invite, source, mention, etc.)
- [ ] Title in bold, body preview below (truncated)
- [ ] Relative timestamp (e.g., "2 hours ago")
- [ ] Blue dot indicator for unread
- [ ] Hover state with subtle background
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-028: Create NotificationDropdown component
**Description:** As a user, I want a dropdown panel showing my recent notifications.

**Acceptance Criteria:**
- [ ] Create `components/features/notifications/NotificationDropdown.tsx`
- [ ] Dropdown panel triggered by NotificationBell click
- [ ] Header: "Notifications" with "Mark all as read" button
- [ ] List of NotificationItem components (max 10, scrollable)
- [ ] Empty state: "No notifications yet"
- [ ] Footer link: "View all notifications"
- [ ] Close on click outside
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-029: Create useNotifications hook
**Description:** As a developer, I need a hook to fetch and manage notification state.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/useNotifications.ts`
- [ ] Fetch notifications with React Query
- [ ] `unreadCount` state from API
- [ ] `markAsRead(id)` mutation
- [ ] `markAllAsRead()` mutation
- [ ] Refetch on window focus
- [ ] Typecheck passes

---

### US-030: Integrate NotificationBell into app header
**Description:** As a user, I want to see the notification bell in the main app header.

**Acceptance Criteria:**
- [ ] Add NotificationBell to app header/navbar
- [ ] Position before user profile menu
- [ ] Only show when authenticated
- [ ] Fetch unread count on mount
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-031: Set up Pusher client for real-time notifications
**Description:** As a developer, I need Pusher client configured for real-time updates.

**Acceptance Criteria:**
- [ ] Install `pusher-js` package
- [ ] Create `frontend/src/lib/pusher.ts` with client setup
- [ ] Use `NEXT_PUBLIC_PUSHER_KEY` and cluster from env
- [ ] Export configured Pusher instance
- [ ] Add auth endpoint configuration for private channels
- [ ] Typecheck passes

---

### US-032: Create usePusherNotifications hook for real-time
**Description:** As a user, I want notifications to appear instantly without refreshing.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/usePusherNotifications.ts`
- [ ] Subscribe to `private-user-{userId}` channel
- [ ] Listen for `notification` event
- [ ] Update React Query cache with new notification
- [ ] Listen for `badge_update` event to update count
- [ ] Cleanup subscription on unmount
- [ ] Typecheck passes

---

### US-033: Create toast notification system
**Description:** As a user, I want toast popups for real-time notifications.

**Acceptance Criteria:**
- [ ] Create `components/features/notifications/NotificationToast.tsx`
- [ ] Toast shows icon, title, body preview
- [ ] Auto-dismiss after 5 seconds
- [ ] Stack up to 3 toasts (newest at bottom)
- [ ] Click toast to navigate and dismiss
- [ ] Dismiss button (X)
- [ ] Slide-in animation from right
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-034: Integrate toast notifications with Pusher
**Description:** As a user, I want toasts to appear when I receive real-time notifications.

**Acceptance Criteria:**
- [ ] Hook usePusherNotifications triggers toast on new notification
- [ ] Use existing toast/sonner system if available, or NotificationToast
- [ ] Don't show toast if notification dropdown is open
- [ ] Don't show toast if page is not visible (document.hidden)
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-035: Implement notification click navigation
**Description:** As a user, I want clicking a notification to take me to the relevant item.

**Acceptance Criteria:**
- [ ] Each notification type maps to a route:
  - `vault_invite` → `/vaults/{vault_id}`
  - `member_joined` → `/vaults/{vault_id}/members`
  - `source_added` → `/vaults/{vault_id}/sources/{source_id}`
  - `annotation_reply` → `/vaults/{vault_id}/sources/{source_id}#annotation-{annotation_id}`
  - `mention` → same as annotation_reply
- [ ] Mark as read on click
- [ ] Close dropdown after navigation
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-036: Create notification preferences page layout
**Description:** As a user, I want a settings page to manage my notification preferences.

**Acceptance Criteria:**
- [ ] Create `frontend/src/app/settings/notifications/page.tsx`
- [ ] Page title: "Notification Preferences"
- [ ] Sections: "Email Notifications", "Push Notifications", "Muted Vaults"
- [ ] Card-based layout matching app design
- [ ] Loading skeleton while fetching preferences
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-037: Add email notification toggles to preferences
**Description:** As a user, I want to toggle which email notifications I receive.

**Acceptance Criteria:**
- [ ] Toggle switches for: "Vault activity", "Mentions"
- [ ] Each toggle updates API immediately (optimistic update)
- [ ] Show saved confirmation
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-038: Add email frequency selector to preferences
**Description:** As a user, I want to choose how often I receive email digests.

**Acceptance Criteria:**
- [ ] Radio group or select for: "Immediate", "Daily digest", "Weekly digest", "None"
- [ ] Show description for each option
- [ ] Update API on selection change
- [ ] Disable email toggles if frequency is "None"
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-039: Add push notification controls to preferences
**Description:** As a user, I want to enable/disable push notifications.

**Acceptance Criteria:**
- [ ] Master toggle for "Enable push notifications"
- [ ] Sub-toggles: "New sources", "Annotation activity"
- [ ] Request browser permission when enabling
- [ ] Show permission status (granted/denied/prompt)
- [ ] Disable sub-toggles if master is off
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-040: Add muted vaults management to preferences
**Description:** As a user, I want to see and manage which vaults I've muted.

**Acceptance Criteria:**
- [ ] List of muted vaults with vault name
- [ ] Unmute button for each vault
- [ ] Empty state: "No muted vaults"
- [ ] Note: "Mute vaults from the vault settings page"
- [ ] Refresh list after unmuting
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-041: Add mute vault button to vault settings
**Description:** As a user, I want to mute a vault from its settings page.

**Acceptance Criteria:**
- [ ] Add "Mute notifications" toggle to vault settings
- [ ] Show current mute status
- [ ] Toggle calls mute/unmute API
- [ ] Show confirmation toast
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-042: Create mention autocomplete component
**Description:** As a user, I want to see suggestions when typing @mentions in annotations.

**Acceptance Criteria:**
- [ ] Create `components/features/annotations/MentionAutocomplete.tsx`
- [ ] Trigger on typing `@` in annotation input
- [ ] Show dropdown with matching vault members
- [ ] Filter as user types after @
- [ ] Show user avatar, name, username
- [ ] Keyboard navigation (arrow keys, enter to select)
- [ ] Insert selected username at cursor
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-043: Integrate mention autocomplete into annotation editor
**Description:** As a user, I want @mention suggestions while writing annotations.

**Acceptance Criteria:**
- [ ] Add MentionAutocomplete to annotation input/textarea
- [ ] Fetch vault members for suggestions
- [ ] Position dropdown near cursor
- [ ] Close on escape or click outside
- [ ] Works in both new annotation and reply forms
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-044: Add comprehensive notification tests
**Description:** As a developer, I need tests to ensure notification system reliability.

**Acceptance Criteria:**
- [ ] Test Notification model creation
- [ ] Test signal handlers create correct notifications
- [ ] Test API endpoints (list, read, read-all, count, preferences)
- [ ] Test muted vault filtering
- [ ] Test mention extraction utility
- [ ] Test email digest generation
- [ ] All tests pass
- [ ] Typecheck passes

---

## Non-Goals

- Native mobile push notifications (web push only)
- Notification sounds/audio
- Notification scheduling (post at specific time)
- Notification templates/customization by admins
- Read receipts for notifications
- Notification categories/folders
- Bulk notification actions beyond "mark all read"
- Real-time collaborative cursors (separate feature)

## Technical Considerations

- **Pusher**: Use existing Pusher credentials from env; private channels require auth endpoint
- **Celery Beat**: Add to existing beat schedule in `config/celery.py`
- **Email Templates**: Place in `backend/templates/notifications/`
- **Signal Registration**: Connect in `apps/notifications/apps.py` ready() method
- **Frontend State**: Use React Query for caching, invalidate on Pusher events
- **Toast System**: Use existing Radix toast if available, or create standalone
- **Mention Regex**: `/(?:^|\s)@(\w+)/g` handles most cases
