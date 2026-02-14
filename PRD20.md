# PRD: Onboarding & Interactive Tutorial

## Introduction

Create a comprehensive new user onboarding experience for SyncScript that guides users through their first interactions with the platform. The onboarding includes a welcome flow, choice between guided vault creation or exploring a pre-built demo vault, an interactive tutorial highlighting key UI elements, and celebratory completion. Users can resume from their last step if they abandon mid-flow, and the demo vault is deletable with prompts to recreate.

## Goals

- Reduce time-to-value for new users by providing immediate, guided context
- Demonstrate SyncScript's core features (vaults, sources, annotations, collaboration)
- Provide a pre-populated demo vault with real research content for exploration
- Track basic onboarding metrics (path chosen, completion status)
- Deliver a polished, mobile-responsive onboarding experience
- Allow users to restart tutorial or reset demo vault from settings

## User Stories

### US-001: Add onboarding fields to User model
**Description:** As a developer, I need to store onboarding state on the user model so we can track progress and resume from last step.

**Acceptance Criteria:**
- [x] Add `onboarding_completed` BooleanField (default False)
- [x] Add `onboarding_step` CharField (max 50, nullable) to track current step
- [x] Add `onboarding_data` JSONField (default dict) for path choice and metadata
- [x] Add `onboarding_path` CharField choices: 'guided', 'demo', 'skipped' (nullable)
- [x] Generate and run migration successfully
- [x] Typecheck passes

### US-002: Create onboarding progress API endpoint
**Description:** As a frontend developer, I need an API endpoint to update onboarding progress so the UI can persist state.

**Acceptance Criteria:**
- [x] Create `PATCH /api/v1/users/me/onboarding/` endpoint
- [x] Accepts: `step`, `completed`, `path`, `data` (all optional)
- [x] Returns updated onboarding state
- [x] Only authenticated users can access their own onboarding
- [x] Add `GET /api/v1/users/me/onboarding/` to fetch current state
- [x] Typecheck passes
- [x] Tests pass

### US-003: Create demo vault fixture data
**Description:** As a developer, I need a fixture/template with demo vault content so we can populate it for new users.

**Acceptance Criteria:**
- [x] Create `apps/users/fixtures/demo_vault.json` with:
  - Vault: "AI Research Papers 2025"
  - 10 real sources (arXiv links, freely available papers)
  - 15+ annotations with threaded replies demonstrating features
- [x] Sources include mix: PDF links, arXiv, web articles
- [x] Annotations demonstrate: threading, citations, metadata extraction
- [x] Fixture is loadable via Django management command
- [x] Typecheck passes

### US-004: Create demo vault service
**Description:** As a developer, I need a service to create the demo vault for a user on first login so they have content to explore.

**Acceptance Criteria:**
- [x] Create `apps/users/services/onboarding.py` with `create_demo_vault(user)` function
- [x] Creates vault owned by user (not shared)
- [x] Populates with sources and annotations from fixture template
- [x] Annotations are created by the user (not a system user)
- [x] Returns created vault instance
- [x] Idempotent: does not create duplicate if vault exists with same name
- [x] Typecheck passes
- [x] Tests pass

### US-005: Create demo vault reset endpoint
**Description:** As a user, I want to reset my demo vault to its original state so I can start fresh after experimenting.

**Acceptance Criteria:**
- [x] Create `POST /api/v1/users/me/demo-vault/reset/` endpoint
- [x] Deletes existing demo vault and all its sources/annotations
- [x] Creates fresh demo vault from template
- [x] Returns new vault data
- [x] Typecheck passes
- [x] Tests pass

### US-006: Prompt to recreate deleted demo vault
**Description:** As a user, I want to be prompted to recreate the demo vault if I delete it so I don't lose access to the learning resource.

**Acceptance Criteria:**
- [x] Create `GET /api/v1/users/me/demo-vault/status/` endpoint
- [x] Returns `{ exists: boolean, vault_id: string | null }`
- [x] Create `POST /api/v1/users/me/demo-vault/create/` endpoint
- [x] Creates demo vault if it doesn't exist, returns vault data
- [x] Returns error if demo vault already exists
- [x] Typecheck passes
- [x] Tests pass

