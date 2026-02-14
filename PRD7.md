# PRD: Frontend Authentication & User Flows

## Introduction

SyncScript needs a complete frontend authentication system that enables users to register, login, manage their profiles, and securely access protected areas of the application. The UI follows the Bitcoin DeFi aesthetic with glass card containers, gradient buttons, and bottom-border inputs. All auth state is managed via Zustand with JWT tokens handled through httpOnly cookies via the backend API.

## Goals

- Provide secure, user-friendly authentication flows (login, register, forgot/reset password)
- Implement client-side validation with inline error messages
- Create a profile page with editable user info and separate security section for password changes
- Build a reusable protected route wrapper that redirects to login with return URL support
- Set up Zustand auth store with persistent state and axios interceptors for token refresh
- Display loading states and toast notifications for all auth operations

## User Stories

### US-001: Create Zustand auth store
**Description:** As a developer, I need a centralized auth state store so that auth state is accessible throughout the app.

**Acceptance Criteria:**
- [x] Create `frontend/src/stores/authStore.ts` with Zustand
- [x] Store shape: `{ user: User | null, isAuthenticated: boolean, isLoading: boolean }`
- [x] Actions: `setUser`, `clearUser`, `setLoading`
- [x] Export `useAuthStore` hook
- [x] Typecheck passes

---

### US-002: Create axios instance with interceptors
**Description:** As a developer, I need a configured axios instance so that API calls include credentials and handle token refresh automatically.

**Acceptance Criteria:**
- [x] Create `frontend/src/lib/api.ts` with axios instance
- [x] Base URL from `NEXT_PUBLIC_API_URL` env var
- [x] `withCredentials: true` for httpOnly cookie handling
- [x] Response interceptor: on 401, attempt token refresh via `/auth/refresh/`
- [x] If refresh fails, clear auth store and redirect to `/login`
- [x] Export configured `api` instance
- [x] Typecheck passes

---

### US-003: Create useAuth hook with auth operations
**Description:** As a developer, I need a custom hook encapsulating auth operations so that components can easily trigger login/register/logout.

**Acceptance Criteria:**
- [x] Create `frontend/src/hooks/useAuth.ts`
- [x] Expose: `login(email, password)`, `register(data)`, `logout()`, `refreshUser()`
- [x] `login` calls POST `/auth/login/`, updates store on success
- [x] `register` calls POST `/auth/register/`, auto-logs in on success
- [x] `logout` calls POST `/auth/logout/`, clears store
- [x] `refreshUser` calls GET `/auth/me/` to hydrate user on app load
- [x] All methods return `{ success, error }` for UI handling
- [x] Typecheck passes

---

### US-004: Create AuthProvider for app initialization
**Description:** As a developer, I need an auth provider component so that user state is hydrated on app load.

**Acceptance Criteria:**
- [x] Create `frontend/src/providers/AuthProvider.tsx`
- [x] On mount, call `refreshUser()` to check existing session
- [x] Show loading spinner while checking auth
- [x] Wrap children once auth check completes
- [x] Add to root layout
- [x] Typecheck passes

---

