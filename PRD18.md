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
- [ ] Create `backend/apps/search/tasks.py`
- [ ] Create `update_source_search_vector` task accepting source_id
- [ ] Task combines title (weight A), description (weight B), metadata values (weight C)
- [ ] Uses `SearchVector` with `config='english'`
- [ ] Task is idempotent (safe to retry)
- [ ] Typecheck passes

---

### US-006: Create Celery task to update Annotation search vectors
**Description:** As a developer, I need a background task to update Annotation search vectors when content changes.

**Acceptance Criteria:**
- [ ] Create `update_annotation_search_vector` task in tasks.py
- [ ] Task accepts annotation_id parameter
- [ ] Combines content field with weight A
- [ ] Uses `SearchVector` with `config='english'`
- [ ] Task is idempotent
- [ ] Typecheck passes

---

### US-007: Add signals to trigger search vector updates
**Description:** As a developer, I need Django signals to automatically queue search vector updates when models change.

**Acceptance Criteria:**
- [ ] Create `backend/apps/search/signals.py`
- [ ] Post-save signal on Source triggers `update_source_search_vector.delay()`
- [ ] Post-save signal on Annotation triggers `update_annotation_search_vector.delay()`
- [ ] Signals connected in search app's `ready()` method
- [ ] Only trigger on relevant field changes (title, description, content)
- [ ] Typecheck passes

---

### US-008: Create search serializers
**Description:** As a developer, I need serializers for search results and search history.

**Acceptance Criteria:**
- [ ] Create `SearchResultSerializer` with fields: `id`, `type`, `title`, `snippet`, `highlight`, `relevance`, `vault_id`, `vault_name`, `breadcrumb`
- [ ] Create `SearchHistorySerializer` with fields: `id`, `query`, `result_count`, `created_at`
- [ ] Create `SearchSuggestionSerializer` with fields: `text`, `type`, `count`
- [ ] Serializers in `backend/apps/search/serializers.py`
- [ ] Typecheck passes

---

### US-009: Create main search endpoint
**Description:** As a user, I want to search across all my accessible content so I can find relevant information quickly.

**Acceptance Criteria:**
- [ ] Create `GET /api/v1/search/` endpoint
- [ ] Query params: `q` (required), `type` (optional: sources,annotations,vaults), `vault_id` (optional), `limit` (default 20)
- [ ] Filter results to vaults where user is Owner/Contributor/Viewer
- [ ] Return grouped results by type with relevance scores
- [ ] Highlight matching text with `<mark>` tags in snippet
- [ ] Minimum query length: 2 characters
- [ ] Return 400 if query too short
- [ ] Typecheck passes

---

### US-010: Create search suggestions endpoint
**Description:** As a user, I want search suggestions as I type so I can find content faster.

**Acceptance Criteria:**
- [ ] Create `GET /api/v1/search/suggestions/` endpoint
- [ ] Query param: `q` (required, min 2 chars)
- [ ] Return top 5 completions based on Source titles and Annotation content
- [ ] Filter to user's accessible vaults
- [ ] Include suggestion type (source/annotation) and match count
- [ ] Response time < 100ms for typical queries
- [ ] Typecheck passes

---

### US-011: Create recent searches endpoint
**Description:** As a user, I want to see my recent searches so I can quickly re-run previous queries.

**Acceptance Criteria:**
- [ ] Create `GET /api/v1/search/recent/` endpoint
- [ ] Return last 10 searches for authenticated user
- [ ] Ordered by most recent first
- [ ] Create `DELETE /api/v1/search/recent/` to clear history
- [ ] Create `DELETE /api/v1/search/recent/{id}/` to remove single entry
- [ ] Typecheck passes

---

### US-012: Implement search analytics tracking
**Description:** As a developer, I need to track search queries for analytics without storing user identity.

**Acceptance Criteria:**
- [ ] Create `track_search_analytics` function in `backend/apps/search/services.py`
- [ ] Hash query with SHA-256, normalize to lowercase
- [ ] Increment `search_count` if exists, create if not
- [ ] Update `last_searched` timestamp
- [ ] Call from search endpoint after returning results
- [ ] Typecheck passes

---

### US-013: Create search history recording
**Description:** As a developer, I need to record search queries in user history for recent searches feature.