### US-007: Create OnboardingProvider context
**Description:** As a frontend developer, I need a React context to manage onboarding state so components can access and update it.

**Acceptance Criteria:**
- [x] Create `providers/OnboardingProvider.tsx`
- [x] Fetches onboarding state on mount for authenticated users
- [x] Provides: `step`, `completed`, `path`, `data`, `updateOnboarding()`, `completeOnboarding()`
- [x] Syncs state changes to backend via PATCH endpoint
- [x] Handles loading and error states
- [x] Typecheck passes

### US-008: Create WelcomeModal component
**Description:** As a new user, I want to see a welcome modal after first login so I understand what SyncScript offers.

**Acceptance Criteria:**
- [x] Create `components/features/onboarding/WelcomeModal.tsx`
- [x] Shows "Welcome to SyncScript, {name}!" heading with gradient text
- [x] Displays 3 feature highlights with illustrations/icons:
  - Knowledge Vaults for organized research
  - Real-time collaboration with team
  - Annotations and citations management
- [x] "Let's get started" CTA button styled per design system
- [x] Modal uses glass morphism aesthetic
- [x] Responsive: works on mobile screens
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-009: Create PathSelection component
**Description:** As a new user, I want to choose my onboarding path so I can learn in my preferred way.

**Acceptance Criteria:**
- [x] Create `components/features/onboarding/PathSelection.tsx`
- [x] Three options as large cards:
  - "Create your first vault" (guided icon)
  - "Explore demo vault" (explore icon)
  - "Skip tutorial" (skip icon)
- [x] Cards have hover effects per design system
- [x] Selecting a path updates onboarding state and advances flow
- [x] "Skip" dismisses onboarding, marks path as 'skipped'
- [x] Responsive grid: 3 columns desktop, 1 column mobile
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-010: Create GuidedVaultWizard component - Step 1 (Name)
**Description:** As a new user choosing guided creation, I want to name my first vault as the first step.

**Acceptance Criteria:**
- [x] Create `components/features/onboarding/GuidedVaultWizard.tsx`
- [x] Step 1: "Name your vault" with input field
- [x] Input styled per design system (bottom border, orange focus)
- [x] Progress indicator shows "Step 1 of 3"
- [x] "Next" button (disabled until name entered)
- [x] Stores vault name in local state
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-011: GuidedVaultWizard Step 2 (Add Source)
**Description:** As a new user, I want to add my first source URL as step 2 of vault creation.

**Acceptance Criteria:**
- [x] Step 2: "Add your first source" with URL input
- [x] URL validation (basic format check)
- [x] "Back" button to return to Step 1
- [x] "Next" button to proceed (can skip with "Skip this step" link)
- [x] Progress indicator shows "Step 2 of 3"
- [x] Stores source URL in local state
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-012: GuidedVaultWizard Step 3 (Invite Collaborator)
**Description:** As a new user, I want to optionally invite a collaborator as the final step.

**Acceptance Criteria:**
- [x] Step 3: "Invite a collaborator (optional)" with email input
- [x] Email validation (basic format check)
- [x] "Back" button to return to Step 2
- [x] "Create Vault" button to complete wizard
- [x] "Skip" link to create without inviting
- [x] Progress indicator shows "Step 3 of 3"
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-013: GuidedVaultWizard submission logic
**Description:** As a new user completing the wizard, I want my vault created with the source and invite applied.

**Acceptance Criteria:**
- [x] On "Create Vault" click:
  - Creates vault via API
  - Adds source if URL provided
  - Sends invite if email provided
- [x] Shows loading state during creation
- [x] On success: advances to tutorial step
- [x] On error: shows error message, allows retry
- [x] Updates onboarding state to 'tutorial' step
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-014: Install and configure react-joyride
**Description:** As a developer, I need react-joyride installed and configured so we can build the interactive tutorial.

