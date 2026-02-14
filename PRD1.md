# PRD: SyncScript Django Backend User Authentication System

## Introduction

Implement a secure, production-ready authentication system for SyncScript's collaborative research platform. This system provides JWT-based authentication, email verification, password reset flows, user profile management, and comprehensive rate limiting using Django REST Framework with Redis-backed security controls.

**Source PRD:** `tasks/prd-syncscript-django-backend-user-authentication-system.md`

## Goals

- Implement custom User model with email as primary identifier
- JWT authentication with access (15min) and refresh (7 days) tokens
- Email verification flow for new registrations
- Secure password reset via email
- User profile management (avatar URL, bio, institution)
- Redis-backed rate limiting on all auth endpoints
- Token rotation and blacklisting for security
- Comprehensive test coverage (>90%)

## User Stories

---

### US-001: Create custom User model
**Description:** As a developer, I need a custom User model that uses email as the primary identifier and includes profile fields.

**Acceptance Criteria:**
- [x] Create `apps/users/models.py` with User model extending AbstractUser
- [x] Add fields: email (unique), avatar_url (URLField), bio (TextField max 500), institution (CharField max 200), email_verified (BooleanField)
- [x] Add created_at and updated_at timestamp fields
- [x] Set USERNAME_FIELD = 'email' and REQUIRED_FIELDS = ['username']
- [x] Add database indexes on email and email_verified fields
- [x] Set db_table = 'users'
- [x] Typecheck passes

---

### US-002: Create EmailVerificationToken model
**Description:** As a developer, I need to store email verification tokens with expiration.

**Acceptance Criteria:**
- [x] Add EmailVerificationToken model to `apps/users/models.py`
- [x] Fields: user (ForeignKey to User), token (CharField max 64, unique), created_at, expires_at
- [x] Set db_table = 'email_verification_tokens'
- [x] Typecheck passes

---

### US-003: Create users app and generate initial migration
**Description:** As a developer, I need the users app structure and initial database migration.

**Acceptance Criteria:**
- [x] Create `apps/users/__init__.py`
- [x] Create `apps/users/apps.py` with UsersConfig
- [x] Create `apps/users/admin.py` (empty for now)
- [x] Generate migration with `python manage.py makemigrations users`
- [x] Migration file created in `apps/users/migrations/`
- [x] Typecheck passes

---

### US-004: Configure Django settings for custom User model
**Description:** As a developer, I need Django configured to use the custom User model and SimpleJWT.

**Acceptance Criteria:**
- [x] Add 'apps.users' to INSTALLED_APPS in `config/settings.py`
- [x] Add 'rest_framework_simplejwt' to INSTALLED_APPS
- [x] Add 'rest_framework_simplejwt.token_blacklist' to INSTALLED_APPS
- [x] Set AUTH_USER_MODEL = 'users.User'
- [x] Add SIMPLE_JWT config: ACCESS_TOKEN_LIFETIME=15min, REFRESH_TOKEN_LIFETIME=7days
- [x] Enable ROTATE_REFRESH_TOKENS = True and BLACKLIST_AFTER_ROTATION = True
- [x] Typecheck passes

---

### US-005: Configure Redis cache backend
**Description:** As a developer, I need Redis configured as the cache backend for rate limiting.

**Acceptance Criteria:**
- [x] Add django-redis to requirements.txt if not present
- [x] Configure CACHES in settings.py with Redis backend
- [x] Use REDIS_URL from environment variable with fallback
- [x] Add RATELIMIT_USE_CACHE = 'default' setting
- [x] Typecheck passes

---

### US-006: Configure email backend settings
**Description:** As a developer, I need email backend configured for sending verification and reset emails.

**Acceptance Criteria:**
- [x] Add EMAIL_BACKEND setting (SMTP backend)
- [x] Add EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS settings from environment
- [x] Add EMAIL_HOST_USER, EMAIL_HOST_PASSWORD from environment
- [x] Add DEFAULT_FROM_EMAIL setting
- [x] Typecheck passes

---

### US-007: Create UserSerializer
**Description:** As a developer, I need a serializer for returning user profile data in API responses.

