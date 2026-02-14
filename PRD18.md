# PRD: Advanced Search System

## Introduction

Implement a global full-text search system for SyncScript that enables researchers to quickly find vaults, sources, and annotations across their accessible content. The system uses PostgreSQL's native full-text search with tsvector columns and GIN indexes for fast, relevance-ranked results. Features include a Cmd+K modal for quick access, type filtering, highlighted matches, recent searches, and a full search page with advanced filtering.

## Goals

- Enable fast full-text search across vaults, sources, and annotations
- Respect vault permissions (only show results from accessible vaults)
- Provide instant search suggestions based on existing content
- Track recent searches per user for quick re-access
- Collect anonymized search analytics for popular queries
- Deliver responsive Cmd+K modal with keyboard navigation
- Support advanced filtering on dedicated search page

## Dependencies

- **Backend Sources/Annotations models** (exist)
- **Backend Vaults app with membership system** (exists)
- **Celery for background tasks** (configured)
- **Frontend design system** (exists)

## User Stories

---

### US-001: Add tsvector search columns to Source model
**Description:** As a developer, I need searchable tsvector columns on the Source model so PostgreSQL can perform fast full-text search.

**Acceptance Criteria:**
- [x] Add `search_vector` field to Source model: `SearchVectorField(null=True)`
- [x] Create migration adding the column
- [x] Add GIN index on `search_vector` column
- [x] Migration runs successfully
- [x] Typecheck passes

---

### US-002: Add tsvector search column to Annotation model
**Description:** As a developer, I need a searchable tsvector column on the Annotation model for full-text search on annotation content.

**Acceptance Criteria:**
- [x] Add `search_vector` field to Annotation model: `SearchVectorField(null=True)`
- [x] Create migration adding the column
- [x] Add GIN index on `search_vector` column
- [x] Migration runs successfully
- [x] Typecheck passes

---

### US-003: Create search app with SearchHistory model
**Description:** As a developer, I need a new search app with a model to store user search history.

**Acceptance Criteria:**
- [x] Create `backend/apps/search/` app with models.py, views.py, urls.py, serializers.py
- [x] Add `SearchHistory` model with fields: `user` (FK), `query` (CharField), `result_count` (IntegerField), `created_at` (DateTimeField)
- [x] Add index on `user` and `created_at` for efficient retrieval
- [x] Register app in settings.py INSTALLED_APPS
- [x] Migration runs successfully
- [x] Typecheck passes

---

### US-004: Create SearchAnalytics model for popular searches
**Description:** As a developer, I need a model to track anonymized search query popularity.

**Acceptance Criteria:**
- [x] Create `SearchAnalytics` model with fields: `query_hash` (CharField, indexed), `query_normalized` (CharField), `search_count` (IntegerField), `last_searched` (DateTimeField)
- [x] Query normalized to lowercase, trimmed
- [x] Hash uses SHA-256 for privacy
- [x] Unique constraint on `query_hash`
- [x] Migration runs successfully
- [x] Typecheck passes

---

### US-005: Create Celery task to update Source search vectors
**Description:** As a developer, I need a background task to update Source search vectors when content changes.

**Acceptance Criteria:**
- [x] Create `backend/apps/search/tasks.py`
- [x] Create `update_source_search_vector` task accepting source_id
- [x] Task combines title (weight A), description (weight B), metadata values (weight C)
- [x] Uses `SearchVector` with `config='english'`
- [x] Task is idempotent (safe to retry)
- [x] Typecheck passes

---

### US-006: Create Celery task to update Annotation search vectors
**Description:** As a developer, I need a background task to update Annotation search vectors when content changes.

**Acceptance Criteria:**
- [x] Create `update_annotation_search_vector` task in tasks.py
- [x] Task accepts annotation_id parameter
- [x] Combines content field with weight A
- [x] Uses `SearchVector` with `config='english'`
- [x] Task is idempotent
- [x] Typecheck passes

---

### US-007: Add signals to trigger search vector updates
**Description:** As a developer, I need Django signals to automatically queue search vector updates when models change.

**Acceptance Criteria:**
- [x] Create `backend/apps/search/signals.py`
- [x] Post-save signal on Source triggers `update_source_search_vector.delay()`
- [x] Post-save signal on Annotation triggers `update_annotation_search_vector.delay()`
- [x] Signals connected in search app's `ready()` method
- [x] Only trigger on relevant field changes (title, description, content)
- [x] Typecheck passes

---

### US-008: Create search serializers
**Description:** As a developer, I need serializers for search results and search history.

