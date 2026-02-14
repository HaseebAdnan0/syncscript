# PRD9: Frontend Sources & Annotations UI - Browser Verification - 2026-02-14

## Prerequisites
1. Backend server running: `cd backend && python manage.py runserver`
2. Frontend dev server running: `cd frontend && npm run dev`
3. PostgreSQL and Redis running
4. At least one test vault with sources and annotations
5. Two user accounts (for testing real-time collaboration features)
6. Browser with DevTools for inspecting WebSocket connections

## US-002, US-003, US-004: Source Display Components
- [ ] Navigate to `/vaults/[id]/sources` page
- [ ] Verify SourceCard displays with:
  - Glass morphism style (dark bg, white border with 10% opacity, rounded-2xl)
  - Source title, type badge, contributor avatar (gradient circle), date
  - Truncated URL or citation preview (80 chars max)
  - Hover effect: card lifts (-translate-y-1) and border changes to orange/50
  - Click navigates to source detail page
- [ ] Verify SourceTypeBadge shows correct icon and color:
  - URL: globe icon, blue theme
  - PDF: file icon, red theme
  - Citation: quote icon, purple theme
  - Article: newspaper icon, green theme
- [ ] Toggle to table view
- [ ] Verify SourceTableRow displays:
  - Type badge, linked title, contributor, date, actions menu
  - Row hover highlights with bg-white/5
  - Actions dropdown (MoreVertical icon) includes View, Edit, Delete
  - Delete option has red styling and separator above it

## US-005, US-007, US-008: Source List Views and Filters
- [ ] Verify SourcesListHeader shows:
  - "Sources" title with orange count badge
  - Grid/List view toggle buttons (active state has orange gradient)
  - "Add Source" button (gradient style, rounded-full)
- [ ] Click grid view toggle - verify sources display as card grid (3 columns on desktop)
- [ ] Click table view toggle - verify sources display as table with sticky header
- [ ] Verify view preference persists after page reload (check localStorage)
- [ ] Verify SourcesFilterBar displays:
  - Type filter dropdown (All Types, URL, PDF, Citation, Article)
  - Date filter dropdown (Any Time, Today, This Week, This Month)
  - Contributor filter dropdown (populated from vault members)
  - Clear filters button appears when any filter active
- [ ] Apply type filter (e.g., PDF) - verify only PDFs shown
- [ ] Apply date filter - verify sources filtered correctly
- [ ] Verify URL search params update when filters change (shareable URL)
- [ ] Click clear filters - verify all filters reset
- [ ] Verify empty state when no sources (FileQuestion icon, "Add your first source" CTA)
- [ ] Verify loading skeletons appear while fetching:
  - 6 card skeletons in grid view with pulsing animation
  - 10 row skeletons in table view with pulsing animation

## US-010, US-011, US-012, US-013, US-014: Add Source Modals
- [ ] Click "Add Source" button
- [ ] Verify AddSourceModal opens with glass morphism backdrop
- [ ] Enter URL in input field (bottom-border focus style, orange on focus)
- [ ] Press Enter or click "Fetch Metadata" button
- [ ] Verify loading spinner appears with "Fetching metadata from URL..."
- [ ] Verify SourceMetadataPreview appears with:
  - Favicon (or Globe icon fallback)
  - Detected source type badge
  - Editable title field (can customize before saving)
  - Description text
  - "Add Source" button (gradient style) and "Cancel" button (glass style)
- [ ] Edit title field - verify changes persist
- [ ] Click "Add Source" - verify:
  - Success toast appears with source title
  - Modal closes
  - New source appears in list without page refresh (React Query cache update)
- [ ] Test error state by entering invalid URL - verify error box shows with retry option
- [ ] Click keyboard shortcut `n` - verify modal opens (when not in input field)
- [ ] Press Escape - verify modal closes

- [ ] Click keyboard shortcut `b` to open Bulk Import modal
- [ ] Paste multiple URLs (one per line) in textarea
- [ ] Click "Parse URLs" button
- [ ] Verify BulkImportModal shows:
  - Count of valid/invalid URLs
  - Invalid URLs highlighted in red boxes with error messages
  - "Continue with N URLs" button appears
- [ ] Click "Continue with N URLs"
- [ ] Verify BulkImportPreviewList shows:
  - Each URL with checkbox (valid URLs only)
  - Green check icon for valid URLs, red X for invalid
  - "Select All" / "Deselect All" toggle button
  - Selection count indicator "N of M selected"
  - Remove button per URL (trash icon, hover shows red)
