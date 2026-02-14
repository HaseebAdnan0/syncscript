# PRD 11: Production Email System & Verification

## Introduction

Replace stub email implementation with production-ready email system using Hostinger SMTP. This includes proper email verification flows, password reset, branded HTML templates matching the Bitcoin DeFi aesthetic, and async email delivery via Celery. Unverified users are blocked from login entirely, and the frontend redirects unverified users to a verification-pending page.

## Goals

- Configure Django email backend for Hostinger SMTP (smtp.hostinger.com:465 SSL)
- Implement robust email verification with secure tokens and rate limiting
- Implement password reset flow with 1-hour token expiry
- Create branded HTML email templates with Bitcoin DeFi dark theme aesthetic
- Send all emails asynchronously via Celery for non-blocking requests
- Build frontend pages for verification pending, password reset, and success/error states
- Support vault invitations for unverified users (prompted to verify on first action)

## User Stories

### US-001: Configure Hostinger SMTP email backend
**Description:** As a developer, I need Django configured with Hostinger SMTP so emails are sent through production mail servers.

**Acceptance Criteria:**
- [x] Update `config/settings.py` EMAIL settings for Hostinger:
  - `EMAIL_HOST = 'smtp.hostinger.com'`
  - `EMAIL_PORT = 465`
  - `EMAIL_USE_SSL = True` (not TLS)
  - `EMAIL_USE_TLS = False`
- [x] Add `EMAIL_USE_SSL` env var support
- [x] Add email connection test management command: `python manage.py test_email`
- [x] Command sends test email to specified address and reports success/failure
- [x] Typecheck passes

---

### US-002: Create Celery email tasks module
**Description:** As a developer, I need Celery tasks for sending emails asynchronously so API responses aren't blocked by SMTP.

**Acceptance Criteria:**
- [x] Create `apps/users/tasks.py` with Celery tasks
- [x] `send_verification_email_task(user_id, token)` - sends verification email
- [x] `send_password_reset_email_task(user_id, uid, token)` - sends reset email
- [x] `send_welcome_email_task(user_id)` - sends welcome after verification
- [x] `send_vault_invite_email_task(invite_id)` - sends vault invitation
- [x] `send_collaboration_notification_task(notification_data)` - sends activity notifications
- [x] All tasks have `autoretry_for` with exponential backoff (max 3 retries)
- [x] Tasks log success/failure with user email (not full email content)
- [x] Typecheck passes

---

### US-003: Update emails.py with all email sender functions
**Description:** As a developer, I need email helper functions that render templates and send via SMTP for all email types.

**Acceptance Criteria:**
- [x] Update `apps/users/emails.py` with functions:
  - `send_verification_email(user, token)` - verification link
  - `send_password_reset_email(user, uid, token)` - reset link
  - `send_welcome_email(user)` - welcome after verification
  - `send_vault_invite_email(invite)` - vault invitation
  - `send_collaboration_notification(user, notification_data)` - activity notification
- [x] All functions render HTML template + plaintext fallback
- [x] All functions use `DEFAULT_FROM_EMAIL` from settings
- [x] Add `get_unsubscribe_token(user)` helper for notification emails
- [x] Typecheck passes

---

### US-004: Create base email template with Bitcoin DeFi styling
**Description:** As a developer, I need a base HTML email template with the dark Bitcoin DeFi aesthetic that other templates extend.

