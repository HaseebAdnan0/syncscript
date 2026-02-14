# PRD: Sources & Annotations System

## Introduction

Build a robust source and annotation management system for SyncScript that enables researchers to collaboratively collect, organize, and annotate research materials within Knowledge Vaults. The system supports various source types (URLs, PDFs, books, journals, datasets) with rich metadata, threaded annotations (2-level max), and comprehensive audit logging for research integrity.

## Goals

- Researchers can add sources to vaults with auto-extracted metadata via `newspaper3k`
- Bulk import of multiple sources (up to 50 URLs) with validation
- Annotations support flexible positioning (PDF highlights, web text selections)
- Two-level annotation threading (top-level + replies only)
- All vault members can view annotations; only authors can edit their own
- Comprehensive filtering by vault, type, date, user, tags, and search
- Soft delete for sources with restoration capability
- Detailed audit logs capture all changes with JSON diffs

## User Stories

---

### US-001: Create sources Django app structure
**Description:** As a developer, I need the sources app scaffolding so I can build source management features.

**Acceptance Criteria:**
- [x] Create `backend/apps/sources/` directory with `__init__.py`
- [x] Create `models.py`, `views.py`, `serializers.py`, `filters.py`, `permissions.py`, `services.py`
- [x] Create `tests/` directory with `__init__.py`, `test_models.py`, `test_views.py`, `test_services.py`
- [x] Add `'apps.sources'` to `INSTALLED_APPS` in settings
- [x] Typecheck passes

---

### US-002: Create Source model with SourceType enum
**Description:** As a developer, I need the Source model to store research sources linked to vaults.

**Acceptance Criteria:**
- [x] Create `SourceType` TextChoices enum: URL, PDF, BOOK, JOURNAL, DATASET
- [x] Create `Source` model with fields: `vault` (FK to vaults.Vault), `url` (URLField max 2048), `title` (CharField max 512), `description` (TextField blank), `source_type` (default URL), `metadata` (JSONField default dict), `created_by` (FK to users.User, SET_NULL), `is_deleted` (BooleanField default False), `created_at`, `updated_at`
- [x] Add `ordering = ['-created_at']` to Meta
- [x] Add indexes on `['vault', 'is_deleted']`, `['source_type']`, `['created_at']`
- [x] Add UniqueConstraint for `['vault', 'url']` where `is_deleted=False` named `unique_active_source_per_vault`
- [x] Typecheck passes

---

### US-003: Create Source migration and register admin
**Description:** As a developer, I need the database migration and admin access for Source model.

**Acceptance Criteria:**
- [x] Run `python manage.py makemigrations sources`
- [x] Run `python manage.py migrate`
- [x] Register `Source` model in `admin.py` with list_display showing id, title, vault, source_type, is_deleted, created_at
- [x] Add list_filter for source_type, is_deleted
- [x] Add search_fields for title, url
- [x] Typecheck passes

---

### US-004: Write Source model tests
**Description:** As a developer, I need tests to verify Source model constraints work correctly.

**Acceptance Criteria:**
- [x] Test creating a valid Source with all fields
- [x] Test unique constraint prevents duplicate vault+url for active sources
- [x] Test unique constraint allows same url if one is soft-deleted
- [x] Test SourceType enum values are correct
- [x] Test default values (is_deleted=False, source_type=URL, metadata={})
- [x] All tests pass with `python manage.py test apps.sources.tests.test_models`
- [x] Typecheck passes

---

### US-005: Create metadata extraction service
**Description:** As a developer, I need a service to auto-extract metadata from URLs using newspaper3k.

**Acceptance Criteria:**
- [ ] Add `newspaper3k>=0.2.8` and `lxml>=5.0` to requirements.txt
- [ ] Create `extract_metadata(url: str) -> dict` function in `services.py`
- [ ] Extract title, authors (list), publication_date (string or None), abstract (first 500 chars of text)
- [ ] Set timeout of 10 seconds for download
- [ ] On any exception, return `{'title': url, 'error': str(e)}`
- [ ] Typecheck passes

---

### US-006: Write metadata extraction service tests
**Description:** As a developer, I need tests to verify metadata extraction handles success and failure cases.