**Acceptance Criteria:**
- [ ] Create `record_search_history` function in services.py
- [ ] Store query, user, and result count
- [ ] Limit to 10 most recent per user (delete oldest on insert)
- [ ] Deduplicate: if same query exists, update timestamp instead
- [ ] Call from search endpoint after returning results
- [ ] Typecheck passes

---

### US-014: Create management command to backfill search vectors
**Description:** As a developer, I need a command to populate search vectors for existing data.

**Acceptance Criteria:**
- [ ] Create `python manage.py rebuild_search_index` command
- [ ] Processes all Sources in batches of 100
- [ ] Processes all Annotations in batches of 100
- [ ] Shows progress bar with total count
- [ ] Supports `--sources-only` and `--annotations-only` flags
- [ ] Typecheck passes

---

### US-015: Create search TypeScript types and API client
**Description:** As a developer, I need TypeScript types and API functions for the search feature.

**Acceptance Criteria:**
- [ ] Create `frontend/src/lib/types/search.ts` with `SearchResult`, `SearchResultType`, `SearchSuggestion`, `SearchHistory` types
- [ ] Create `frontend/src/lib/api/search.ts` with functions: `search`, `getSuggestions`, `getRecentSearches`, `clearRecentSearches`, `deleteRecentSearch`
- [ ] All functions properly typed with generics
- [ ] Uses existing axios instance
- [ ] Typecheck passes

---

### US-016: Create useSearchQuery hook
**Description:** As a developer, I need a React Query hook for search with debouncing.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/useSearchQuery.ts`
- [ ] Accepts query string and optional filters (type, vaultId)
- [ ] Debounces API calls by 200ms
- [ ] Only fires when query >= 2 characters
- [ ] Returns `{ data, isLoading, error }`
- [ ] Stale time: 30 seconds
- [ ] Typecheck passes

---

### US-017: Create useSuggestionsQuery hook
**Description:** As a developer, I need a hook for search suggestions with fast debouncing.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/useSuggestionsQuery.ts`
- [ ] Debounce: 150ms (faster than full search)
- [ ] Only fires when query >= 2 characters
- [ ] Returns top 5 suggestions
- [ ] Lightweight response for speed
- [ ] Typecheck passes

---

### US-018: Create useRecentSearches hook
**Description:** As a developer, I need a hook to manage recent searches state.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/useRecentSearches.ts`
- [ ] Fetches recent searches on mount
- [ ] Provides `clearAll` and `removeOne` mutation functions
- [ ] Optimistic updates for delete operations
- [ ] Refetches on window focus
- [ ] Typecheck passes

---

### US-019: Create GlobalSearchModal base component
**Description:** As a user, I want a search modal that opens with Cmd+K so I can search without leaving my current context.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/search/GlobalSearchModal.tsx`
- [ ] Uses Radix Dialog with glass morphism backdrop
- [ ] Modal width: 640px max, centered vertically (slightly above center)
- [ ] Smooth fade-in animation
- [ ] Closes on Escape or backdrop click
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-020: Create SearchInput component
**Description:** As a user, I want a search input with icon and clear button so I can enter and modify queries easily.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/search/SearchInput.tsx`
- [ ] Search icon (magnifying glass) on left
- [ ] Input uses bottom-border focus style (orange)
- [ ] Clear button (X) appears when input has value
- [ ] Placeholder: "Search vaults, sources, annotations..."
- [ ] Auto-focus when modal opens
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-021: Create SearchTypeFilter component
**Description:** As a user, I want filter tabs to narrow results by type so I can find specific content types.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/search/SearchTypeFilter.tsx`
- [ ] Tab options: All, Vaults, Sources, Annotations
- [ ] Active tab has orange underline/highlight
- [ ] Tabs show result count badge when results available
- [ ] Clicking tab filters results immediately
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-022: Create SearchResultItem component
**Description:** As a user, I want search results displayed with highlighted matches so I can quickly identify relevant content.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/search/SearchResultItem.tsx`
- [ ] Shows type icon (vault, file, annotation icons)
- [ ] Title with `<mark>` highlights rendered as orange background
- [ ] Breadcrumb for context: "Vault Name > Source Title" for annotations
- [ ] Preview snippet with highlighted text (max 2 lines)
- [ ] Hover state with `bg-white/5`
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-023: Create SearchResultsList component
**Description:** As a user, I want search results grouped by type so I can scan results efficiently.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/search/SearchResultsList.tsx`
- [ ] Groups results by type with section headers
- [ ] Shows max 5 results per type in quick view
- [ ] "See all X results" link per section when more exist
- [ ] Scrollable with max height
- [ ] Empty sections hidden
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-024: Create SearchResultsSkeleton component
**Description:** As a user, I want to see loading skeletons while search results load so I know the search is working.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/search/SearchResultsSkeleton.tsx`
- [ ] Shows 5 skeleton items with pulsing animation
- [ ] Matches SearchResultItem dimensions
- [ ] Uses `bg-white/10` for skeleton blocks
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-025: Create RecentSearchesList component
**Description:** As a user, I want to see my recent searches when the search input is empty so I can quickly re-run queries.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/search/RecentSearchesList.tsx`
- [ ] Shows when search input is empty
- [ ] List of recent queries with clock icon
- [ ] Click to populate search input and run search
- [ ] "Clear all" link in header
- [ ] Individual remove (X) button on hover
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-026: Create NoResultsState component
**Description:** As a user, I want helpful feedback when no results are found so I know my search was processed.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/search/NoResultsState.tsx`
- [ ] Shows "No results for [query]" message
- [ ] Suggests: "Try different keywords" or "Search in all types"
- [ ] Shows popular searches if available
- [ ] Uses muted styling
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-027: Create useSearchKeyboardNavigation hook
**Description:** As a power user, I want keyboard navigation in search results so I can select items without a mouse.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/useSearchKeyboardNavigation.ts`
- [ ] Arrow up/down moves selection through results
- [ ] Enter opens selected result
- [ ] Escape closes modal (when at top) or clears selection
- [ ] Selection wraps at boundaries
- [ ] Visual highlight on selected item
- [ ] Typecheck passes

