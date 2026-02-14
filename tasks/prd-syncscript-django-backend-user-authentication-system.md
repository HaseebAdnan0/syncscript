# PRD: SyncScript Django Backend User Authentication System

## 1. Overview

### 1.1 Purpose
Implement a secure, production-ready authentication system for SyncScript's collaborative research platform using Django REST Framework with JWT tokens, custom user profiles, and comprehensive security controls.

### 1.2 Success Metrics
- All auth endpoints respond within 200ms (p95)
- Rate limiting prevents brute force attacks (5 attempts/minute)
- Zero token leakage via proper httpOnly cookie handling
- Email verification completion rate >70%
- Password reset flow completion rate >60%

### 1.3 Target Users
- Researchers registering for knowledge vault access
- Returning users authenticating to existing accounts
- Users managing profile information and recovering accounts

---

## 2. User Stories

### US1: User Registration with Email Verification
**As a** new researcher  
**I want to** register an account with email verification  
**So that** I can securely access SyncScript's knowledge vaults

**Acceptance Criteria:**
- User submits email, password, optional profile fields (bio, institution)
- System validates email uniqueness and password strength
- Verification email sent via Django's email backend
- User clicks verification link to activate account
- Unverified users cannot access protected endpoints
- Registration rate-limited to 5 attempts/minute per IP

**Dependencies:** PostgreSQL user table, Django email configuration, Redis for rate limiting

---

### US2: JWT-Based Login and Token Management
**As a** registered user  
**I want to** login with email/password and receive JWT tokens  
**So that** I can authenticate subsequent API requests securely

**Acceptance Criteria:**
- Login endpoint accepts email + password
- Returns access token (15min expiry) + refresh token (7 day expiry)
- Access token stored in response body for mobile clients
- Refresh token optionally stored in httpOnly cookie
- Failed login attempts rate-limited (5/minute)
- Tokens include user ID and email claims
- Login rate-limited to 5 attempts/minute per IP

**Dependencies:** djangorestframework-simplejwt, Redis for rate limiting

---

### US3: Token Refresh and Logout
**As an** authenticated user  
**I want to** refresh my access token without re-login and logout securely  
**So that** my session remains valid and I can terminate sessions cleanly

**Acceptance Criteria:**
- Refresh endpoint accepts refresh token, returns new access token
- Blacklist tracks revoked refresh tokens (djangorestframework-simplejwt)
- Logout endpoint blacklists current refresh token
- Blacklist stored in database (SimpleJWT default) with expiry cleanup
- Refresh token rotation: old token invalidated when new one issued

**Dependencies:** SimpleJWT token blacklist app, periodic cleanup task

---

### US4: Password Reset Flow
**As a** user who forgot their password  
**I want to** request a password reset via email  
**So that** I can regain access to my account

**Acceptance Criteria:**
- "Forgot Password" endpoint accepts email address
- System generates secure reset token using Django's `PasswordResetTokenGenerator`
- Email sent with reset link containing token and user ID (base64 encoded)
- Reset link valid for 1 hour
- "Reset Password" endpoint validates token and updates password
- Rate-limited to 3 reset requests per email per hour
- No user enumeration (always return success message)

**Dependencies:** Django email backend, PasswordResetTokenGenerator

---

### US5: User Profile Management
**As an** authenticated user  
**I want to** view and update my profile (avatar URL, bio, institution)  
**So that** I can personalize my researcher identity

**Acceptance Criteria:**
- GET `/api/v1/users/profile/` returns own profile
- PATCH `/api/v1/users/profile/` updates avatar_url, bio, institution
- Cannot update email or password via this endpoint (separate flows)
- Avatar URL validated as proper URL format
- Bio limited to 500 characters
- Institution limited to 200 characters

**Dependencies:** Custom User model with profile fields

---

## 3. Technical Requirements

### 3.1 Data Model

#### Custom User Model (`apps/users/models.py`)
```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['email_verified']),
        ]
```

#### Email Verification Token Model
```python
class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'email_verification_tokens'
```