**Acceptance Criteria:**
- [ ] Test successful extraction returns dict with title, authors, publication_date, abstract
- [ ] Test timeout handling returns fallback with url as title
- [ ] Test invalid URL returns fallback with error message
- [ ] Test HTTP error (404, 500) returns fallback
- [ ] Use `unittest.mock.patch` to mock newspaper3k Article class
- [ ] All tests pass with `python manage.py test apps.sources.tests.test_services`
- [ ] Typecheck passes

---

### US-007: Create SourceSerializer
**Description:** As a developer, I need a serializer for Source CRUD operations with auto metadata extraction.

**Acceptance Criteria:**
- [ ] Create `SourceSerializer` in `serializers.py` extending `ModelSerializer`
- [ ] Fields: id, vault, url, title, description, source_type, metadata, created_by, created_at, updated_at
- [ ] Read-only fields: created_by, created_at, updated_at
- [ ] `created_by` uses `StringRelatedField`
- [ ] Override `create()` to call `extract_metadata(url)` if title not provided
- [ ] Merge extracted metadata into `validated_data['metadata']`
- [ ] Typecheck passes

---

### US-008: Create SourceViewSet with basic CRUD
**Description:** As a developer, I need a ViewSet for Source list, retrieve, create, update operations.

**Acceptance Criteria:**
- [ ] Create `SourceViewSet` extending `ModelViewSet` in `views.py`
- [ ] Set `queryset = Source.objects.filter(is_deleted=False)`
- [ ] Set `serializer_class = SourceSerializer`
- [ ] Override `perform_create()` to set `created_by` from request.user
- [ ] Override `get_queryset()` to filter by vaults user has access to
- [ ] Add URL route in `urls.py`: `router.register(r'sources', SourceViewSet)`
- [ ] Typecheck passes

---

### US-009: Add VaultPermission to SourceViewSet
**Description:** As a developer, I need permission checks ensuring only vault members can access sources.

**Acceptance Criteria:**
- [ ] Import or create `VaultSourcePermission` class in `permissions.py`
- [ ] Check: list/retrieve requires vault membership (any role)
- [ ] Check: create/update requires Owner or Contributor role
- [ ] Check: delete requires Owner role only
- [ ] Add `permission_classes = [IsAuthenticated, VaultSourcePermission]` to ViewSet
- [ ] Typecheck passes

---

### US-010: Add soft delete to SourceViewSet
**Description:** As a developer, I need DELETE to soft-delete sources instead of hard delete.

**Acceptance Criteria:**
- [ ] Override `destroy()` method in `SourceViewSet`
- [ ] Set `instance.is_deleted = True` and save
- [ ] Return `Response(status=204)`
- [ ] Verify soft-deleted sources excluded from default queryset
- [ ] Typecheck passes

---

### US-011: Add restore action to SourceViewSet
**Description:** As a developer, I need an endpoint to restore soft-deleted sources.

**Acceptance Criteria:**
- [ ] Add `@action(detail=True, methods=['post'])` named `restore`
- [ ] Override `get_queryset()` in restore action to include `is_deleted=True`
- [ ] Set `instance.is_deleted = False` and save
- [ ] Return serialized source with status 200
- [ ] Only Owner role can restore (check permission)
- [ ] Typecheck passes

---

### US-012: Create SourceFilter with django-filter
**Description:** As a developer, I need filtering on sources by vault, type, creator, and dates.

**Acceptance Criteria:**
- [ ] Create `SourceFilter` class in `filters.py` extending `FilterSet`
- [ ] Add filters: `vault`, `source_type`, `created_by` (standard lookups)
- [ ] Add `date_from` as DateFilter on `created_at` with `lookup_expr='gte'`
- [ ] Add `date_to` as DateFilter on `created_at` with `lookup_expr='lte'`
- [ ] Set `filterset_class = SourceFilter` in SourceViewSet
- [ ] Typecheck passes

---

### US-013: Add tags filter to SourceFilter
**Description:** As a developer, I need to filter sources by tags stored in metadata JSON.

**Acceptance Criteria:**
- [ ] Add `tags` CharFilter with `method='filter_tags'`
- [ ] Implement `filter_tags()` to split comma-separated tags
- [ ] Use PostgreSQL `metadata__tags__overlap` lookup for array overlap
- [ ] Test: `?tags=ml,nlp` returns sources with either tag
- [ ] Typecheck passes

