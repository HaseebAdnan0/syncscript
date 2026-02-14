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
- [ ] Update `config/settings.py` EMAIL settings for Hostinger:
  - `EMAIL_HOST = 'smtp.hostinger.com'`
  - `EMAIL_PORT = 465`
  - `EMAIL_USE_SSL = True` (not TLS)
  - `EMAIL_USE_TLS = False`
- [ ] Add `EMAIL_USE_SSL` env var support
- [ ] Add email connection test management command: `python manage.py test_email`
- [ ] Command sends test email to specified address and reports success/failure
- [ ] Typecheck passes

---

### US-002: Create Celery email tasks module
**Description:** As a developer, I need Celery tasks for sending emails asynchronously so API responses aren't blocked by SMTP.

**Acceptance Criteria:**
- [ ] Create `apps/users/tasks.py` with Celery tasks
- [ ] `send_verification_email_task(user_id, token)` - sends verification email
- [ ] `send_password_reset_email_task(user_id, uid, token)` - sends reset email
- [ ] `send_welcome_email_task(user_id)` - sends welcome after verification
- [ ] `send_vault_invite_email_task(invite_id)` - sends vault invitation
- [ ] `send_collaboration_notification_task(notification_data)` - sends activity notifications
- [ ] All tasks have `autoretry_for` with exponential backoff (max 3 retries)
- [ ] Tasks log success/failure with user email (not full email content)
- [ ] Typecheck passes

---

### US-003: Update emails.py with all email sender functions
**Description:** As a developer, I need email helper functions that render templates and send via SMTP for all email types.

**Acceptance Criteria:**
- [ ] Update `apps/users/emails.py` with functions:
  - `send_verification_email(user, token)` - verification link
  - `send_password_reset_email(user, uid, token)` - reset link
  - `send_welcome_email(user)` - welcome after verification
  - `send_vault_invite_email(invite)` - vault invitation
  - `send_collaboration_notification(user, notification_data)` - activity notification
- [ ] All functions render HTML template + plaintext fallback
- [ ] All functions use `DEFAULT_FROM_EMAIL` from settings
- [ ] Add `get_unsubscribe_token(user)` helper for notification emails
- [ ] Typecheck passes

---

### US-004: Create base email template with Bitcoin DeFi styling
**Description:** As a developer, I need a base HTML email template with the dark Bitcoin DeFi aesthetic that other templates extend.