**Acceptance Criteria:**
- [x] Create `apps/users/serializers.py`
- [x] Create UserSerializer with fields: id, email, username, avatar_url, bio, institution, email_verified, created_at
- [x] Mark email and created_at as read_only
- [x] Typecheck passes

---

### US-008: Create RegisterSerializer with password validation
**Description:** As a developer, I need a serializer for user registration with password strength validation.

**Acceptance Criteria:**
- [x] Add RegisterSerializer to `apps/users/serializers.py`
- [x] Fields: email, password, username, bio (optional), institution (optional)
- [x] Password field write_only with min_length=8
- [x] Add validate_password method using Django's password validators
- [x] Add validate_email method to check uniqueness
- [x] Implement create method that hashes password
- [x] Typecheck passes

---

### US-009: Create ProfileUpdateSerializer
**Description:** As a developer, I need a serializer for updating user profile fields.

**Acceptance Criteria:**
- [x] Add ProfileUpdateSerializer to `apps/users/serializers.py`
- [x] Fields: avatar_url, bio, institution (all optional)
- [x] Add validate_avatar_url to ensure valid URL format
- [x] Add validate_bio to enforce 500 char limit
- [x] Add validate_institution to enforce 200 char limit
- [x] Typecheck passes

---

### US-010: Create password reset serializers
**Description:** As a developer, I need serializers for password reset request and confirmation.

**Acceptance Criteria:**
- [x] Add PasswordResetRequestSerializer with email field
- [x] Add PasswordResetConfirmSerializer with uid, token, new_password fields
- [x] Add password validation to PasswordResetConfirmSerializer
- [x] Typecheck passes

---

### US-011: Create email verification token logic
**Description:** As a developer, I need functions to generate and validate email verification tokens.

**Acceptance Criteria:**
- [x] Create `apps/users/tokens.py`
- [x] Implement generate_verification_token(user) using secrets.token_urlsafe(32)
- [x] Token expires in 24 hours
- [x] Implement verify_token(token) that validates and returns user or None
- [x] Delete token after successful verification
- [x] Typecheck passes

---

### US-012: Create email verification HTML template
**Description:** As a developer, I need an HTML email template for account verification.

**Acceptance Criteria:**
- [x] Create `templates/emails/verify_email.html`
- [x] Include user's name/email in greeting
- [x] Include verification link with token
- [x] Include expiration notice (24 hours)
- [x] Simple, professional styling
- [x] Typecheck passes

---

### US-013: Create email helper functions
**Description:** As a developer, I need helper functions to send verification and password reset emails.

**Acceptance Criteria:**
- [x] Create `apps/users/emails.py`
- [x] Implement send_verification_email(user, token) using Django's send_mail
- [x] Render HTML template with context
- [x] Include plain text fallback
- [x] Typecheck passes

---

### US-014: Create RegisterView endpoint
**Description:** As a user, I want to register an account so I can access SyncScript.

**Acceptance Criteria:**
- [x] Create `apps/users/views.py`
- [x] Implement RegisterView as APIView (POST /api/v1/auth/register/)
- [x] Use RegisterSerializer for validation
- [x] Create user with email_verified=False
- [x] Generate verification token and send email
- [x] Return user data with message about verification email
- [x] Apply @ratelimit decorator (5/min per IP)
- [x] Typecheck passes

---

### US-015: Create VerifyEmailView endpoint
**Description:** As a user, I want to verify my email address to activate my account.

**Acceptance Criteria:**
- [x] Add VerifyEmailView to `apps/users/views.py`
- [x] POST /api/v1/auth/verify-email/ accepts token in body
- [x] Validate token using tokens.py logic
- [x] Set user.email_verified = True on success
- [x] Return success/error message
- [x] Apply @ratelimit decorator (10/min per IP)
- [x] Typecheck passes

---

### US-016: Create LoginView endpoint
**Description:** As a user, I want to login with email/password to receive JWT tokens.