---

### US-014: Add search filter to SourceFilter
**Description:** As a developer, I need text search across title and description fields.

**Acceptance Criteria:**
- [ ] Add `search` CharFilter with `method='filter_search'`
- [ ] Implement `filter_search()` using Q objects with `icontains`
- [ ] Search both `title` and `description` fields (OR)
- [ ] Test: `?search=neural` returns matching sources
- [ ] Typecheck passes

---

### US-015: Create nested source creation endpoint
**Description:** As a developer, I need POST `/api/v1/vaults/{vault_id}/sources/` to create sources within a vault.

**Acceptance Criteria:**
- [ ] Add nested route: `vaults/{vault_id}/sources/` using DRF nested routers or custom URL
- [ ] Override `perform_create()` to set vault from URL `vault_id`
- [ ] Validate user has Owner/Contributor role on vault
- [ ] Return 201 with created source
- [ ] Typecheck passes

---

### US-016: Create BulkSourceSerializer
**Description:** As a developer, I need a serializer for bulk importing multiple URLs.

**Acceptance Criteria:**
- [ ] Create `BulkSourceSerializer` with field `urls` as ListField of URLFields
- [ ] Add validation: max 50 URLs
- [ ] Add validation: all URLs must be unique within the request
- [ ] Return validation errors for invalid URLs
- [ ] Typecheck passes

---

### US-017: Add bulk_import action to SourceViewSet
**Description:** As a developer, I need an endpoint to bulk import sources with duplicate detection.

**Acceptance Criteria:**
- [ ] Add `@action(detail=False, methods=['post'])` named `bulk_import`
- [ ] Accept `{"urls": [...]}` in request body
- [ ] Check existing sources in vault to detect duplicates
- [ ] For each new URL: create Source with auto metadata extraction
- [ ] Return `{"created": [...], "skipped": [...], "errors": [...]}`
- [ ] Wrap in database transaction for atomicity
- [ ] Typecheck passes

---

### US-018: Write Source view tests for CRUD
**Description:** As a developer, I need tests verifying Source API endpoints work correctly.

**Acceptance Criteria:**
- [ ] Test POST creates source with auto-extracted metadata
- [ ] Test GET list returns only non-deleted sources in user's vaults
- [ ] Test GET detail returns source if user has vault access
- [ ] Test PATCH updates title, description, metadata, source_type
- [ ] Test PATCH cannot change url, vault, created_by
- [ ] Test DELETE soft-deletes (sets is_deleted=True)
- [ ] Test restore action sets is_deleted=False
- [ ] All tests pass
- [ ] Typecheck passes

---

### US-019: Write Source view tests for permissions
**Description:** As a developer, I need tests verifying vault permission checks on sources.

**Acceptance Criteria:**
- [ ] Test non-member cannot list vault sources (403)
- [ ] Test Viewer can list and retrieve but not create (403)
- [ ] Test Contributor can create and update
- [ ] Test Contributor cannot delete (403)
- [ ] Test Owner can delete and restore
- [ ] All tests pass
- [ ] Typecheck passes

---

### US-020: Write Source filter tests
**Description:** As a developer, I need tests verifying source filtering works correctly.

**Acceptance Criteria:**
- [ ] Test filter by vault returns only that vault's sources
- [ ] Test filter by source_type returns matching types
- [ ] Test filter by date_from/date_to returns date range
- [ ] Test filter by tags with comma-separated values
- [ ] Test search filter searches title and description
- [ ] Test combined filters work together
- [ ] All tests pass
- [ ] Typecheck passes

---

### US-021: Create annotations Django app structure
**Description:** As a developer, I need the annotations app scaffolding so I can build annotation features.

**Acceptance Criteria:**
- [ ] Create `backend/apps/annotations/` directory with `__init__.py`
- [ ] Create `models.py`, `views.py`, `serializers.py`, `filters.py`, `permissions.py`
- [ ] Create `tests/` directory with `__init__.py`, `test_models.py`, `test_views.py`
- [ ] Add `'apps.annotations'` to `INSTALLED_APPS` in settings
- [ ] Typecheck passes

---

### US-022: Create Annotation model
**Description:** As a developer, I need the Annotation model to store user annotations on sources.