### 3.2 API Endpoints

| Endpoint | Method | Auth Required | Rate Limit | Description |
|----------|--------|---------------|------------|-------------|
| `/api/v1/auth/register/` | POST | No | 5/min | Create account + send verification email |
| `/api/v1/auth/verify-email/` | POST | No | 10/min | Verify email with token |
| `/api/v1/auth/login/` | POST | No | 5/min | Login with email/password |
| `/api/v1/auth/logout/` | POST | Yes | - | Blacklist refresh token |
| `/api/v1/auth/refresh/` | POST | No | 20/min | Get new access token |
| `/api/v1/auth/password-reset/` | POST | No | 3/hour per email | Request password reset email |
| `/api/v1/auth/password-reset-confirm/` | POST | No | 10/min | Confirm password reset with token |
| `/api/v1/users/profile/` | GET | Yes | - | Get own profile |
| `/api/v1/users/profile/` | PATCH | Yes | - | Update own profile |

### 3.3 Request/Response Schemas

#### Registration Request
```json
{
  "email": "researcher@university.edu",
  "password": "SecurePass123!",
  "username": "jdoe",
  "bio": "PhD candidate in Quantum Computing",
  "institution": "MIT"
}
```

#### Registration Response
```json
{
  "id": "uuid",
  "email": "researcher@university.edu",
  "username": "jdoe",
  "email_verified": false,
  "message": "Verification email sent to researcher@university.edu"
}
```

#### Login Response
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "uuid",
    "email": "researcher@university.edu",
    "username": "jdoe",
    "avatar_url": "https://example.com/avatar.jpg",
    "email_verified": true
  }
}
```

#### Profile Response
```json
{
  "id": "uuid",
  "email": "researcher@university.edu",
  "username": "jdoe",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "PhD candidate in Quantum Computing",
  "institution": "MIT",
  "email_verified": true,
  "created_at": "2026-02-14T10:00:00Z"
}
```

### 3.4 Technology Stack

**Core:**
- Django 6.x
- Django REST Framework 3.16+
- PostgreSQL (user storage)
- Redis (rate limiting, token blacklist cache)

**Packages:**
- `djangorestframework-simplejwt==5.5.1` (JWT tokens)
- `django-ratelimit==4.1.0` (endpoint throttling)
- `django-redis==5.4.0` (Redis cache backend)

**Configuration:**
- Access token expiry: 15 minutes
- Refresh token expiry: 7 days
- Rate limit backend: Redis
- Email backend: Django's SMTP backend (configurable via settings)

### 3.5 Security Requirements

1. **Token Rotation & Blacklisting:**
   - Enable `ROTATE_REFRESH_TOKENS = True` in SimpleJWT settings
   - Enable `BLACKLIST_AFTER_ROTATION = True`
   - Store blacklist in database via `rest_framework_simplejwt.token_blacklist` app

2. **Rate Limiting (django-ratelimit):**
   - Registration: 5 attempts/minute per IP
   - Login: 5 attempts/minute per IP
   - Password reset request: 3 attempts/hour per email
   - Token refresh: 20 attempts/minute per IP

3. **Password Requirements:**
   - Minimum 8 characters
   - At least one uppercase, one lowercase, one digit
   - Use Django's built-in password validators

4. **Email Verification:**
   - Tokens expire after 24 hours
   - Cryptographically secure token generation (secrets.token_urlsafe)

5. **Password Reset:**
   - Tokens expire after 1 hour
   - Use Django's `PasswordResetTokenGenerator`
   - No user enumeration (always return success)

### 3.6 File Structure

```
backend/apps/users/
├── migrations/
│   └── 0001_initial.py
├── __init__.py
├── admin.py
├── apps.py
├── models.py              # User, EmailVerificationToken
├── serializers.py         # UserSerializer, RegisterSerializer, etc.
├── views.py               # Auth views (register, login, etc.)
├── urls.py                # URL routing
├── permissions.py         # Custom permissions (IsEmailVerified, etc.)
├── tokens.py              # Email verification token logic
├── emails.py              # Email template rendering
└── tests/
    ├── test_models.py
    ├── test_auth.py
    ├── test_profile.py
    └── test_rate_limiting.py
