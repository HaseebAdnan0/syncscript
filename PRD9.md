# PRD: Frontend Sources & Annotations UI

## Introduction

Build the source and annotation management interface for SyncScript's Knowledge Vaults. This feature enables researchers to add, organize, and annotate sources (URLs, PDFs, citations) within a vault. The UI follows the Bitcoin DeFi aesthetic with glass morphism cards, supports both grid and table views, integrates react-pdf for document viewing, and provides real-time collaboration via WebSockets.

## Goals

- Display sources within a vault with toggleable card grid/table views
- Enable adding single sources with URL metadata preview
- Support bulk import of multiple URLs with validation preview
- Integrate react-pdf for basic PDF rendering on source detail pages
- Provide annotation sidebar with single-level threaded replies
- Implement real-time updates for collaborative annotation
- Apply consistent glass morphism styling to annotation cards
- Enable filtering sources by type, date, and contributor

## Dependencies

- **Backend Sources/Annotations API** (must exist)
- **Frontend Design System** (Bitcoin DeFi tokens, components)
- **Vaults UI** (vault detail page shell)

## User Stories

---

### US-001: Create Source TypeScript types and API client
**Description:** As a developer, I need TypeScript types and API client functions for sources and annotations so that components can fetch and mutate data with type safety.

**Acceptance Criteria:**
- [x] Create `frontend/src/lib/types/sources.ts` with `Source`, `SourceType`, `SourceMetadata` types
- [x] Create `frontend/src/lib/types/annotations.ts` with `Annotation`, `AnnotationReply` types
- [x] Create `frontend/src/lib/api/sources.ts` with CRUD functions: `getSources`, `getSource`, `createSource`, `updateSource`, `deleteSource`
- [x] Create `frontend/src/lib/api/annotations.ts` with CRUD functions: `getAnnotations`, `createAnnotation`, `createReply`, `deleteAnnotation`
- [x] All API functions use axios instance from existing lib/api setup
- [x] Typecheck passes

---

