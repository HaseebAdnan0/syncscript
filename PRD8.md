# PRD: Vaults Management UI

## Introduction

Create the complete vault management interface for SyncScript, enabling researchers to browse, create, and manage Knowledge Vaults. This includes a responsive grid listing, vault detail pages with tabbed navigation (Sources, Members, Settings), member invitation system, and role-based UI rendering. The interface follows the Bitcoin DeFi aesthetic with orange glows, hover lift effects, and glass morphism patterns.

## Goals

- Display user's vaults (owned + member) in a responsive card grid with visual role badges
- Enable vault creation via modal dialog with form validation
- Provide tabbed vault detail view with Sources, Members, and Settings content
- Support member management: invite by email, add existing users, change roles, remove members
- Implement type-to-confirm pattern for destructive actions (delete vault)
- Server-side search with debounced API calls for vault filtering
- Render UI elements conditionally based on user's role (Owner/Contributor/Viewer)
- Provide meaningful empty states for no vaults and no sources scenarios

## Dependencies

- **Backend:** Vaults API endpoints (`/api/v1/vaults/`, `/api/v1/vaults/{id}/members/`)
- **Frontend:** Design system components (Button, Card, Dialog, Input, Tabs, Badge)
- **Libraries:** React Query for data fetching, Zustand for UI state

## User Stories

### US-001: Vault TypeScript types and API client
**Description:** As a developer, I need TypeScript types and API client functions for vaults so that all components have type-safe data access.

**Acceptance Criteria:**
- [x] Create `frontend/src/lib/types/vault.ts` with Vault, VaultMember, VaultRole types
- [x] Create `frontend/src/lib/api/vaults.ts` with API functions: getVaults, getVault, createVault, updateVault, deleteVault, archiveVault
- [x] API functions use axios instance from existing `frontend/src/lib/api/client.ts`
- [x] VaultRole enum: OWNER, CONTRIBUTOR, VIEWER
- [x] Typecheck passes

### US-002: React Query hooks for vaults
**Description:** As a developer, I need React Query hooks for vault data fetching so components can easily query and mutate vault data with caching.

**Acceptance Criteria:**
- [x] Create `frontend/src/hooks/useVaults.ts` with useVaults, useVault, useCreateVault, useUpdateVault, useDeleteVault hooks
- [x] useVaults accepts optional search query parameter for server-side filtering
- [x] Mutations invalidate relevant queries on success
- [x] Hooks use query keys that support cache invalidation
- [x] Typecheck passes

### US-003: Vault members API client and hooks
**Description:** As a developer, I need API functions and hooks for vault membership management.

**Acceptance Criteria:**
- [x] Add to `frontend/src/lib/api/vaults.ts`: getVaultMembers, addVaultMember, inviteVaultMember, updateMemberRole, removeMember
- [x] Create `frontend/src/hooks/useVaultMembers.ts` with useVaultMembers, useAddMember, useInviteMember, useUpdateRole, useRemoveMember
- [x] inviteVaultMember sends email invite for new users
- [x] addVaultMember adds existing users by email/username
- [x] Typecheck passes

### US-004: Zustand store for vaults UI state
**Description:** As a developer, I need a Zustand store to manage vaults UI state like modals and filters.

**Acceptance Criteria:**
- [x] Create `frontend/src/stores/vaultsStore.ts`
- [x] Store state: isCreateModalOpen, searchQuery, activeTab (for detail page)
- [x] Store actions: openCreateModal, closeCreateModal, setSearchQuery, setActiveTab
- [x] Typecheck passes