**Acceptance Criteria:**
- [x] Add LoginView to `apps/users/views.py`
- [x] POST /api/v1/auth/login/ accepts email and password
- [x] Authenticate using Django's authenticate()
- [x] Check email_verified status (reject if not verified)
- [x] Generate access and refresh tokens using SimpleJWT
- [x] Return tokens and user data
- [x] Apply @ratelimit decorator (5/min per IP)
- [x] Typecheck passes

---

### US-017: Create LogoutView endpoint
**Description:** As a user, I want to logout to invalidate my refresh token.

**Acceptance Criteria:**
- [x] Add LogoutView to `apps/users/views.py`
- [x] POST /api/v1/auth/logout/ requires authentication
- [x] Accept refresh token in request body
- [x] Blacklist the refresh token using SimpleJWT
- [x] Return success message
- [x] Typecheck passes

---

### US-018: Create RefreshTokenView endpoint
**Description:** As a user, I want to refresh my access token without re-authenticating.

**Acceptance Criteria:**
- [x] Add RefreshTokenView to `apps/users/views.py`
- [x] POST /api/v1/auth/refresh/ accepts refresh token
- [x] Use SimpleJWT's TokenRefreshView as base or custom implementation
- [x] Return new access token (and rotated refresh token per settings)
- [x] Apply @ratelimit decorator (20/min per IP)
- [x] Typecheck passes

---

### US-019: Create PasswordResetRequestView endpoint
**Description:** As a user, I want to request a password reset email when I forget my password.

**Acceptance Criteria:**
- [x] Add PasswordResetRequestView to `apps/users/views.py`
- [x] POST /api/v1/auth/password-reset/ accepts email
- [x] Generate reset token using Django's PasswordResetTokenGenerator
- [x] Encode user ID in base64
- [x] Send password reset email (create if needed)
- [x] Always return success (no user enumeration)
- [x] Apply @ratelimit decorator (3/hour per email)
- [x] Typecheck passes

---

### US-020: Create password reset email template
**Description:** As a developer, I need an HTML email template for password reset.

**Acceptance Criteria:**
- [x] Create `templates/emails/password_reset.html`
- [x] Include reset link with uid and token
- [x] Include expiration notice (1 hour)
- [x] Simple, professional styling
- [x] Add send_password_reset_email function to emails.py
- [x] Typecheck passes

---

### US-021: Create PasswordResetConfirmView endpoint
**Description:** As a user, I want to set a new password using the reset link.

**Acceptance Criteria:**
- [x] Add PasswordResetConfirmView to `apps/users/views.py`
- [x] POST /api/v1/auth/password-reset-confirm/ accepts uid, token, new_password
- [x] Decode uid and fetch user
- [x] Validate token using PasswordResetTokenGenerator
- [x] Update user password (hashed)
- [x] Return success/error message
- [x] Apply @ratelimit decorator (10/min per IP)
- [x] Typecheck passes

---

### US-022: Create ProfileView endpoint
**Description:** As a user, I want to view and update my profile information.

**Acceptance Criteria:**
- [x] Add ProfileView to `apps/users/views.py`
- [x] GET /api/v1/users/profile/ returns current user's profile (UserSerializer)
- [x] PATCH /api/v1/users/profile/ updates avatar_url, bio, institution
- [x] Require authentication (IsAuthenticated permission)
- [x] Reject attempts to change email or password via this endpoint
- [x] Typecheck passes

---

### US-023: Create users app URL routing
**Description:** As a developer, I need URL routing for all auth and user endpoints.

**Acceptance Criteria:**
- [x] Create `apps/users/urls.py`
- [x] Add auth URLs: register, verify-email, login, logout, refresh
- [x] Add password reset URLs: password-reset, password-reset-confirm
- [x] Add profile URL: users/profile
- [x] Use proper URL naming convention
- [x] Typecheck passes

---

### US-024: Include users URLs in main config
**Description:** As a developer, I need the users app URLs included in the main URL configuration.

**Acceptance Criteria:**
- [x] Update `config/urls.py`
- [x] Include auth endpoints at /api/v1/auth/
- [x] Include user endpoints at /api/v1/users/
- [x] Typecheck passes

---

### US-025: Create custom permissions
**Description:** As a developer, I need custom permission classes for email verification checks.