### US-005: Create reusable form input component (Bitcoin DeFi style)
**Description:** As a user, I want styled form inputs so that the auth forms match the app's design system.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/ui/FormInput.tsx`
- [x] Bottom border style: `border-b-2 border-white/20 focus:border-[#F7931A]`
- [x] Background: `bg-black/50`
- [x] Support props: `label`, `error`, `type`, `placeholder`, standard input props
- [x] Display inline error message in red below input when `error` prop present
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-006: Create gradient button component
**Description:** As a user, I want styled buttons so that auth forms have the signature gradient CTA style.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/ui/GradientButton.tsx`
- [x] Gradient: `bg-gradient-to-r from-[#EA580C] to-[#F7931A]`
- [x] Pill shape: `rounded-full`
- [x] Glow shadow: `shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)]`
- [x] Hover scale: `hover:scale-105`
- [x] Support `isLoading` prop showing spinner and disabling button
- [x] Support `disabled` prop with reduced opacity
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-007: Create glass card container component
**Description:** As a user, I want auth forms wrapped in glass cards so that they have the premium aesthetic.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/ui/GlassCard.tsx`
- [x] Style: `backdrop-blur-lg bg-white/5 border border-white/10 rounded-2xl`
- [x] Accept `className` prop for size customization
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-008: Create auth layout with centered card
**Description:** As a user, I want auth pages to have a consistent centered layout so that the experience feels cohesive.

**Acceptance Criteria:**
- [x] Create `frontend/src/app/(auth)/layout.tsx`
- [x] Full viewport height, centered content
- [x] Dark background `bg-[#030304]`
- [x] Optional floating decorative elements (subtle gradients)
- [x] Slot for page content
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-009: Build login page UI
**Description:** As a user, I want a login page so that I can access my account.

**Acceptance Criteria:**
- [x] Create `frontend/src/app/(auth)/login/page.tsx`
- [x] Glass card container with logo/title
- [x] Email input with FormInput component
- [x] Password input with FormInput component (type="password")
- [x] "Forgot password?" link to `/forgot-password`
- [x] Gradient submit button "Sign In"
- [x] Link to register page: "Don't have an account? Sign up"
- [x] Form is presentational only (no logic yet)
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-010: Add login form validation and submission
**Description:** As a user, I want the login form to validate my input and submit so that I can authenticate.

**Acceptance Criteria:**
- [x] Email validation: required, valid email format
- [x] Password validation: required, minimum 8 characters
- [x] Inline error messages displayed below invalid fields
- [x] On submit, call `useAuth().login()`
- [x] Show loading state on button during submission
- [x] On success, redirect to `returnUrl` query param or `/dashboard`
- [x] On error, display error toast notification
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-011: Build registration page UI
**Description:** As a user, I want a registration page so that I can create an account.

**Acceptance Criteria:**
- [x] Create `frontend/src/app/(auth)/register/page.tsx`
- [x] Glass card container with title "Create Account"
- [x] Fields: name, email, password, confirm password
- [x] All fields use FormInput component
- [x] Gradient submit button "Create Account"
- [x] Link to login: "Already have an account? Sign in"
- [x] Form is presentational only (no logic yet)
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-012: Add registration form validation and submission
**Description:** As a user, I want the registration form to validate and submit so that I can create my account.

**Acceptance Criteria:**
- [x] Name validation: required, minimum 2 characters
- [x] Email validation: required, valid email format
- [x] Password validation: required, min 8 chars, show strength indicator (weak/medium/strong)
- [x] Confirm password: must match password field
- [x] Inline error messages for all validation failures
- [x] On submit, call `useAuth().register()`
- [x] Show loading state during submission
- [x] On success, auto-login and redirect to `/dashboard`
- [x] On error, display error toast
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-013: Build forgot password page
**Description:** As a user, I want a forgot password page so that I can request a password reset link.

**Acceptance Criteria:**
- [x] Create `frontend/src/app/(auth)/forgot-password/page.tsx`
- [x] Glass card with title "Reset Password"
- [x] Email input field
- [x] Gradient submit button "Send Reset Link"
- [x] Link back to login page
- [x] Email validation: required, valid format
- [x] On submit, POST to `/auth/password-reset/`
- [x] On success, show success message "Check your email for reset link"
- [x] On error, show error toast
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-014: Build reset password page
**Description:** As a user, I want a reset password page so that I can set a new password using my reset token.

**Acceptance Criteria:**
- [x] Create `frontend/src/app/(auth)/reset-password/page.tsx`
- [x] Read `token` from URL query params
- [x] Glass card with title "Set New Password"
- [x] New password field with strength indicator
- [x] Confirm password field
- [x] Validation: passwords match, min 8 chars
- [x] On submit, POST to `/auth/password-reset/confirm/` with token
- [x] On success, show toast and redirect to `/login`
- [x] On invalid/expired token, show error message with link to forgot-password
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-015: Create ProtectedRoute wrapper component
**Description:** As a developer, I need a protected route wrapper so that unauthenticated users are redirected to login.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/auth/ProtectedRoute.tsx`
- [x] Check `isAuthenticated` from auth store
- [x] If not authenticated and not loading, redirect to `/login?returnUrl={currentPath}`
- [x] Show loading spinner while auth state is being determined
- [x] Render children when authenticated
- [x] Typecheck passes

---

### US-016: Create toast notification system
**Description:** As a user, I want toast notifications so that I receive feedback on auth operations.

**Acceptance Criteria:**
- [x] Set up toast provider using Radix Toast or similar
- [x] Create `useToast` hook with `toast.success()`, `toast.error()` methods
- [x] Toast appears in top-right corner
- [x] Auto-dismiss after 5 seconds
- [x] Style: dark background, orange accent for success, red for error
- [x] Add ToastProvider to root layout
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-017: Build profile page layout with tabs
**Description:** As a user, I want a profile page with tabs so that I can manage my account settings.

**Acceptance Criteria:**
- [ ] Create `frontend/src/app/(protected)/profile/page.tsx`
- [ ] Wrap with ProtectedRoute
- [ ] Two tabs: "Profile" and "Security"
- [ ] Use Radix Tabs component
- [ ] Tab styling matches Bitcoin DeFi aesthetic (orange active indicator)
- [ ] Default to "Profile" tab
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-018: Build profile info form
**Description:** As a user, I want to view and edit my profile information so that I can keep my account up to date.

**Acceptance Criteria:**
- [ ] Profile tab shows form with: name, email (read-only), bio (optional textarea)
- [ ] Pre-populate with current user data from store
- [ ] Editable fields use FormInput components
- [ ] Gradient "Save Changes" button
- [ ] On submit, PUT to `/auth/me/`
- [ ] Show loading state during save
- [ ] On success, update store and show success toast
- [ ] On error, show error toast
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-019: Build security tab with password change
**Description:** As a user, I want to change my password from the security tab so that I can keep my account secure.

**Acceptance Criteria:**
- [ ] Security tab shows password change form
- [ ] Fields: current password, new password (with strength indicator), confirm new password
- [ ] Validation: current required, new min 8 chars, confirm must match
- [ ] Gradient "Update Password" button
- [ ] On submit, POST to `/auth/password-change/`
- [ ] Show loading state during submission
- [ ] On success, clear form and show success toast
- [ ] On error (wrong current password), show inline error
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-020: Add logout functionality to app header
**Description:** As a user, I want a logout button so that I can securely end my session.

**Acceptance Criteria:**
- [ ] Add user dropdown/menu to app header (or create minimal header if none exists)
- [ ] Show user name/avatar when authenticated
- [ ] Dropdown includes "Logout" option
- [ ] On click, call `useAuth().logout()`
- [ ] Show loading state briefly
- [ ] On success, redirect to `/login` and show toast "Logged out successfully"
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-021: Add password strength indicator component
**Description:** As a user, I want to see password strength feedback so that I create secure passwords.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/ui/PasswordStrength.tsx`
- [ ] Accepts `password` prop, calculates strength
- [ ] Strength levels: weak (red), medium (yellow), strong (green)
- [ ] Visual bar that fills based on strength
- [ ] Text label showing current strength
- [ ] Criteria: length, uppercase, lowercase, numbers, special chars
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-022: Integration test - complete auth flow
**Description:** As a developer, I need to verify the complete auth flow works end-to-end.

**Acceptance Criteria:**
- [ ] Verify register → auto-login → dashboard redirect works
- [ ] Verify login → returnUrl redirect works
- [ ] Verify protected route redirects unauthenticated users
- [ ] Verify logout clears state and redirects
- [ ] Verify token refresh happens silently on 401
- [ ] Verify forgot/reset password flow completes
- [ ] Document any issues found in progress7.txt
- [ ] Typecheck passes

## Non-Goals

- OAuth/social login (Google, GitHub) - not included in this phase
- Email verification flow - registration auto-logs in
- Two-factor authentication (2FA)
- Remember me / persistent sessions beyond default token expiry
- Account deletion functionality
- Avatar upload on profile page

## Technical Considerations

- **Depends on:** Backend auth API endpoints must be complete (PRD1/US-001 through US-010)
- **Cookie handling:** Backend sets httpOnly cookies; frontend uses `withCredentials: true`
- **Token refresh:** Handled transparently via axios interceptor; no manual token storage in frontend
- **Form library:** Can use react-hook-form for validation or native controlled components
- **Routing:** Next.js App Router with route groups `(auth)` and `(protected)`
- **Components:** Build on ShadCN primitives, customize per DESIGN_RULES.md
- **State persistence:** Zustand with no persistence (auth state comes from cookies/API)