**Acceptance Criteria:**
- [ ] Create `Annotation` model with fields: `source` (FK to sources.Source, CASCADE), `user` (FK to users.User, CASCADE), `content` (TextField), `page_number` (IntegerField null/blank), `position` (JSONField default dict), `parent` (self-FK, CASCADE, null/blank, related_name='replies'), `created_at`, `updated_at`
- [ ] Add `ordering = ['created_at']` to Meta
- [ ] Add indexes on `['source', 'parent']` and `['user']`
- [ ] Typecheck passes

---

### US-023: Add threading validation to Annotation model
**Description:** As a developer, I need to enforce maximum 2-level threading on annotations.

**Acceptance Criteria:**
- [ ] Override `clean()` method on Annotation model
- [ ] If `self.parent` exists and `self.parent.parent` exists, raise `ValidationError`
- [ ] Error message: "Maximum nesting level (2) exceeded. Cannot reply to a reply."
- [ ] Override `save()` to call `full_clean()` before saving
- [ ] Typecheck passes

---

### US-024: Create Annotation migration and register admin
**Description:** As a developer, I need the database migration and admin access for Annotation model.

**Acceptance Criteria:**
- [ ] Run `python manage.py makemigrations annotations`
- [ ] Run `python manage.py migrate`
- [ ] Register `Annotation` model in `admin.py`
- [ ] list_display: id, source, user, content (truncated), parent, created_at
- [ ] list_filter: source, user
- [ ] Typecheck passes

---

### US-025: Write Annotation model tests
**Description:** As a developer, I need tests to verify Annotation threading constraints.

**Acceptance Criteria:**
- [ ] Test creating top-level annotation (parent=None) succeeds
- [ ] Test creating reply to top-level (parent=top_level) succeeds
- [ ] Test creating reply to reply raises ValidationError
- [ ] Test position JSON field stores complex objects
- [ ] Test cascade delete removes annotations when source deleted
- [ ] All tests pass with `python manage.py test apps.annotations.tests.test_models`
- [ ] Typecheck passes

---

### US-026: Create AnnotationSerializer with nested replies
**Description:** As a developer, I need a serializer for Annotation CRUD with threaded replies.

**Acceptance Criteria:**
- [ ] Create `AnnotationSerializer` in `serializers.py` extending `ModelSerializer`
- [ ] Fields: id, source, user, content, page_number, position, parent, replies, created_at, updated_at
- [ ] Read-only: user, created_at, updated_at, replies
- [ ] `user` uses `StringRelatedField`
- [ ] `replies` uses `SerializerMethodField`
- [ ] `get_replies()` returns nested `AnnotationSerializer` for top-level only (parent=None)
- [ ] Typecheck passes

---

### US-027: Add threading validation to AnnotationSerializer
**Description:** As a developer, I need serializer validation to prevent replying to replies.

**Acceptance Criteria:**
- [ ] Override `validate()` method
- [ ] If `data.get('parent')` exists and `data['parent'].parent` exists, raise `ValidationError`
- [ ] Error message: "Cannot reply to a reply (max 2 levels)."
- [ ] Typecheck passes

---

### US-028: Create IsAuthorOrReadOnly permission
**Description:** As a developer, I need a permission class allowing only authors to edit their annotations.

**Acceptance Criteria:**
- [ ] Create `IsAuthorOrReadOnly` class in `permissions.py` extending `BasePermission`
- [ ] `has_object_permission()` returns True for safe methods (GET, HEAD, OPTIONS)
- [ ] For unsafe methods, return `obj.user == request.user`
- [ ] Typecheck passes

---

### US-029: Create AnnotationViewSet
**Description:** As a developer, I need a ViewSet for Annotation CRUD operations.

**Acceptance Criteria:**
- [ ] Create `AnnotationViewSet` extending `ModelViewSet` in `views.py`
- [ ] Set `queryset = Annotation.objects.all()`
- [ ] Set `serializer_class = AnnotationSerializer`
- [ ] Set `permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]`
- [ ] Override `perform_create()` to set `user` from request.user
- [ ] Override `get_queryset()` to filter by sources in user's vaults
- [ ] Add URL route: `router.register(r'annotations', AnnotationViewSet)`
- [ ] Typecheck passes