**Acceptance Criteria:**
- [x] Create `SearchResultSerializer` with fields: `id`, `type`, `title`, `snippet`, `highlight`, `relevance`, `vault_id`, `vault_name`, `breadcrumb`
- [x] Create `SearchHistorySerializer` with fields: `id`, `query`, `result_count`, `created_at`
- [x] Create `SearchSuggestionSerializer` with fields: `text`, `type`, `count`
- [x] Serializers in `backend/apps/search/serializers.py`
- [x] Typecheck passes

---

### US-009: Create main search endpoint
**Description:** As a user, I want to search across all my accessible content so I can find relevant information quickly.

**Acceptance Criteria:**
- [x] Create `GET /api/v1/search/` endpoint
- [x] Query params: `q` (required), `type` (optional: sources,annotations,vaults), `vault_id` (optional), `limit` (default 20)
- [x] Filter results to vaults where user is Owner/Contributor/Viewer
- [x] Return grouped results by type with relevance scores
- [x] Highlight matching text with `<mark>` tags in snippet
- [x] Minimum query length: 2 characters
- [x] Return 400 if query too short
- [x] Typecheck passes

---

### US-010: Create search suggestions endpoint
**Description:** As a user, I want search suggestions as I type so I can find content faster.

**Acceptance Criteria:**
- [x] Create `GET /api/v1/search/suggestions/` endpoint
- [x] Query param: `q` (required, min 2 chars)
- [x] Return top 5 completions based on Source titles and Annotation content
- [x] Filter to user's accessible vaults
- [x] Include suggestion type (source/annotation) and match count
- [x] Response time < 100ms for typical queries
- [x] Typecheck passes

---

### US-011: Create recent searches endpoint
**Description:** As a user, I want to see my recent searches so I can quickly re-run previous queries.

**Acceptance Criteria:**
- [x] Create `GET /api/v1/search/recent/` endpoint
- [x] Return last 10 searches for authenticated user
- [x] Ordered by most recent first
- [x] Create `DELETE /api/v1/search/recent/` to clear history
- [x] Create `DELETE /api/v1/search/recent/{id}/` to remove single entry
- [x] Typecheck passes

---

### US-012: Implement search analytics tracking
**Description:** As a developer, I need to track search queries for analytics without storing user identity.

**Acceptance Criteria:**
- [x] Create `track_search_analytics` function in `backend/apps/search/services.py`
- [x] Hash query with SHA-256, normalize to lowercase
- [x] Increment `search_count` if exists, create if not
- [x] Update `last_searched` timestamp
- [x] Call from search endpoint after returning results
- [x] Typecheck passes

---

### US-013: Create search history recording
**Description:** As a developer, I need to record search queries in user history for recent searches feature.

**Acceptance Criteria:**
- [x] Create `record_search_history` function in services.py
- [x] Store query, user, and result count
- [x] Limit to 10 most recent per user (delete oldest on insert)
- [x] Deduplicate: if same query exists, update timestamp instead
- [x] Call from search endpoint after returning results
- [x] Typecheck passes

---

### US-014: Create management command to backfill search vectors
**Description:** As a developer, I need a command to populate search vectors for existing data.

**Acceptance Criteria:**
- [x] Create `python manage.py rebuild_search_index` command
- [x] Processes all Sources in batches of 100
- [x] Processes all Annotations in batches of 100
- [x] Shows progress bar with total count
- [x] Supports `--sources-only` and `--annotations-only` flags
- [x] Typecheck passes

---

### US-015: Create search TypeScript types and API client
**Description:** As a developer, I need TypeScript types and API functions for the search feature.

**Acceptance Criteria:**
- [x] Create `frontend/src/lib/types/search.ts` with `SearchResult`, `SearchResultType`, `SearchSuggestion`, `SearchHistory` types
- [x] Create `frontend/src/lib/api/search.ts` with functions: `search`, `getSuggestions`, `getRecentSearches`, `clearRecentSearches`, `deleteRecentSearch`
- [x] All functions properly typed with generics
- [x] Uses existing axios instance
- [x] Typecheck passes

---

### US-016: Create useSearchQuery hook
**Description:** As a developer, I need a React Query hook for search with debouncing.

**Acceptance Criteria:**
- [x] Create `frontend/src/hooks/useSearchQuery.ts`
- [x] Accepts query string and optional filters (type, vaultId)
- [x] Debounces API calls by 200ms
- [x] Only fires when query >= 2 characters
- [x] Returns `{ data, isLoading, error }`
- [x] Stale time: 30 seconds
- [x] Typecheck passes

---

### US-017: Create useSuggestionsQuery hook
**Description:** As a developer, I need a hook for search suggestions with fast debouncing.

**Acceptance Criteria:**
- [x] Create `frontend/src/hooks/useSuggestionsQuery.ts`
- [x] Debounce: 150ms (faster than full search)
- [x] Only fires when query >= 2 characters
- [x] Returns top 5 suggestions
- [x] Lightweight response for speed
- [x] Typecheck passes