### US-005: VaultCard component
**Description:** As a user, I want to see vault information in a card format so I can quickly scan my vaults.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/vaults/VaultCard.tsx`
- [x] Card displays: vault name, description (truncated), source count, member count, last updated
- [x] Card shows role badge: "Owner" (orange), "Contributor" (blue), "Viewer" (gray)
- [x] Card uses `bg-[#0F1115] border border-white/10 rounded-2xl` styling
- [x] Hover effect: `-translate-y-1` lift and `border-[#F7931A]/50` orange glow
- [x] Card is clickable, navigates to vault detail page
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-006: Vaults listing page with grid layout
**Description:** As a user, I want to see all my vaults in a grid so I can browse and select one to work on.

**Acceptance Criteria:**
- [x] Create `frontend/src/app/vaults/page.tsx`
- [x] Page header with title "My Vaults" and "Create Vault" button
- [x] Responsive grid: 1 column on mobile, 2 on tablet, 3 on desktop
- [x] Grid uses `gap-6` spacing
- [x] Uses useVaults hook to fetch data
- [x] Shows loading skeleton while fetching
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-007: Empty state for no vaults
**Description:** As a new user with no vaults, I want to see a helpful empty state so I know how to get started.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/vaults/EmptyVaultsState.tsx`
- [x] Displays illustration or icon (use Lucide `FolderOpen` or similar)
- [x] Heading: "No vaults yet"
- [x] Subtext: "Create your first Knowledge Vault to start organizing research"
- [x] Primary CTA button: "Create Vault" (triggers create modal)
- [x] Integrate into vaults listing page when vault count is 0
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-008: Search input for vaults filtering
**Description:** As a user, I want to search my vaults by name so I can quickly find what I'm looking for.

**Acceptance Criteria:**
- [x] Add search input to vaults listing page header
- [x] Input uses bottom-border style: `border-b-2 border-white/20 focus:border-[#F7931A]`
- [x] Search icon (Lucide `Search`) inside input
- [x] Debounce input by 300ms before triggering API call
- [x] Search query passed to useVaults hook for server-side filtering
- [x] Clear button appears when search has value
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-009: Create vault modal dialog
**Description:** As a user, I want to create a new vault via a modal form so I can start a new research project.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/vaults/CreateVaultModal.tsx`
- [x] Modal uses Radix Dialog with glass morphism: `backdrop-blur-lg bg-white/5 border border-white/10`
- [x] Form fields: Name (required), Description (optional, textarea)
- [x] Submit button: gradient orange, disabled while submitting
- [x] Uses useCreateVault mutation
- [x] On success: close modal, show toast, navigate to new vault
- [x] On error: display error message in modal
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-010: Vault detail page layout with tabs
**Description:** As a user, I want to see vault details in a tabbed layout so I can switch between Sources, Members, and Settings.

**Acceptance Criteria:**
- [x] Create `frontend/src/app/vaults/[id]/page.tsx`
- [x] Page header: vault name, description, back button
- [x] Radix Tabs with three tabs: Sources, Members, Settings
- [x] Tab styling: underline indicator in orange when active
- [x] Active tab stored in Zustand store (persists during session)
- [x] Uses useVault hook to fetch vault data
- [x] Shows loading state while fetching
- [x] 404 handling if vault not found
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-011: Sources tab list component
**Description:** As a user, I want to see all sources in a vault so I can browse the research materials.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/vaults/SourcesList.tsx`
- [x] Display sources in a list/card format with: title, URL (truncated), added date, added by
- [x] Each source card has hover effect consistent with VaultCard
- [x] Source cards are clickable (link to source detail - can be placeholder route)
- [x] Shows source count in tab badge: "Sources (12)"
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-012: Empty state for no sources
**Description:** As a user viewing an empty vault, I want to see a helpful message so I know how to add sources.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/vaults/EmptySourcesState.tsx`
- [x] Displays icon (Lucide `FileText` or `Link`)
- [x] Heading: "No sources yet"
- [x] Subtext: "Add URLs, PDFs, or citations to build your knowledge base"
- [x] CTA button: "Add Source" (can be placeholder action for now)
- [x] Only show CTA if user has Contributor or Owner role
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-013: Members tab list component
**Description:** As a user, I want to see all vault members so I know who has access.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/vaults/MembersList.tsx`
- [x] Display members in list with: avatar (initials fallback), name, email, role badge
- [x] Role badges use colors: Owner (orange), Contributor (blue), Viewer (gray)
- [x] Members sorted: Owner first, then alphabetically
- [x] Shows member count in tab badge: "Members (5)"
- [x] Uses useVaultMembers hook
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-014: Add existing user to vault
**Description:** As a vault owner, I want to add an existing user to my vault so they can collaborate.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/vaults/AddMemberModal.tsx`
- [x] Modal has two tabs: "Add Existing" and "Invite New"
- [x] "Add Existing" tab: email/username search input with autocomplete dropdown
- [x] Role selector dropdown: Contributor (default), Viewer
- [x] Add button uses useAddMember mutation
- [x] On success: close modal, show toast, refresh members list
- [x] On error: show error message (e.g., "User not found")
- [x] Only accessible to Owner role
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-015: Invite new user by email
**Description:** As a vault owner, I want to invite someone by email so they can join even if they don't have an account yet.

**Acceptance Criteria:**
- [x] "Invite New" tab in AddMemberModal
- [x] Email input field with validation
- [x] Role selector: Contributor (default), Viewer
- [x] "Send Invite" button uses useInviteMember mutation
- [x] On success: show toast "Invitation sent to {email}"
- [x] Pending invites shown in members list with "Pending" status badge
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-016: Change member role
**Description:** As a vault owner, I want to change a member's role so I can adjust their permissions.

**Acceptance Criteria:**
- [ ] Add role dropdown to each member row (except Owner)
- [ ] Dropdown options: Contributor, Viewer
- [ ] Dropdown triggers useUpdateRole mutation on change
- [ ] Show loading state on dropdown while updating
- [ ] On success: update UI optimistically
- [ ] Only visible to Owner role
- [ ] Cannot change own role or other Owner's role
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-017: Remove member from vault
**Description:** As a vault owner, I want to remove a member so they no longer have access.

**Acceptance Criteria:**
- [ ] Add remove button (trash icon) to each member row (except Owner)
- [ ] Click shows confirm dialog: "Remove {name} from this vault?"
- [ ] Confirm triggers useRemoveMember mutation
- [ ] On success: remove from list, show toast
- [ ] Only visible to Owner role
- [ ] Cannot remove self (Owner)
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-018: Settings tab - rename vault
**Description:** As a vault owner, I want to rename my vault so I can keep it organized.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/vaults/VaultSettings.tsx`
- [ ] Form section: "Vault Details" with name input and description textarea
- [ ] Pre-populated with current values
- [ ] "Save Changes" button, disabled if no changes
- [ ] Uses useUpdateVault mutation
- [ ] On success: show toast, update page header
- [ ] Only editable fields shown to Owner role
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-019: Settings tab - archive vault
**Description:** As a vault owner, I want to archive my vault so I can hide it without deleting.

**Acceptance Criteria:**
- [ ] "Danger Zone" section in settings with red/orange border
- [ ] "Archive Vault" button with warning text
- [ ] Click shows confirm dialog explaining archive behavior
- [ ] Confirm triggers archive mutation
- [ ] On success: redirect to vaults list, show toast
- [ ] Archived vaults hidden from main list (can add filter later)
- [ ] Only visible to Owner role
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-020: Settings tab - delete vault with type-to-confirm
**Description:** As a vault owner, I want to permanently delete my vault with confirmation so I don't accidentally lose data.

**Acceptance Criteria:**
- [ ] "Delete Vault" button in Danger Zone (red styling)
- [ ] Click opens modal with warning: "This action cannot be undone"
- [ ] Modal requires typing vault name exactly to enable delete button
- [ ] Input shows validation: green check when matches, red X when doesn't
- [ ] Delete button disabled until name matches
- [ ] Confirm triggers useDeleteVault mutation
- [ ] On success: redirect to vaults list, show toast
- [ ] Only visible to Owner role
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-021: Role-based UI rendering
**Description:** As a user, I want to see only the actions I'm allowed to perform based on my role.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/useVaultPermissions.ts` hook
- [ ] Hook returns: canEdit, canManageMembers, canDelete, isOwner, isContributor, isViewer
- [ ] Settings tab: hidden for Viewers, read-only for Contributors
- [ ] Add Member button: hidden for non-Owners
- [ ] Role dropdowns and remove buttons: hidden for non-Owners
- [ ] "Add Source" buttons: hidden for Viewers
- [ ] Edit buttons throughout: hidden for Viewers
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-022: Loading skeletons for vault pages
**Description:** As a user, I want to see loading skeletons while data loads so the page doesn't flash empty.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/vaults/VaultCardSkeleton.tsx`
- [ ] Create `frontend/src/components/features/vaults/VaultDetailSkeleton.tsx`
- [ ] Skeletons use `animate-pulse` with `bg-white/5` placeholder blocks
- [ ] Skeletons match layout dimensions of actual components
- [ ] Integrate into listing page and detail page
- [ ] Typecheck passes
- [ ] Verify changes work in browser

## Non-Goals

- Source creation/upload UI (separate PRD)
- Annotation system and PDF viewer (separate PRD)
- Vault activity/audit log viewing (separate PRD)
- Bulk operations on vaults (multi-select, bulk delete)
- Vault templates or duplication
- Vault sharing via public links
- Real-time collaboration indicators (who's online)
- Mobile-specific navigation patterns (bottom tabs)

## Technical Considerations

- **React Query:** Use query keys like `['vaults']`, `['vault', id]`, `['vault', id, 'members']` for proper cache invalidation
- **Zustand:** Keep store minimal—only truly global UI state (modals, active tab)
- **Debouncing:** Use `useDebouncedValue` hook or lodash debounce for search input
- **Optimistic Updates:** Consider for role changes and member removal for snappy UX
- **Error Boundaries:** Wrap vault detail page in error boundary for 404/500 handling
- **Route Structure:**
  - `/vaults` - listing page
  - `/vaults/[id]` - detail page (tabs handled via state, not routes)
- **Accessibility:** Ensure modals trap focus, buttons have aria-labels, role badges have aria-describedby

## File Structure

```
frontend/src/
├── app/vaults/
│   ├── page.tsx                    # Vaults listing
│   └── [id]/
│       └── page.tsx                # Vault detail with tabs
├── components/features/vaults/
│   ├── VaultCard.tsx
│   ├── VaultCardSkeleton.tsx
│   ├── VaultDetailSkeleton.tsx
│   ├── EmptyVaultsState.tsx
│   ├── EmptySourcesState.tsx
│   ├── CreateVaultModal.tsx
│   ├── AddMemberModal.tsx
│   ├── DeleteVaultModal.tsx
│   ├── SourcesList.tsx
│   ├── MembersList.tsx
│   ├── MemberRow.tsx
│   └── VaultSettings.tsx
├── hooks/
│   ├── useVaults.ts
│   ├── useVaultMembers.ts
│   └── useVaultPermissions.ts
├── stores/
│   └── vaultsStore.ts
└── lib/
    ├── types/
    │   └── vault.ts
    └── api/
        └── vaults.ts
```