---

### US-030: Create nested annotation list endpoint
**Description:** As a developer, I need GET `/api/v1/sources/{source_id}/annotations/` with threaded structure.

**Acceptance Criteria:**
- [ ] Add nested route: `sources/{source_id}/annotations/`
- [ ] Override `get_queryset()` to filter by source_id and parent=None (top-level only)
- [ ] Use `prefetch_related('replies')` for performance
- [ ] Return nested structure with replies included
- [ ] Pagination: 50 top-level annotations per page
- [ ] Typecheck passes

---

### US-031: Create nested annotation create endpoint
**Description:** As a developer, I need POST `/api/v1/sources/{source_id}/annotations/` to create annotations.

**Acceptance Criteria:**
- [ ] POST to nested route creates annotation on that source
- [ ] Override `perform_create()` to set source from URL `source_id`
- [ ] Validate user has membership in source's vault
- [ ] Return 201 with created annotation
- [ ] Typecheck passes

---

### US-032: Add AnnotationFilter
**Description:** As a developer, I need filtering on annotations by user and page_number.

**Acceptance Criteria:**
- [ ] Create `AnnotationFilter` class in `filters.py` extending `FilterSet`
- [ ] Add filters: `user`, `page_number`
- [ ] Set `filterset_class = AnnotationFilter` in AnnotationViewSet
- [ ] Typecheck passes

---

### US-033: Write Annotation view tests for CRUD
**Description:** As a developer, I need tests verifying Annotation API endpoints work correctly.

**Acceptance Criteria:**
- [ ] Test POST creates top-level annotation
- [ ] Test POST with parent creates reply
- [ ] Test POST with parent of reply fails (400)
- [ ] Test GET list returns nested structure with replies
- [ ] Test PATCH updates content only
- [ ] Test PATCH cannot change position, parent, source
- [ ] Test DELETE removes annotation and cascades to replies
- [ ] All tests pass
- [ ] Typecheck passes

---

### US-034: Write Annotation view tests for permissions
**Description:** As a developer, I need tests verifying annotation permission checks.

**Acceptance Criteria:**
- [ ] Test non-vault-member cannot list annotations (403)
- [ ] Test any vault member can create annotation
- [ ] Test author can update own annotation
- [ ] Test non-author cannot update annotation (403)
- [ ] Test author can delete own annotation
- [ ] Test non-author cannot delete annotation (403)
- [ ] All tests pass
- [ ] Typecheck passes

---

### US-035: Extend AuditLog model for change tracking
**Description:** As a developer, I need the AuditLog model to support JSON diff tracking.

**Acceptance Criteria:**
- [ ] In `core/models.py`, ensure `AuditLog` model exists with: `action` (CharField), `user` (FK to users.User, SET_NULL), `timestamp` (DateTimeField auto_now_add), `object_type` (CharField), `object_id` (PositiveIntegerField), `changes` (JSONField default dict)
- [ ] If model doesn't exist, create it
- [ ] Add index on `['object_type', 'object_id']`
- [ ] Run migrations
- [ ] Typecheck passes

---

### US-036: Add django-dirtyfields for change tracking
**Description:** As a developer, I need dirty field tracking to capture before/after diffs.

**Acceptance Criteria:**
- [ ] Add `django-dirtyfields>=1.9` to requirements.txt
- [ ] Add `DirtyFieldsMixin` to Source model (before models.Model)
- [ ] Add `DirtyFieldsMixin` to Annotation model
- [ ] Verify `get_dirty_fields()` returns changed fields
- [ ] Typecheck passes

---

### US-037: Create Source audit log signals
**Description:** As a developer, I need signals to auto-create audit logs for Source changes.

**Acceptance Criteria:**
- [ ] Create `signals.py` in `apps/sources/`
- [ ] Create `log_source_change` receiver for `post_save` signal
- [ ] On create: log action `source.created` with empty changes
- [ ] On update: log action `source.updated` with before/after from dirty fields
- [ ] Create `log_source_delete` receiver for `pre_delete` signal (for hard delete)
- [ ] Log action `source.deleted` with full object snapshot
- [ ] Import signals in `apps.py` `ready()` method
- [ ] Typecheck passes

---