**Acceptance Criteria:**
- [x] Create `apps/users/permissions.py`
- [x] Implement IsEmailVerified permission class
- [x] Returns False if user.email_verified is False
- [x] Include appropriate error message
- [x] Typecheck passes

---

### US-026: Apply rate limiting to all auth views
**Description:** As a developer, I need rate limiting applied consistently to prevent brute force attacks.

**Acceptance Criteria:**
- [x] Verify @ratelimit decorators on RegisterView (5/min)
- [x] Verify @ratelimit decorators on LoginView (5/min)
- [x] Verify @ratelimit decorators on VerifyEmailView (10/min)
- [x] Verify @ratelimit decorators on RefreshTokenView (20/min)
- [x] Verify @ratelimit decorators on PasswordResetRequestView (3/hour per email)
- [x] Verify @ratelimit decorators on PasswordResetConfirmView (10/min)
- [x] Typecheck passes

---

### US-027: Create rate limit exceeded response handler
**Description:** As a developer, I need a consistent 429 response when rate limits are exceeded.

**Acceptance Criteria:**
- [x] Create rate limit exception handler in views.py or separate module
- [x] Return 429 status code with JSON error message
- [x] Include Retry-After header
- [x] Register handler in DRF exception handling
- [x] Typecheck passes

---

### US-028: Create User model tests
**Description:** As a developer, I need unit tests for the User model.

**Acceptance Criteria:**
- [x] Create `apps/users/tests/__init__.py`
- [x] Create `apps/users/tests/test_models.py`
- [x] Test user creation with all fields
- [x] Test email uniqueness constraint
- [x] Test email_verified default is False
- [x] Test EmailVerificationToken creation and relationships
- [x] All tests pass

---

### US-029: Create serializer tests
**Description:** As a developer, I need unit tests for all serializers.

**Acceptance Criteria:**
- [x] Create `apps/users/tests/test_serializers.py`
- [x] Test RegisterSerializer validation (email uniqueness, password strength)
- [x] Test ProfileUpdateSerializer field limits
- [x] Test PasswordResetConfirmSerializer password validation
- [x] All tests pass

---

### US-030: Create registration flow tests
**Description:** As a developer, I need integration tests for the registration flow.

**Acceptance Criteria:**
- [x] Create `apps/users/tests/test_auth.py`
- [x] Test successful registration returns 201
- [x] Test registration creates unverified user
- [x] Test duplicate email returns 400
- [x] Test weak password returns 400
- [x] All tests pass

---

### US-031: Create email verification flow tests
**Description:** As a developer, I need integration tests for email verification.

**Acceptance Criteria:**
- [x] Add tests to `apps/users/tests/test_auth.py`
- [x] Test valid token activates account
- [x] Test expired token returns error
- [x] Test invalid token returns error
- [x] Test already verified user handles gracefully
- [x] All tests pass

---

### US-032: Create login and logout flow tests
**Description:** As a developer, I need integration tests for login and logout.

**Acceptance Criteria:**
- [x] Add tests to `apps/users/tests/test_auth.py`
- [x] Test successful login returns tokens
- [x] Test unverified user cannot login
- [x] Test wrong password returns 401
- [x] Test logout blacklists refresh token
- [x] Test blacklisted token cannot be used
- [x] All tests pass

---

### US-033: Create token refresh tests
**Description:** As a developer, I need integration tests for token refresh.

**Acceptance Criteria:**
- [x] Add tests to `apps/users/tests/test_auth.py`
- [x] Test valid refresh token returns new access token
- [x] Test expired refresh token returns error
- [x] Test blacklisted refresh token returns error
- [x] Test token rotation (old refresh token invalidated)
- [x] All tests pass

---

### US-034: Create password reset flow tests
**Description:** As a developer, I need integration tests for password reset.

**Acceptance Criteria:**
- [x] Add tests to `apps/users/tests/test_auth.py`
- [x] Test password reset request returns success (even for non-existent email)
- [x] Test valid reset token allows password change
- [x] Test expired reset token returns error
- [x] Test new password must meet strength requirements
- [x] All tests pass

---

