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
- [ ] Create `apps/users/tokens.py`
- [ ] Implement generate_verification_token(user) using secrets.token_urlsafe(32)
- [ ] Token expires in 24 hours
- [ ] Implement verify_token(token) that validates and returns user or None
- [ ] Delete token after successful verification
- [ ] Typecheck passes

---

### US-012: Create email verification HTML template
**Description:** As a developer, I need an HTML email template for account verification.

**Acceptance Criteria:**
- [ ] Create `templates/emails/verify_email.html`
- [ ] Include user's name/email in greeting
- [ ] Include verification link with token
- [ ] Include expiration notice (24 hours)
- [ ] Simple, professional styling
- [ ] Typecheck passes

---

### US-013: Create email helper functions
**Description:** As a developer, I need helper functions to send verification and password reset emails.

**Acceptance Criteria:**
- [ ] Create `apps/users/emails.py`
- [ ] Implement send_verification_email(user, token) using Django's send_mail
- [ ] Render HTML template with context
- [ ] Include plain text fallback
- [ ] Typecheck passes

---

### US-014: Create RegisterView endpoint
**Description:** As a user, I want to register an account so I can access SyncScript.

**Acceptance Criteria:**
- [ ] Create `apps/users/views.py`
- [ ] Implement RegisterView as APIView (POST /api/v1/auth/register/)
- [ ] Use RegisterSerializer for validation
- [ ] Create user with email_verified=False
- [ ] Generate verification token and send email
- [ ] Return user data with message about verification email
- [ ] Apply @ratelimit decorator (5/min per IP)
- [ ] Typecheck passes

---

### US-015: Create VerifyEmailView endpoint
**Description:** As a user, I want to verify my email address to activate my account.

**Acceptance Criteria:**
- [ ] Add VerifyEmailView to `apps/users/views.py`
- [ ] POST /api/v1/auth/verify-email/ accepts token in body
- [ ] Validate token using tokens.py logic
- [ ] Set user.email_verified = True on success
- [ ] Return success/error message
- [ ] Apply @ratelimit decorator (10/min per IP)
- [ ] Typecheck passes

---

### US-016: Create LoginView endpoint
**Description:** As a user, I want to login with email/password to receive JWT tokens.

**Acceptance Criteria:**
- [ ] Add LoginView to `apps/users/views.py`
- [ ] POST /api/v1/auth/login/ accepts email and password
- [ ] Authenticate using Django's authenticate()
- [ ] Check email_verified status (reject if not verified)
- [ ] Generate access and refresh tokens using SimpleJWT
- [ ] Return tokens and user data
- [ ] Apply @ratelimit decorator (5/min per IP)
- [ ] Typecheck passes

---

### US-017: Create LogoutView endpoint
**Description:** As a user, I want to logout to invalidate my refresh token.

**Acceptance Criteria:**
- [ ] Add LogoutView to `apps/users/views.py`
- [ ] POST /api/v1/auth/logout/ requires authentication
- [ ] Accept refresh token in request body
- [ ] Blacklist the refresh token using SimpleJWT
- [ ] Return success message
- [ ] Typecheck passes

---

### US-018: Create RefreshTokenView endpoint
**Description:** As a user, I want to refresh my access token without re-authenticating.

**Acceptance Criteria:**
- [ ] Add RefreshTokenView to `apps/users/views.py`
- [ ] POST /api/v1/auth/refresh/ accepts refresh token
- [ ] Use SimpleJWT's TokenRefreshView as base or custom implementation
- [ ] Return new access token (and rotated refresh token per settings)
- [ ] Apply @ratelimit decorator (20/min per IP)
- [ ] Typecheck passes

---

### US-019: Create PasswordResetRequestView endpoint
**Description:** As a user, I want to request a password reset email when I forget my password.

**Acceptance Criteria:**
- [ ] Add PasswordResetRequestView to `apps/users/views.py`
- [ ] POST /api/v1/auth/password-reset/ accepts email
- [ ] Generate reset token using Django's PasswordResetTokenGenerator
- [ ] Encode user ID in base64
- [ ] Send password reset email (create if needed)
- [ ] Always return success (no user enumeration)
- [ ] Apply @ratelimit decorator (3/hour per email)
- [ ] Typecheck passes