### US-038: Add soft delete audit logging for Source
**Description:** As a developer, I need audit logging when sources are soft-deleted or restored.

**Acceptance Criteria:**
- [ ] In SourceViewSet `destroy()`, create audit log with action `source.soft_deleted`
- [ ] In SourceViewSet `restore()`, create audit log with action `source.restored`
- [ ] Include source id and vault id in changes JSON
- [ ] Typecheck passes

---

### US-039: Create Annotation audit log signals
**Description:** As a developer, I need signals to auto-create audit logs for Annotation changes.

**Acceptance Criteria:**
- [ ] Create `signals.py` in `apps/annotations/`
- [ ] Create `log_annotation_change` receiver for `post_save` signal
- [ ] On create: log action `annotation.created`
- [ ] On create with parent: log action `annotation.replied`
- [ ] On update: log action `annotation.updated` with content diff
- [ ] Create `log_annotation_delete` receiver for `pre_delete` signal
- [ ] Log action `annotation.deleted`
- [ ] Import signals in `apps.py` `ready()` method
- [ ] Typecheck passes

---

### US-040: Write audit log signal tests
**Description:** As a developer, I need tests verifying audit logs are created correctly.

**Acceptance Criteria:**
- [ ] Test Source create generates `source.created` log
- [ ] Test Source update generates `source.updated` log with changes
- [ ] Test Source soft delete generates `source.soft_deleted` log
- [ ] Test Source restore generates `source.restored` log
- [ ] Test Annotation create generates `annotation.created` log
- [ ] Test Annotation reply generates `annotation.replied` log
- [ ] Test Annotation update generates `annotation.updated` log
- [ ] Test Annotation delete generates `annotation.deleted` log
- [ ] All tests pass
- [ ] Typecheck passes

---

### US-041: Add bulk import audit logging
**Description:** As a developer, I need a single audit log entry for bulk imports.

**Acceptance Criteria:**
- [ ] In `bulk_import` action, create single audit log after all sources created
- [ ] Action: `source.bulk_imported`
- [ ] Changes JSON: `{"count": N, "urls": [...]}`
- [ ] Include vault_id in changes
- [ ] Typecheck passes

---

### US-042: Register URL routes in project urls.py
**Description:** As a developer, I need all new endpoints registered in the main URL configuration.

**Acceptance Criteria:**
- [ ] Include `apps.sources.urls` at `/api/v1/` prefix
- [ ] Include `apps.annotations.urls` at `/api/v1/` prefix
- [ ] Verify `/api/v1/sources/` endpoint accessible
- [ ] Verify `/api/v1/annotations/` endpoint accessible
- [ ] Verify nested routes work: `/api/v1/vaults/{id}/sources/`
- [ ] Verify nested routes work: `/api/v1/sources/{id}/annotations/`
- [ ] Typecheck passes

---

### US-043: Run full integration test suite
**Description:** As a developer, I need to verify all tests pass together.

**Acceptance Criteria:**
- [ ] Run `python manage.py test apps.sources apps.annotations`
- [ ] All tests pass (0 failures)
- [ ] No warnings about missing migrations
- [ ] Typecheck passes

---

## Non-Goals

- File attachments for annotations (text-only MVP)
- AI-powered citation generation (BibTeX/APA from metadata)
- Full-text search with Elasticsearch
- Annotation conflict resolution (CRDT/OT)
- Export annotations to CSV/JSON
- Async bulk import via Celery (synchronous MVP)
- Shared annotation highlights / collaborative mode

## Technical Considerations

- **Existing Dependencies:** `apps.vaults` (Vault model, VaultPermission), `apps.users` (User model), `core` (AuditLog model)
- **New Packages:** `newspaper3k>=0.2.8`, `lxml>=5.0`, `django-dirtyfields>=1.9`
- **Database:** PostgreSQL 15+ required for JSON field overlap queries
- **Metadata Extraction:** 10s timeout per URL, fallback to URL as title on failure
- **Bulk Import:** Max 50 URLs, synchronous processing, atomic transaction
- **Threading:** 2-level max (top-level + replies), enforced in model.clean() and serializer.validate()
- **Soft Delete:** Sources only, annotations use hard delete with cascade
- **Audit Logs:** Immutable records, dirty field tracking for diffs