---

### US-028: Create useGlobalSearchShortcut hook
**Description:** As a user, I want Cmd+K (Mac) / Ctrl+K (Windows) to open search from anywhere in the app.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/useGlobalSearchShortcut.ts`
- [ ] Detects platform for correct modifier key
- [ ] Prevents default browser behavior
- [ ] Only triggers when not in input/textarea
- [ ] Returns `{ isOpen, open, close, toggle }`
- [ ] Typecheck passes

---

### US-029: Integrate GlobalSearchModal into app layout
**Description:** As a user, I want the search modal accessible from anywhere in the app.

**Acceptance Criteria:**
- [ ] Add GlobalSearchModal to root layout or providers
- [ ] Search state managed via Zustand store or context
- [ ] Modal renders above all other content (z-50)
- [ ] Cmd+K works on all pages
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-030: Create full search page route
**Description:** As a user, I want a dedicated search page for advanced filtering and browsing all results.

**Acceptance Criteria:**
- [ ] Create `frontend/src/app/search/page.tsx`
- [ ] Reads initial query from URL: `/search?q=query`
- [ ] Full-width search input at top
- [ ] Type filter tabs below input
- [ ] Paginated results list
- [ ] URL updates as filters change
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-031: Create SearchFiltersPanel component
**Description:** As a user, I want advanced filters on the search page so I can narrow down results precisely.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/search/SearchFiltersPanel.tsx`
- [ ] Filter by vault (dropdown of user's vaults)
- [ ] Filter by date range (created within)
- [ ] Filter by contributor (for sources/annotations)
- [ ] "Clear filters" button
- [ ] Filters persist in URL params
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-032: Create SearchPagination component
**Description:** As a user, I want pagination on the search page so I can browse through many results.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/search/SearchPagination.tsx`
- [ ] Shows current page / total pages
- [ ] Previous/Next buttons
- [ ] Page number buttons for nearby pages
- [ ] Updates URL with page param
- [ ] Scrolls to top on page change
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-033: Add search button to navigation header
**Description:** As a user, I want a visible search button in the header as an alternative to keyboard shortcut.

**Acceptance Criteria:**
- [ ] Add search icon button to main navigation header
- [ ] Shows "Cmd+K" or "Ctrl+K" hint tooltip
- [ ] Click opens GlobalSearchModal
- [ ] Button uses glass morphism style
- [ ] Typecheck passes
- [ ] Verify changes work in browser

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
