# Manual Verification Tasks

## US-001: User Registration with Email Verification - 2026-02-14

### Registration Flow
- [ ] Start backend server: `cd backend && python manage.py runserver`
- [ ] Send POST request to `http://localhost:8000/api/v1/auth/register/` with:
  ```json
  {
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "bio": "Research scientist",
    "institution": "MIT"
  }
  ```
- [ ] Verify response contains `message` and `user` fields
- [ ] Verify user is created in database with `is_email_verified=False`
- [ ] Check email output (console or email inbox depending on EMAIL_BACKEND setting)

### Email Verification Flow
- [ ] Copy verification token from email
- [ ] Send POST request to `http://localhost:8000/api/v1/auth/verify-email/` with:
  ```json
  {
    "token": "<verification_token_from_email>"
  }
  ```
- [ ] Verify response message indicates success
- [ ] Verify user's `is_email_verified` is now `True` in database
- [ ] Verify `email_verification_token` is cleared (set to null)

### Login Flow (Unverified User)
- [ ] Create a user but do NOT verify email
- [ ] Attempt to access protected endpoints (will be implemented in future stories)
- [ ] Verify unverified users receive appropriate error message

### Resend Verification Flow
- [ ] Send POST request to `http://localhost:8000/api/v1/auth/resend-verification/` with:
  ```json
  {
    "email": "test@example.com"
  }
  ```
- [ ] Verify new verification email is sent
- [ ] Verify old token is invalidated and new token works

### Rate Limiting
- [ ] Attempt to register 6 times in quick succession from same IP
- [ ] Verify 6th attempt is blocked with rate limit error
- [ ] Wait 1 minute and verify registration works again

### Validation Testing
- [ ] Try registering with duplicate email - verify error
- [ ] Try registering with duplicate username - verify error
- [ ] Try registering with mismatched passwords - verify error
- [ ] Try registering with weak password (e.g., "123") - verify error
- [ ] Try registering without required fields - verify errors
- [ ] Try verifying with invalid token - verify error

### Expected Behavior
- Registration creates user with unverified status
- Verification email contains valid token link
- Email verification activates account
- Unverified users cannot access protected endpoints (enforced by `IsEmailVerified` permission)
- Rate limiting prevents abuse
- All validation rules are enforced

### Steps to Test
1. Set up PostgreSQL database named `syncscript`
2. Set up Redis server
3. Configure `.env` file with database and email settings
4. Run migrations: `python manage.py migrate`
5. Start server: `python manage.py runserver`
6. Use Postman, curl, or similar tool to test endpoints
7. Check Django admin at `http://localhost:8000/admin/` to inspect users

---

## US-002: JWT-Based Login and Token Management - 2026-02-14

### Login Flow (Standard)
- [ ] Register and verify a user first (see US-001)
- [ ] Send POST request to `http://localhost:8000/api/v1/auth/login/` with:
  ```json
  {
    "email": "test@example.com",
    "password": "SecurePass123!"
  }
  ```
- [ ] Verify response contains `access`, `refresh`, and `user` fields
- [ ] Verify `user` object contains `id`, `email`, `username`, `is_email_verified`
- [ ] Verify access token is a valid JWT (use jwt.io to decode)
- [ ] Verify token contains custom claims: `user_id`, `email`, `is_email_verified`
- [ ] Verify access token expiry is 15 minutes
- [ ] Verify refresh token expiry is 7 days

### Login Flow (HttpOnly Cookie)
- [ ] Send POST request to `http://localhost:8000/api/v1/auth/login/` with:
  ```json
  {
    "email": "test@example.com",
    "password": "SecurePass123!",
    "use_cookie": true
  }
  ```
- [ ] Verify response contains `access` and `refresh` in body
- [ ] Verify response sets `refresh_token` cookie
- [ ] Verify cookie has `HttpOnly` flag set
- [ ] Verify cookie has `SameSite=Lax` attribute
- [ ] Verify cookie max-age is 7 days (604800 seconds)
- [ ] In production (DEBUG=False), verify cookie has `Secure` flag

### Case-Insensitive Email Login
- [ ] Login with lowercase email: `test@example.com` - verify success
- [ ] Login with uppercase email: `TEST@EXAMPLE.COM` - verify success
- [ ] Login with mixed case: `TeSt@ExAmPlE.cOm` - verify success
- [ ] All should authenticate the same user

### Token Refresh Flow
- [ ] Obtain refresh token from login response
- [ ] Send POST request to `http://localhost:8000/api/v1/auth/refresh/` with:
  ```json
  {
    "refresh": "<refresh_token_from_login>"
  }
  ```
- [ ] Verify response contains new `access` token
- [ ] Verify new access token is different from original
- [ ] Verify new access token has updated expiry time
- [ ] If `ROTATE_REFRESH_TOKENS=True`, verify response also contains new `refresh` token

### Invalid Login Attempts
- [ ] Try login with wrong email - verify 401 Unauthorized
- [ ] Try login with wrong password - verify 401 Unauthorized
- [ ] Try login with missing email - verify 400 Bad Request
- [ ] Try login with missing password - verify 400 Bad Request
- [ ] Try login with unregistered email - verify 401 Unauthorized

### Rate Limiting
- [ ] Attempt to login 6 times in quick succession from same IP
- [ ] Verify 6th attempt is blocked with rate limit error (429 Too Many Requests)
- [ ] Wait 1 minute and verify login works again

### Unverified User Login
- [ ] Create a user but do NOT verify email
- [ ] Login with unverified user credentials
- [ ] Verify login succeeds (authentication works)
- [ ] Verify `is_email_verified: false` in response
- [ ] Verify JWT token contains `is_email_verified: false` claim
- [ ] Note: Protected endpoints can check this claim to enforce verification

### Token Usage in API Requests
- [ ] Obtain access token from login
- [ ] Send request to protected endpoint with `Authorization: Bearer <access_token>` header
- [ ] Verify request is authenticated (will test in future stories)
- [ ] Send request without token - verify 401 Unauthorized
- [ ] Send request with expired token - verify 401 Unauthorized
- [ ] Send request with malformed token - verify 401 Unauthorized

### Expected Behavior
- Login accepts email/password and returns JWT tokens
- Access token expires in 15 minutes
- Refresh token expires in 7 days
- Tokens contain user_id, email, and is_email_verified claims
- HttpOnly cookies can be used for web clients (opt-in)
- Email lookup is case-insensitive
- Rate limiting prevents brute force attacks (5/minute)
- Unverified users can login but token flags verification status