**Acceptance Criteria:**
- [ ] Create `templates/emails/base.html` with:
  - Dark background (#030304 body, #0F1115 content card)
  - SyncScript logo header (text-based, orange gradient)
  - White text (#FFFFFF) on dark background
  - Orange accent color (#F7931A) for links and buttons
  - Responsive design (max-width 600px container)
  - Footer with SyncScript branding and unsubscribe placeholder
- [ ] Use inline CSS (email client compatibility)
- [ ] Include `{% block content %}{% endblock %}` for child templates
- [ ] Include `{% block preheader %}{% endblock %}` for email preview text
- [ ] Typecheck passes (templates render without error)

---

### US-005: Create verification email template
**Description:** As a user, I want to receive a branded verification email so I can activate my account.

**Acceptance Criteria:**
- [ ] Create `templates/emails/verification.html` extending base.html
- [ ] Preheader: "Verify your email to start using SyncScript"
- [ ] Greeting: "Welcome to SyncScript, {{ user.first_name|default:user.username }}!"
- [ ] Body text explaining verification purpose
- [ ] Prominent orange CTA button: "Verify Email Address" linking to verification URL
- [ ] Fallback text link below button
- [ ] "Link expires in 24 hours" notice
- [ ] Create `templates/emails/verification.txt` plaintext version
- [ ] Typecheck passes

---

### US-006: Create password reset email template
**Description:** As a user, I want to receive a branded password reset email with security notice.

**Acceptance Criteria:**
- [ ] Create `templates/emails/password_reset.html` extending base.html
- [ ] Preheader: "Reset your SyncScript password"
- [ ] Security notice: "We received a request to reset your password"
- [ ] Orange CTA button: "Reset Password" linking to reset URL
- [ ] "Link expires in 1 hour" notice
- [ ] "If you didn't request this, ignore this email" security text
- [ ] IP address and timestamp of request (passed as context)
- [ ] Create `templates/emails/password_reset.txt` plaintext version
- [ ] Typecheck passes

---

### US-007: Create welcome email template
**Description:** As a user, I want to receive a welcome email after verifying my account.

**Acceptance Criteria:**
- [ ] Create `templates/emails/welcome.html` extending base.html
- [ ] Preheader: "Your SyncScript account is ready!"
- [ ] Celebratory heading: "You're all set!"
- [ ] Brief intro to SyncScript features (3 bullet points max)
- [ ] Orange CTA button: "Go to Dashboard" linking to app
- [ ] Create `templates/emails/welcome.txt` plaintext version
- [ ] Typecheck passes

---

### US-008: Create vault invitation email template
**Description:** As a user, I want to receive a branded invitation when someone adds me to a vault.

**Acceptance Criteria:**
- [ ] Create `templates/emails/vault_invite.html` extending base.html
- [ ] Preheader: "{{ inviter.username }} invited you to collaborate"
- [ ] Show inviter name and vault name prominently
- [ ] Show role being granted (Contributor/Viewer)
- [ ] Orange CTA button: "Accept Invitation" linking to vault
- [ ] Brief description of what the vault contains (if provided)
- [ ] Create `templates/emails/vault_invite.txt` plaintext version
- [ ] Typecheck passes

---

### US-009: Create collaboration notification email template
**Description:** As a user, I want to receive notifications about vault activity.

**Acceptance Criteria:**
- [ ] Create `templates/emails/collaboration_notification.html` extending base.html
- [ ] Preheader: "New activity in {{ vault.name }}"
- [ ] Support notification types: source_added, annotation_created, member_joined
- [ ] Show actor name, action, and target (e.g., "John added a new source")
- [ ] Orange CTA button: "View in SyncScript"
- [ ] Unsubscribe link in footer (using unsubscribe token)
- [ ] Create `templates/emails/collaboration_notification.txt` plaintext version
- [ ] Typecheck passes

---

### US-010: Add EmailPreference model for unsubscribe
**Description:** As a developer, I need to track user email preferences so users can unsubscribe from notifications.

**Acceptance Criteria:**
- [ ] Create `EmailPreference` model in `apps/users/models.py`:
  - `user` (OneToOne FK to User)
  - `collaboration_notifications` (BooleanField, default=True)
  - `marketing_emails` (BooleanField, default=True)
  - `unsubscribe_token` (CharField, unique, auto-generated UUID)
  - `created_at`, `updated_at` timestamps
- [ ] Add signal to create EmailPreference on User creation
- [ ] Generate migration
- [ ] Typecheck passes

---

### US-011: Create unsubscribe endpoint
**Description:** As a user, I want to click unsubscribe links in emails to stop receiving notifications.

**Acceptance Criteria:**
- [ ] Add `GET /api/v1/auth/unsubscribe/{token}/` endpoint
- [ ] Validates unsubscribe token against EmailPreference
- [ ] Sets `collaboration_notifications = False`
- [ ] Returns success page redirect or JSON response
- [ ] Add `POST /api/v1/users/email-preferences/` to update preferences (authenticated)
- [ ] Add to `apps/users/urls.py`
- [ ] Typecheck passes

---

### US-012: Update registration to use Celery email task
**Description:** As a developer, I need registration to send verification emails asynchronously.

**Acceptance Criteria:**
- [ ] Update `RegisterView` in `apps/users/views.py`
- [ ] Replace direct `send_verification_email()` call with `send_verification_email_task.delay()`
- [ ] Ensure token is saved to database before queuing task
- [ ] Add error handling if Celery is unavailable (fallback to sync)
- [ ] Typecheck passes

---

### US-013: Update password reset to use Celery email task
**Description:** As a developer, I need password reset to send emails asynchronously.

**Acceptance Criteria:**
- [ ] Update `PasswordResetRequestView` in `apps/users/views.py`
- [ ] Replace direct `send_password_reset_email()` call with `send_password_reset_email_task.delay()`
- [ ] Pass request IP and timestamp to task for security notice in email
- [ ] Add error handling if Celery is unavailable (fallback to sync)
- [ ] Typecheck passes

---

### US-014: Send welcome email after verification
**Description:** As a user, I want to receive a welcome email after successfully verifying my account.

**Acceptance Criteria:**
- [ ] Update `VerifyEmailView` in `apps/users/views.py`
- [ ] After setting `email_verified = True`, queue `send_welcome_email_task.delay(user.id)`
- [ ] Only send if this is first-time verification (not re-verification)
- [ ] Typecheck passes

---

### US-015: Create verification pending page (frontend)
**Description:** As a user who just registered, I want to see a "check your email" page with resend option.

**Acceptance Criteria:**
- [ ] Create `frontend/src/app/auth/verify-email/pending/page.tsx`
- [ ] Display "Check your email" message with envelope icon
- [ ] Show the email address verification was sent to (from URL param or context)
- [ ] "Resend verification email" button with countdown timer (60 seconds)
- [ ] Button disabled during countdown, shows remaining time
- [ ] Call `/api/v1/auth/resend-verification/` on click
- [ ] Show success/error toast after resend
- [ ] "Back to login" link
- [ ] Bitcoin DeFi dark theme styling
- [ ] Typecheck passes

---

### US-016: Add resend verification API call to frontend
**Description:** As a developer, I need frontend API function to resend verification emails.

**Acceptance Criteria:**
- [ ] Add `resendVerificationEmail(email: string)` to `frontend/src/lib/api.ts`
- [ ] POST to `/api/v1/auth/resend-verification/` with email in body
- [ ] Handle rate limit error (429) with appropriate message
- [ ] Return typed response
- [ ] Typecheck passes

---

### US-017: Create email verification success page (frontend)
**Description:** As a user, I want to see a success page after clicking the verification link.

**Acceptance Criteria:**
- [ ] Create `frontend/src/app/auth/verify-email/page.tsx`
- [ ] Read `token` from URL search params
- [ ] Call verification API on mount
- [ ] Show loading state while verifying
- [ ] On success: show checkmark icon, "Email Verified!" message, "Continue to Login" button
- [ ] On error: show error icon, error message, "Resend Verification" button
- [ ] Bitcoin DeFi dark theme styling
- [ ] Typecheck passes

---

### US-018: Create password reset request page (frontend)
**Description:** As a user, I want a page to request a password reset link.

**Acceptance Criteria:**
- [ ] Create `frontend/src/app/auth/forgot-password/page.tsx`
- [ ] Email input field with validation
- [ ] "Send Reset Link" submit button
- [ ] Call `/api/v1/auth/password-reset/` on submit
- [ ] Show success message: "If an account exists, we've sent a reset link"
- [ ] "Back to login" link
- [ ] Bitcoin DeFi dark theme styling with orange accents
- [ ] Typecheck passes

---

### US-019: Add password reset API calls to frontend
**Description:** As a developer, I need frontend API functions for password reset flow.

**Acceptance Criteria:**
- [ ] Add `requestPasswordReset(email: string)` to `frontend/src/lib/api.ts`
- [ ] Add `confirmPasswordReset(uid: string, token: string, newPassword: string)` to API
- [ ] Both return typed responses
- [ ] Handle error responses appropriately
- [ ] Typecheck passes

---

### US-020: Create password reset form page (frontend)
**Description:** As a user, I want a page to set my new password after clicking the reset link.

**Acceptance Criteria:**
- [ ] Create `frontend/src/app/auth/reset-password/page.tsx`
- [ ] Read `uid` and `token` from URL search params
- [ ] New password input with visibility toggle
- [ ] Confirm password input with match validation
- [ ] Password strength indicator (min 8 chars, mixed case, number)
- [ ] "Reset Password" submit button
- [ ] Call `/api/v1/auth/password-reset-confirm/` on submit
- [ ] On success: show success message, redirect to login after 3 seconds
- [ ] On error: show error message with "Request New Link" button
- [ ] Bitcoin DeFi dark theme styling
- [ ] Typecheck passes

---

### US-021: Redirect unverified users to verification pending page
**Description:** As an unverified user, I should be redirected to verification page instead of dashboard.

**Acceptance Criteria:**
- [ ] Update `frontend/src/providers/AuthProvider.tsx`
- [ ] Check `user.email_verified` status after login/auth check
- [ ] If `email_verified === false`, redirect to `/auth/verify-email/pending?email={email}`
- [ ] Store redirect intent so user goes to original destination after verification
- [ ] Typecheck passes

---

### US-022: Add "Forgot Password" link to login page
**Description:** As a user, I want a link on the login page to reset my password.

**Acceptance Criteria:**
- [ ] Update `frontend/src/app/auth/login/page.tsx`
- [ ] Add "Forgot your password?" link below password field
- [ ] Link navigates to `/auth/forgot-password`
- [ ] Styled as subtle link (muted color, underline on hover)
- [ ] Typecheck passes

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
