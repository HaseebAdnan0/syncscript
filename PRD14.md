# PRD 14: AI Citation Generator

## Introduction

SyncScript's AI-powered citation generation system enables researchers to generate properly formatted citations for any source in their Knowledge Vaults. The system uses a two-tier approach: structured generation via citeproc-py for sources with complete metadata, and Claude AI generation for sources with incomplete or missing metadata. This differentiator feature supports multiple citation formats (APA7, MLA9, Chicago17, BibTeX, IEEE, Harvard) and includes DOI/ISBN lookup for automatic metadata enrichment.

## Goals

- Generate accurate, properly formatted citations in 6 major academic formats
- Automatically enrich source metadata via DOI (CrossRef) and ISBN (OpenLibrary) lookups
- Use AI to intelligently handle sources with incomplete metadata
- Cache generated citations to avoid redundant API calls
- Provide batch export for entire vaults (progressive approach based on vault size)
- Track AI usage for billing/analytics and rate limit to control costs
- Allow users to set default citation format (global + per-vault override)

## User Stories

### US-001: Create citations app structure
**Description:** As a developer, I need the Django app scaffolding for citations so I can build the citation system in a clean, isolated module.

**Acceptance Criteria:**
- [x] Create `apps/citations/` with `__init__.py`, `apps.py`, `admin.py`, `urls.py`
- [x] Create `models.py` with `CitationFormat` TextChoices enum (APA7, MLA9, CHICAGO17, BIBTEX, IEEE, HARVARD)
- [x] Create empty `services.py`, `views.py`, `serializers.py`, `tasks.py`
- [x] Register app in `config/settings.py` INSTALLED_APPS
- [x] Add `path('citations/', include('apps.citations.urls'))` to main urlconf
- [x] Typecheck passes

### US-002: Implement DOI metadata lookup service
**Description:** As a researcher, I want DOI URLs to automatically fetch metadata from CrossRef so citations are accurate without manual entry.

