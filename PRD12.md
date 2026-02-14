# PRD 12: OAuth Authentication (Google + GitHub)

## Introduction

Add social authentication to SyncScript using Google and GitHub OAuth providers. Users can sign up/login with their existing social accounts, reducing friction and password fatigue. OAuth accounts can be linked to existing email/password accounts with secure password confirmation.

## Goals

- Enable one-click registration/login via Google OAuth 2.0
- Enable one-click registration/login via GitHub OAuth
- Securely link OAuth providers to existing accounts (requires password confirmation)
- Generate JWT tokens after successful OAuth authentication
- Handle edge cases gracefully (private GitHub email, account conflicts)
- Provide "Connected Accounts" management in user settings

## User Stories

### US-001: Install and configure django-allauth
**Description:** As a developer, I need django-allauth installed and configured so OAuth providers can be added.

**Acceptance Criteria:**
- [ ] Add `django-allauth[socialaccount]` to requirements.txt
- [ ] Add allauth apps to INSTALLED_APPS: `allauth`, `allauth.account`, `allauth.socialaccount`, `allauth.socialaccount.providers.google`, `allauth.socialaccount.providers.github`
- [ ] Add `allauth.account.middleware.AccountMiddleware` to MIDDLEWARE
- [ ] Configure AUTHENTICATION_BACKENDS to include allauth
- [ ] Set `ACCOUNT_EMAIL_REQUIRED = True`, `ACCOUNT_AUTHENTICATION_METHOD = 'email'`
- [ ] Set `SOCIALACCOUNT_AUTO_SIGNUP = True` for new users
- [ ] Set `SOCIALACCOUNT_EMAIL_AUTHENTICATION = False` (we handle linking manually)
- [ ] Add allauth URLs to urlpatterns (under `/api/v1/auth/`)
- [ ] Run migrations for allauth tables
- [ ] Typecheck passes

---

### US-002: Configure Google OAuth provider settings
**Description:** As a developer, I need Google OAuth configured so users can authenticate with Google.

**Acceptance Criteria:**
- [ ] Add SOCIALACCOUNT_PROVIDERS config for Google with required scopes (`email`, `profile`)
- [ ] Create environment variables: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- [ ] Add Google provider configuration to load from env vars
- [ ] Set callback URL pattern: `/api/v1/auth/google/callback/`
- [ ] Document required Google Cloud Console setup in USER_SETUP.md
- [ ] Typecheck passes

---

### US-003: Configure GitHub OAuth provider settings
**Description:** As a developer, I need GitHub OAuth configured so users can authenticate with GitHub.