---

### US-020: Create password reset email template
**Description:** As a developer, I need an HTML email template for password reset.

**Acceptance Criteria:**
- [ ] Create `templates/emails/password_reset.html`
- [ ] Include reset link with uid and token
- [ ] Include expiration notice (1 hour)
- [ ] Simple, professional styling
- [ ] Add send_password_reset_email function to emails.py
- [ ] Typecheck passes

---

### US-021: Create PasswordResetConfirmView endpoint
**Description:** As a user, I want to set a new password using the reset link.

**Acceptance Criteria:**
- [ ] Add PasswordResetConfirmView to `apps/users/views.py`
- [ ] POST /api/v1/auth/password-reset-confirm/ accepts uid, token, new_password
- [ ] Decode uid and fetch user
- [ ] Validate token using PasswordResetTokenGenerator
- [ ] Update user password (hashed)
- [ ] Return success/error message
- [ ] Apply @ratelimit decorator (10/min per IP)
- [ ] Typecheck passes

---

### US-022: Create ProfileView endpoint
**Description:** As a user, I want to view and update my profile information.

**Acceptance Criteria:**
- [ ] Add ProfileView to `apps/users/views.py`
- [ ] GET /api/v1/users/profile/ returns current user's profile (UserSerializer)
- [ ] PATCH /api/v1/users/profile/ updates avatar_url, bio, institution
- [ ] Require authentication (IsAuthenticated permission)
- [ ] Reject attempts to change email or password via this endpoint
- [ ] Typecheck passes

---

### US-023: Create users app URL routing
**Description:** As a developer, I need URL routing for all auth and user endpoints.

**Acceptance Criteria:**
- [ ] Create `apps/users/urls.py`
- [ ] Add auth URLs: register, verify-email, login, logout, refresh
- [ ] Add password reset URLs: password-reset, password-reset-confirm
- [ ] Add profile URL: users/profile
- [ ] Use proper URL naming convention
- [ ] Typecheck passes

---

### US-024: Include users URLs in main config
**Description:** As a developer, I need the users app URLs included in the main URL configuration.

**Acceptance Criteria:**
- [ ] Update `config/urls.py`
- [ ] Include auth endpoints at /api/v1/auth/
- [ ] Include user endpoints at /api/v1/users/
- [ ] Typecheck passes

---

### US-025: Create custom permissions
**Description:** As a developer, I need custom permission classes for email verification checks.

**Acceptance Criteria:**
- [ ] Create `apps/users/permissions.py`
- [ ] Implement IsEmailVerified permission class
- [ ] Returns False if user.email_verified is False
- [ ] Include appropriate error message
- [ ] Typecheck passes

---

### US-026: Apply rate limiting to all auth views
**Description:** As a developer, I need rate limiting applied consistently to prevent brute force attacks.

**Acceptance Criteria:**
- [ ] Verify @ratelimit decorators on RegisterView (5/min)
- [ ] Verify @ratelimit decorators on LoginView (5/min)
- [ ] Verify @ratelimit decorators on VerifyEmailView (10/min)
- [ ] Verify @ratelimit decorators on RefreshTokenView (20/min)
- [ ] Verify @ratelimit decorators on PasswordResetRequestView (3/hour per email)
- [ ] Verify @ratelimit decorators on PasswordResetConfirmView (10/min)
- [ ] Typecheck passes

---

### US-027: Create rate limit exceeded response handler
**Description:** As a developer, I need a consistent 429 response when rate limits are exceeded.

**Acceptance Criteria:**
- [ ] Create rate limit exception handler in views.py or separate module
- [ ] Return 429 status code with JSON error message
- [ ] Include Retry-After header
- [ ] Register handler in DRF exception handling
- [ ] Typecheck passes

---

### US-028: Create User model tests
**Description:** As a developer, I need unit tests for the User model.