**Acceptance Criteria:**
- [x] Install `react-joyride` package
- [x] Create `components/features/onboarding/TutorialProvider.tsx` wrapper
- [x] Configure global styles to match design system (orange accent, dark theme)
- [x] Custom tooltip component with glass morphism styling
- [x] Typecheck passes

### US-015: Create InteractiveTutorial component
**Description:** As a new user, I want an interactive tutorial highlighting key UI elements so I learn where things are.

**Acceptance Criteria:**
- [x] Create `components/features/onboarding/InteractiveTutorial.tsx`
- [x] Define 5-7 tutorial steps highlighting:
  - Vault list sidebar
  - "Add Source" button
  - "Invite Collaborator" button
  - Annotations panel
  - Search functionality
- [x] Each step has title, description, and target element selector
- [x] "Next" / "Back" / "Skip" controls
- [x] Progress dots showing current step
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-016: Tutorial navigation and completion
**Description:** As a user in the tutorial, I want smooth navigation between steps and clear completion.

**Acceptance Criteria:**
- [ ] Tutorial advances on "Next" click
- [ ] Tutorial goes back on "Back" click
- [ ] "Skip" exits tutorial and advances to completion
- [ ] Completing final step advances to completion
- [ ] Scroll target element into view if needed
- [ ] Highlight pulses to draw attention
- [ ] Updates onboarding step in backend on each navigation
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-017: Create CompletionCelebration component
**Description:** As a user completing onboarding, I want a celebratory finish so I feel accomplished.

**Acceptance Criteria:**
- [ ] Create `components/features/onboarding/CompletionCelebration.tsx`
- [ ] Install `canvas-confetti` package
- [ ] Trigger confetti animation on mount
- [ ] "You're all set!" heading with gradient text
- [ ] Celebratory message thanking user
- [ ] Three quick action buttons:
  - "Add Source" (links to add source flow)
  - "Invite Team" (links to invite flow)
  - "Explore Features" (dismisses and opens help/docs)
- [ ] "Get Started" button to dismiss and mark complete
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-018: Create OnboardingFlow orchestrator
**Description:** As a developer, I need an orchestrator component to manage the onboarding flow state machine.

**Acceptance Criteria:**
- [ ] Create `components/features/onboarding/OnboardingFlow.tsx`
- [ ] Renders appropriate component based on current step:
  - 'welcome' → WelcomeModal
  - 'path' → PathSelection
  - 'guided-1/2/3' → GuidedVaultWizard at correct step
  - 'demo' → redirects to demo vault, then tutorial
  - 'tutorial' → InteractiveTutorial
  - 'complete' → CompletionCelebration
- [ ] Handles step transitions and state updates
- [ ] Only renders for users with `onboarding_completed === false`
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-019: Integrate onboarding into app layout
**Description:** As a new user, I want onboarding to appear automatically after first login.

**Acceptance Criteria:**
- [ ] Add OnboardingProvider to app providers
- [ ] Add OnboardingFlow to authenticated layout
- [ ] Onboarding modal overlays main content
- [ ] Main app still visible but dimmed behind modal
- [ ] Onboarding only shows for authenticated users with incomplete onboarding
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-020: Resume onboarding on return
**Description:** As a user who abandoned onboarding, I want to resume from my last step when I return.

**Acceptance Criteria:**
- [ ] On app load, fetch onboarding state from API
- [ ] If `onboarding_completed === false` and `step` exists, resume from that step
- [ ] If step is 'guided-2', open wizard at step 2
- [ ] If step is 'tutorial', start tutorial from beginning (simpler than tracking sub-step)
- [ ] Show brief "Continuing where you left off..." toast
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-021: Add restart tutorial to settings
**Description:** As a user, I want to restart the tutorial from settings so I can refresh my memory.

**Acceptance Criteria:**
- [ ] Add "Onboarding" section to user settings page
- [ ] "Restart Tutorial" button that:
  - Sets `onboarding_completed` to false
  - Sets `step` to 'tutorial'
  - Reloads to trigger tutorial