### US-002: Create SourceCard component
**Description:** As a user, I want to see sources displayed as visually appealing cards so I can quickly scan my research materials.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/sources/SourceCard.tsx`
- [x] Card uses glass morphism style: `bg-[#0F1115] border border-white/10 rounded-2xl`
- [x] Displays source title, type badge, contributor avatar, and created date
- [x] Shows truncated URL or citation preview
- [x] Hover effect: `-translate-y-1` and `border-[#F7931A]/50`
- [x] Click navigates to source detail page
- [x] Typecheck passes
- [ ] Verify changes work in browser

---

### US-003: Create SourceTypeBadge component
**Description:** As a user, I want visual badges indicating source type so I can distinguish between URLs, PDFs, and citations at a glance.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/sources/SourceTypeBadge.tsx`
- [x] Badge variants: `url` (globe icon), `pdf` (file icon), `citation` (quote icon), `article` (newspaper icon)
- [x] Each type has distinct color: URL=blue, PDF=red, Citation=purple, Article=green
- [x] Uses pill shape with icon + text label
- [x] Typecheck passes
- [ ] Verify changes work in browser

---

### US-004: Create SourceTableRow component
**Description:** As a user, I want a compact table row view for sources so I can see more items when working with large collections.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/sources/SourceTableRow.tsx`
- [x] Displays: type badge, title (linked), contributor, date added, actions menu
- [x] Row hover highlights with `bg-white/5`
- [x] Actions dropdown includes: View, Edit, Delete
- [x] Typecheck passes
- [ ] Verify changes work in browser

---

### US-005: Create SourcesListHeader with view toggle
**Description:** As a user, I want to toggle between grid and table views so I can choose the layout that works best for my workflow.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/sources/SourcesListHeader.tsx`
- [x] Contains title "Sources", source count badge, and view toggle buttons (grid/table icons)
- [x] View preference persists in localStorage key `syncscript:sources-view`
- [x] Toggle buttons use active/inactive states with orange highlight for active
- [x] Includes "Add Source" button (primary gradient style)
- [x] Typecheck passes
- [ ] Verify changes work in browser

---

### US-006: Create useSourcesViewPreference hook
**Description:** As a developer, I need a hook to manage view preference state with localStorage persistence.

**Acceptance Criteria:**
- [x] Create `frontend/src/hooks/useSourcesViewPreference.ts`
- [x] Returns `[viewMode, setViewMode]` where viewMode is `'grid' | 'table'`
- [x] Default to `'grid'` if no preference stored
- [x] Persist changes to localStorage immediately
- [x] Typecheck passes

---

### US-007: Create SourcesFilterBar component
**Description:** As a user, I want to filter sources by type, date range, and contributor so I can find specific materials quickly.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/sources/SourcesFilterBar.tsx`
- [x] Type filter dropdown: All Types, URL, PDF, Citation, Article
- [x] Date filter dropdown: Any Time, Today, This Week, This Month, Custom Range
- [x] Contributor filter dropdown populated from vault members
- [x] Clear filters button appears when any filter active
- [x] Filters update URL search params for shareability
- [x] Uses glass morphism dropdown styling
- [x] Typecheck passes
- [ ] Verify changes work in browser

---

### US-008: Create SourcesList container component
**Description:** As a user, I want to see all sources in my selected view mode with active filters applied.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/sources/SourcesList.tsx`
- [x] Reads view preference from hook, renders grid or table accordingly
- [x] Grid uses CSS grid: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6`
- [x] Table renders with sticky header and scrollable body
- [x] Shows loading skeleton while fetching
- [x] Shows empty state with illustration when no sources
- [x] Empty state includes "Add your first source" CTA
- [x] Typecheck passes
- [ ] Verify changes work in browser

---

### US-009: Create useSourcesQuery hook with React Query
**Description:** As a developer, I need a React Query hook to fetch and cache sources for a vault with filter support.

**Acceptance Criteria:**
- [x] Create `frontend/src/hooks/useSourcesQuery.ts`
- [x] Accepts `vaultId` and optional filter params
- [x] Uses `@tanstack/react-query` with cache key including filters
- [x] Returns `{ data, isLoading, error, refetch }`
- [x] Stale time set to 30 seconds
- [x] Typecheck passes

---

### US-010: Create AddSourceModal component
**Description:** As a user, I want a modal to add a new source by entering a URL so I can expand my research collection.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/sources/AddSourceModal.tsx`
- [x] Modal uses Radix Dialog with glass morphism backdrop
- [x] URL input field with bottom-border focus style
- [x] "Fetch Metadata" button triggers preview
- [x] Shows loading spinner while fetching metadata
- [x] Typecheck passes
- [ ] Verify changes work in browser

---

### US-011: Create SourceMetadataPreview component
**Description:** As a user, I want to preview fetched metadata before adding a source so I can verify it's correct.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/sources/SourceMetadataPreview.tsx`
- [x] Displays: title (editable), description, favicon, detected type
- [x] Shows source type badge based on URL/content-type detection
- [x] "Add Source" primary button and "Cancel" secondary button
- [x] Error state if metadata fetch fails with retry option
- [x] Typecheck passes
- [ ] Verify changes work in browser

---

### US-012: Create useAddSourceMutation hook
**Description:** As a developer, I need a mutation hook to create sources with optimistic updates.

**Acceptance Criteria:**
- [x] Create `frontend/src/hooks/useAddSourceMutation.ts`
- [x] Uses React Query `useMutation`
- [x] Invalidates sources query on success
- [x] Returns `{ mutate, isLoading, error }`
- [x] Shows toast notification on success/error
- [x] Typecheck passes

---

### US-013: Create BulkImportModal component
**Description:** As a user, I want to paste multiple URLs at once so I can quickly import many sources.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/sources/BulkImportModal.tsx`
- [x] Large textarea for pasting URLs (one per line)
- [x] "Parse URLs" button extracts and validates URLs
- [x] Shows count of valid/invalid URLs detected
- [x] Invalid URLs highlighted in red with error message
- [x] Typecheck passes
- [ ] Verify changes work in browser

---

### US-014: Create BulkImportPreviewList component
**Description:** As a user, I want to see a preview list of URLs before bulk importing so I can review and remove unwanted items.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/sources/BulkImportPreviewList.tsx`
- [x] Lists each valid URL with checkbox for selection
- [x] Shows validation status icon per URL (valid=green check, invalid=red X)
- [x] "Select All" / "Deselect All" toggle
- [x] Remove button per item
- [x] "Import Selected" button with count
- [x] Typecheck passes
- [ ] Verify changes work in browser

---

### US-015: Create sources page route and layout
**Description:** As a user, I want to access the sources page within a vault via URL navigation.

**Acceptance Criteria:**
- [ ] Create `frontend/src/app/vaults/[id]/sources/page.tsx`
- [ ] Page fetches vault ID from params
- [ ] Renders SourcesListHeader, SourcesFilterBar, SourcesList
- [ ] Integrates AddSourceModal triggered from header button
- [ ] Page title set to "[Vault Name] - Sources"
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-016: Create SourceDetailPage layout
**Description:** As a user, I want a dedicated page for viewing a single source with its PDF and annotations.

**Acceptance Criteria:**
- [ ] Create `frontend/src/app/vaults/[id]/sources/[sourceId]/page.tsx`
- [ ] Two-column layout: PDF viewer (70%) + Annotation sidebar (30%)
- [ ] Header shows source title, type badge, metadata
- [ ] Back button returns to sources list
- [ ] Breadcrumb navigation: Vault > Sources > [Source Title]
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-017: Create PDFViewer component with react-pdf
**Description:** As a user, I want to view PDF documents within the app so I don't need to download them separately.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/sources/PDFViewer.tsx`
- [ ] Install and configure `react-pdf` with worker
- [ ] Renders PDF from source URL
- [ ] Shows page navigation controls (prev/next, page input)
- [ ] Displays current page / total pages
- [ ] Shows loading state while PDF loads
- [ ] Error state if PDF fails to load
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-018: Create PDFViewerControls component
**Description:** As a user, I want zoom and navigation controls for the PDF viewer so I can read documents comfortably.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/sources/PDFViewerControls.tsx`
- [ ] Zoom in/out buttons with percentage display
- [ ] Fit to width / Fit to page toggle
- [ ] Download original PDF button
- [ ] Fullscreen toggle button
- [ ] Controls fixed at top of viewer area
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-019: Create AnnotationCard component
**Description:** As a user, I want to see annotations displayed as elegant glass morphism cards so they're visually distinct from the document.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/sources/AnnotationCard.tsx`
- [ ] Glass morphism style: `backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl`
- [ ] Shows annotation text, author avatar, timestamp in muted text
- [ ] Optional page number badge if annotation linked to specific page
- [ ] Reply count indicator with expand/collapse toggle
- [ ] Hover shows quick action buttons (reply, edit, delete)
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-020: Create AnnotationReplyCard component
**Description:** As a user, I want to see replies indented under their parent annotation so I can follow the conversation.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/sources/AnnotationReplyCard.tsx`
- [ ] Indented with left border accent (orange gradient)
- [ ] Smaller text size than parent annotation
- [ ] Shows author, timestamp in muted style
- [ ] Delete button for own replies
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-021: Create AnnotationSidebar component
**Description:** As a user, I want a sidebar panel listing all annotations for the current source so I can review and add notes.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/sources/AnnotationSidebar.tsx`
- [ ] Fixed height with scrollable content
- [ ] Header shows "Annotations" title with count badge
- [ ] "Add Annotation" button at top
- [ ] Lists AnnotationCards sorted by newest first
- [ ] Empty state: "No annotations yet. Be the first to add one!"
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-022: Create AddAnnotationForm component
**Description:** As a user, I want a form to add new annotations so I can share my notes with collaborators.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/sources/AddAnnotationForm.tsx`
- [ ] Textarea with placeholder "Add your annotation..."
- [ ] Optional page number input field
- [ ] Character count indicator
- [ ] Submit button (disabled when empty)
- [ ] Cancel button to collapse form
- [ ] Form uses bottom-border input style
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-023: Create AddReplyForm component
**Description:** As a user, I want to reply to annotations so I can discuss insights with my team.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/sources/AddReplyForm.tsx`
- [ ] Compact inline form appearing below annotation
- [ ] Single-line input that expands on focus
- [ ] Submit on Enter, cancel on Escape
- [ ] Shows author avatar next to input
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-024: Create useAnnotationsQuery hook
**Description:** As a developer, I need a React Query hook to fetch annotations for a source with real-time invalidation support.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/useAnnotationsQuery.ts`
- [ ] Accepts `sourceId` parameter
- [ ] Fetches annotations with nested replies
- [ ] Returns `{ data, isLoading, error, refetch }`
- [ ] Stale time set to 10 seconds (shorter for collaboration)
- [ ] Typecheck passes

---

### US-025: Create useAnnotationMutations hook
**Description:** As a developer, I need mutation hooks for creating annotations and replies with optimistic updates.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/useAnnotationMutations.ts`
- [ ] Exports `useCreateAnnotation`, `useCreateReply`, `useDeleteAnnotation`
- [ ] Each mutation invalidates annotations query on success
- [ ] Optimistic update shows new annotation immediately
- [ ] Rollback on error with toast notification
- [ ] Typecheck passes

---

### US-026: Create DeleteConfirmationDialog component
**Description:** As a user, I want a confirmation dialog before deleting sources or annotations so I don't accidentally lose data.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/sources/DeleteConfirmationDialog.tsx`
- [ ] Radix AlertDialog with glass morphism styling
- [ ] Shows item type and title being deleted
- [ ] "Delete" button in destructive red style
- [ ] "Cancel" button as secondary
- [ ] Accepts `onConfirm` callback
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-027: Create useSourcesWebSocket hook
**Description:** As a developer, I need a WebSocket hook to receive real-time source updates within a vault.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/useSourcesWebSocket.ts`
- [ ] Connects to `ws://.../ws/vault/{vaultId}/`
- [ ] Listens for events: `source.created`, `source.updated`, `source.deleted`
- [ ] Invalidates React Query cache on relevant events
- [ ] Auto-reconnect on disconnect with exponential backoff
- [ ] Cleanup on unmount
- [ ] Typecheck passes

---

### US-028: Create useAnnotationsWebSocket hook
**Description:** As a developer, I need a WebSocket hook to receive real-time annotation updates for collaborative editing.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/useAnnotationsWebSocket.ts`
- [ ] Connects to same vault WebSocket channel
- [ ] Listens for events: `annotation.created`, `annotation.deleted`, `reply.created`
- [ ] Invalidates annotations query on events
- [ ] Shows subtle toast when another user adds annotation
- [ ] Typecheck passes

---

### US-029: Integrate WebSocket hooks into SourcesList
**Description:** As a user, I want the sources list to update in real-time when collaborators add or remove sources.

**Acceptance Criteria:**
- [ ] Import and activate `useSourcesWebSocket` in sources page
- [ ] New sources appear without manual refresh
- [ ] Deleted sources disappear without manual refresh
- [ ] Subtle "New source added" indicator when update occurs
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-030: Integrate WebSocket hooks into AnnotationSidebar
**Description:** As a user, I want annotations to update in real-time when collaborators add notes.

**Acceptance Criteria:**
- [ ] Import and activate `useAnnotationsWebSocket` in SourceDetailPage
- [ ] New annotations appear without manual refresh
- [ ] New replies appear under their parent annotation
- [ ] "New annotation by [name]" toast appears briefly
- [ ] Scroll indicator if new annotation added below fold
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-031: Add keyboard shortcuts for source management
**Description:** As a power user, I want keyboard shortcuts so I can manage sources efficiently without using the mouse.

**Acceptance Criteria:**
- [ ] `n` opens Add Source modal (when not in input)
- [ ] `b` opens Bulk Import modal
- [ ] `g` toggles grid view, `t` toggles table view
- [ ] `Escape` closes any open modal
- [ ] `?` shows keyboard shortcuts help overlay
- [ ] Shortcuts only active when sources page focused
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-032: Add loading skeletons for sources and annotations
**Description:** As a user, I want to see loading skeletons so I know content is loading rather than missing.

**Acceptance Criteria:**
- [ ] Create `SourceCardSkeleton` matching SourceCard dimensions
- [ ] Create `SourceTableRowSkeleton` for table view
- [ ] Create `AnnotationCardSkeleton` for sidebar
- [ ] Skeletons use pulsing animation with `bg-white/10`
- [ ] Show 6 card skeletons or 10 row skeletons while loading
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

## Non-Goals

- Full-featured PDF annotation overlay (highlighting, drawing on PDF)
- Nested annotation replies beyond single level
- Source version history or diff tracking
- AI-powered metadata extraction (future enhancement)
- Auto-citation generation from URLs (future enhancement)
- Offline support for sources/PDFs
- Drag-and-drop file upload (URL-only for now)
- Source deduplication detection
- Export annotations to external formats

## Technical Considerations

- **react-pdf**: Use `@react-pdf/renderer` or `react-pdf` with PDF.js worker configured in Next.js
- **WebSocket**: Reuse existing vault WebSocket connection from Vaults UI if available
- **State Management**: React Query for server state, Zustand for UI state (view preferences)
- **URL Params**: Use Next.js `useSearchParams` for filter state to enable shareable filtered views
- **localStorage**: Use for view preference persistence only, not for caching data
- **Glass Morphism**: Consistent use of `backdrop-blur-lg bg-white/5 border border-white/10`
- **Muted Metadata**: Use `text-[#94A3B8]` (Stardust color) for timestamps, contributor names

## File Structure

```
frontend/src/
├── app/vaults/[id]/sources/
│   ├── page.tsx                    # Sources list page
│   └── [sourceId]/
│       └── page.tsx                # Source detail page
├── components/features/sources/
│   ├── SourceCard.tsx
│   ├── SourceCardSkeleton.tsx
│   ├── SourceTableRow.tsx
│   ├── SourceTableRowSkeleton.tsx
│   ├── SourceTypeBadge.tsx
│   ├── SourcesListHeader.tsx
│   ├── SourcesFilterBar.tsx
│   ├── SourcesList.tsx
│   ├── AddSourceModal.tsx
│   ├── SourceMetadataPreview.tsx
│   ├── BulkImportModal.tsx
│   ├── BulkImportPreviewList.tsx
│   ├── PDFViewer.tsx
│   ├── PDFViewerControls.tsx
│   ├── AnnotationCard.tsx
│   ├── AnnotationCardSkeleton.tsx
│   ├── AnnotationReplyCard.tsx
│   ├── AnnotationSidebar.tsx
│   ├── AddAnnotationForm.tsx
│   ├── AddReplyForm.tsx
│   └── DeleteConfirmationDialog.tsx
├── hooks/
│   ├── useSourcesQuery.ts
│   ├── useSourcesViewPreference.ts
│   ├── useAddSourceMutation.ts
│   ├── useAnnotationsQuery.ts
│   ├── useAnnotationMutations.ts
│   ├── useSourcesWebSocket.ts
│   └── useAnnotationsWebSocket.ts
└── lib/
    ├── types/
    │   ├── sources.ts
    │   └── annotations.ts
    └── api/
        ├── sources.ts
        └── annotations.ts
```
