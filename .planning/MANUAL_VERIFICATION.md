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