```

---

## 4. Implementation Plan

### Phase 1: Models & Migrations (Day 1)
**Tasks:**
- Create custom User model extending AbstractUser
- Add EmailVerificationToken model
- Generate and apply initial migration
- Update `settings.py` with `AUTH_USER_MODEL = 'users.User'`
- Configure SimpleJWT settings (token expiry, rotation, blacklist)

**Files:**
- `apps/users/models.py`
- `apps/users/migrations/0001_initial.py`
- `config/settings.py`

**Verification:**
- [ ] `python manage.py makemigrations users`
- [ ] `python manage.py migrate`
- [ ] Create test user via Django shell

---

### Phase 2: Serializers & Validators (Day 1-2)
**Tasks:**
- Create `RegisterSerializer` with password validation
- Create `UserSerializer` for profile responses
- Create `ProfileUpdateSerializer` for PATCH operations
- Create `PasswordResetRequestSerializer`
- Create `PasswordResetConfirmSerializer`
- Add custom validators for bio length, avatar URL format

**Files:**
- `apps/users/serializers.py`

**Verification:**
- [ ] Unit tests for serializer validation rules
- [ ] Test password strength validation

---

### Phase 3: Email Verification System (Day 2)
**Tasks:**
- Implement token generation in `tokens.py`
- Create verification email template (HTML + plain text)
- Create `send_verification_email()` helper in `emails.py`
- Create `VerifyEmailView` (POST endpoint)
- Configure Django email backend in settings

**Files:**
- `apps/users/tokens.py`
- `apps/users/emails.py`
- `apps/users/views.py` (VerifyEmailView)
- `templates/emails/verify_email.html`
- `config/settings.py` (EMAIL_* settings)

**Verification:**
- [ ] Send test verification email
- [ ] Verify token validation works
- [ ] Test expired token rejection

---

### Phase 4: Registration & Login Views (Day 2-3)
**Tasks:**
- Create `RegisterView` (POST endpoint)
- Create `LoginView` (POST endpoint, override SimpleJWT)
- Create `LogoutView` (POST endpoint with token blacklist)
- Create `RefreshTokenView` (override SimpleJWT default)
- Apply rate limiting decorators

**Files:**
- `apps/users/views.py`

**Verification:**
- [ ] Test registration flow end-to-end
- [ ] Test login returns valid JWT tokens
- [ ] Test logout blacklists refresh token
- [ ] Test rate limiting triggers on 6th attempt

---

### Phase 5: Password Reset Flow (Day 3)
**Tasks:**
- Create `PasswordResetRequestView` (POST endpoint)
- Create `PasswordResetConfirmView` (POST endpoint)
- Implement token generation using Django's `PasswordResetTokenGenerator`
- Create password reset email template
- Add rate limiting (3 requests/hour per email)

**Files:**
- `apps/users/views.py`
- `apps/users/emails.py`
- `templates/emails/password_reset.html`

**Verification:**
- [ ] Request password reset, receive email
- [ ] Confirm reset with valid token
- [ ] Test expired token rejection
- [ ] Test rate limiting on reset requests

---

### Phase 6: Profile Management (Day 3)
**Tasks:**
- Create `ProfileView` (GET/PATCH endpoint)
- Apply `IsAuthenticated` permission
- Implement partial update logic for avatar_url, bio, institution
- Prevent email/password updates via this endpoint

**Files:**
- `apps/users/views.py`

**Verification:**
- [ ] GET returns user's own profile
- [ ] PATCH updates allowed fields
- [ ] PATCH rejects email/password changes
- [ ] Unauthorized users get 401

---

### Phase 7: URL Routing (Day 3-4)
**Tasks:**
- Create `apps/users/urls.py`
- Register auth endpoints with proper naming
- Include users URLs in `config/urls.py`

**Files:**
- `apps/users/urls.py`
- `config/urls.py`

**Verification:**
- [ ] All endpoints accessible at correct paths
- [ ] OPTIONS requests return allowed methods

---

### Phase 8: Rate Limiting Configuration (Day 4)
**Tasks:**
- Configure Redis cache backend in settings
- Apply `@ratelimit` decorators to auth views
- Test rate limit storage in Redis
- Create custom rate limit response (429 status)

**Files:**
- `config/settings.py` (CACHES config)
- `apps/users/views.py` (decorators)

**Verification:**
- [ ] Redis connection established
- [ ] Rate limits enforced on login/register
- [ ] 429 response returned on limit exceeded
- [ ] Limits reset after time window

---

### Phase 9: Testing Suite (Day 4-5)
**Tasks:**
- Write model tests (User creation, email uniqueness)
- Write serializer tests (validation rules)
- Write auth flow tests (register → verify → login → refresh → logout)
- Write rate limiting tests (mock Redis)
- Write password reset tests
- Write profile CRUD tests
- Achieve >90% code coverage

**Files:**
- `apps/users/tests/test_models.py`
- `apps/users/tests/test_serializers.py`
- `apps/users/tests/test_auth.py`
- `apps/users/tests/test_profile.py`
- `apps/users/tests/test_rate_limiting.py`

**Verification:**
- [ ] `python manage.py test apps.users`
- [ ] All tests pass
- [ ] Coverage report shows >90%

---

### Phase 10: Documentation & Deployment Prep (Day 5)
**Tasks:**
- Document API endpoints in OpenAPI/Swagger schema
- Add environment variables to `.env.example`
- Update `MANUAL_VERIFICATION.md` with email testing steps
- Update `USER_SETUP.md` with email backend configuration
- Create admin interface for User model

**Files:**
- `.env.example`
- `.planning/MANUAL_VERIFICATION.md`
- `.planning/USER_SETUP.md`
- `apps/users/admin.py`

**Verification:**
- [ ] Admin can view/edit users in Django admin
- [ ] Environment variables documented
- [ ] Manual testing checklist complete

---

## 5. Dependencies & Integrations

### External Services
- **Email Provider:** SMTP server (Gmail, SendGrid, Mailgun, etc.)
- **Redis:** Cache backend for rate limiting and token blacklist

### Internal Dependencies
- **PostgreSQL:** User and token storage
- **Django Settings:** Email configuration, JWT settings, cache backend

### Future Integrations (Out of Scope)
- OAuth2 social login (Google, GitHub)
- Two-factor authentication (TOTP)
- Session management UI (view active sessions, revoke tokens)

---

## 6. Testing & Validation

### Unit Tests
- All models, serializers, views covered
- Password validation edge cases
- Token expiry and blacklisting

### Integration Tests
- Full registration → verification → login flow
- Password reset end-to-end
- Profile update with authenticated requests

### Manual Testing Checklist (`.planning/MANUAL_VERIFICATION.md`)
- [ ] Register new user, receive verification email
- [ ] Click verification link, account activated
- [ ] Login with verified account, receive JWT tokens
- [ ] Refresh access token using refresh token
- [ ] Logout, verify token blacklisted
- [ ] Request password reset, receive email
- [ ] Reset password with valid token
- [ ] Update profile fields (avatar URL, bio, institution)
- [ ] Test rate limiting on login (6th attempt blocked)

### Performance Requirements
- Registration: <300ms (excluding email send)
- Login: <200ms
- Token refresh: <100ms
- Profile GET: <150ms

---

## 7. Security Considerations

### OWASP Top 10 Mitigations
1. **Broken Access Control:** JWT-based auth, profile endpoints check ownership
2. **Cryptographic Failures:** Passwords hashed with Django's PBKDF2, tokens cryptographically secure
3. **Injection:** ORM prevents SQL injection, serializers validate input
4. **Insecure Design:** Rate limiting prevents brute force
5. **Security Misconfiguration:** DEBUG=False in production, secrets in environment variables
6. **Vulnerable Components:** Pinned dependencies in `requirements.txt`
7. **Identification & Authentication Failures:** Email verification, strong password policy, token rotation
8. **Software & Data Integrity Failures:** Token blacklist prevents replay attacks
9. **Logging Failures:** Log failed login attempts (future enhancement)
10. **SSRF:** Avatar URL validation (future: restrict to allowed domains)

### Additional Measures
- **No User Enumeration:** Password reset always returns success
- **Token Expiry:** Short-lived access tokens, long-lived refresh tokens
- **CORS Configuration:** Restrict allowed origins in production
- **HTTPS Only:** Enforce in production (nginx/load balancer level)

---

## 8. Environment Variables

Add to `backend/.env`:
```bash
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@syncscript.io
EMAIL_HOST_PASSWORD=<app-password>
DEFAULT_FROM_EMAIL=SyncScript <noreply@syncscript.io>

