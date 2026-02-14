# PRD 17: User Dashboard & Analytics

## Introduction

Create a comprehensive user dashboard as the primary logged-in landing page for SyncScript. The dashboard provides at-a-glance research insights, quick access to recent work, activity tracking, and analytics visualizations. This replaces `/vaults` as the default post-login destination and serves as the central hub for researchers.

## Goals

- Provide personalized landing experience with time-based greetings and user stats
- Surface recently accessed vaults for quick continuation of work
- Display activity feed across all vaults for awareness of changes
- Visualize research analytics (sources over time, source types, collaborators)
- Enable quick actions without navigating away (new vault, add source, invite)
- Centralize notification management with unread badges and mark-as-read
- Implement responsive sidebar navigation for consistent app-wide navigation

## User Stories

### US-001: Create dashboard stats API endpoint
**Description:** As a developer, I need a dedicated API endpoint that returns aggregated dashboard statistics so the frontend can display quick stats efficiently.

**Acceptance Criteria:**
- [x] Create `GET /api/v1/dashboard/stats/` endpoint
- [x] Returns JSON: `{ vaults_count, sources_count, annotations_this_week }`
- [x] `vaults_count`: total vaults user owns or is member of
- [x] `sources_count`: total sources across all accessible vaults
- [x] `annotations_this_week`: annotations created by user in last 7 days
- [x] Endpoint requires authentication
- [x] Add to `apps/` as new `dashboard` app or add to existing app
- [x] Typecheck passes

### US-002: Create recent vaults API endpoint
**Description:** As a developer, I need an endpoint that returns the user's most recently accessed vaults so the dashboard can show "Continue Research" section.

**Acceptance Criteria:**
- [x] Create `GET /api/v1/dashboard/recent-vaults/` endpoint
- [x] Returns last 3 vaults the user accessed (by last access timestamp)
- [x] Each vault includes: `id`, `name`, `description`, `last_accessed_at`, `sources_count`, `role`
- [x] If vault has no `last_accessed_at`, use `updated_at` as fallback
- [x] Consider adding `last_accessed_at` field to VaultMembership if not exists
- [x] Endpoint requires authentication
- [x] Typecheck passes

### US-003: Create activity feed API endpoint
**Description:** As a developer, I need an endpoint that returns recent activity across all user's vaults using existing AuditLog data.

**Acceptance Criteria:**
- [x] Create `GET /api/v1/dashboard/activity/` endpoint
- [x] Returns last 10 audit log entries for vaults user has access to
- [x] Create `ActivityFeedSerializer` with fields: `id`, `action`, `description`, `actor` (user info), `vault_id`, `vault_name`, `target_type`, `target_id`, `created_at`
- [x] Format `description` as human-readable (e.g., "added source 'Research Paper'")
- [x] Supports `?limit=N` query param (default 10, max 50)
- [x] Endpoint requires authentication
- [x] Typecheck passes

### US-004: Create analytics endpoints
**Description:** As a developer, I need analytics API endpoints for chart data so the frontend can render visualizations.

**Acceptance Criteria:**
- [x] Create `GET /api/v1/dashboard/analytics/sources-timeline/` - sources added per day, last 30 days
- [x] Returns array: `[{ date: "2026-02-01", count: 5 }, ...]`
- [x] Create `GET /api/v1/dashboard/analytics/source-types/` - breakdown by source type
- [x] Returns array: `[{ type: "pdf", count: 15, percentage: 45 }, ...]`
- [x] Create `GET /api/v1/dashboard/analytics/top-collaborators/` - users with most contributions
- [x] Returns array: `[{ user_id, name, avatar_url, contributions_count }, ...]` (top 5)
- [x] All endpoints scoped to vaults user has access to
- [x] All endpoints require authentication
- [x] Typecheck passes

### US-005: Extend notifications app for dashboard
**Description:** As a developer, I need notification endpoints that support unread counts and mark-as-read so the dashboard can display notification panel.

**Acceptance Criteria:**
- [x] Verify/create Notification model in `apps/notifications/` with: `user`, `title`, `message`, `type`, `is_read`, `link`, `created_at`
- [x] Create `GET /api/v1/notifications/` - list notifications for current user
- [x] Create `GET /api/v1/notifications/unread-count/` - returns `{ count: N }`
- [x] Create `POST /api/v1/notifications/{id}/mark-read/` - mark single as read
- [x] Create `POST /api/v1/notifications/mark-all-read/` - mark all as read
- [x] Endpoints require authentication
- [x] Typecheck passes