### US-035: Create profile endpoint tests
**Description:** As a developer, I need integration tests for profile management.

**Acceptance Criteria:**
- [x] Create `apps/users/tests/test_profile.py`
- [x] Test GET profile returns current user data
- [x] Test PATCH updates allowed fields
- [x] Test PATCH rejects email/password changes
- [x] Test unauthenticated request returns 401
- [x] Test field length validation
- [x] All tests pass

---

### US-036: Create rate limiting tests
**Description:** As a developer, I need tests to verify rate limiting works correctly.

**Acceptance Criteria:**
- [x] Create `apps/users/tests/test_rate_limiting.py`
- [x] Test 6th login attempt within minute returns 429
- [x] Test 6th registration attempt within minute returns 429
- [x] Test rate limit resets after time window
- [x] Mock Redis for consistent test behavior
- [x] All tests pass

---

### US-037: Create User admin interface
**Description:** As an admin, I want to view and manage users in Django admin.

**Acceptance Criteria:**
- [x] Update `apps/users/admin.py`
- [x] Register User model with custom UserAdmin
- [x] Display: email, username, email_verified, created_at
- [x] Add filters: email_verified, is_active, is_staff
- [x] Add search: email, username
- [x] Make email_verified editable in list view
- [x] Typecheck passes

---

### US-038: Update environment documentation
**Description:** As a developer, I need environment variables documented for setup.

**Acceptance Criteria:**
- [ ] Update `.env.example` with all required email settings
- [ ] Add JWT configuration variables
- [ ] Add Redis URL variable
- [ ] Include comments explaining each variable
- [ ] Typecheck passes

---

### US-039: Create manual verification checklist
**Description:** As a developer, I need a checklist for manually testing the auth system.

**Acceptance Criteria:**
- [ ] Create or update `.planning/MANUAL_VERIFICATION.md`
- [ ] Add auth system section with date
- [ ] Include steps: register, verify email, login, refresh, logout
- [ ] Include password reset flow steps
- [ ] Include profile update steps
- [ ] Include rate limiting test steps
- [ ] Typecheck passes

---

### US-040: Update user setup documentation
**Description:** As a developer, I need setup instructions for email and Redis configuration.

**Acceptance Criteria:**
- [ ] Create or update `.planning/USER_SETUP.md`
- [ ] Add Email Configuration section with SMTP setup steps
- [ ] Add Redis Configuration section with installation steps
- [ ] Add JWT secret key generation instructions
- [ ] List all required environment variables
- [ ] Typecheck passes

---

## Non-Goals

- OAuth2/social login integration (Google, GitHub)
- Two-factor authentication (TOTP, SMS)
- Account deletion/anonymization
- Session management UI (view active sessions)
- Avatar file uploads (URL field only)
- Email template customization beyond basic HTML
- Internationalization (i18n) for emails
- Admin dashboard for user moderation
- Celery task for token cleanup (can be added later)

## Technical Considerations

### Dependencies (add to requirements.txt)
```
djangorestframework-simplejwt==5.5.1
django-ratelimit==4.1.0
django-redis==5.4.0
```

### File Structure
```
backend/apps/users/
├── migrations/
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_serializers.py
│   ├── test_auth.py
│   ├── test_profile.py
│   └── test_rate_limiting.py
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── permissions.py
├── tokens.py
└── emails.py
```

### Key Configuration Values
- Access token: 15 minutes
- Refresh token: 7 days
- Email verification token: 24 hours
- Password reset token: 1 hour
- Rate limits: See US-026

### API Endpoints Summary
| Endpoint | Method | Rate Limit |
|----------|--------|------------|
| /api/v1/auth/register/ | POST | 5/min |
| /api/v1/auth/verify-email/ | POST | 10/min |
| /api/v1/auth/login/ | POST | 5/min |
| /api/v1/auth/logout/ | POST | - |
| /api/v1/auth/refresh/ | POST | 20/min |
| /api/v1/auth/password-reset/ | POST | 3/hour |
| /api/v1/auth/password-reset-confirm/ | POST | 10/min |
| /api/v1/users/profile/ | GET/PATCH | - |