# JWT Configuration (optional overrides)
JWT_ACCESS_TOKEN_LIFETIME=15  # minutes
JWT_REFRESH_TOKEN_LIFETIME=10080  # 7 days in minutes

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
```

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Email delivery failures | Users cannot verify accounts | Retry logic, status page for email queue |
| Redis downtime | Rate limiting fails open | Graceful degradation, fallback to in-memory cache |
| Token blacklist growth | Database bloat | Periodic cleanup task (Celery beat) |
| Brute force attacks | Account compromise | Rate limiting, account lockout (future) |
| Email enumeration | Privacy leak | Consistent responses for reset requests |

---

## 10. Success Criteria

### Definition of Done
- [ ] All 9 API endpoints functional and tested
- [ ] Email verification flow works end-to-end
- [ ] Password reset flow works end-to-end
- [ ] JWT tokens issued and validated correctly
- [ ] Rate limiting enforced on all auth endpoints
- [ ] Token blacklist prevents reuse of revoked tokens
- [ ] Profile CRUD operations secured and tested
- [ ] Test coverage >90%
- [ ] Manual verification checklist completed
- [ ] Documentation updated in `.planning/`

### Acceptance Testing
- Product owner verifies registration email received
- Product owner tests full login/logout flow
- Product owner confirms rate limiting blocks 6th attempt
- Product owner validates profile update UI integration

---

## 11. Out of Scope

The following are explicitly excluded from this PRD:
- OAuth2/social login integration
- Two-factor authentication (TOTP, SMS)
- Account deletion/anonymization
- Session management UI
- Admin dashboard for user moderation
- Avatar file uploads (only URL field in Phase 1)
- Email template customization beyond basic HTML
- Internationalization (i18n) for emails

---

## 12. Appendix

### A. Database Schema Diagram
```
┌─────────────────────────────────┐
│ users                           │
├─────────────────────────────────┤
│ id (PK, UUID)                   │
│ email (unique, indexed)         │
│ username                        │
│ password (hashed)               │
│ avatar_url                      │
│ bio                             │
│ institution                     │
│ email_verified (indexed)        │
│ created_at                      │
│ updated_at                      │
└─────────────────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────────────────┐
│ email_verification_tokens       │
├─────────────────────────────────┤
│ id (PK)                         │
│ user_id (FK)                    │
│ token (unique)                  │
│ created_at                      │
│ expires_at                      │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ token_blacklist_*               │
│ (managed by SimpleJWT)          │
└─────────────────────────────────┘
```

### B. Email Templates

**Verification Email Subject:** "Verify your SyncScript account"

**Password Reset Email Subject:** "Reset your SyncScript password"

### C. Rate Limit Keys
- Registration: `user:register:{ip}`
- Login: `user:login:{ip}`
- Password reset: `user:reset:{email}`
- Token refresh: `user:refresh:{ip}`

---

**Document Version:** 1.0  
**Author:** Product Team  
**Date:** 2026-02-14  
**Status:** Ready for Implementation