---

### US-018: Create useRecentSearches hook
**Description:** As a developer, I need a hook to manage recent searches state.

**Acceptance Criteria:**
- [x] Create `frontend/src/hooks/useRecentSearches.ts`
- [x] Fetches recent searches on mount
- [x] Provides `clearAll` and `removeOne` mutation functions
- [x] Optimistic updates for delete operations
- [x] Refetches on window focus
- [x] Typecheck passes

---

### US-019: Create GlobalSearchModal base component
**Description:** As a user, I want a search modal that opens with Cmd+K so I can search without leaving my current context.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/search/GlobalSearchModal.tsx`
- [x] Uses Radix Dialog with glass morphism backdrop
- [x] Modal width: 640px max, centered vertically (slightly above center)
- [x] Smooth fade-in animation
- [x] Closes on Escape or backdrop click
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-020: Create SearchInput component
**Description:** As a user, I want a search input with icon and clear button so I can enter and modify queries easily.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/search/SearchInput.tsx`
- [x] Search icon (magnifying glass) on left
- [x] Input uses bottom-border focus style (orange)
- [x] Clear button (X) appears when input has value
- [x] Placeholder: "Search vaults, sources, annotations..."
- [x] Auto-focus when modal opens
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-021: Create SearchTypeFilter component
**Description:** As a user, I want filter tabs to narrow results by type so I can find specific content types.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/search/SearchTypeFilter.tsx`
- [x] Tab options: All, Vaults, Sources, Annotations
- [x] Active tab has orange underline/highlight
- [x] Tabs show result count badge when results available
- [x] Clicking tab filters results immediately
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-022: Create SearchResultItem component
**Description:** As a user, I want search results displayed with highlighted matches so I can quickly identify relevant content.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/search/SearchResultItem.tsx`
- [x] Shows type icon (vault, file, annotation icons)
- [x] Title with `<mark>` highlights rendered as orange background
- [x] Breadcrumb for context: "Vault Name > Source Title" for annotations
- [x] Preview snippet with highlighted text (max 2 lines)
- [x] Hover state with `bg-white/5`
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-023: Create SearchResultsList component
**Description:** As a user, I want search results grouped by type so I can scan results efficiently.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/search/SearchResultsList.tsx`
- [x] Groups results by type with section headers
- [x] Shows max 5 results per type in quick view
- [x] "See all X results" link per section when more exist
- [x] Scrollable with max height
- [x] Empty sections hidden
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-024: Create SearchResultsSkeleton component
**Description:** As a user, I want to see loading skeletons while search results load so I know the search is working.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/search/SearchResultsSkeleton.tsx`
- [x] Shows 5 skeleton items with pulsing animation
- [x] Matches SearchResultItem dimensions
- [x] Uses `bg-white/10` for skeleton blocks
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-025: Create RecentSearchesList component
**Description:** As a user, I want to see my recent searches when the search input is empty so I can quickly re-run queries.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/search/RecentSearchesList.tsx`
- [x] Shows when search input is empty
- [x] List of recent queries with clock icon
- [x] Click to populate search input and run search
- [x] "Clear all" link in header
- [x] Individual remove (X) button on hover
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-026: Create NoResultsState component
**Description:** As a user, I want helpful feedback when no results are found so I know my search was processed.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/search/NoResultsState.tsx`
- [x] Shows "No results for [query]" message
- [x] Suggests: "Try different keywords" or "Search in all types"
- [x] Shows popular searches if available
- [x] Uses muted styling
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-027: Create useSearchKeyboardNavigation hook
**Description:** As a power user, I want keyboard navigation in search results so I can select items without a mouse.

**Acceptance Criteria:**
- [x] Create `frontend/src/hooks/useSearchKeyboardNavigation.ts`
- [x] Arrow up/down moves selection through results
- [x] Enter opens selected result
- [x] Escape closes modal (when at top) or clears selection
- [x] Selection wraps at boundaries
- [x] Visual highlight on selected item
- [x] Typecheck passes

---

### US-028: Create useGlobalSearchShortcut hook
**Description:** As a user, I want Cmd+K (Mac) / Ctrl+K (Windows) to open search from anywhere in the app.

**Acceptance Criteria:**
- [x] Create `frontend/src/hooks/useGlobalSearchShortcut.ts`
- [x] Detects platform for correct modifier key
- [x] Prevents default browser behavior
- [x] Only triggers when not in input/textarea
- [x] Returns `{ isOpen, open, close, toggle }`
- [x] Typecheck passes

---

### US-029: Integrate GlobalSearchModal into app layout
**Description:** As a user, I want the search modal accessible from anywhere in the app.