- [ ] Test "Select All" / "Deselect All" toggle
- [ ] Remove a URL - verify it disappears from list
- [ ] Click "Import Selected (N)" - verify:
  - Success toast appears
  - Modal closes
  - New sources appear in list (React Query cache update)

## US-015, US-016, US-017, US-018: Source Detail and PDF Viewer
- [ ] Click on a PDF source from sources list
- [ ] Verify SourceDetailPage displays:
  - Breadcrumb navigation: Vault > Sources > [Source Title]
  - Back button (ArrowLeft icon) returns to sources list
  - Header with source title (font-heading), type badge, metadata (URL/citation, contributor, date)
  - Two-column layout: PDF viewer (70%) + Annotation sidebar (30%)
- [ ] Verify PDFViewer shows:
  - PDF document rendered from source URL
  - Loading state while PDF loads (Loader2 spinner with "Loading PDF...")
  - Error state if PDF fails (red alert box with retry button)
  - Page navigation controls at top:
    - Previous/Next buttons (disabled at boundaries)
    - Page number input (1-N range validation)
    - "Page X of Y" indicator
- [ ] Click Next button - verify page advances
- [ ] Click Previous button - verify page goes back
- [ ] Type page number in input - verify PDF jumps to that page
- [ ] Test invalid page number (0, -1, N+1) - verify ignored

- [ ] Verify PDFViewerControls displays at top (fixed position, glass morphism pill):
  - Zoom In/Out buttons with percentage display
  - Fit Width / Fit Page toggle buttons (active state has gradient)
  - Download button (downloads original PDF)
  - Fullscreen toggle button (Maximize/Minimize icon switches)
- [ ] Click Zoom In - verify PDF zooms in (50% to 200% range)
- [ ] Click Zoom Out - verify PDF zooms out
- [ ] Verify zoom buttons disabled at min/max limits
- [ ] Click "Fit Width" - verify PDF fits to container width
- [ ] Click "Fit Page" - verify PDF fits entire page
- [ ] Click Download - verify PDF downloads
- [ ] Click Fullscreen - verify fullscreen mode activates (icon changes to Minimize)

## US-019, US-020, US-021, US-022, US-023: Annotations
- [ ] Verify AnnotationSidebar displays:
  - "Annotations" header with orange count badge
  - "Add Annotation" button (gradient pill style, MessageSquarePlus icon)
  - List of AnnotationCards sorted newest first
  - Empty state with encouraging message and CTA if no annotations
- [ ] Verify AnnotationCard displays:
  - Glass morphism style (backdrop-blur-lg, bg-white/5, border white/10)
  - Annotation text, author avatar (gradient circle), username, timestamp
  - Optional page number badge (orange pill)
  - Reply count indicator "N replies • Show/Hide"
  - Hover shows quick action buttons: reply, edit (own only), delete (own only)
- [ ] Click "Show replies" - verify:
  - Replies expand with left orange accent border
  - AnnotationReplyCards display inline (smaller text, indented)
  - Each reply shows author avatar, username, timestamp, text
  - Delete button appears on hover for own replies
- [ ] Hover over AnnotationCard - verify action buttons appear
- [ ] Click Edit button (own annotation) - verify edit mode activates
- [ ] Click Delete button - verify DeleteConfirmationDialog opens

- [ ] Click "Add Annotation" button
- [ ] Verify AddAnnotationForm appears:
  - Glass morphism card wrapping
  - Textarea with placeholder hinting at Cmd/Ctrl + Enter shortcut
  - Optional page number input field
  - Character count indicator (color-coded: orange <100 remaining, red over limit)
  - Submit button (disabled when empty or over 2000 chars)
  - Cancel button (glass style)
- [ ] Type annotation text
- [ ] Verify character count updates in real-time
- [ ] Type over 2000 chars - verify count turns red and submit disabled
- [ ] Enter page number (optional)
- [ ] Press Cmd/Ctrl + Enter - verify annotation submits
- [ ] Verify:
  - Form auto-resets (clears text and page number)
  - New annotation appears at top of list (newest first)
  - Success feedback (annotation appears immediately)
- [ ] Press Escape while form open - verify form closes

- [ ] Click Reply button on an AnnotationCard
- [ ] Verify AddReplyForm appears inline:
  - Compact single-line input (not textarea)
  - Author avatar (small gradient circle) next to input
  - Bottom-border focus style (orange on focus)
  - Placeholder hints at Enter/Escape shortcuts
  - Character count appears when focused or has text (500 char max)
  - Cancel (X icon) and Send buttons appear when focused
- [ ] Type reply text
- [ ] Press Enter - verify reply submits
- [ ] Verify:
  - Form auto-resets and closes
  - New reply appears under parent annotation (indented, left border)
  - Parent annotation reply count increments