**Acceptance Criteria:**
- [x] Create `apps/citations/services/doi_lookup.py`
- [x] Function `fetch_doi_metadata(doi: str) -> dict` calls CrossRef API
- [x] Extract: title, authors (list), publication_date, journal, volume, issue, pages, publisher, DOI
- [x] Handle DOI formats: `10.xxxx/yyyy`, `doi.org/10.xxxx/yyyy`, `https://doi.org/10.xxxx/yyyy`
- [x] Return `None` on API failure or invalid DOI (don't raise)
- [x] Add `crossref-commons` to requirements.txt
- [x] Unit tests for DOI parsing and metadata extraction
- [x] Typecheck passes

### US-003: Implement ISBN metadata lookup service
**Description:** As a researcher, I want book sources with ISBNs to automatically fetch metadata from OpenLibrary so I don't need to manually enter book details.

**Acceptance Criteria:**
- [x] Create `apps/citations/services/isbn_lookup.py`
- [x] Function `fetch_isbn_metadata(isbn: str) -> dict` calls OpenLibrary API
- [x] Extract: title, authors (list), publication_date, publisher, edition, pages, ISBN-10, ISBN-13
- [x] Handle ISBN formats: ISBN-10, ISBN-13, with/without hyphens
- [x] Return `None` on API failure or invalid ISBN
- [x] Unit tests for ISBN parsing and metadata extraction
- [x] Typecheck passes

### US-004: Implement citeproc-py structured citation service
**Description:** As a developer, I need a service that generates citations using citeproc-py for sources with complete metadata.

**Acceptance Criteria:**
- [x] Create `apps/citations/services/structured_citation.py`
- [x] Add `citeproc-py` to requirements.txt
- [x] Function `generate_structured_citation(metadata: dict, format: CitationFormat) -> str`
- [x] Support all 6 formats: APA7, MLA9, Chicago17, BibTeX, IEEE, Harvard
- [x] Load appropriate CSL style files for each format
- [x] Function `has_complete_metadata(metadata: dict) -> bool` checks required fields
- [x] Required fields: title, author(s), date (at minimum)
- [x] Unit tests for each citation format with sample metadata
- [x] Typecheck passes

### US-005: Implement Claude AI citation service
**Description:** As a developer, I need a service that uses Claude to generate citations when metadata is incomplete, ensuring academic accuracy.

**Acceptance Criteria:**
- [x] Create `apps/citations/services/ai_citation.py`
- [x] Add `anthropic` SDK to requirements.txt (if not present)
- [x] Function `generate_ai_citation(source_data: dict, format: CitationFormat) -> str`
- [x] Prompt engineering for academic citation accuracy (include format rules in system prompt)
- [x] Handle missing fields gracefully: author="Unknown", date="n.d."
- [x] Include access date for web sources
- [x] Return both plain text and HTML versions (for italicization)
- [x] Unit tests with mocked Claude responses
- [x] Typecheck passes

### US-006: Create citation generation endpoint
**Description:** As a frontend developer, I need an API endpoint to generate citations for a single source so users can cite sources in their preferred format.

**Acceptance Criteria:**
- [x] Create `POST /api/v1/sources/{id}/citation/` endpoint
- [x] Request body: `{"format": "apa7"}` (one of 6 formats)
- [x] Response: `{"citation": "...", "citation_html": "...", "format": "apa7", "source": "structured|ai", "cached": bool}`
- [x] Structured citations return synchronously
- [x] AI citations: if source has incomplete metadata, return sync if fast, else return 202 with task_id
- [x] Permission: user must have vault access (viewer+)
- [x] Serializer validates format enum
- [x] Typecheck passes

### US-007: Implement citation caching
**Description:** As a system, I need to cache generated citations in source metadata to avoid redundant API calls and reduce latency.

**Acceptance Criteria:**
- [x] Store citations in `source.metadata['citations'][format]` JSON structure
- [x] Cache structure: `{"text": "...", "html": "...", "generated_at": "ISO8601", "source": "structured|ai"}`
- [x] Check cache before generating new citation
- [x] Invalidate cache when source metadata is updated (via signal)
- [x] Add `invalidate_citation_cache(source)` utility function
- [x] Endpoint returns `cached: true` when serving from cache
- [x] Typecheck passes

### US-008: Implement async task for AI citations
**Description:** As a developer, I need AI citation generation to run asynchronously via Celery so users aren't blocked waiting for Claude API responses.

**Acceptance Criteria:**
- [x] Create `apps/citations/tasks.py` with `generate_ai_citation_task`
- [x] Task accepts source_id and format, generates citation, updates cache
- [x] Endpoint returns 202 with `{"task_id": "...", "status_url": "/api/v1/tasks/{id}/"}` for AI citations
- [x] Create `GET /api/v1/citations/tasks/{task_id}/` to poll status
- [x] Status response: `{"status": "pending|completed|failed", "result": {...}}`
- [x] Task timeout: 30 seconds
- [x] Typecheck passes

### US-009: Add rate limiting for AI citations
**Description:** As a platform operator, I need to rate limit AI citation generation to control costs and prevent abuse.

**Acceptance Criteria:**
- [x] Rate limit: 50 AI citations per user per day
- [x] Rate limit: 200 AI citations per vault per day
- [x] Store counters in Redis with daily expiry
- [x] Return 429 Too Many Requests when limit exceeded
- [x] Response includes `Retry-After` header and remaining quota
- [x] Add `get_ai_citation_quota(user, vault) -> dict` utility
- [x] Typecheck passes

### US-010: Track AI citation usage in AuditLog
**Description:** As a platform operator, I need AI citation usage tracked in the audit log for billing and analytics.

**Acceptance Criteria:**
- [x] Log each AI citation generation with: user_id, vault_id, source_id, format, token_count, model_used
- [x] Use existing AuditLog model with action type `AI_CITATION_GENERATED`
- [x] Include input/output token counts from Claude response
- [x] Add helper `log_ai_citation_usage(user, vault, source, format, usage_data)`
- [x] Typecheck passes

### US-011: Implement batch citation export endpoint
**Description:** As a researcher, I want to export all citations from a vault so I can import them into reference managers or include in papers.

**Acceptance Criteria:**
- [ ] Create `GET /api/v1/vaults/{id}/citations/export/` endpoint
- [ ] Query param: `format=bibtex|apa7|mla9|chicago17|ieee|harvard`
- [ ] Returns file download with appropriate content-type
- [ ] BibTeX: returns `.bib` file with all sources
- [ ] Other formats: returns `.txt` file with citations separated by blank lines
- [ ] Permission: user must have vault access (viewer+)
- [ ] Typecheck passes

### US-012: Implement progressive batch export strategy
**Description:** As a system, I need batch exports to handle vaults of any size without timing out.

**Acceptance Criteria:**
- [ ] Small vaults (≤50 sources): generate all on-demand, return immediately
- [ ] Medium vaults (51-200 sources): use cached citations, generate missing sync
- [ ] Large vaults (>200 sources): queue background job, return 202 with status URL
- [ ] Background job sends notification when export is ready
- [ ] Export file stored temporarily (24h) for download
- [ ] Status endpoint: `GET /api/v1/vaults/{id}/citations/export/status/`
- [ ] Typecheck passes

### US-013: Add user citation format preference
**Description:** As a user, I want to set my default citation format in my profile so I don't have to select it every time.

**Acceptance Criteria:**
- [x] Add `default_citation_format` field to User profile (nullable, CharField)
- [x] Default: null (no preference, UI shows format selector)
- [x] Create migration for new field
- [x] Update user serializer to include `default_citation_format`
- [x] Add `PATCH /api/v1/users/me/` support for updating preference
- [x] Typecheck passes

### US-014: Add vault citation format override
**Description:** As a vault owner, I want to set a default citation format for my vault so team members use consistent formatting.

**Acceptance Criteria:**
- [x] Add `default_citation_format` field to Vault model (nullable, CharField)
- [x] Create migration for new field
- [x] Update vault serializer to include `default_citation_format`
- [x] Owners/Contributors can update via `PATCH /api/v1/vaults/{id}/`
- [x] API returns effective format: vault override > user preference > none
- [x] Typecheck passes

### US-015: Create CitationButton component
**Description:** As a user, I want a "Cite" button on source cards that opens a citation dropdown so I can quickly generate citations.

**Acceptance Criteria:**
- [x] Create `components/features/sources/CitationButton.tsx`
- [x] Button with citation icon (Quote or similar from Lucide)
- [x] Clicking opens dropdown menu with format options
- [x] Dropdown shows: APA 7th, MLA 9th, Chicago 17th, BibTeX, IEEE, Harvard
- [x] Uses Radix DropdownMenu for accessibility
- [x] Loading state while fetching citation
- [x] Matches Bitcoin DeFi design system (orange accent, dark theme)
- [x] Typecheck passes

### US-016: Implement citation format selector with preview
**Description:** As a user, I want to see a preview of my citation before copying so I can verify it's correct.

**Acceptance Criteria:**
- [x] Clicking format in dropdown triggers API call to generate citation
- [x] Show loading spinner in dropdown while generating
- [x] On success, open CitationPreviewModal with formatted citation
- [x] Modal shows citation with proper formatting (italics rendered in HTML)
- [x] Handle async citations: show "Generating..." with polling
- [x] Handle errors: show toast with error message
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-017: Create CitationPreviewModal component
**Description:** As a user, I want a modal that shows my formatted citation with copy functionality so I can review and copy it.

**Acceptance Criteria:**
- [x] Create `components/features/sources/CitationPreviewModal.tsx`
- [x] Modal header shows format name (e.g., "APA 7th Edition")
- [x] Body shows rendered citation with proper typography
- [x] HTML version for formats with italics (journal names, etc.)
- [x] "Copy Citation" button (primary action)
- [x] "Copy as Plain Text" secondary option (strips HTML)
- [x] Close button and click-outside-to-close
- [x] Matches Bitcoin DeFi design system
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-018: Implement copy to clipboard with toast
**Description:** As a user, I want one-click copy with confirmation so I know the citation was copied successfully.

**Acceptance Criteria:**
- [x] Copy button uses `navigator.clipboard.writeText()`
- [x] Success shows toast: "Copied APA 7th citation to clipboard"
- [x] Toast includes format name and source title (truncated)
- [x] Toast auto-dismisses after 3 seconds
- [x] Toast matches design system (dark with orange accent)
- [x] Fallback for browsers without clipboard API
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-019: Add batch export button to vault page
**Description:** As a user, I want to export all citations from my vault so I can import them into my reference manager.

**Acceptance Criteria:**
- [x] Add "Export All Citations" button to vault page header/toolbar
- [x] Button opens dropdown with format options
- [x] Clicking format triggers export API call
- [x] Small/medium vaults: direct file download
- [x] Large vaults: show toast "Export started, you'll be notified when ready"
- [x] Button disabled with tooltip if vault has no sources
- [x] Download filename: `{vault-name}-citations.{ext}`
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-020: Add citation format settings UI
**Description:** As a user, I want to set my default citation format in settings so my preference is remembered.

**Acceptance Criteria:**
- [x] Add "Citation Preferences" section to user settings page
- [x] Dropdown to select default format (or "Always Ask")
- [x] Save preference via API on change
- [x] Show success toast on save
- [x] For vault settings: add similar dropdown for vault owners
- [x] Vault setting shows "Use User Preference" as default option
- [x] Typecheck passes
- [ ] Verify changes work in browser

### US-021: Handle BibTeX special character escaping
**Description:** As a researcher, I need BibTeX exports to properly escape special characters so they compile correctly in LaTeX.

**Acceptance Criteria:**
- [x] Create `apps/citations/bibtex_utils.py` with escape utilities
- [x] Escape: `&` → `\&`, `%` → `\%`, `$` → `\$`, `#` → `\#`, `_` → `\_`, `{` → `\{`, `}` → `\}`
- [x] Handle Unicode characters (é → `{\'e}`, ü → `{\"u}`, etc.)
- [x] Generate valid BibTeX keys: `AuthorYear` format, handle duplicates with a/b/c suffix
- [x] Unit tests for escaping edge cases (37 tests pass)
- [x] Typecheck passes

### US-022: Add metadata enrichment on source creation
**Description:** As a researcher, I want sources with DOIs or ISBNs to automatically fetch metadata when added so citations are accurate from the start.

**Acceptance Criteria:**
- [x] On source creation, detect DOI pattern in URL
- [x] On source creation, detect ISBN in metadata or for BOOK type
- [x] Trigger async task to fetch metadata from CrossRef/OpenLibrary
- [x] Merge fetched metadata into `source.metadata` (don't overwrite user entries)
- [x] Update source title if fetched title is better (longer, more complete)
- [x] Log enrichment in audit log
- [x] Typecheck passes

## Non-Goals

- **Full reference manager features** - Not building import from Zotero/Mendeley/EndNote
- **Citation network analysis** - Not building citation graphs or impact metrics
- **Inline citation insertion** - Not integrating with Word/Google Docs plugins
- **Citation style customization** - Using standard CSL styles only, no custom modifications
- **PDF citation extraction** - Not parsing citations from within PDF documents
- **Multi-language citations** - English citation formats only for v1

## Technical Considerations

### Dependencies
- `citeproc-py` - CSL citation processor for structured generation
- `anthropic` - Claude SDK for AI citations (already in project)
- `crossref-commons` - CrossRef API client for DOI lookup
- Standard library `urllib` for OpenLibrary API (simple REST)

### Citation Format CSL Files
CSL style files available from: https://github.com/citation-style-language/styles
- `apa-7th-edition.csl`
- `modern-language-association-9th-edition.csl`
- `chicago-author-date-17th-edition.csl`
- `ieee.csl`
- `harvard-cite-them-right.csl`

Store in `apps/citations/styles/` directory.

### Claude Prompt Engineering
For AI citations, use structured prompts that:
1. Specify exact format rules (indentation, punctuation, italics markers)
2. Provide examples of correct citations
3. Instruct on handling missing fields
4. Request both plain text and HTML output

### Caching Strategy
```python
source.metadata = {
    "existing": "metadata",
    "citations": {
        "apa7": {
            "text": "Author, A. (2024). Title...",
            "html": "Author, A. (2024). <i>Title</i>...",
            "generated_at": "2024-01-15T10:30:00Z",
            "source": "structured"
        }
    }
}
```

### Rate Limiting Keys
```
ai_citation:user:{user_id}:daily  # Counter with midnight expiry
ai_citation:vault:{vault_id}:daily  # Counter with midnight expiry
```

### File Locations
- Backend: `apps/citations/*`
- Frontend: `components/features/sources/CitationButton.tsx`
- Frontend: `components/features/sources/CitationPreviewModal.tsx`
- Frontend: `components/features/vaults/ExportCitationsButton.tsx`
- Frontend: `lib/api/citations.ts`
- Frontend: `hooks/useCitation.ts`