**Acceptance Criteria:**
- [x] Add GlobalSearchModal to root layout or providers
- [x] Search state managed via Zustand store or context
- [x] Modal renders above all other content (z-50)
- [x] Cmd+K works on all pages
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-030: Create full search page route
**Description:** As a user, I want a dedicated search page for advanced filtering and browsing all results.

**Acceptance Criteria:**
- [x] Create `frontend/src/app/search/page.tsx`
- [x] Reads initial query from URL: `/search?q=query`
- [x] Full-width search input at top
- [x] Type filter tabs below input
- [x] Paginated results list
- [x] URL updates as filters change
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-031: Create SearchFiltersPanel component
**Description:** As a user, I want advanced filters on the search page so I can narrow down results precisely.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/search/SearchFiltersPanel.tsx`
- [x] Filter by vault (dropdown of user's vaults)
- [x] Filter by date range (created within)
- [x] Filter by contributor (for sources/annotations)
- [x] "Clear filters" button
- [x] Filters persist in URL params
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-032: Create SearchPagination component
**Description:** As a user, I want pagination on the search page so I can browse through many results.

**Acceptance Criteria:**
- [x] Create `frontend/src/components/features/search/SearchPagination.tsx`
- [x] Shows current page / total pages
- [x] Previous/Next buttons
- [x] Page number buttons for nearby pages
- [x] Updates URL with page param
- [x] Scrolls to top on page change
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-033: Add search button to navigation header
**Description:** As a user, I want a visible search button in the header as an alternative to keyboard shortcut.

**Acceptance Criteria:**
- [x] Add search icon button to main navigation header
- [x] Shows "Cmd+K" or "Ctrl+K" hint tooltip
- [x] Click opens GlobalSearchModal
- [x] Button uses glass morphism style
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-034: Wire up search result navigation
**Description:** As a user, I want clicking a search result to navigate to that item so I can access the content.

**Acceptance Criteria:**
- [ ] Vault results navigate to `/vaults/[id]`
- [ ] Source results navigate to `/vaults/[vaultId]/sources/[sourceId]`
- [ ] Annotation results navigate to source page with annotation highlighted
- [ ] Modal closes after navigation
- [ ] Search query preserved in recent searches
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

## Non-Goals

- Elasticsearch or external search service (using PostgreSQL native)
- Real-time search-as-you-type with WebSockets
- Fuzzy/typo-tolerant search (future enhancement)
- Search within PDF content (requires OCR, future enhancement)
- Search filters by custom metadata fields
- Saved searches or search alerts
- Search result ranking customization
- Multi-language search configuration

## Technical Considerations

- **PostgreSQL Full-Text Search**: Use `django.contrib.postgres.search` with `SearchVector`, `SearchQuery`, `SearchRank`
- **GIN Indexes**: Essential for search performance on tsvector columns
- **Celery**: Background tasks for index updates to avoid blocking requests
- **Debouncing**: 200ms for search, 150ms for suggestions to balance UX and API load
- **Highlighting**: Use `SearchHeadline` with `<mark>` tags for snippet highlighting
- **Permissions**: Filter all search queries through vault membership checks
- **Caching**: Consider caching popular search results with short TTL
- **URL State**: Persist search state in URL for shareability and browser history

## File Structure

```
backend/apps/search/
├── __init__.py
├── admin.py
├── apps.py
├── models.py              # SearchHistory, SearchAnalytics
├── serializers.py         # SearchResultSerializer, etc.
├── services.py            # track_search_analytics, record_search_history
├── signals.py             # Post-save signals for vector updates
├── tasks.py               # Celery tasks for vector updates
├── urls.py
├── views.py               # SearchView, SuggestionsView, RecentSearchesView
└── management/
    └── commands/
        └── rebuild_search_index.py

frontend/src/
├── app/search/
│   └── page.tsx                      # Full search page
├── components/features/search/
│   ├── GlobalSearchModal.tsx
│   ├── SearchInput.tsx
│   ├── SearchTypeFilter.tsx
│   ├── SearchResultItem.tsx
│   ├── SearchResultsList.tsx
│   ├── SearchResultsSkeleton.tsx
│   ├── RecentSearchesList.tsx
│   ├── NoResultsState.tsx
│   ├── SearchFiltersPanel.tsx
│   └── SearchPagination.tsx
├── hooks/
│   ├── useSearchQuery.ts
│   ├── useSuggestionsQuery.ts
│   ├── useRecentSearches.ts
│   ├── useSearchKeyboardNavigation.ts
│   └── useGlobalSearchShortcut.ts
└── lib/
    ├── types/
    │   └── search.ts
    └── api/
        └── search.ts
```