- [ ] Press Escape while typing - verify form clears and closes

## US-026: Delete Confirmation
- [ ] Click Delete button on source/annotation/reply
- [ ] Verify DeleteConfirmationDialog opens:
  - Glass morphism AlertDialog styling
  - Shows item type (Source/Annotation/Reply) and title
  - Delete button (red destructive style, rounded-full)
  - Cancel button (glass style, rounded-full)
- [ ] Click Cancel - verify dialog closes without deleting
- [ ] Click Delete - verify:
  - Loading state appears ("Deleting..." with spinner)
  - Item deleted from backend
  - UI updates (item removed from list)
  - Success toast appears
  - Dialog closes

## US-027, US-029: Real-time Source Updates (WebSocket)
- [ ] Open two browser tabs logged in as different users
- [ ] Navigate both to same vault's sources page
- [ ] User A: Add a new source
- [ ] User B: Verify:
  - New source appears in list without manual refresh
  - Subtle "New source added" indicator shows (if implemented)
  - React Query cache invalidates automatically
- [ ] User A: Delete a source
- [ ] User B: Verify source disappears without manual refresh
- [ ] Open DevTools > Network > WS - verify WebSocket connection active
- [ ] Verify events: source.created, source.updated, source.deleted

## US-028, US-030: Real-time Annotation Updates (WebSocket)
- [ ] Open two browser tabs logged in as different users
- [ ] Navigate both to same source detail page
- [ ] User A: Add a new annotation
- [ ] User B: Verify:
  - New annotation appears without manual refresh
  - Toast notification: "New annotation - [User A] added an annotation"
  - Annotation appears at top of list (newest first)
- [ ] User A: Reply to an annotation
- [ ] User B: Verify:
  - New reply appears under parent annotation without manual refresh
  - Toast notification: "New reply - [User A] replied to an annotation"
  - Parent annotation reply count increments
- [ ] User A: Add annotation while User B scrolled down (below fold)
- [ ] User B: Verify:
  - Scroll indicator button appears (orange gradient, bounce animation, "New annotation")
  - Click button - verify smooth scroll to top where new annotation is
  - Indicator auto-hides when scrolled near top
- [ ] User A: Delete an annotation
- [ ] User B: Verify annotation disappears without manual refresh
- [ ] Verify DevTools > Network > WS shows events: annotation.created, annotation.deleted, reply.created

## US-031: Keyboard Shortcuts
- [ ] On sources page, press `?` (question mark)
- [ ] Verify keyboard shortcuts help dialog opens with:
  - List of all shortcuts with kbd elements (glass morphism styling)
  - Note: "Shortcuts are disabled when typing in input fields"
- [ ] Press Escape - verify help dialog closes
- [ ] Test shortcuts (when NOT in input field):
  - Press `n` - verify Add Source modal opens
  - Press `b` - verify Bulk Import modal opens
  - Press `g` - verify grid view activates
  - Press `t` - verify table view activates
  - Press Escape - verify any open modal closes
- [ ] Test shortcuts disabled in input:
  - Focus on filter input field
  - Press `n` - verify modal does NOT open (character typed in input instead)
  - Press Escape - verify input clears but modal doesn't trigger

## US-032: Loading Skeletons
- [ ] Refresh sources page while network throttled (DevTools > Network > Slow 3G)
- [ ] Verify SourceCardSkeleton appears:
  - Matches SourceCard dimensions
  - Pulsing animation (animate-pulse)
  - bg-white/10 skeleton elements
  - 6 skeletons shown in grid view
- [ ] Switch to table view
- [ ] Verify SourceTableRowSkeleton appears:
  - Matches SourceTableRow dimensions
  - 10 skeletons shown in table view
- [ ] Navigate to source detail page
- [ ] Verify AnnotationCardSkeleton appears in sidebar:
  - Matches AnnotationCard layout (avatar, author, text lines, reply count)
  - Glass morphism style matching actual cards
  - Varying text line widths for natural look

## Expected Behavior
- All components follow Bitcoin DeFi aesthetic (dark bg, orange accents, glass morphism)
- Real-time updates appear without page refresh via WebSocket events
- Toast notifications show for collaborative events
- Loading skeletons match component dimensions with pulsing animation
- Keyboard shortcuts improve UX for power users
- All modals close on Escape key
- View preferences persist in localStorage
- Filter state persists in URL search params (shareable links)
- All forms show validation errors and loading states
- All hover effects smooth with transition-all duration-300

## Issues Found
(Append any bugs, edge cases, or unexpected behavior discovered during testing)
