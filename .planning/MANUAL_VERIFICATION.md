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