**Acceptance Criteria:**
- [x] Create `templates/emails/base.html` with:
  - Dark background (#030304 body, #0F1115 content card)
  - SyncScript logo header (text-based, orange gradient)
  - White text (#FFFFFF) on dark background
  - Orange accent color (#F7931A) for links and buttons
  - Responsive design (max-width 600px container)
  - Footer with SyncScript branding and unsubscribe placeholder
- [x] Use inline CSS (email client compatibility)
- [x] Include `{% block content %}{% endblock %}` for child templates
- [x] Include `{% block preheader %}{% endblock %}` for email preview text
- [x] Typecheck passes (templates render without error)

---

### US-005: Create verification email template
**Description:** As a user, I want to receive a branded verification email so I can activate my account.

**Acceptance Criteria:**
- [x] Create `templates/emails/verification.html` extending base.html
- [x] Preheader: "Verify your email to start using SyncScript"
- [x] Greeting: "Welcome to SyncScript, {{ user.first_name|default:user.username }}!"
- [x] Body text explaining verification purpose
- [x] Prominent orange CTA button: "Verify Email Address" linking to verification URL
- [x] Fallback text link below button
- [x] "Link expires in 24 hours" notice
- [x] Create `templates/emails/verification.txt` plaintext version
- [x] Typecheck passes

---

### US-006: Create password reset email template
**Description:** As a user, I want to receive a branded password reset email with security notice.

**Acceptance Criteria:**
- [x] Create `templates/emails/password_reset.html` extending base.html
- [x] Preheader: "Reset your SyncScript password"
- [x] Security notice: "We received a request to reset your password"
- [x] Orange CTA button: "Reset Password" linking to reset URL
- [x] "Link expires in 1 hour" notice
- [x] "If you didn't request this, ignore this email" security text
- [x] IP address and timestamp of request (passed as context)
- [x] Create `templates/emails/password_reset.txt` plaintext version
- [x] Typecheck passes

---

### US-007: Create welcome email template
**Description:** As a user, I want to receive a welcome email after verifying my account.

**Acceptance Criteria:**
- [x] Create `templates/emails/welcome.html` extending base.html
- [x] Preheader: "Your SyncScript account is ready!"
- [x] Celebratory heading: "You're all set!"
- [x] Brief intro to SyncScript features (3 bullet points max)
- [x] Orange CTA button: "Go to Dashboard" linking to app
- [x] Create `templates/emails/welcome.txt` plaintext version
- [x] Typecheck passes

---

### US-008: Create vault invitation email template
**Description:** As a user, I want to receive a branded invitation when someone adds me to a vault.

**Acceptance Criteria:**
- [x] Create `templates/emails/vault_invite.html` extending base.html
- [x] Preheader: "{{ inviter.username }} invited you to collaborate"
- [x] Show inviter name and vault name prominently
- [x] Show role being granted (Contributor/Viewer)
- [x] Orange CTA button: "Accept Invitation" linking to vault
- [x] Brief description of what the vault contains (if provided)
- [x] Create `templates/emails/vault_invite.txt` plaintext version
- [x] Typecheck passes

---

### US-009: Create collaboration notification email template
**Description:** As a user, I want to receive notifications about vault activity.

**Acceptance Criteria:**
- [x] Create `templates/emails/collaboration_notification.html` extending base.html
- [x] Preheader: "New activity in {{ vault.name }}"
- [x] Support notification types: source_added, annotation_created, member_joined
- [x] Show actor name, action, and target (e.g., "John added a new source")
- [x] Orange CTA button: "View in SyncScript"
- [x] Unsubscribe link in footer (using unsubscribe token)
- [x] Create `templates/emails/collaboration_notification.txt` plaintext version
- [x] Typecheck passes

---

### US-010: Add EmailPreference model for unsubscribe
**Description:** As a developer, I need to track user email preferences so users can unsubscribe from notifications.

**Acceptance Criteria:**
- [x] Create `EmailPreference` model in `apps/users/models.py`:
  - `user` (OneToOne FK to User)
  - `collaboration_notifications` (BooleanField, default=True)
  - `marketing_emails` (BooleanField, default=True)
  - `unsubscribe_token` (CharField, unique, auto-generated UUID)
  - `created_at`, `updated_at` timestamps
- [x] Add signal to create EmailPreference on User creation
- [x] Generate migration
- [x] Typecheck passes

---

### US-011: Create unsubscribe endpoint
**Description:** As a user, I want to click unsubscribe links in emails to stop receiving notifications.

**Acceptance Criteria:**
- [x] Add `GET /api/v1/auth/unsubscribe/{token}/` endpoint
- [x] Validates unsubscribe token against EmailPreference
- [x] Sets `collaboration_notifications = False`
- [x] Returns success page redirect or JSON response
- [x] Add `POST /api/v1/users/email-preferences/` to update preferences (authenticated)
- [x] Add to `apps/users/urls.py`
- [x] Typecheck passes

---

### US-012: Update registration to use Celery email task
**Description:** As a developer, I need registration to send verification emails asynchronously.

**Acceptance Criteria:**
- [x] Update `RegisterView` in `apps/users/views.py`
- [x] Replace direct `send_verification_email()` call with `send_verification_email_task.delay()`
- [x] Ensure token is saved to database before queuing task
- [x] Add error handling if Celery is unavailable (fallback to sync)
- [x] Typecheck passes

---

### US-013: Update password reset to use Celery email task
**Description:** As a developer, I need password reset to send emails asynchronously.

**Acceptance Criteria:**
- [x] Update `PasswordResetRequestView` in `apps/users/views.py`
- [x] Replace direct `send_password_reset_email()` call with `send_password_reset_email_task.delay()`
- [x] Pass request IP and timestamp to task for security notice in email
- [x] Add error handling if Celery is unavailable (fallback to sync)
- [x] Typecheck passes

---

### US-014: Send welcome email after verification
**Description:** As a user, I want to receive a welcome email after successfully verifying my account.

**Acceptance Criteria:**
- [x] Update `VerifyEmailView` in `apps/users/views.py`
- [x] After setting `email_verified = True`, queue `send_welcome_email_task.delay(user.id)`
- [x] Only send if this is first-time verification (not re-verification)
- [x] Typecheck passes

---

### US-015: Create verification pending page (frontend)
**Description:** As a user who just registered, I want to see a "check your email" page with resend option.

**Acceptance Criteria:**
- [x] Create `frontend/src/app/auth/verify-email/pending/page.tsx`
- [x] Display "Check your email" message with envelope icon
- [x] Show the email address verification was sent to (from URL param or context)
- [x] "Resend verification email" button with countdown timer (60 seconds)
- [x] Button disabled during countdown, shows remaining time
- [x] Call `/api/v1/auth/resend-verification/` on click
- [x] Show success/error toast after resend
- [x] "Back to login" link
- [x] Bitcoin DeFi dark theme styling
- [x] Typecheck passes

---

### US-016: Add resend verification API call to frontend
**Description:** As a developer, I need frontend API function to resend verification emails.

**Acceptance Criteria:**
- [x] Add `resendVerificationEmail(email: string)` to `frontend/src/lib/api.ts`
- [x] POST to `/api/v1/auth/resend-verification/` with email in body
- [x] Handle rate limit error (429) with appropriate message
- [x] Return typed response
- [x] Typecheck passes

---

### US-017: Create email verification success page (frontend)
**Description:** As a user, I want to see a success page after clicking the verification link.

**Acceptance Criteria:**
- [x] Create `frontend/src/app/auth/verify-email/page.tsx`
- [x] Read `token` from URL search params
- [x] Call verification API on mount
- [x] Show loading state while verifying
- [x] On success: show checkmark icon, "Email Verified!" message, "Continue to Login" button
- [x] On error: show error icon, error message, "Resend Verification" button
- [x] Bitcoin DeFi dark theme styling
- [x] Typecheck passes

---

### US-018: Create password reset request page (frontend)
**Description:** As a user, I want a page to request a password reset link.

**Acceptance Criteria:**
- [x] Create `frontend/src/app/auth/forgot-password/page.tsx`
- [x] Email input field with validation
- [x] "Send Reset Link" submit button
- [x] Call `/api/v1/auth/password-reset/` on submit
- [x] Show success message: "If an account exists, we've sent a reset link"
- [x] "Back to login" link
- [x] Bitcoin DeFi dark theme styling with orange accents
- [x] Typecheck passes

---

### US-019: Add password reset API calls to frontend
**Description:** As a developer, I need frontend API functions for password reset flow.

**Acceptance Criteria:**
- [x] Add `requestPasswordReset(email: string)` to `frontend/src/lib/api.ts`
- [x] Add `confirmPasswordReset(uid: string, token: string, newPassword: string)` to API
- [x] Both return typed responses
- [x] Handle error responses appropriately
- [x] Typecheck passes

---

### US-020: Create password reset form page (frontend)
**Description:** As a user, I want a page to set my new password after clicking the reset link.

**Acceptance Criteria:**
- [x] Create `frontend/src/app/auth/reset-password/page.tsx`
- [x] Read `uid` and `token` from URL search params
- [x] New password input with visibility toggle
- [x] Confirm password input with match validation
- [x] Password strength indicator (min 8 chars, mixed case, number)
- [x] "Reset Password" submit button
- [x] Call `/api/v1/auth/password-reset-confirm/` on submit
- [x] On success: show success message, redirect to login after 3 seconds
- [x] On error: show error message with "Request New Link" button
- [x] Bitcoin DeFi dark theme styling
- [x] Typecheck passes

---

### US-021: Redirect unverified users to verification pending page
**Description:** As an unverified user, I should be redirected to verification page instead of dashboard.

**Acceptance Criteria:**
- [x] Update `frontend/src/providers/AuthProvider.tsx`
- [x] Check `user.email_verified` status after login/auth check
- [x] If `email_verified === false`, redirect to `/auth/verify-email/pending?email={email}`
- [x] Store redirect intent so user goes to original destination after verification
- [x] Typecheck passes

---

### US-022: Add "Forgot Password" link to login page
**Description:** As a user, I want a link on the login page to reset my password.

**Acceptance Criteria:**
- [x] Update `frontend/src/app/auth/login/page.tsx`
- [x] Add "Forgot your password?" link below password field
- [x] Link navigates to `/auth/forgot-password`
- [x] Styled as subtle link (muted color, underline on hover)
- [x] Typecheck passes

---

### US-023: Handle vault invites for unverified users
**Description:** As an unverified user accepting a vault invite, I should be prompted to verify my email.

**Acceptance Criteria:**
- [ ] Update vault invite acceptance logic in backend
- [ ] Allow unverified users to be added to vault memberships
- [ ] When unverified user tries to access vault content, return 403 with `email_verification_required: true`
- [ ] Frontend shows modal: "Verify your email to access this vault"
- [ ] Modal has "Resend Verification" button and "Check your inbox" message
- [ ] Typecheck passes

---

### US-024: Write tests for email verification flow
**Description:** As a developer, I need tests to verify email verification works correctly.

**Acceptance Criteria:**
- [ ] Create/update `apps/users/tests/test_email_verification.py`
- [ ] Test registration creates EmailVerificationToken
- [ ] Test verification endpoint marks email as verified
- [ ] Test expired token returns error
- [ ] Test resend verification rate limiting (3/hour)
- [ ] Test welcome email is queued after verification
- [ ] All tests pass

---

### US-025: Write tests for password reset flow
**Description:** As a developer, I need tests to verify password reset works correctly.

**Acceptance Criteria:**
- [ ] Create/update `apps/users/tests/test_password_reset.py`
- [ ] Test reset request sends email (mock Celery task)
- [ ] Test reset confirm with valid token updates password
- [ ] Test reset confirm with expired token returns error
- [ ] Test reset confirm with invalid uid returns error
- [ ] Test user can login with new password after reset
- [ ] All tests pass

---

## Non-Goals

- Email analytics/tracking (open rates, click rates)
- Rich text email composer in admin
- Multiple email provider failover (single Hostinger SMTP)
- Email scheduling (send later)
- Internationalization/translated email templates
- Push notification integration (separate PRD)
- SMS verification (email only)

## Technical Considerations

- **Existing code:** `emails.py`, `tokens.py`, basic templates already exist - enhance, don't replace
- **Celery:** Already configured in `config/celery.py` and `settings.py`
- **Templates:** Use Django template inheritance with `{% extends "emails/base.html" %}`
- **Inline CSS:** Email clients strip `<style>` tags - use inline styles for compatibility
- **Token security:** Use `secrets.token_urlsafe(32)` for verification tokens
- **Rate limiting:** Already configured with `django-ratelimit` - maintain 3/hour for resend
- **SMTP SSL:** Hostinger uses port 465 with SSL (not TLS on 587)

## Dependencies

- PRD 1 (Auth system) - already implemented
- Celery worker must be running for async emails
- Hostinger SMTP credentials in environment variables