### US-006: Create dashboard page layout and sidebar
**Description:** As a user, I want a dashboard layout with collapsible sidebar navigation so I can easily navigate between sections of the app.

**Acceptance Criteria:**
- [x] Create `frontend/src/app/(app)/dashboard/page.tsx`
- [x] Create `frontend/src/app/(app)/layout.tsx` with sidebar (shared across app routes)
- [x] Sidebar items: Dashboard, My Vaults, Shared With Me, Recent, Settings
- [x] Each item has icon (lucide-react) and label
- [x] Active item highlighted with Bitcoin orange accent
- [x] Sidebar collapsible on mobile (hamburger menu)
- [x] Sidebar collapsed state shows icons only on desktop
- [x] Main content area uses responsive grid
- [x] Follows Bitcoin DeFi design system (dark theme, orange accents)
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-007: Create welcome header component
**Description:** As a user, I want to see a personalized greeting with my quick stats so I feel welcomed and informed at a glance.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/dashboard/WelcomeHeader.tsx`
- [x] Time-based greeting: "Good morning/afternoon/evening, {firstName}"
- [x] Morning: 5am-12pm, Afternoon: 12pm-5pm, Evening: 5pm-5am
- [x] Quick stats row showing: Vaults count, Sources count, Annotations this week
- [x] Stats displayed as cards with icons and values
- [x] Uses gradient text for greeting (orange to gold)
- [x] Fetches data from `/api/v1/dashboard/stats/`
- [x] Shows skeleton loader while fetching
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-008: Create continue research section
**Description:** As a user, I want to see my recently accessed vaults so I can quickly continue where I left off.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/dashboard/ContinueResearch.tsx`
- [x] Section title: "Continue Research"
- [x] Displays 3 most recently accessed vault cards
- [x] Each card shows: vault name, last accessed time (relative), source count
- [x] Quick action buttons on each card: Open, Add Source
- [x] "View all vaults" link at bottom navigates to `/vaults`
- [x] Cards follow design system (dark bg, border, hover lift)
- [x] Fetches from `/api/v1/dashboard/recent-vaults/`
- [x] Empty state if no vaults: "Create your first vault to get started"
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-009: Create recent activity section
**Description:** As a user, I want to see a timeline of recent actions across my vaults so I stay aware of changes and collaboration.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/dashboard/RecentActivity.tsx`
- [x] Section title: "Recent Activity"
- [x] Timeline displays last 10 actions
- [x] Each item shows: user avatar, action description, relative time
- [x] Items are clickable and navigate to the relevant item (vault/source/annotation)
- [x] "View all activity" link at bottom (can link to a future activity page or show more)
- [x] Fetches from `/api/v1/dashboard/activity/`
- [x] Empty state: "No activity yet. Start by adding sources to a vault."
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-010: Install and configure Recharts
**Description:** As a developer, I need Recharts installed and configured so I can build analytics charts.

**Acceptance Criteria:**
- [x] Run `npm install recharts` in frontend directory
- [x] Verify recharts is added to package.json
- [x] Create `frontend/src/components/features/dashboard/charts/` directory
- [x] Create base chart wrapper component with consistent styling
- [x] Configure chart colors using design system tokens (Bitcoin orange: #F7931A, gold: #FFD600)
- [x] Typecheck passes

### US-011: Create sources timeline chart
**Description:** As a user, I want to see a line chart of sources added over time so I can visualize my research productivity.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/dashboard/charts/SourcesTimelineChart.tsx`
- [x] Line chart showing sources added per day, last 30 days
- [x] X-axis: dates, Y-axis: count
- [x] Line color: Bitcoin orange (#F7931A)
- [x] Custom tooltip matching design system (dark bg, orange accent)
- [x] Responsive - resizes with container
- [x] Fetches from `/api/v1/dashboard/analytics/sources-timeline/`
- [x] Empty state: onboarding prompt "Add your first source to see analytics"
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-012: Create source types donut chart
**Description:** As a user, I want to see a breakdown of my source types so I understand my research composition.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/dashboard/charts/SourceTypesChart.tsx`
- [x] Donut/pie chart showing source type distribution
- [x] Colors: gradient from orange (#F7931A) to gold (#FFD600) for segments
- [x] Shows percentage labels
- [x] Custom tooltip with count and percentage
- [x] Legend below chart with type names
- [x] Responsive - resizes with container
- [x] Fetches from `/api/v1/dashboard/analytics/source-types/`
- [x] Empty state: onboarding prompt "Add your first source to see analytics"
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-013: Create top collaborators section
**Description:** As a user, I want to see my top collaborators so I recognize who contributes most to shared research.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/dashboard/TopCollaborators.tsx`
- [x] Section title: "Top Collaborators"
- [x] Avatar list with top 5 collaborators
- [x] Each shows: avatar, name, contribution count
- [x] Avatar has fallback to initials if no image
- [x] Contribution count styled as badge
- [x] Fetches from `/api/v1/dashboard/analytics/top-collaborators/`
- [x] Empty state: "Invite collaborators to see who contributes most"
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-014: Create analytics section container
**Description:** As a user, I want the analytics charts organized in a visually appealing section so I can quickly understand my research metrics.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/dashboard/AnalyticsSection.tsx`
- [x] Section title: "Analytics"
- [x] Responsive grid layout: 2 columns on desktop, 1 on mobile
- [x] Contains: SourcesTimelineChart, SourceTypesChart, TopCollaborators
- [x] Cards have consistent styling (dark bg, border, padding)
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-015: Create quick actions FAB
**Description:** As a user, I want a floating action button with quick actions so I can create content without navigating away.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/dashboard/QuickActionsFAB.tsx`
- [x] Floating button fixed to bottom-right corner
- [x] Plus icon, Bitcoin orange gradient background
- [x] On click, expands to show 3 actions: New Vault, Add Source, Invite Collaborator
- [x] Each action has icon and label
- [x] Click outside or action closes menu
- [x] Actions navigate to appropriate pages/modals
- [x] Smooth expand/collapse animation
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-016: Create notifications dropdown component
**Description:** As a user, I want a notifications bell in the header with dropdown so I can see and manage notifications without leaving the page.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/dashboard/NotificationsDropdown.tsx`
- [x] Bell icon in header area
- [x] Unread badge showing count (red dot with number)
- [x] Click opens dropdown with recent notifications
- [x] Each notification shows: title, message preview, relative time
- [x] Unread items visually distinguished (brighter, left border)
- [x] "Mark as read" button per notification
- [x] "Mark all as read" button at top
- [x] "Notification settings" link at bottom
- [x] Fetches from `/api/v1/notifications/` and `/api/v1/notifications/unread-count/`
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-017: Integrate notifications into app header
**Description:** As a developer, I need to add the notifications dropdown to the shared app header so it's accessible from all pages.

**Acceptance Criteria:**
- [x] Add NotificationsDropdown to app layout header
- [x] Position in top-right area alongside user menu
- [x] Ensure proper z-index for dropdown overlay
- [x] Works on mobile (dropdown may be full-width)
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-018: Assemble dashboard page with all sections
**Description:** As a user, I want all dashboard sections assembled on the dashboard page in a cohesive layout.

**Acceptance Criteria:**
- [x] Dashboard page imports and renders all sections
- [x] Order: WelcomeHeader, ContinueResearch, RecentActivity, AnalyticsSection
- [x] Responsive grid layout with proper spacing
- [x] QuickActionsFAB rendered (fixed position)
- [x] Page has proper loading states (skeleton loaders)
- [x] Page has error boundaries for failed API calls
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-019: Update post-login redirect to dashboard
**Description:** As a user, I want to land on the dashboard after logging in so I see my personalized home page.

**Acceptance Criteria:**
- [x] Update AuthProvider to redirect to `/dashboard` after successful login
- [x] Update any hardcoded `/vaults` redirects to `/dashboard`
- [x] Ensure protected route logic includes `/dashboard`
- [x] If user navigates to `/` while logged in, redirect to `/dashboard`
- [x] Typecheck passes
- [ ] Verify redirect works in browser after login

### US-020: Create API client functions for dashboard
**Description:** As a developer, I need frontend API client functions for all dashboard endpoints so components can fetch data consistently.

**Acceptance Criteria:**
- [x] Add to `frontend/src/lib/api.ts` or create `frontend/src/lib/api/dashboard.ts`
- [x] `getDashboardStats()` - fetches `/dashboard/stats/`
- [x] `getRecentVaults()` - fetches `/dashboard/recent-vaults/`
- [x] `getActivityFeed(limit?)` - fetches `/dashboard/activity/`
- [x] `getSourcesTimeline()` - fetches `/dashboard/analytics/sources-timeline/`
- [x] `getSourceTypes()` - fetches `/dashboard/analytics/source-types/`
- [x] `getTopCollaborators()` - fetches `/dashboard/analytics/top-collaborators/`
- [x] `getNotifications()` - fetches `/notifications/`
- [x] `getUnreadCount()` - fetches `/notifications/unread-count/`
- [x] `markNotificationRead(id)` - POST to `/notifications/{id}/mark-read/`
- [x] `markAllNotificationsRead()` - POST to `/notifications/mark-all-read/`
- [x] All functions handle errors appropriately
- [x] Typecheck passes

### US-021: Add React Query hooks for dashboard data
**Description:** As a developer, I need React Query hooks for dashboard data so components have consistent caching and loading states.

**Acceptance Criteria:**
- [x] Create `frontend/src/hooks/useDashboard.ts`
- [x] `useDashboardStats()` hook with appropriate stale time
- [x] `useRecentVaults()` hook
- [x] `useActivityFeed(limit?)` hook
- [x] `useSourcesTimeline()` hook
- [x] `useSourceTypes()` hook
- [x] `useTopCollaborators()` hook
- [x] `useNotifications()` hook
- [x] `useUnreadNotificationCount()` hook with short stale time for freshness
- [x] Mutations for mark read actions with cache invalidation
- [x] Typecheck passes

## Non-Goals

- Real-time WebSocket updates for dashboard stats (polling or manual refresh is acceptable)
- Customizable dashboard layout (drag-and-drop widget arrangement)
- Dashboard data export functionality
- Advanced analytics filters (date range selection, vault-specific)
- Notification preferences/settings page (only link to it)
- Push notifications to mobile/desktop (browser only via existing Pusher)
- Historical analytics beyond 30 days
- Comparison analytics (this week vs last week)

## Technical Considerations

- **Recharts**: Use for all chart components. Already React-based, good TypeScript support.
- **Design System**: All components must follow Bitcoin DeFi aesthetic from CLAUDE.md
- **Caching**: Dashboard stats can be cached for 5 minutes. Activity feed for 1 minute.
- **AuditLog**: Reuse existing model - ensure it captures enough detail for activity descriptions
- **Notifications App**: Verify existing model structure in `apps/notifications/` before extending
- **Sidebar**: Consider using Radix NavigationMenu or custom implementation with proper accessibility
- **Mobile**: Sidebar should be drawer/overlay on mobile, triggered by hamburger menu
- **Empty States**: Critical for new users - guide them to take first actions

## File Structure

```
backend/
├── apps/
│   ├── dashboard/           # New app for dashboard endpoints
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   └── notifications/       # Extend existing
│       ├── models.py        # Verify/add Notification model
│       ├── views.py         # Add new endpoints
│       └── serializers.py

frontend/
├── src/
│   ├── app/(app)/
│   │   ├── layout.tsx       # Shared layout with sidebar
│   │   └── dashboard/
│   │       └── page.tsx
│   ├── components/features/dashboard/
│   │   ├── WelcomeHeader.tsx
│   │   ├── ContinueResearch.tsx
│   │   ├── RecentActivity.tsx
│   │   ├── AnalyticsSection.tsx
│   │   ├── TopCollaborators.tsx
│   │   ├── QuickActionsFAB.tsx
│   │   ├── NotificationsDropdown.tsx
│   │   └── charts/
│   │       ├── ChartWrapper.tsx
│   │       ├── SourcesTimelineChart.tsx
│   │       └── SourceTypesChart.tsx
│   ├── hooks/
│   │   └── useDashboard.ts
│   └── lib/api/
│       └── dashboard.ts
```