**Acceptance Criteria:**
- [ ] Add SOCIALACCOUNT_PROVIDERS config for GitHub with required scopes (`read:user`, `user:email`)
- [ ] Create environment variables: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`
- [ ] Add GitHub provider configuration to load from env vars
- [ ] Set callback URL pattern: `/api/v1/auth/github/callback/`
- [ ] Document required GitHub OAuth App setup in USER_SETUP.md
- [ ] Typecheck passes

---

### US-004: Create custom OAuth adapter for JWT integration
**Description:** As a developer, I need a custom adapter that generates JWT tokens after successful OAuth instead of session-based auth.

**Acceptance Criteria:**
- [ ] Create `apps/users/adapters.py` with custom SocialAccountAdapter
- [ ] Override `authentication_success_response` to return JWT tokens (access + refresh)
- [ ] Use existing `get_tokens_for_user` utility from simplejwt
- [ ] Store tokens in httpOnly cookies (same as regular login)
- [ ] Redirect to frontend success URL with success indicator
- [ ] Configure adapter in settings: `SOCIALACCOUNT_ADAPTER`
- [ ] Typecheck passes

---

### US-005: Create Google OAuth redirect endpoint
**Description:** As a user, I want to click "Continue with Google" and be redirected to Google's consent screen.

**Acceptance Criteria:**
- [ ] Create `GET /api/v1/auth/google/` endpoint in `apps/users/views.py`
- [ ] Accept optional `next` query param for post-auth redirect
- [ ] Store `next` URL in session for callback retrieval
- [ ] Redirect to Google OAuth consent screen via allauth
- [ ] Handle missing/invalid Google credentials with 503 error
- [ ] Typecheck passes

---

### US-006: Create Google OAuth callback handler
**Description:** As a user returning from Google, I need the callback to create/link my account and log me in.

**Acceptance Criteria:**
- [ ] Create `GET /api/v1/auth/google/callback/` endpoint
- [ ] Extract user info: email, name (first + last), profile picture URL
- [ ] If email is new: create User + SocialAccount, generate JWT, redirect to frontend
- [ ] If email exists with OAuth: login, generate JWT, redirect to frontend
- [ ] If email exists with password only: redirect to frontend with `link_required=true` and `provider=google`
- [ ] Store OAuth data temporarily in session for linking flow
- [ ] Handle errors: redirect to frontend with `error` query param
- [ ] Typecheck passes

---

### US-007: Create GitHub OAuth redirect endpoint
**Description:** As a user, I want to click "Continue with GitHub" and be redirected to GitHub's authorization screen.

**Acceptance Criteria:**
- [ ] Create `GET /api/v1/auth/github/` endpoint in `apps/users/views.py`
- [ ] Accept optional `next` query param for post-auth redirect
- [ ] Store `next` URL in session for callback retrieval
- [ ] Redirect to GitHub OAuth authorization screen via allauth
- [ ] Handle missing/invalid GitHub credentials with 503 error
- [ ] Typecheck passes

---

### US-008: Create GitHub OAuth callback handler
**Description:** As a user returning from GitHub, I need the callback to create/link my account and log me in.

**Acceptance Criteria:**
- [ ] Create `GET /api/v1/auth/github/callback/` endpoint
- [ ] Extract user info: email (from user:email scope), username, avatar URL
- [ ] If email is available and new: create User + SocialAccount, generate JWT, redirect
- [ ] If email is available and exists: same logic as Google (link_required or login)
- [ ] If email is unavailable (private): redirect to frontend with `email_required=true` and temp token
- [ ] Store GitHub OAuth data in session for email prompt flow
- [ ] Typecheck passes

---

### US-009: Create account linking endpoint with password confirmation
**Description:** As a user with an existing password account, I want to link my OAuth provider after confirming my password.

**Acceptance Criteria:**
- [ ] Create `POST /api/v1/auth/oauth/link/` endpoint
- [ ] Accept JSON body: `{ password: string, provider: 'google' | 'github' }`
- [ ] Verify user password is correct
- [ ] Retrieve OAuth data from session (stored during callback)
- [ ] Create SocialAccount linking OAuth provider to existing user
- [ ] Clear OAuth session data after successful link
- [ ] Generate new JWT tokens and return them
- [ ] Return 401 if password incorrect
- [ ] Return 400 if no pending OAuth data in session
- [ ] Typecheck passes

---

### US-010: Create email submission endpoint for GitHub private email
**Description:** As a user with a private GitHub email, I need to provide my email to complete registration.

**Acceptance Criteria:**
- [ ] Create `POST /api/v1/auth/oauth/complete-email/` endpoint
- [ ] Accept JSON body: `{ email: string, temp_token: string }`
- [ ] Validate temp_token matches session data
- [ ] Validate email format and uniqueness
- [ ] If email exists: return `link_required=true` for linking flow
- [ ] If email is new: create User + SocialAccount, generate JWT, return tokens
- [ ] Clear session data after completion
- [ ] Typecheck passes

---

### US-011: Create connected accounts list endpoint
**Description:** As an authenticated user, I want to see which OAuth providers are connected to my account.

**Acceptance Criteria:**
- [ ] Create `GET /api/v1/auth/oauth/connected/` endpoint (requires auth)
- [ ] Return list of connected providers: `[{ provider: string, connected_at: datetime, email: string }]`
- [ ] Include provider-specific data: Google profile picture, GitHub username
- [ ] Return empty array if no OAuth providers connected
- [ ] Typecheck passes

---

### US-012: Create OAuth provider unlink endpoint
**Description:** As a user, I want to disconnect an OAuth provider from my account.

**Acceptance Criteria:**
- [ ] Create `DELETE /api/v1/auth/oauth/connected/{provider}/` endpoint (requires auth)
- [ ] Validate provider is 'google' or 'github'
- [ ] Check user has at least one other auth method (password or another OAuth)
- [ ] If this is the only auth method: return 400 with error message
- [ ] Delete SocialAccount for this provider
- [ ] Return 204 on success
- [ ] Typecheck passes

---

### US-013: Create OAuthButtons component
**Description:** As a user, I want visually distinct OAuth buttons following brand guidelines.

**Acceptance Criteria:**
- [ ] Create `components/features/auth/OAuthButtons.tsx`
- [ ] Google button: white background, Google "G" logo, "Continue with Google" text
- [ ] GitHub button: dark background (#24292e), GitHub logo, "Continue with GitHub" text
- [ ] Both buttons full-width, consistent height (48px), rounded corners
- [ ] Hover states with subtle shadow/brightness change
- [ ] Accept `disabled` prop to disable both buttons
- [ ] Accept `loading` prop to show loading state
- [ ] Clicking triggers redirect to respective OAuth endpoint
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-014: Add OAuth buttons to login page
**Description:** As a user on the login page, I want to see OAuth options prominently.

**Acceptance Criteria:**
- [ ] Import and add OAuthButtons to login page
- [ ] Position above email/password form with "OR" divider
- [ ] Divider styled: horizontal line with "or" text centered
- [ ] OAuth buttons disabled while email/password form is submitting
- [ ] Maintain existing login form functionality
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-015: Add OAuth buttons to registration page
**Description:** As a user on the registration page, I want to see OAuth options prominently.

**Acceptance Criteria:**
- [ ] Import and add OAuthButtons to registration page
- [ ] Position above email/password form with "OR" divider
- [ ] Same styling as login page for consistency
- [ ] OAuth buttons disabled while registration form is submitting
- [ ] Maintain existing registration form functionality
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-016: Handle OAuth redirect loading state
**Description:** As a user who clicked an OAuth button, I want to see a loading state while being redirected.

**Acceptance Criteria:**
- [ ] Show full-page loading overlay when OAuth redirect starts
- [ ] Display message: "Redirecting to {Provider}..."
- [ ] Show spinner animation
- [ ] Prevent duplicate clicks during redirect
- [ ] Use zustand or local state to track redirect status
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-017: Create OAuth callback landing page
**Description:** As a user returning from OAuth, I need a page to process the callback and redirect appropriately.

**Acceptance Criteria:**
- [ ] Create `/auth/callback` page in Next.js
- [ ] Parse query params: `success`, `error`, `link_required`, `email_required`, `provider`
- [ ] If `success=true`: show success message, redirect to dashboard after 1s
- [ ] If `link_required=true`: redirect to account linking modal/page
- [ ] If `email_required=true`: redirect to email prompt modal/page
- [ ] If `error`: show error message with retry option
- [ ] Handle token cookie setting (backend sets httpOnly cookie)
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-018: Create account linking confirmation modal
**Description:** As a user with an existing account, I need to confirm linking by entering my password.

**Acceptance Criteria:**
- [ ] Create `components/features/auth/AccountLinkingModal.tsx`
- [ ] Display: "An account with this email already exists"
- [ ] Show which provider is being linked (Google/GitHub icon + name)
- [ ] Password input field with show/hide toggle
- [ ] "Link Account" button, "Cancel" button
- [ ] Call `POST /api/v1/auth/oauth/link/` on submit
- [ ] Show loading state during API call
- [ ] On success: close modal, redirect to dashboard
- [ ] On error: show inline error message
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-019: Create email prompt modal for GitHub users
**Description:** As a GitHub user with a private email, I need to provide my email to complete registration.

**Acceptance Criteria:**
- [ ] Create `components/features/auth/EmailPromptModal.tsx`
- [ ] Display: "GitHub couldn't provide your email"
- [ ] Email input field with validation
- [ ] "Complete Registration" button, "Cancel" button
- [ ] Call `POST /api/v1/auth/oauth/complete-email/` on submit
- [ ] Handle `link_required` response: show linking modal instead
- [ ] On success: close modal, redirect to dashboard
- [ ] On validation error: show inline message
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-020: Create Connected Accounts settings section
**Description:** As a user, I want to manage my connected OAuth providers in settings.

**Acceptance Criteria:**
- [ ] Create `components/features/settings/ConnectedAccounts.tsx`
- [ ] Fetch connected accounts from `GET /api/v1/auth/oauth/connected/`
- [ ] Display each provider: icon, name, connected email, "Disconnect" button
- [ ] Show "Connect" button for providers not yet connected
- [ ] Connect button redirects to OAuth flow with `next=/settings`
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-021: Implement OAuth provider disconnect functionality
**Description:** As a user, I want to disconnect an OAuth provider from my account.

**Acceptance Criteria:**
- [ ] Add disconnect handler to ConnectedAccounts component
- [ ] Show confirmation dialog: "Disconnect {Provider}?"
- [ ] Call `DELETE /api/v1/auth/oauth/connected/{provider}/`
- [ ] Handle "last auth method" error: show message explaining they need password first
- [ ] On success: remove provider from list, show success toast
- [ ] Disable disconnect button while request is pending
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-022: Add Connected Accounts to settings page
**Description:** As a user, I want to access Connected Accounts from my settings page.

**Acceptance Criteria:**
- [ ] Import ConnectedAccounts into settings page
- [ ] Add new section/tab: "Connected Accounts"
- [ ] Position after password/security section
- [ ] Include section heading and description
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-023: Handle OAuth error states in UI
**Description:** As a user, I want clear error messages when OAuth fails.

**Acceptance Criteria:**
- [ ] Create error message mappings for common OAuth errors
- [ ] "access_denied": "You cancelled the sign-in process"
- [ ] "invalid_request": "Something went wrong. Please try again"
- [ ] "email_exists": "This email is already registered. Please login with your password"
- [ ] "provider_error": "Could not connect to {Provider}. Please try again"
- [ ] Display errors on callback page and in modals
- [ ] Include "Try Again" button that restarts OAuth flow
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-024: Add API client methods for OAuth endpoints
**Description:** As a frontend developer, I need typed API methods for OAuth operations.

**Acceptance Criteria:**
- [ ] Add to `lib/api.ts`: `linkOAuthAccount(password, provider)`
- [ ] Add to `lib/api.ts`: `completeOAuthEmail(email, tempToken)`
- [ ] Add to `lib/api.ts`: `getConnectedAccounts()`
- [ ] Add to `lib/api.ts`: `disconnectOAuthProvider(provider)`
- [ ] Add TypeScript types for request/response shapes
- [ ] Handle error responses consistently
- [ ] Typecheck passes

---

### US-025: Write backend tests for OAuth flows
**Description:** As a developer, I need tests to verify OAuth functionality works correctly.

**Acceptance Criteria:**
- [ ] Test Google callback creates new user when email is new
- [ ] Test Google callback returns link_required when email exists
- [ ] Test GitHub callback handles missing email correctly
- [ ] Test account linking endpoint validates password
- [ ] Test account linking endpoint rejects wrong password
- [ ] Test unlink endpoint prevents removing last auth method
- [ ] Test connected accounts endpoint returns correct data
- [ ] All tests pass
- [ ] Typecheck passes

## Non-Goals

- Mobile/native OAuth flows (deep linking)
- Additional OAuth providers (Apple, Microsoft, Twitter)
- OAuth token refresh for API access to Google/GitHub
- Importing user data from OAuth providers (contacts, repos, etc.)
- Two-factor authentication via OAuth
- Enterprise SSO/SAML integration

## Technical Considerations

### django-allauth Configuration
- Use `DefaultSocialAccountAdapter` as base for custom adapter
- Session-based temporary storage for linking flow (not cookies for security)
- Custom redirect URLs to Next.js frontend

### Frontend State Management
- OAuth redirect state in zustand (persists across redirects)
- React Query for connected accounts data fetching
- Modal state managed locally in callback page

### Security
- CSRF protection on OAuth endpoints
- Validate `state` parameter in callbacks
- Password confirmation required for account linking
- httpOnly cookies for JWT storage
- Rate limit OAuth endpoints to prevent abuse

### Environment Variables Required
```
# Backend
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# Frontend
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_GOOGLE_CLIENT_ID=  # For button branding only
```

### File Locations
- Backend: `apps/users/adapters.py`, `apps/users/views.py`, `apps/users/urls.py`
- Frontend: `components/features/auth/OAuthButtons.tsx`, `components/features/auth/AccountLinkingModal.tsx`, `components/features/auth/EmailPromptModal.tsx`, `components/features/settings/ConnectedAccounts.tsx`
- Pages: `app/auth/callback/page.tsx`