**Acceptance Criteria:**
- [ ] Create `apps/users/tests/__init__.py`
- [ ] Create `apps/users/tests/test_models.py`
- [ ] Test user creation with all fields
- [ ] Test email uniqueness constraint
- [ ] Test email_verified default is False
- [ ] Test EmailVerificationToken creation and relationships
- [ ] All tests pass

---

### US-029: Create serializer tests
**Description:** As a developer, I need unit tests for all serializers.

**Acceptance Criteria:**
- [ ] Create `apps/users/tests/test_serializers.py`
- [ ] Test RegisterSerializer validation (email uniqueness, password strength)
- [ ] Test ProfileUpdateSerializer field limits
- [ ] Test PasswordResetConfirmSerializer password validation
- [ ] All tests pass

---

### US-030: Create registration flow tests
**Description:** As a developer, I need integration tests for the registration flow.

**Acceptance Criteria:**
- [ ] Create `apps/users/tests/test_auth.py`
- [ ] Test successful registration returns 201
- [ ] Test registration creates unverified user
- [ ] Test duplicate email returns 400
- [ ] Test weak password returns 400
- [ ] All tests pass

---

### US-031: Create email verification flow tests
**Description:** As a developer, I need integration tests for email verification.

**Acceptance Criteria:**
- [ ] Add tests to `apps/users/tests/test_auth.py`
- [ ] Test valid token activates account
- [ ] Test expired token returns error
- [ ] Test invalid token returns error
- [ ] Test already verified user handles gracefully
- [ ] All tests pass

---

### US-032: Create login and logout flow tests
**Description:** As a developer, I need integration tests for login and logout.

**Acceptance Criteria:**
- [ ] Add tests to `apps/users/tests/test_auth.py`
- [ ] Test successful login returns tokens
- [ ] Test unverified user cannot login
- [ ] Test wrong password returns 401
- [ ] Test logout blacklists refresh token
- [ ] Test blacklisted token cannot be used
- [ ] All tests pass

---

### US-033: Create token refresh tests
**Description:** As a developer, I need integration tests for token refresh.

**Acceptance Criteria:**
- [ ] Add tests to `apps/users/tests/test_auth.py`
- [ ] Test valid refresh token returns new access token
- [ ] Test expired refresh token returns error
- [ ] Test blacklisted refresh token returns error
- [ ] Test token rotation (old refresh token invalidated)
- [ ] All tests pass

---

### US-034: Create password reset flow tests
**Description:** As a developer, I need integration tests for password reset.

**Acceptance Criteria:**
- [ ] Add tests to `apps/users/tests/test_auth.py`
- [ ] Test password reset request returns success (even for non-existent email)
- [ ] Test valid reset token allows password change
- [ ] Test expired reset token returns error
- [ ] Test new password must meet strength requirements
- [ ] All tests pass

---

### US-035: Create profile endpoint tests
**Description:** As a developer, I need integration tests for profile management.

**Acceptance Criteria:**
- [ ] Create `apps/users/tests/test_profile.py`
- [ ] Test GET profile returns current user data
- [ ] Test PATCH updates allowed fields
- [ ] Test PATCH rejects email/password changes
- [ ] Test unauthenticated request returns 401
- [ ] Test field length validation
- [ ] All tests pass

---

### US-036: Create rate limiting tests
**Description:** As a developer, I need tests to verify rate limiting works correctly.

**Acceptance Criteria:**
- [ ] Create `apps/users/tests/test_rate_limiting.py`
- [ ] Test 6th login attempt within minute returns 429
- [ ] Test 6th registration attempt within minute returns 429
- [ ] Test rate limit resets after time window
- [ ] Mock Redis for consistent test behavior
- [ ] All tests pass

---

### US-037: Create User admin interface
**Description:** As an admin, I want to view and manage users in Django admin.

**Acceptance Criteria:**
- [ ] Update `apps/users/admin.py`
- [ ] Register User model with custom UserAdmin
- [ ] Display: email, username, email_verified, created_at
- [ ] Add filters: email_verified, is_active, is_staff
- [ ] Add search: email, username
- [ ] Make email_verified editable in list view
- [ ] Typecheck passes

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