- [ ] Confirmation dialog before restarting
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-022: Add reset demo vault to settings
**Description:** As a user, I want to reset the demo vault from settings so I can restore it to original state.

**Acceptance Criteria:**
- [ ] "Reset Demo Vault" button in onboarding settings section
- [ ] Shows current demo vault status (exists/deleted)
- [ ] If deleted: button says "Recreate Demo Vault"
- [ ] Confirmation dialog explaining reset will delete changes
- [ ] Calls appropriate API endpoint
- [ ] Shows success/error toast
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-023: Demo vault deletion prompt
**Description:** As a user deleting the demo vault, I want to be informed I can recreate it later.

**Acceptance Criteria:**
- [ ] Intercept vault delete for demo vault specifically
- [ ] Show custom confirmation: "This is your demo vault. You can recreate it anytime from Settings."
- [ ] "Delete Anyway" and "Cancel" buttons
- [ ] On delete: proceed with normal vault deletion
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-024: Mobile-responsive onboarding modals
**Description:** As a mobile user, I want onboarding to work well on my device.

**Acceptance Criteria:**
- [ ] All onboarding modals are full-screen on mobile (< 768px)
- [ ] Touch-friendly button sizes (min 44px tap targets)
- [ ] Wizard steps stack vertically on mobile
- [ ] Tutorial tooltips position correctly on mobile
- [ ] Confetti animation performs well on mobile
- [ ] Test on iOS Safari and Android Chrome viewports
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-025: Basic onboarding analytics tracking
**Description:** As a product owner, I want to track basic onboarding metrics so I can measure effectiveness.

**Acceptance Criteria:**
- [ ] Add `onboarding_started_at` DateTimeField to User model (set on first step)
- [ ] Add `onboarding_completed_at` DateTimeField (set on completion)
- [ ] Create migration for new fields
- [ ] Log to console (or analytics service if configured):
  - Path chosen (guided/demo/skipped)
  - Completion status (completed/abandoned)
  - Time to complete (if completed)
- [ ] Typecheck passes
- [ ] Tests pass

### US-026: Create onboarding API client functions
**Description:** As a frontend developer, I need API client functions for onboarding endpoints.

**Acceptance Criteria:**
- [ ] Add to `lib/api.ts`:
  - `getOnboardingState(): Promise<OnboardingState>`
  - `updateOnboardingState(data: Partial<OnboardingState>): Promise<OnboardingState>`
  - `resetDemoVault(): Promise<Vault>`
  - `createDemoVault(): Promise<Vault>`
  - `getDemoVaultStatus(): Promise<{ exists: boolean, vault_id: string | null }>`
- [ ] Add TypeScript types for OnboardingState
- [ ] Typecheck passes

### US-027: Add onboarding feature flag
**Description:** As a developer, I need a feature flag to enable/disable onboarding for testing.

**Acceptance Criteria:**
- [ ] Add `ONBOARDING_ENABLED` to backend settings (default True)
- [ ] Add `NEXT_PUBLIC_ONBOARDING_ENABLED` to frontend env
- [ ] OnboardingFlow checks flag before rendering
- [ ] API endpoints return 404 if flag disabled
- [ ] Document flag in .env.example files
- [ ] Typecheck passes

## Non-Goals

- No gamification elements (badges, points, leaderboards)
- No video tutorials or embedded media (just text + illustrations)
- No A/B testing of different onboarding flows (single flow)
- No integration with external analytics platforms (just basic logging)
- No onboarding for specific features post-initial setup (only first-time user flow)
- No admin dashboard for onboarding metrics (console logging only)
- No localization/i18n for onboarding content (English only)

## Technical Considerations

- **react-joyride** for interactive tutorial (user selected)
- **canvas-confetti** for celebration animation
- Demo vault fixture should use real, freely available papers (arXiv, open access)
- Onboarding state persisted in User model, not localStorage (survives device changes)
- Tutorial element selectors should use data attributes (`data-tour="vault-list"`) for stability
- Consider lazy-loading onboarding components to reduce initial bundle size
- Demo vault creation should be idempotent and handle race conditions