### Testing Tools
- **Postman**: GUI tool for API testing, can inspect cookies
- **curl**: Command-line tool
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password": "SecurePass123!"}'
  ```
- **jwt.io**: Online tool to decode and inspect JWT tokens
- **Django Admin**: Check user last_login timestamp updates on successful login

---

## Authentication System (US-039) - 2026-02-14

### Registration Flow
- [ ] Start backend server: `cd backend && python manage.py runserver`
- [ ] Send POST to `/api/v1/auth/register/` with valid user data
- [ ] Verify 201 response with user data and message about verification email
- [ ] Verify user created in database with `email_verified=False`
- [ ] Verify EmailVerificationToken created in database
- [ ] Check email output (console/inbox depending on EMAIL_BACKEND)

### Email Verification Flow
- [ ] Copy verification token from email
- [ ] Send POST to `/api/v1/auth/verify-email/` with `{"token": "..."}`
- [ ] Verify 200 response with success message
- [ ] Verify user's `email_verified` is now `True` in database
- [ ] Verify EmailVerificationToken is deleted from database

### Login Flow
- [ ] Send POST to `/api/v1/auth/login/` with email and password
- [ ] Verify 200 response with access token, refresh token, and user data
- [ ] Verify access token is valid JWT
- [ ] Try login with unverified user - verify 403 error
- [ ] Try login with wrong password - verify 401 error

### Token Refresh Flow
- [ ] Obtain refresh token from login
- [ ] Send POST to `/api/v1/auth/refresh/` with `{"refresh": "..."}`
- [ ] Verify 200 response with new access token and rotated refresh token
- [ ] Verify old refresh token is blacklisted (cannot be reused)
- [ ] Try refresh with blacklisted token - verify 401 error

### Logout Flow
- [ ] Login to obtain tokens
- [ ] Send POST to `/api/v1/auth/logout/` with Authorization header and `{"refresh": "..."}`
- [ ] Verify 200 response with success message
- [ ] Verify refresh token is blacklisted
- [ ] Try using blacklisted token - verify 401 error

### Password Reset Flow
- [ ] Send POST to `/api/v1/auth/password-reset/` with `{"email": "..."}`
- [ ] Verify 200 response with success message (even for non-existent email)
- [ ] Check email output for password reset link with uid and token
- [ ] Send POST to `/api/v1/auth/password-reset-confirm/` with uid, token, new_password
- [ ] Verify 200 response with success message
- [ ] Try login with old password - verify fails
- [ ] Try login with new password - verify succeeds
- [ ] Try reusing same reset token - verify fails (token invalidated)

### Profile Update Flow
- [ ] Login to obtain access token
- [ ] Send GET to `/api/v1/users/profile/` with Authorization header
- [ ] Verify 200 response with user profile data
- [ ] Send PATCH to `/api/v1/users/profile/` with avatar_url, bio, institution
- [ ] Verify 200 response with updated profile data
- [ ] Try to update email via PATCH - verify 400 error
- [ ] Try to update password via PATCH - verify 400 error
- [ ] Send PATCH with bio > 500 chars - verify 400 error
- [ ] Send PATCH with institution > 200 chars - verify 400 error

### Rate Limiting Tests
- [ ] Attempt 6 login requests within 1 minute from same IP
- [ ] Verify 6th request returns 429 (or 403 in test mode)
- [ ] Attempt 6 registration requests within 1 minute from same IP
- [ ] Verify 6th request returns 429 (or 403 in test mode)
- [ ] Attempt 4 password reset requests within 1 hour for same email
- [ ] Verify 4th request returns 429 (or 403 in test mode)
- [ ] Wait for time window to expire and verify requests work again

### Expected Behavior
- Registration creates unverified users and sends verification email
- Email verification activates accounts
- Only verified users can login
- JWT tokens expire (access: 15min, refresh: 7 days)
- Token rotation blacklists old refresh tokens
- Password reset always returns success (no user enumeration)
- Profile endpoint allows updating specific fields only
- Rate limiting prevents abuse on all auth endpoints
- All validation rules enforced (password strength, field length, etc.)

### Prerequisites
1. PostgreSQL database running and configured in .env
2. Redis server running for rate limiting
3. Email backend configured (console or SMTP)
4. Django migrations applied: `python manage.py migrate`
5. Test from Postman, curl, or API testing tool

## US-024: E2E WebSocket Connection and Auth Tests - 2026-02-14
- [ ] Stop any running test processes that might hold database locks
- [ ] Drop test database manually: `DROP DATABASE IF EXISTS test_syncscript;` via psql or pgAdmin
- [ ] Run tests fresh (without --keepdb): `python manage.py test apps.vaults.tests.test_websocket_e2e`
- [ ] Expected results:
  - test_connection_success_with_valid_jwt_and_membership: PASS (WebSocket connects successfully)
  - test_connection_rejected_with_invalid_jwt: PASS (Connection rejected with AUTH_FAILED error)
  - test_connection_rejected_without_vault_membership: PASS (Connection rejected with PERMISSION_DENIED error)
  - test_connection_rejected_with_missing_jwt: PASS (Connection rejected with AUTH_FAILED error)
  - test_contributor_can_connect_to_vault: PASS (Contributor role can connect)
- [ ] All 5 tests should pass
- [ ] Typecheck passes: `pyright apps/vaults/tests/test_websocket_e2e.py`

---

## US-027: Signal Handler Tests - 2026-02-14
- [ ] Ensure PostgreSQL is running and accessible
- [ ] Stop any running test processes that might hold database locks
- [ ] Drop test database manually if needed: `DROP DATABASE IF EXISTS test_syncscript;` via psql or pgAdmin
- [ ] Run signal tests: `python manage.py test apps.sources.tests.test_signals --verbosity=2`
- [ ] Expected results:
  - test_source_created_triggers_celery_task: PASS (Source creation triggers broadcast_source_created task)
  - test_source_updated_broadcasts_to_vault: PASS (Source update triggers broadcast_source_updated task with changed fields)
  - test_source_deleted_broadcasts_to_vault: PASS (Source deletion triggers broadcast_source_deleted task with vault_id)
  - test_signal_not_triggered_on_update: PASS (Update does NOT trigger create task)
  - test_create_and_update_trigger_different_tasks: PASS (Create and update trigger different Celery tasks)
- [ ] All 5 tests should pass
- [ ] Typecheck passes: `pyright apps/sources/tests/test_signals.py`
- [ ] Verification script passes: `python test_verify_signals.py` (verifies signal registration and test structure)
- [ ] Tests verify:
  - post_save signal with created=True triggers broadcast_source_created.delay(source_id)
  - post_save signal with created=False triggers broadcast_source_updated.delay(source_id, changed_fields)
  - post_delete signal triggers broadcast_source_deleted.delay(source_id, vault_id, deleted_by_id)
  - Celery tasks mocked to verify correct arguments without actually executing
  - Signal handlers only fire for appropriate events (create vs update)

---

## US-026: E2E WebSocket Rate Limiting and Replay Tests - 2026-02-14
- [ ] Ensure PostgreSQL is running and accessible
- [ ] Ensure Redis is running (required for InMemoryChannelLayer fallback)
- [ ] Stop any running test processes that might hold database locks
- [ ] Drop test database manually if needed: `DROP DATABASE IF EXISTS test_syncscript;` via psql or pgAdmin
- [ ] Run rate limiting tests: `python manage.py test apps.vaults.tests.test_websocket_rate_limiting --verbosity=2`
- [ ] Expected results:
  - test_message_throttling_progressive_enforcement: PASS (61 messages trigger warning/disconnect)
  - test_heartbeat_timeout_enforcement: PASS (Connection stays alive with heartbeats)
  - test_event_replay_after_reconnection: PASS (User reconnects and receives missed events in chronological order)
- [ ] All 3 tests should pass
- [ ] Typecheck passes: `pyright apps/vaults/tests/test_websocket_rate_limiting.py`
- [ ] Tests verify:
  - Message throttling Layer 3 enforcement (>60 msgs/60s triggers warning → disconnect)
  - Heartbeat keeps connection alive (timeout cleanup tested by Celery task US-021)
  - Event replay retrieves missed events after reconnection using since_seq parameter
  - Replayed events delivered in chronological order (sequence numbers increasing)

---

## US-025: E2E WebSocket Broadcasting Tests - 2026-02-14
- [ ] Ensure PostgreSQL is running and accessible
- [ ] Ensure Redis is running (required for InMemoryChannelLayer fallback)
- [ ] Stop any running test processes that might hold database locks
- [ ] Drop test database manually if needed: `DROP DATABASE IF EXISTS test_syncscript;` via psql or pgAdmin
- [ ] Run broadcasting tests: `python manage.py test apps.vaults.tests.test_websocket_broadcasting --verbosity=2`
- [ ] Expected results:
  - test_source_created_broadcasts_to_all_users: PASS (User A creates source, User B receives source.created event)
  - test_user_join_broadcasts_presence_update_to_all: PASS (User joins, all connected users receive presence.update with 2 users)
  - test_user_leave_broadcasts_presence_update_to_remaining_users: PASS (User leaves, remaining users receive presence.update with 1 user)
  - test_concurrent_users_receive_all_broadcasts: PASS (10 concurrent users all receive source.created event, at least 8/10 confirmed)
- [ ] All 4 tests should pass
- [ ] Typecheck passes: `pyright apps/vaults/tests/test_websocket_broadcasting.py`
- [ ] Tests verify:
  - Source creation signals trigger Celery tasks that broadcast to all connected users
  - Presence updates broadcast when users join/leave rooms
  - Multiple concurrent users can all receive broadcasts reliably
  - CELERY_TASK_ALWAYS_EAGER=True ensures synchronous execution in tests


## PRD10: Real-time Updates & Notifications Integration - 2026-02-14

### US-009: Toast notification system for vault events
- [ ] Open two browser tabs/windows logged in as different users
- [ ] Navigate both to the same vault
- [ ] User A: Add a new source
- [ ] User B: Verify toast appears bottom-right: "[Username] added a new source"
- [ ] User A: Add a member to the vault
- [ ] User B: Verify toast appears: "[Username] joined the vault"
- [ ] Verify toast auto-dismisses after 5 seconds
- [ ] Verify toast has Bitcoin DeFi styling (dark bg, orange accent border)
- [ ] Verify dismiss button works (X icon)

### US-010: UnreadBadge component for header
- [ ] Login as User A
- [ ] Navigate to vault detail page
- [ ] Observe bell icon in header (should show unread count badge if notifications exist)
- [ ] Badge displays "9+" for counts > 9
- [ ] Badge hidden when count is 0
- [ ] Verify subtle pulse animation when count increases (trigger by having another user create activity)
- [ ] Badge positioned top-right of bell icon
- [ ] Orange pill badge with Bitcoin primary color (#F7931A)

### US-011: NotificationPanel dropdown component
- [ ] Login as user
- [ ] Click bell icon in header
- [ ] Verify dropdown panel appears below bell icon
- [ ] Panel shows list of notifications with icon, message, timestamp
- [ ] Unread notifications have left orange accent border
- [ ] Click "Mark all as read" button - verify all notifications marked read
- [ ] Click individual notification - verify it marks as read
- [ ] Verify empty state message when no notifications
- [ ] Panel max height with scroll, shows last 20 notifications
- [ ] Verify glass morphism styling (backdrop-blur, white/5 bg)
- [ ] Click outside panel - verify it closes
- [ ] Press Escape key - verify it closes

### US-012: NotificationPreferences panel for user settings
- [ ] Navigate to /settings page
- [ ] Locate "Notifications" section
- [ ] Toggle "Enable notifications" switch - verify it saves to backend
- [ ] Toggle "Browser push notifications" - verify browser permission request appears
- [ ] Grant browser permission - verify toggle stays on
- [ ] Toggle "Sound notifications" - verify sound preference saved to localStorage
- [ ] Verify sound and push toggles disabled when main notifications toggle is off
- [ ] Verify switches use Bitcoin DeFi styling (gradient orange when checked)
- [ ] Reload page - verify preferences persist

### US-013: Integrate Pusher for browser push notifications
- [ ] Enable browser push notifications in user settings
- [ ] Grant browser notification permission
- [ ] Open second browser tab as different user
- [ ] User B: Add User A to a vault (member.joined event)
- [ ] User A: Verify native browser notification appears (even if tab not focused)
- [ ] Click notification - verify app tab focuses and navigates to vault
- [ ] User B: Mention @UserA in an annotation (mention.created event)
- [ ] User A: Verify browser push notification appears
- [ ] Verify notification has vault name and event details

### US-014: Implement sound notification with global toggle
- [ ] Ensure notification sound file exists at /sounds/notification.mp3
- [ ] Enable sound in notification preferences
- [ ] Trigger a vault event (source added, member joined)
- [ ] Verify notification sound plays when toast appears
- [ ] Disable sound in preferences
- [ ] Trigger another event - verify no sound plays
- [ ] Focus a different tab (app tab in background)
- [ ] Trigger event - verify no sound plays when tab not visible
- [ ] Return to app tab - verify sound plays for new events

### US-015: Integrate notification components into app header
- [ ] Navigate to any authenticated page (/vaults, /settings, etc.)
- [ ] Verify app header visible at top with:
  - SyncScript logo/brand (left)
  - Bell icon with unread badge (right)
  - ConnectionStatus indicator (right, when in vault)
- [ ] Click bell icon - verify NotificationPanel dropdown opens
- [ ] Click outside - verify panel closes
- [ ] Press Escape - verify panel closes
- [ ] Verify header is sticky (stays visible when scrolling)
- [ ] Verify glass morphism styling (backdrop-blur, dark bg)

### US-016: Integrate PresenceIndicator into vault detail page
- [ ] Open vault detail page as User A
- [ ] Open same vault in second tab/window as User B
- [ ] Verify PresenceIndicator shows both users (2 avatars)
- [ ] Verify active members have green dot with animate-ping effect
- [ ] Hover over avatar - verify tooltip shows member name
- [ ] Close User B's tab - wait 60 seconds
- [ ] User A: Verify User B's avatar disappears (marked inactive)
- [ ] Verify max 5 avatars shown, overflow as "+N"
- [ ] Verify responsive: collapses to count-only on mobile screens
- [ ] Verify glass morphism container styling

### US-017: Add notification preferences to user settings page
- [ ] Navigate to /settings page
- [ ] Verify "Notifications" section exists with bell icon header
- [ ] Verify NotificationPreferences component embedded
- [ ] Verify section styling consistent with other settings sections
- [ ] Verify section has description text explaining notification preferences
- [ ] Verify all three toggle switches render properly
- [ ] Test all preference toggles (same as US-012)

### US-018: Handle WebSocket reconnection with state recovery
- [ ] Open vault detail page as User A
- [ ] Note current sources count and active members
- [ ] Simulate network interruption:
  - Open browser DevTools > Network tab
  - Set throttling to "Offline"
  - Wait 5 seconds
  - Verify ConnectionStatus shows red/yellow (disconnected/reconnecting)
- [ ] Have User B add a new source while User A offline
- [ ] User A: Set throttling back to "No throttling"
- [ ] Verify toast appears: "Reconnected - Syncing latest changes..."
- [ ] Verify sources list refreshes with User B's new source
- [ ] Verify ConnectionStatus shows green (connected)
- [ ] Verify User A's presence heartbeat re-sent (User B sees User A online)
- [ ] Verify no duplicate data or stale state

### Expected Behavior
- Real-time updates appear instantly without page refresh
- Toast notifications styled with Bitcoin DeFi aesthetic (dark, orange accents)
- Unread badge shows accurate count, updates in real-time
- Notification panel shows history, mark-as-read functionality works
- Browser push works for high-priority events (member.joined, mention.created)
- Sound plays only when enabled and tab is visible
- Presence indicators show active collaborators with animate-ping effect
- Reconnection recovers state gracefully, syncs latest data, re-establishes presence
- All components keyboard accessible (Escape to close dropdowns)

### Prerequisites
1. Backend WebSocket server running (Daphne or uvicorn)
2. Redis running for channel layer
3. Pusher account configured with valid credentials in .env
4. Notification sound file placed at frontend/public/sounds/notification.mp3
5. Two user accounts and at least one shared vault for testing
6. Environment variables set:
   - NEXT_PUBLIC_WS_URL (WebSocket endpoint)
   - NEXT_PUBLIC_PUSHER_KEY
   - NEXT_PUBLIC_PUSHER_CLUSTER


## PRD7: Frontend Authentication & User Flows - US-022 Integration Test - 2026-02-14

### Complete Auth Flow Testing
- [ ] **Register → Auto-login → Dashboard redirect**
  - Navigate to http://localhost:3000/register
  - Fill in registration form with: name, email, password (min 8 chars), confirm password
  - Verify password strength indicator shows (weak/medium/strong)
  - Click "Create Account" button
  - Verify loading state appears (button shows "Loading...")
  - Verify auto-login on success (user logged in without manual login)
  - Verify redirect to /dashboard (or /vaults if dashboard doesn't exist)
  - Verify success toast appears

- [ ] **Login → ReturnUrl redirect**
  - Logout from current session
  - Navigate to a protected route (e.g., /profile) without being authenticated
  - Verify redirect to /login?returnUrl=/profile
  - Fill in email and password
  - Click "Sign In" button
  - Verify successful login redirects to /profile (the returnUrl)
  - If no returnUrl param, verify redirect goes to /dashboard (or /vaults)

- [ ] **Protected route redirects unauthenticated users**
  - Logout from current session (or use incognito window)
  - Navigate directly to /profile (protected route)
  - Verify immediate redirect to /login?returnUrl=/profile
  - Verify ProtectedRoute shows loading spinner briefly before redirect
  - Verify no flash of protected content

- [ ] **Logout clears state and redirects**
  - Login as a user
  - Navigate to any authenticated page (/vaults, /profile, etc.)
  - Click user avatar/name dropdown in app header (top-right)
  - Click "Logout" option
  - Verify loading state appears ("Logging out...")
  - Verify success toast: "Logged out successfully"
  - Verify redirect to /login page
  - Verify user state cleared (no user data in auth store)
  - Try navigating to /profile - verify redirect to /login (session cleared)

- [ ] **Token refresh happens silently on 401**
  - Login as a user
  - Wait for access token to expire (default: 15 minutes, or modify backend to 1 minute for testing)
  - Make an API call to protected endpoint (e.g., navigate to /profile, which calls /auth/me/)
  - Verify axios interceptor catches 401 response
  - Verify refresh token sent to /auth/refresh/ endpoint
  - Verify new access token received
  - Verify original API call retries automatically with new token
  - Verify page loads successfully without manual re-login
  - Note: If refresh token expires, user should be logged out and redirected to /login

- [ ] **Forgot/Reset password flow completes**
  - Navigate to /login
  - Click "Forgot password?" link
  - Verify redirect to /forgot-password
  - Enter email address
  - Click "Send Reset Link" button
  - Verify success message: "Check your email for reset link"
  - Open email (check backend console or email inbox)
  - Copy reset token from email URL (e.g., http://localhost:3000/reset-password?token=abc123)
  - Navigate to reset password URL with token
  - Enter new password (min 8 chars, verify strength indicator shows)
  - Enter confirm password (must match)
  - Click "Reset Password" button
  - Verify success toast appears
  - Verify redirect to /login after 2 seconds
  - Login with new password - verify success
  - Try login with old password - verify failure

### Expected Behavior
- Registration flow auto-logs in user and redirects to dashboard/vaults
- Login respects returnUrl query parameter for post-auth navigation
- Protected routes redirect unauthenticated users to /login with returnUrl
- Logout clears all auth state and redirects to /login with success toast
- Token refresh handled transparently via axios interceptor on 401 errors
- Forgot/reset password flow completes with email link and password update
- All forms show inline validation errors for invalid input
- All operations show loading states during API calls
- Toast notifications appear for success/error states

### Prerequisites
1. Backend server running: `cd backend && python manage.py runserver`
2. Frontend dev server running: `cd frontend && npm run dev`
3. PostgreSQL and Redis running
4. Email backend configured (console or SMTP)
5. At least one test user account or ability to register new users
6. Browser with DevTools for inspecting network requests and cookies

### Testing Notes
- Use browser DevTools Network tab to inspect API calls and cookie handling
- Check Application tab > Cookies to verify httpOnly cookies are set
- Test in incognito/private window to simulate unauthenticated user
- To test token expiry faster, temporarily reduce ACCESS_TOKEN_LIFETIME in backend settings
- Document any issues found below:

### Issues Found
(Append any bugs, edge cases, or unexpected behavior discovered during testing)


## PRD20: Onboarding & Interactive Tutorial - US-018 OnboardingFlow Orchestrator - 2026-02-14

### OnboardingFlow State Machine Testing
- [ ] **Setup: Create test user without onboarding completed**
  - Register a new user account OR reset existing user's onboarding state in database:
    ```sql
    UPDATE users_user SET onboarding_completed = FALSE, onboarding_step = 'welcome' WHERE id = <user_id>;
    ```
  - Verify backend server running: `cd backend && python manage.py runserver`
  - Verify frontend dev server running: `cd frontend && npm run dev`

- [ ] **Step 1: Welcome Modal**
  - Login as user with incomplete onboarding
  - Verify WelcomeModal appears automatically
  - Verify modal shows: "Welcome to SyncScript, {name}!" with gradient text
  - Verify 3 feature highlights visible (Knowledge Vaults, Real-time collaboration, Annotations)
  - Verify glass morphism styling (backdrop-blur, dark bg, orange accents)
  - Click "Let's get started" button
  - Verify modal transitions to PathSelection step

- [ ] **Step 2: Path Selection**
  - Verify PathSelection component displays 3 path cards:
    - Create your first vault (guided icon with orange gradient)
    - Explore demo vault (explore icon with orange-gold gradient)
    - Skip tutorial (skip icon with gray gradient)
  - Verify cards have hover effects (translate-y, border glow, icon scale)
  - Verify responsive grid (3 cols desktop, 1 col mobile)

- [ ] **Step 3a: Guided Path - Vault Creation**
  - Click "Create your first vault" card
  - Verify GuidedVaultWizard appears at Step 1
  - Verify progress indicator shows "Step 1 of 3" with visual circles
  - Enter vault name (e.g., "My Research Vault")
  - Click "Next" button
  - Verify wizard advances to Step 2
  - Enter source URL (e.g., "https://arxiv.org/abs/1706.03762")
  - Click "Next" button OR "Skip this step" link
  - Verify wizard advances to Step 3
  - Enter collaborator email (e.g., "colleague@example.com") OR click "Skip"
  - Click "Create Vault" button
  - Verify loading state appears
  - Verify vault created successfully
  - Verify onboarding transitions to 'tutorial' step
  - Verify source added if URL was provided
  - Verify collaborator invite sent if email was provided
  - Verify error handling: if creation fails, error message shown, retry allowed

- [ ] **Step 3b: Demo Path - Explore Demo Vault**
  - Reset onboarding state to 'path' step
  - Click "Explore demo vault" card
  - Verify demo vault created (if doesn't exist)
  - Verify redirect to demo vault detail page: `/vaults/{demo_vault_id}`
  - Verify demo vault contains 10 AI research paper sources
  - Verify demo vault contains multiple annotations demonstrating threading
  - Verify onboarding transitions to 'tutorial' step after navigation

- [ ] **Step 3c: Skip Path**
  - Reset onboarding state to 'path' step
  - Click "Skip tutorial" card
  - Verify onboarding marked as completed immediately
  - Verify onboarding_path set to 'skipped'
  - Verify onboarding modal dismisses
  - Verify normal app UI is accessible

- [ ] **Step 4: Interactive Tutorial**
  - Complete guided or demo path to reach 'tutorial' step
  - Verify InteractiveTutorial starts automatically
  - Verify tutorial highlights 7 UI elements in sequence:
    - Vault list sidebar (data-tour="vault-list")
    - Add source button (data-tour="add-source")
    - Invite collaborator button (data-tour="invite-collaborator")
    - Annotations panel (data-tour="annotations")
    - Search functionality (data-tour="search")
    - Settings & preferences (data-tour="settings")
    - Vault header completion (data-tour="vault-header")
  - Verify each tooltip shows title, description, and custom Bitcoin DeFi styling
  - Verify orange gradient buttons (Back, Next, Skip Tutorial)
  - Verify progress dots show current step
  - Click "Next" through all steps
  - Verify scroll behavior brings target elements into view
  - Verify beacon pulse on first step
  - Click "Skip Tutorial" button mid-flow
  - Verify tutorial exits and advances to completion
  - Note: Tutorial step persistence - if user navigates away, does tutorial resume from last step?

- [ ] **Step 5: Completion Celebration**
  - Complete tutorial to reach 'complete' step
  - Verify CompletionCelebration component displays
  - Verify confetti animation launches from both sides of screen
  - Verify confetti uses Bitcoin colors (orange, gold, white)
  - Verify "You're all set!" gradient heading visible
  - Verify 3 quick action cards visible:
    - Add Source (Plus icon)
    - Invite Team (Users icon)
    - Explore Features (BookOpen icon)
  - Verify cards have hover effects
  - Click "Get Started" button
  - Verify onboarding marked as completed
  - Verify redirect to normal app UI
  - Verify onboarding modal no longer appears on page reload

- [ ] **Edge Cases and State Recovery**
  - Login with incomplete onboarding at step 'guided-2'
  - Verify wizard opens at Step 2 (resumes from saved state)
  - Verify saved data (vaultName) is pre-filled from onboarding.data
  - Navigate away from onboarding (close tab, logout)
  - Login again - verify onboarding resumes from last saved step
  - Verify onboarding only shows for users with `onboarding_completed === false`
  - Complete user's onboarding, verify modal never appears again

- [ ] **Mobile Responsiveness**
  - Test onboarding flow on mobile viewport (< 768px)
  - Verify all modals are full-screen on mobile
  - Verify button sizes are touch-friendly (min 44px tap targets)
  - Verify wizard steps stack vertically on mobile
  - Verify PathSelection grid shows 1 column
  - Verify CompletionCelebration action cards stack vertically

### Expected Behavior
- OnboardingFlow orchestrates entire onboarding state machine
- Welcome → Path → (Guided/Demo/Skip) → Tutorial → Completion flow works seamlessly
- Guided path creates vault with optional source and collaborator
- Demo path creates/fetches demo vault and redirects to it
- Skip path immediately completes onboarding
- Tutorial highlights key UI elements with custom Bitcoin DeFi styling
- Completion shows confetti celebration and quick actions
- Onboarding state persists and resumes from last step on return
- Completed onboarding never shows again
- All components mobile-responsive

### Prerequisites
1. Backend server running with all onboarding endpoints functional
2. Frontend dev server running with all components built
3. PostgreSQL database with User model onboarding fields
4. Test user account with onboarding_completed = false
5. Demo vault fixture data available at backend/apps/users/fixtures/demo_vault.json
6. Browser DevTools for inspecting network requests and state changes
7. Mobile device or responsive design mode for mobile testing

### Issues Found
(Append any bugs, edge cases, or unexpected behavior discovered during testing)


---

## US-019: Integrate onboarding into app layout - 2026-02-14

### Setup
- [ ] Start backend server: `cd backend && python manage.py runserver`
- [ ] Start frontend dev server: `cd frontend && npm run dev`
- [ ] Create test user with onboarding incomplete:
  ```python
  # Django shell: python manage.py shell
  from apps.users.models import User
  user = User.objects.create_user(
    username='onboarding_test',
    email='onboarding@test.com',
    password='testpass123',
    onboarding_completed=False,
    onboarding_step=None
  )
  ```

### Verification Steps

- [ ] **OnboardingProvider Integration**
  - Open browser DevTools Network tab
  - Login with test user (onboarding_completed=False)
  - Verify GET request to `/api/v1/users/me/onboarding/` is made after login
  - Verify onboarding state is fetched successfully
  - Check React DevTools - verify OnboardingProvider context is available

- [ ] **OnboardingFlow Renders in App Layout**
  - After login, verify onboarding modal appears automatically
  - Verify main app content (AppHeader, Sidebar) is still visible but dimmed behind modal
  - Verify onboarding modal overlays the main content
  - Verify z-index stacking is correct (onboarding on top)

- [ ] **Onboarding Only Shows for Incomplete Onboarding**
  - Complete onboarding flow for test user
  - Verify onboarding modal disappears after completion
  - Logout and login again
  - Verify onboarding modal does NOT appear (onboarding_completed=true)
  - Navigate to different pages in app
  - Verify onboarding never reappears once completed

- [ ] **Onboarding Only Shows for Authenticated Users**
  - Logout (return to unauthenticated state)
  - Verify no onboarding modal appears on marketing pages
  - Navigate to /login page
  - Verify no onboarding modal appears (not in app layout)
  - Login with user that has incomplete onboarding
  - Verify onboarding appears immediately after reaching authenticated app layout

- [ ] **Layout Structure Verification**
  - Inspect DOM structure in DevTools
  - Verify OnboardingProvider wraps all children in root layout
  - Verify OnboardingFlow is rendered as sibling to main content in app layout
  - Verify main app content structure is not affected by onboarding integration
  - Verify Toaster component still renders correctly

### Expected Behavior
- OnboardingProvider added to root layout, wrapping children inside AuthProvider
- OnboardingFlow added to authenticated app layout (app/(app)/layout.tsx)
- Onboarding modal automatically appears for users with onboarding_completed=false
- Main app content visible but dimmed/overlayed by onboarding modal
- Onboarding only shows for authenticated users in app layout
- Onboarding never shows for users with completed onboarding
- App providers hierarchy: ThemeProvider > QueryProvider > AuthProvider > OnboardingProvider
- No breaking changes to existing layout or functionality

### Prerequisites
1. Backend server running on http://localhost:8000
2. Frontend dev server running on http://localhost:3000
3. Test user with onboarding_completed=false in database
4. React DevTools browser extension (for context inspection)
5. All previous US-001 through US-018 tasks completed

### Issues Found
(Append any bugs, edge cases, or unexpected behavior discovered during testing)


---

## PRD15: AI Research Assistant - US-014 Integration - 2026-02-14

### AISummaryCard Integration in Source Detail Page
- [ ] Start backend server: `cd backend && python manage.py runserver`
- [ ] Start frontend dev server: `cd frontend && npm run dev`
- [ ] Login with valid user account
- [ ] Navigate to a vault and open any source detail page
- [ ] Verify AISummaryCard component renders above PDF viewer in left column (70% width)

### Generate Summary Flow
- [ ] Click "Generate Summary" button on source without ai_summary
- [ ] Verify AILoadingSkeleton appears with "Analyzing..." text
- [ ] Verify skeleton shows pulsing orange accents
- [ ] Wait for Claude API response (10-30 seconds depending on source length)
- [ ] Verify AISummaryCard appears with summary content:
  - Abstract section
  - Key Findings (list)
  - Methodology section
  - Limitations section
  - Keywords (tag pills)
  - Language indicator (if non-English)
  - Quality flags (if present: "preprint", "not peer-reviewed", etc.)
  - Generated timestamp
- [ ] Verify success toast appears: "Summary generated successfully"
- [ ] Verify "Regenerate" button now visible in card header

### Regenerate Summary Flow
- [ ] Click "Regenerate" button on source with existing summary
- [ ] Verify loading skeleton replaces card during regeneration
- [ ] Verify new summary appears after completion
- [ ] Verify updated timestamp reflects regeneration time
- [ ] Verify success toast appears

### Rate Limit Error Handling
- [ ] Trigger 20+ AI requests in one day to hit rate limit
- [ ] Click "Generate Summary" button after limit exceeded
- [ ] Verify error toast appears with message: "AI request limit reached. Resets at {time}"
- [ ] Verify summary does NOT generate
- [ ] Verify cached summary still visible (if exists)

### Error Handling (General)
- [ ] Disconnect internet or stop backend server
- [ ] Click "Generate Summary" button
- [ ] Verify error toast appears: "Failed to generate summary"
- [ ] Verify card state resets (button re-enabled)
- [ ] Reconnect and verify retry works

### UI/UX Verification
- [ ] Verify AISummaryCard follows Bitcoin DeFi design:
  - Glass morphism background (backdrop-blur-lg)
  - Orange gradient accents on buttons
  - Dark theme (#0F1115 surface color)
  - Border with white/10 opacity
- [ ] Verify expand/collapse animations smooth
- [ ] Verify card is responsive on mobile viewports
- [ ] Verify quality flags display as warning badges (orange/yellow)
- [ ] Verify language indicator shows for non-English sources

### Expected Behavior
- AISummaryCard integrates seamlessly into source detail page
- Generate/Regenerate buttons trigger AI summarization
- Loading skeleton provides feedback during API processing
- Rate limit errors handled gracefully with informative messages
- Success/error toasts appear for all user actions
- Card styling matches Bitcoin DeFi aesthetic
- Auto-refetch sources after summary generation to update cache

### Prerequisites
1. Backend server running with AI endpoints functional
2. Frontend dev server running
3. Valid Anthropic API key configured in backend .env
4. Test user account with AI usage quota available
5. Vault with sources (PDF or URL) for testing
6. Browser DevTools for inspecting network requests

### Issues Found
(Append any bugs, edge cases, or unexpected behavior discovered during testing)



---

## PRD20: Onboarding & Interactive Tutorial - US-020 Resume Onboarding - 2026-02-14

### Resume Onboarding Flow
- [ ] Prerequisites:
  - Backend running: `cd backend && python manage.py runserver`
  - Frontend running: `cd frontend && npm run dev`
  - Test user with `onboarding_completed=false` and a saved step
- [ ] Update test user's onboarding state via Django admin or shell:
  ```python
  from apps.users.models import User
  user = User.objects.get(username='testuser')
  user.onboarding_step = 'guided-2'  # Or 'path', 'tutorial', etc.
  user.onboarding_completed = False
  user.onboarding_data = {'vaultName': 'Test Vault'}
  user.save()
  ```

### Resume Toast Verification
- [ ] Login to app (or reload page while logged in)
- [ ] Verify "Welcome back!" toast appears in bottom-right corner
- [ ] Verify toast description shows context-aware message:
  - `step='path'`: "Choose your onboarding path to continue"
  - `step='guided-1/2/3'`: "Continue creating your vault"
  - `step='demo'`: "Loading demo vault..."
  - `step='tutorial'`: "Resume your interactive tutorial"
  - `step='complete'`: "Almost done! Complete your onboarding"
- [ ] Verify toast uses Bitcoin DeFi styling (orange border, dark background)
- [ ] Verify toast auto-dismisses after 5-10 seconds

### Resume State Verification
- [ ] Verify onboarding flow resumes at correct step:
  - `step='path'` → PathSelection component visible
  - `step='guided-1'` → GuidedVaultWizard at Step 1 (vault name)
  - `step='guided-2'` → GuidedVaultWizard at Step 2 (add source)
  - `step='guided-3'` → GuidedVaultWizard at Step 3 (invite collaborator)
  - `step='tutorial'` → InteractiveTutorial starts from beginning
  - `step='complete'` → CompletionCelebration with confetti
- [ ] For `step='guided-2'`: Verify saved vaultName from onboarding_data pre-fills input
- [ ] For `step='tutorial'`: Verify tutorial starts from first step (not mid-tutorial)

### Fresh Start (No Resume Toast)
- [ ] Set user's onboarding_step to `null` or `'welcome'` in database
- [ ] Login or reload page
- [ ] Verify NO toast appears (user is starting fresh)
- [ ] Verify WelcomeModal appears as first step

### Completed Onboarding (No Toast)
- [ ] Set user's onboarding_completed to `True` in database
- [ ] Login or reload page
- [ ] Verify NO toast appears
- [ ] Verify NO onboarding flow renders (user bypasses onboarding)

### Toast Only Shows Once
- [ ] Set user's onboarding_step to 'guided-2'
- [ ] Login to app → verify toast appears
- [ ] Without reloading, navigate to different page within app
- [ ] Verify toast does NOT appear again during same session
- [ ] Reload page → verify toast appears again (new session)

### Mobile Responsiveness
- [ ] Test on mobile viewport (< 768px width)
- [ ] Verify toast appears in bottom-right corner
- [ ] Verify toast text is readable (not truncated)
- [ ] Verify toast auto-dismisses correctly on mobile

### Expected Behavior
- OnboardingProvider fetches onboarding state on app load
- OnboardingFlow reads step from provider context
- If `completed=false` and `step` exists and `step != 'welcome'`:
  - Show "Welcome back!" toast with context-specific message
  - Resume onboarding flow at saved step
  - Toast only shows once per session (useRef prevents duplicates)
- If step is 'welcome' or null: No toast (fresh start)
- If completed=true: No toast, no onboarding flow
- GuidedVaultWizard loads saved data from onboarding.data field
- Tutorial starts from beginning (simpler than tracking sub-steps)

### Prerequisites
1. Backend server running
2. Frontend dev server running
3. Test user account with adjustable onboarding state
4. Django admin or shell access to modify user onboarding fields
5. Browser DevTools for inspecting state and network requests

### Issues Found
(Append any bugs, edge cases, or unexpected behavior discovered during testing)


## US-021: Add restart tutorial to settings - 2026-02-14

### What to Verify
- Onboarding section appears in Settings page
- Restart Tutorial button shows confirmation dialog
- Tutorial restarts correctly after confirmation
- Loading states work during restart
- Error handling works if restart fails

### Test Steps
1. **Navigate to Settings**
   - [ ] Login to application
   - [ ] Go to Settings page (/settings)
   - [ ] Verify "Onboarding" section appears with GraduationCap icon
   - [ ] Section should be positioned before "Connected Accounts"

2. **Restart Tutorial Button**
   - [ ] Verify "Restart Tutorial" button is visible
   - [ ] Button shows RotateCcw icon and "Restart" text
   - [ ] Button has orange accent styling (border-[#F7931A])

3. **Confirmation Dialog**
   - [ ] Click "Restart Tutorial" button
   - [ ] Confirmation dialog appears with:
     - Title: "Restart Tutorial?"
     - Description explaining the tutorial will restart
     - "Cancel" button
     - "Restart Tutorial" gradient button
   - [ ] Click "Cancel" - dialog closes without action
   - [ ] Click "Restart Tutorial" button again

4. **Restart Flow**
   - [ ] Click "Restart Tutorial" in confirmation dialog
   - [ ] Button shows "Restarting..." loading text
   - [ ] Success toast appears: "Tutorial Restarted"
   - [ ] Dialog closes automatically
   - [ ] Page refreshes (router.refresh())
   - [ ] Interactive tutorial begins automatically
   - [ ] Tutorial shows first step with pulsing beacon

5. **Error Handling**
   - [ ] Simulate API error (disconnect backend or invalid token)
   - [ ] Click "Restart Tutorial" button
   - [ ] Error toast appears with helpful message
   - [ ] Dialog remains open for retry
   - [ ] Button returns to "Restart Tutorial" text

6. **Backend State**
   - [ ] After restart, verify in Django admin or shell:
     - `onboarding_completed` = False
     - `onboarding_step` = 'tutorial'
     - `onboarding_data` = {} (reset)

### Expected Behavior
- Settings page includes new Onboarding section
- Restart button triggers confirmation before action
- Confirmation dialog uses Bitcoin DeFi design system
- Tutorial restarts successfully and shows immediately
- Backend state is updated correctly
- User can cancel restart without side effects
- Loading and error states provide clear feedback

### Prerequisites
1. Backend server running: `cd backend && python manage.py runserver`
2. Frontend dev server running: `cd frontend && npm run dev`
3. User account with completed onboarding (onboarding_completed=true)
4. Browser DevTools for network inspection

### Issues Found
(Append any bugs, edge cases, or unexpected behavior discovered during testing)



---

## PRD15: AI Research Assistant - US-017 Integration - 2026-02-14

### ResearchInsightsPanel Integration in Vault Dashboard

#### Prerequisites
- [ ] Backend server running: `cd backend && python manage.py runserver`
- [ ] Frontend dev server running: `cd frontend && npm run dev`
- [ ] Valid Anthropic API key configured in backend .env
- [ ] Test user account with AI usage quota available
- [ ] Vault with at least 2 sources for insights generation

#### Insights Tab Visibility
- [ ] Login with valid user account
- [ ] Navigate to a vault detail page
- [ ] Verify "Insights" tab is visible in the tab list (between Sources and Members)
- [ ] Verify tab has orange underline indicator when active
- [ ] Click "Insights" tab
- [ ] Verify tab content area switches to show insights panel

#### Generate Insights Flow (First Time)
- [ ] Navigate to vault with 2+ sources but no insights generated yet
- [ ] Click "Insights" tab
- [ ] Verify ResearchInsightsPanel shows empty state:
  - "Discover Research Insights" heading
  - Description mentioning number of sources
  - "Generate Insights" gradient button
- [ ] Click "Generate Insights" button
- [ ] Verify AILoadingSkeleton appears with "Discovering insights..." text
- [ ] Verify skeleton shows pulsing orange accents and themed animations
- [ ] Wait for Claude API response (20-60 seconds depending on vault size)
- [ ] Verify ResearchInsightsPanel appears with insights content:
  - Header: "Research Insights" with gradient text
  - Last updated timestamp
  - "Refresh" button in header
  - Common Themes section (collapsible, expanded by default)
  - Research Gaps section (collapsible)
  - Cross-References section (collapsible)
  - Suggested Searches section (collapsible)
- [ ] Verify success toast appears: "Insights generated successfully"

#### Insights Content Verification
- [ ] Expand all collapsible sections
- [ ] Verify Themes section shows weighted tag cloud:
  - Larger font size for higher weight themes
  - Orange gradient coloring
  - Source count displayed for each theme
- [ ] Verify Research Gaps section shows bulleted list of identified gaps
- [ ] Verify Cross-References section shows connections between sources
- [ ] Verify Suggested Searches section shows clickable search suggestions

#### Refresh Insights Flow
- [ ] Click "Refresh" button in panel header
- [ ] Verify AILoadingSkeleton appears during refresh
- [ ] Verify new insights appear after completion
- [ ] Verify "Last updated" timestamp reflects refresh time
- [ ] Verify success toast appears

#### Rate Limit Error Handling
- [ ] Trigger 20+ AI requests in one day to hit rate limit
- [ ] Click "Generate Insights" or "Refresh" button after limit exceeded
- [ ] Verify cached insights badge appears above panel:
  - Orange background with border
  - "Using cached data" message
  - Explanation that limit was reached
- [ ] Verify cached insights remain visible (not replaced)
- [ ] Verify error toast appears: "Rate limit reached. Using cached insights."

#### Error Handling (General)
- [ ] Disconnect internet or stop backend server
- [ ] Click "Generate Insights" button
- [ ] Verify error toast appears: "Failed to generate insights"
- [ ] Verify panel state resets (button re-enabled)
- [ ] Reconnect and verify retry works

#### Empty State (< 2 Sources)
- [ ] Navigate to vault with 0 or 1 source
- [ ] Click "Insights" tab
- [ ] Verify empty state appears:
  - AlertCircle icon with orange tint
  - "Not Enough Sources" heading
  - Description explaining minimum 2 sources required
- [ ] Verify no "Generate Insights" button visible
- [ ] Add second source to vault
- [ ] Return to Insights tab
- [ ] Verify "Generate Insights" button now visible

#### UI/UX Verification
- [ ] Verify ResearchInsightsPanel follows Bitcoin DeFi design:
  - Glass morphism background (backdrop-blur-lg)
  - Orange gradient accents on buttons and headers
  - Dark theme (#0F1115 surface color)
  - Border with white/10 opacity
- [ ] Verify expand/collapse animations smooth
- [ ] Verify panel is responsive on mobile viewports
- [ ] Verify collapsible sections open/close smoothly
- [ ] Verify last updated timestamp formats correctly

#### Cache Behavior
- [ ] Generate insights for a vault
- [ ] Add a new source to the vault
- [ ] Return to Insights tab
- [ ] Verify insights are still visible (cache not invalidated yet)
- [ ] Click "Refresh" to regenerate with new source included

### Expected Behavior
- Insights tab integrates seamlessly into vault dashboard
- Generate/Refresh buttons trigger AI insights generation
- Loading skeleton provides feedback during API processing
- Rate limit errors handled gracefully with cached data fallback
- Success/error toasts appear for all user actions
- Panel styling matches Bitcoin DeFi aesthetic
- Empty state guides users when insufficient sources
- Collapsible sections improve UX for dense insight data

### Issues Found
(Append any bugs, edge cases, or unexpected behavior discovered during testing)


## US-023: Demo Vault Deletion Prompt - 2026-02-14

### Prerequisites
- [ ] Backend server running: `cd backend && python manage.py runserver`
- [ ] Frontend server running: `cd frontend && npm run dev`
- [ ] User account with demo vault created
- [ ] User is logged in

### Test Demo Vault Detection
- [ ] Navigate to the demo vault ("AI Research Papers 2025")
- [ ] Open vault Settings tab
- [ ] Scroll to Danger Zone section
- [ ] Click "Delete Vault" button
- [ ] Verify deletion dialog opens

### Verify Custom Demo Vault Message
- [ ] In the deletion dialog, verify there is an orange warning box above the red warning box
- [ ] Verify the orange box has a 📚 emoji and "This is your demo vault" heading
- [ ] Verify the message reads: "You can recreate the demo vault anytime from Settings → Onboarding → Recreate Demo Vault. All the original demo content will be restored."
- [ ] Verify the orange box uses Bitcoin DeFi styling:
  - Background: `bg-[#F7931A]/10`
  - Border: `border-[#F7931A]/30`
  - Text color: `text-[#F7931A]`

### Verify Standard Deletion Flow Still Works
- [ ] Type the vault name "AI Research Papers 2025" in the confirmation input
- [ ] Verify the green checkmark appears when name matches
- [ ] Click "Delete Vault" button
- [ ] Verify vault is deleted successfully
- [ ] Verify redirect to /vaults page
- [ ] Verify success toast appears

### Test Non-Demo Vault Deletion
- [ ] Create a regular vault (not named "AI Research Papers 2025")
- [ ] Navigate to vault Settings tab
- [ ] Click "Delete Vault" in Danger Zone
- [ ] Verify deletion dialog DOES NOT show the orange demo vault message
- [ ] Verify only the red warning box appears
- [ ] Cancel the dialog

### Edge Case: Demo Vault Recreated with Different Name
- [ ] If user renames demo vault to something else, it should NOT show the custom message
- [ ] The demo vault detection is based on exact name match: "AI Research Papers 2025"

### Expected Behavior
- Demo vault deletion shows informative message about recreation option
- Standard deletion flow unchanged (confirmation input, validation)
- Non-demo vaults do not show the custom message
- Orange warning box appears above red warning box
- Styling matches Bitcoin DeFi aesthetic
- Dialog provides clear path to recreate demo vault from settings

### Issues Found
(Append any bugs, edge cases, or unexpected behavior discovered during testing)

## US-021: Integrate AskAI chat into vault sidebar - 2026-02-14
- [ ] Navigate to a vault detail page
- [ ] Verify "Ask AI" collapsible section appears in right sidebar
- [ ] Click "Ask AI" header to expand the section
- [ ] Verify chat interface appears with ChatHistory sidebar and AskAIChat area
- [ ] Click "New Chat" button in ChatHistory sidebar
- [ ] Type a question about vault sources and send it
- [ ] Verify loading skeleton appears while AI responds
- [ ] Verify AI response appears with citations (if applicable)
- [ ] Verify conversation appears in ChatHistory sidebar with preview
- [ ] Click on conversation in history to verify it loads
- [ ] Try creating multiple conversations and switching between them
- [ ] Send enough messages to hit rate limit (20 requests)
- [ ] Verify rate limit error toast appears with retry time
- [ ] Verify collapsible section can be collapsed/expanded without losing state

### Expected Behavior:
- Chat sidebar integrates seamlessly with vault layout
- Conversations persist across page refreshes
- Citations are clickable and show source excerpts
- Rate limit handling is graceful with clear error messages
- Loading states prevent duplicate requests
- UI follows Bitcoin DeFi design system

### Issues Found:
(Document any bugs or UX issues discovered during testing)

## US-024: Integrate TokenUsageDisplay into user settings - 2026-02-14
- [ ] Navigate to the Settings page (/settings)
- [ ] Verify "AI Usage" section appears at the top of the settings page
- [ ] Verify the section has Sparkles icon and proper heading
- [ ] Verify loading spinner appears while usage data is fetched
- [ ] Verify TokenUsageDisplay component renders with usage statistics:
  - [ ] Progress bar showing requests used / limit
  - [ ] "Resets in X hours Y minutes" countdown timer
  - [ ] Token count formatted with locale (e.g., "12,345" not "12345")
- [ ] Send some AI requests to increase usage (use source summarize or vault insights)
- [ ] Refresh settings page and verify usage stats update correctly
- [ ] Send enough requests to exceed 80% threshold (17+ requests)
- [ ] Verify warning state appears:
  - [ ] Progress bar changes to orange-red gradient
  - [ ] "High Usage" badge displayed in header
  - [ ] Warning message showing percentage used
- [ ] Wait for reset time and verify usage resets to 0

### Expected Behavior:
- AI Usage section positioned at top of settings for prominence
- Loading state prevents empty content flash
- Usage stats accurate and update in real-time
- Warning threshold (80%) provides advance notice before hitting limit
- Countdown timer shows accurate time until midnight UTC reset
- Error handling graceful if API call fails
- UI follows Bitcoin DeFi design system (glass card, orange accents)

### Issues Found:
(Document any bugs or UX issues discovered during testing)
