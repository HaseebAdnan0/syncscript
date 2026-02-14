# Product Requirements Document: Sources & Annotations System

**Project:** SyncScript - Collaborative Research & Citation Engine  
**Component:** Backend - Sources & Annotations Management  
**Version:** 1.0  
**Date:** 2026-02-14  
**Author:** Claude Code  

---

## 1. Overview

### 1.1 Purpose
Build a robust source and annotation management system that enables researchers to collaboratively collect, organize, and annotate research materials within Knowledge Vaults. The system supports various source types (URLs, PDFs, books, journals, datasets) with rich metadata, threaded annotations, and comprehensive audit logging for research integrity.

### 1.2 Success Criteria
- [ ] Researchers can add sources to vaults with auto-extracted metadata
- [ ] Bulk import of multiple sources via URL array
- [ ] Annotations support flexible positioning (PDF highlights, web text selections)
- [ ] Two-level annotation threading (top-level + replies)
- [ ] All vault members can view all annotations; only authors can edit their own
- [ ] Comprehensive filtering by vault, type, date, user, tags, and search
- [ ] Soft delete for sources with restoration capability
- [ ] Detailed audit logs capture all changes with JSON diffs

### 1.3 Scope
**In Scope:**
- Source CRUD with vault permission inheritance
- Annotation CRUD with user ownership validation
- Bulk source import endpoint
- Smart metadata extraction using `newspaper3k`/`beautifulsoup`
- Advanced filtering via `django-filter`
- Annotation threading (2-level max)
- Audit logging with change tracking
- Soft delete for sources

**Out of Scope:**
- File attachments for annotations (text-only MVP)
- AI-powered citation generation (future enhancement)
- Full-text search (Elasticsearch - future enhancement)
- Annotation conflict resolution (CRDT/OT - future)

---

## 2. Technical Architecture

### 2.1 Technology Stack
- **Framework:** Django 6+, Django REST Framework 3.16+
- **Database:** PostgreSQL 15+ (JSON fields for metadata/position)
- **Filtering:** `django-filter` 25.1+
- **Metadata Extraction:** `newspaper3k` or `beautifulsoup4` + `requests`
- **Validation:** DRF serializers with custom validators

### 2.2 App Structure
```
backend/apps/
├── sources/
│   ├── migrations/
│   ├── __init__.py
│   ├── models.py           # Source model
│   ├── serializers.py      # SourceSerializer, BulkSourceSerializer
│   ├── views.py            # SourceViewSet
│   ├── filters.py          # SourceFilter
│   ├── permissions.py      # VaultPermission (inherited from vaults app)
│   ├── services.py         # extract_metadata() service
│   └── tests/
│       ├── test_models.py
│       ├── test_views.py
│       └── test_services.py
└── annotations/
    ├── migrations/
    ├── __init__.py
    ├── models.py           # Annotation model
    ├── serializers.py      # AnnotationSerializer
    ├── views.py            # AnnotationViewSet
    ├── filters.py          # AnnotationFilter
    ├── permissions.py      # IsAuthorOrReadOnly
    └── tests/
        ├── test_models.py
        └── test_views.py
```

### 2.3 Database Schema

#### Source Model (`apps/sources/models.py`)
```python
class SourceType(models.TextChoices):
    URL = 'URL', 'URL'
    PDF = 'PDF', 'PDF'
    BOOK = 'BOOK', 'Book'
    JOURNAL = 'JOURNAL', 'Journal Article'
    DATASET = 'DATASET', 'Dataset'

class Source(models.Model):
    vault = models.ForeignKey('vaults.Vault', on_delete=models.CASCADE, related_name='sources')
    url = models.URLField(max_length=2048)
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.URL)
    metadata = models.JSONField(default=dict)  # {authors, publication_date, tags, abstract, doi}
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='created_sources')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vault', 'is_deleted']),
            models.Index(fields=['source_type']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['vault', 'url'], condition=models.Q(is_deleted=False), name='unique_active_source_per_vault')
        ]
```

**Metadata JSON Schema:**
```json
{
  "authors": ["John Doe", "Jane Smith"],
  "publication_date": "2025-01-15",
  "tags": ["machine-learning", "nlp"],
  "abstract": "Summary of the source...",
  "doi": "10.1234/example.doi"
}
```

#### Annotation Model (`apps/annotations/models.py`)
```python
class Annotation(models.Model):
    source = models.ForeignKey('sources.Source', on_delete=models.CASCADE, related_name='annotations')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='annotations')
    content = models.TextField()
    page_number = models.IntegerField(null=True, blank=True)  # For PDF sources
    position = models.JSONField(default=dict)  # {page?, x?, y?, width?, height?, selector?}
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['source', 'parent']),
            models.Index(fields=['user']),
        ]

    def clean(self):
        # Enforce two-level threading max
        if self.parent and self.parent.parent:
            raise ValidationError("Maximum nesting level (2) exceeded. Cannot reply to a reply.")
```

**Position JSON Examples:**
```json
// PDF highlight
{"page": 5, "x": 120, "y": 340, "width": 200, "height": 40, "color": "#F7931A"}

// Web text selection
{"selector": "blockquote:nth-of-type(2)", "text": "Selected quote..."}

// Simple point annotation
{"page": 3, "x": 150, "y": 200}
```

---

## 3. User Stories

### Epic 1: Source Management

#### US-1.1: Create Source with Auto-Metadata Extraction
**As a** researcher  
**I want to** add a source to my vault by providing a URL  
**So that** metadata (title, authors, abstract) is automatically extracted  

**Acceptance Criteria:**
- [ ] POST `/api/v1/vaults/{vault_id}/sources/` creates source
- [ ] Required fields: `url`, `source_type`
- [ ] Optional: `title`, `description`, `metadata`
- [ ] If `title` not provided, auto-extract from URL using `newspaper3k`/`beautifulsoup`
- [ ] Extract metadata: authors, publication_date, abstract (best effort)
- [ ] Vault permission check: user must be Owner or Contributor
- [ ] Audit log created: `source.created`
- [ ] Returns 201 with full source object

**Technical Notes:**
- Service function: `extract_metadata(url) -> dict`
- Fallback: if extraction fails, use URL as title
- Timeout: 10s max for metadata fetch

---

#### US-1.2: Bulk Source Import
**As a** researcher  
**I want to** import multiple sources at once via URL array  
**So that** I can quickly populate my vault from a reference list  

**Acceptance Criteria:**
- [ ] POST `/api/v1/vaults/{vault_id}/sources/bulk_import/` accepts `{"urls": [...]}`
- [ ] Max batch size: 50 URLs
- [ ] Validates all URLs before processing (duplicate check within vault)
- [ ] Checks URL reachability (HTTP HEAD request, 5s timeout)
- [ ] Skips duplicates, returns `{"created": [...], "skipped": [...], "errors": [...]}`
- [ ] Each source gets metadata auto-extracted
- [ ] Vault permission: Owner/Contributor only
- [ ] Single audit log entry: `source.bulk_imported` with count

**Technical Notes:**
- Use Django transactions to ensure atomicity
- Async processing via Celery optional (future enhancement)

---

#### US-1.3: List & Filter Sources
**As a** researcher  
**I want to** filter sources by vault, type, date range, creator, tags, and search text  
**So that** I can quickly find relevant sources  

**Acceptance Criteria:**
- [ ] GET `/api/v1/sources/?vault={id}&source_type=PDF&created_by={user_id}&tags=ml,nlp&search=neural&date_from=2025-01-01&date_to=2025-12-31`
- [ ] Filtering via `django-filter.FilterSet`
- [ ] `search` query searches `title` + `description` (case-insensitive)
- [ ] `tags` filter searches `metadata.tags` array (PostgreSQL JSON query)
- [ ] Only returns non-deleted sources (`is_deleted=False`)
- [ ] Pagination: 20 items per page
- [ ] Vault permission: any vault member can list sources

**Technical Notes:**
- Use `django_filters.CharFilter` with custom method for tags
- Use `SearchFilter` for full-text search

---

#### US-1.4: Update Source
**As a** researcher  
**I want to** edit source title, description, metadata, and type  
**So that** I can correct or enrich source information  

**Acceptance Criteria:**
- [ ] PATCH `/api/v1/sources/{id}/` updates mutable fields
- [ ] Mutable: `title`, `description`, `source_type`, `metadata`
- [ ] Immutable: `url`, `vault`, `created_by`
- [ ] Vault permission: Owner/Contributor only
- [ ] Audit log: `source.updated` with JSON diff of changes
- [ ] Returns 200 with updated source

---

#### US-1.5: Soft Delete Source
**As a** researcher  
**I want to** delete a source without permanently removing it  
**So that** I can restore it later if needed  

**Acceptance Criteria:**
- [ ] DELETE `/api/v1/sources/{id}/` sets `is_deleted=True`
- [ ] Vault permission: Owner only
- [ ] Audit log: `source.deleted` (soft)
- [ ] Deleted sources excluded from list views by default
- [ ] Returns 204 No Content

---

#### US-1.6: Restore Deleted Source
**As a** vault owner  
**I want to** restore a soft-deleted source  
**So that** I can recover accidentally deleted sources  

**Acceptance Criteria:**
- [ ] POST `/api/v1/sources/{id}/restore/` sets `is_deleted=False`
- [ ] Vault permission: Owner only
- [ ] Audit log: `source.restored`
- [ ] Returns 200 with restored source

---

### Epic 2: Annotation Management

#### US-2.1: Create Top-Level Annotation
**As a** researcher  
**I want to** add an annotation to a source with flexible positioning  
**So that** I can highlight and comment on specific parts  

**Acceptance Criteria:**
- [ ] POST `/api/v1/sources/{source_id}/annotations/` creates annotation
- [ ] Required: `content`, `position` JSON
- [ ] Optional: `page_number`, `parent` (must be null for top-level)
- [ ] Vault permission: any vault member can annotate
- [ ] Audit log: `annotation.created`
- [ ] Returns 201 with annotation object

**Technical Notes:**
- `position` schema validation: at least one of `page`, `x`, `y`, `selector` must be present

---

#### US-2.2: Reply to Annotation (One Level Deep)
**As a** researcher  
**I want to** reply to an existing annotation  
**So that** I can engage in threaded discussions  

**Acceptance Criteria:**
- [ ] POST `/api/v1/annotations/` with `parent={annotation_id}` creates reply
- [ ] Validates: parent must not have a parent (2-level max)
- [ ] Required: `content`, `source` (inherited from parent), `parent`
- [ ] `position` optional for replies (defaults to parent's position)
- [ ] Vault permission: any vault member
- [ ] Audit log: `annotation.replied`
- [ ] Returns 201 with reply object

---

#### US-2.3: List Annotations for Source
**As a** researcher  
**I want to** view all annotations for a source grouped by thread  
**So that** I can see discussions in context  

**Acceptance Criteria:**
- [ ] GET `/api/v1/sources/{source_id}/annotations/` returns nested structure
- [ ] Top-level annotations include `replies` array
- [ ] Ordered by `created_at` (oldest first)
- [ ] Vault permission: any vault member
- [ ] Filter by `user`, `page_number`
- [ ] Pagination: 50 top-level annotations per page

**Technical Notes:**
- Use `prefetch_related('replies')` for performance
- Serializer includes nested `AnnotationSerializer(many=True)` for replies

---

#### US-2.4: Update Annotation
**As a** researcher  
**I want to** edit my own annotation content  
**So that** I can correct or clarify my notes  

**Acceptance Criteria:**
- [ ] PATCH `/api/v1/annotations/{id}/` updates `content` only
- [ ] Permission: only annotation author can edit
- [ ] Immutable: `position`, `page_number`, `parent`, `source`
- [ ] Audit log: `annotation.updated` with diff
- [ ] Returns 200 with updated annotation

---

#### US-2.5: Delete Annotation
**As a** researcher  
**I want to** delete my own annotation  
**So that** I can remove outdated or incorrect notes  

**Acceptance Criteria:**
- [ ] DELETE `/api/v1/annotations/{id}/` hard deletes annotation
- [ ] Permission: only annotation author can delete
- [ ] If annotation has replies, cascade delete all replies (warning in response)
- [ ] Audit log: `annotation.deleted`
- [ ] Returns 204 No Content

---

### Epic 3: Audit Logging

#### US-3.1: Log All Source & Annotation Changes
**As a** system administrator  
**I want to** track all changes to sources and annotations  
**So that** research integrity is maintained  

**Acceptance Criteria:**
- [ ] Every create/update/delete action creates an `AuditLog` entry
- [ ] Fields: `action`, `user`, `timestamp`, `object_type`, `object_id`, `changes` (JSON diff)
- [ ] Changes JSON: `{"before": {...}, "after": {...}}`
- [ ] Immutable records (no updates allowed)
- [ ] Queryable via admin interface or API endpoint

**Technical Notes:**
- Use Django signals (`post_save`, `pre_delete`) to auto-create logs
- Store diffs using `django-dirtyfields` or custom snapshot logic

---

## 4. API Endpoints

### Source Endpoints
| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| POST | `/api/v1/vaults/{vault_id}/sources/` | Create source | Owner/Contributor |
| POST | `/api/v1/vaults/{vault_id}/sources/bulk_import/` | Bulk import sources | Owner/Contributor |
| GET | `/api/v1/sources/` | List & filter sources | Vault Member |
| GET | `/api/v1/sources/{id}/` | Retrieve source | Vault Member |
| PATCH | `/api/v1/sources/{id}/` | Update source | Owner/Contributor |
| DELETE | `/api/v1/sources/{id}/` | Soft delete source | Owner |
| POST | `/api/v1/sources/{id}/restore/` | Restore deleted source | Owner |

### Annotation Endpoints
| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| POST | `/api/v1/sources/{source_id}/annotations/` | Create annotation | Vault Member |
| GET | `/api/v1/sources/{source_id}/annotations/` | List annotations (nested) | Vault Member |
| GET | `/api/v1/annotations/{id}/` | Retrieve annotation | Vault Member |
| PATCH | `/api/v1/annotations/{id}/` | Update annotation | Author Only |
| DELETE | `/api/v1/annotations/{id}/` | Delete annotation (cascade) | Author Only |

---

## 5. Implementation Guide

### Phase 1: Core Models & Migrations (Day 1)
**Tasks:**
1. Create `apps/sources/` and `apps/annotations/` apps
2. Define `Source` model with `SourceType` enum
3. Define `Annotation` model with `clean()` validation for threading
4. Create migrations
5. Register models in admin
6. Write model tests (constraints, validation)

**Dependencies:** `apps.vaults`, `apps.users`

---

### Phase 2: Metadata Extraction Service (Day 1-2)
**Tasks:**
1. Install `newspaper3k` or `beautifulsoup4` + `requests`
2. Implement `extract_metadata(url)` in `apps/sources/services.py`
3. Extract: title, authors, publication_date, abstract
4. Handle timeouts, HTTP errors, parse failures
5. Write service tests with mocked HTTP responses

**Technical Notes:**
```python
# apps/sources/services.py
import requests
from newspaper import Article
from bs4 import BeautifulSoup

def extract_metadata(url: str) -> dict:
    try:
        article = Article(url)
        article.download()
        article.parse()
        return {
            'title': article.title or url,
            'authors': article.authors,
            'publication_date': str(article.publish_date) if article.publish_date else None,
            'abstract': article.text[:500],
        }
    except Exception as e:
        return {'title': url, 'error': str(e)}
```

---

### Phase 3: Source Serializers & Views (Day 2-3)
**Tasks:**
1. Create `SourceSerializer` with nested metadata validation
2. Create `BulkSourceSerializer` for bulk import
3. Implement `SourceViewSet` with custom actions: `bulk_import`, `restore`
4. Add `VaultPermission` check (inherit from `apps/vaults/permissions.py`)
5. Integrate metadata extraction in `perform_create()`
6. Write view tests (CRUD, bulk import, permissions)

**Serializer Example:**
```python
# apps/sources/serializers.py
class SourceSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Source
        fields = ['id', 'vault', 'url', 'title', 'description', 'source_type', 'metadata', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        if not validated_data.get('title'):
            metadata = extract_metadata(validated_data['url'])
            validated_data['title'] = metadata.get('title', validated_data['url'])
            validated_data['metadata'].update(metadata)
        return super().create(validated_data)
```

---

### Phase 4: Source Filtering (Day 3)
**Tasks:**
1. Create `SourceFilter` using `django-filter`
2. Add filters: `vault`, `source_type`, `created_by`, `tags`, `date_from`, `date_to`, `search`
3. Implement custom `tags` filter (PostgreSQL JSON query)
4. Add to `SourceViewSet.filterset_class`
5. Write filter tests

**Filter Example:**
```python
# apps/sources/filters.py
import django_filters
from .models import Source

class SourceFilter(django_filters.FilterSet):
    tags = django_filters.CharFilter(method='filter_tags')
    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Source
        fields = ['vault', 'source_type', 'created_by']
    
    def filter_tags(self, queryset, name, value):
        tags = [t.strip() for t in value.split(',')]
        return queryset.filter(metadata__tags__overlap=tags)
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(title__icontains=value) | models.Q(description__icontains=value)
        )
```

---

### Phase 5: Annotation Serializers & Views (Day 4)
**Tasks:**
1. Create `AnnotationSerializer` with nested `replies`
2. Implement `AnnotationViewSet` with custom `list` to group by thread
3. Add `IsAuthorOrReadOnly` permission
4. Validate two-level threading in serializer
5. Write view tests (create, reply, update, delete, threading validation)

**Serializer Example:**
```python
# apps/annotations/serializers.py
class AnnotationSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Annotation
        fields = ['id', 'source', 'user', 'content', 'page_number', 'position', 'parent', 'replies', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_replies(self, obj):
        if obj.parent is None:  # Only include replies for top-level
            return AnnotationSerializer(obj.replies.all(), many=True, context=self.context).data
        return []
    
    def validate(self, data):
        if data.get('parent') and data['parent'].parent:
            raise serializers.ValidationError("Cannot reply to a reply (max 2 levels).")
        return data
```

---

### Phase 6: Audit Logging (Day 5)
**Tasks:**
1. Extend `AuditLog` model (or create in `core/`) to support `changes` JSON field
2. Create Django signals in `apps/sources/signals.py` and `apps/annotations/signals.py`
3. Capture before/after snapshots using `django-dirtyfields` or manual diff
4. Write signal tests (verify log creation on CRUD operations)

**Signal Example:**
```python
# apps/sources/signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from core.models import AuditLog
import json

@receiver(post_save, sender=Source)
def log_source_change(sender, instance, created, **kwargs):
    action = 'source.created' if created else 'source.updated'
    changes = {}
    if not created and hasattr(instance, '_dirty_fields'):
        changes = {'before': instance._dirty_fields, 'after': {...}}
    AuditLog.objects.create(
        action=action,
        user=instance.created_by,
        object_type='source',
        object_id=instance.id,
        changes=changes
    )
```

---

### Phase 7: Integration & Testing (Day 6)
**Tasks:**
1. Run full test suite: `python manage.py test apps.sources apps.annotations`
2. Test bulk import with 50 URLs
3. Test annotation threading edge cases
4. Test soft delete + restore flow
5. Manual API testing with Postman/Thunder Client

---

### Phase 8: Documentation & Manual Verification (Day 6)
**Tasks:**
1. Update `MANUAL_VERIFICATION.md` with test scenarios
2. Update `USER_SETUP.md` if new env vars needed (none expected)
3. Write API documentation (Swagger via `drf-spectacular`)

---

## 6. Non-Functional Requirements

### Performance
- Bulk import: <10s for 50 URLs (network-dependent)
- Metadata extraction: <5s per URL
- List sources: <200ms for 1000 sources with filters
- List annotations: <100ms for 500 annotations (with prefetch)

### Security
- CSRF protection on all POST/PATCH/DELETE
- JWT authentication required
- Vault permission checks on all operations
- SQL injection prevention via ORM (no raw queries)

### Scalability
- Database indexes on `vault`, `source_type`, `created_at`, `is_deleted`
- Pagination on all list endpoints
- Future: Celery for async bulk import

---

## 7. Testing Strategy

### Unit Tests
- Model constraints (unique vault+url, threading validation)
- Serializer validation (position schema, threading)
- Service functions (metadata extraction with mocked responses)

### Integration Tests
- Full CRUD flows with authentication
- Bulk import with duplicate detection
- Annotation threading (create top-level, reply, reject double-reply)
- Soft delete + restore
- Audit log creation

### Manual Testing (see MANUAL_VERIFICATION.md)
- [ ] Create source with auto-metadata extraction
- [ ] Bulk import 20 URLs, verify duplicates skipped
- [ ] Create annotation on PDF with position data
- [ ] Reply to annotation, attempt to reply to reply (should fail)
- [ ] Update annotation as author, attempt as non-author (should fail)
- [ ] Soft delete source, verify hidden in list, restore
- [ ] Check audit logs in admin panel

---

## 8. Dependencies

### New Python Packages
Add to `requirements.txt`:
```
newspaper3k>=0.2.8
beautifulsoup4>=4.12
lxml>=5.0  # For newspaper3k
django-dirtyfields>=1.9  # For audit log diffs
```

### Existing Apps
- `apps.vaults` (Vault model, VaultPermission)
- `apps.users` (User model)
- `core` (AuditLog model - create if not exists)

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Metadata extraction fails for paywalled sites | Medium | Graceful fallback to URL as title; allow manual entry |
| Bulk import times out for 50 URLs | Medium | Add async processing via Celery; reduce batch size to 25 |
| JSON position schema becomes too complex | Low | Document schema clearly; validate in serializer |
| Annotation threading confusion | Medium | Clear UI indicators for thread depth; enforce validation |

---

## 10. Future Enhancements
- AI-powered citation generation (BibTeX/APA from metadata)
- Full-text search with Elasticsearch
- File attachments for annotations (images, PDFs)
- Annotation conflict resolution (CRDT)
- Export annotations to CSV/JSON
- Shared annotation highlights (collaborative mode)

---

## Appendix A: Manual Verification Tasks

**File:** `.planning/MANUAL_VERIFICATION.md`

```markdown
## Sources & Annotations System - 2026-02-14

### Source Creation & Metadata
- [ ] POST /api/v1/vaults/1/sources/ with URL https://arxiv.org/abs/2301.00001
- [ ] Verify title auto-extracted from page
- [ ] Check metadata JSON contains authors, abstract
- [ ] Verify audit log entry created

### Bulk Import
- [ ] POST /api/v1/vaults/1/sources/bulk_import/ with 20 URLs (include 2 duplicates)
- [ ] Verify response shows created count = 18, skipped count = 2
- [ ] Check database for 18 new sources
- [ ] Verify single audit log entry with count

### Source Filtering
- [ ] GET /api/v1/sources/?vault=1&source_type=PDF&tags=ml,nlp&search=neural
- [ ] Verify results match filters
- [ ] Test date_from and date_to parameters
- [ ] Verify pagination works (20 per page)

### Soft Delete & Restore
- [ ] DELETE /api/v1/sources/1/ (soft delete)
- [ ] Verify is_deleted=True in database
- [ ] Verify source not in GET /api/v1/sources/ list
- [ ] POST /api/v1/sources/1/restore/
- [ ] Verify source reappears in list

### Annotation Threading
- [ ] POST /api/v1/sources/1/annotations/ (top-level, page=5, position={x:100, y:200})
- [ ] POST /api/v1/annotations/ with parent={top_level_id} (reply)
- [ ] Attempt POST with parent={reply_id} (should fail: ValidationError)
- [ ] GET /api/v1/sources/1/annotations/ (verify nested structure)

### Annotation Permissions
- [ ] Create annotation as User A
- [ ] Attempt PATCH as User B (should fail: 403)
- [ ] Attempt DELETE as User B (should fail: 403)
- [ ] PATCH as User A (should succeed)

### Audit Logs
- [ ] Perform source update (change title)
- [ ] Check AuditLog table for source.updated entry
- [ ] Verify changes JSON contains before/after diff
```

---

## Appendix B: Implementation Checklist

### Day 1: Models & Services
- [ ] Create `apps/sources/` app
- [ ] Create `apps/annotations/` app
- [ ] Define `Source` model (with indexes, constraints)
- [ ] Define `Annotation` model (with threading validation)
- [ ] Create migrations
- [ ] Implement `extract_metadata()` service
- [ ] Write model tests
- [ ] Write service tests

### Day 2-3: Source API
- [ ] Create `SourceSerializer` + `BulkSourceSerializer`
- [ ] Implement `SourceViewSet` (CRUD + bulk_import + restore)
- [ ] Add `VaultPermission` checks
- [ ] Create `SourceFilter` with django-filter
- [ ] Write view tests
- [ ] Write filter tests

### Day 4: Annotation API
- [ ] Create `AnnotationSerializer` (with nested replies)
- [ ] Implement `AnnotationViewSet`
- [ ] Add `IsAuthorOrReadOnly` permission
- [ ] Write view tests (including threading validation)

### Day 5: Audit Logging
- [ ] Extend/create `AuditLog` model
- [ ] Implement Django signals for sources
- [ ] Implement Django signals for annotations
- [ ] Write signal tests

### Day 6: Testing & Docs
- [ ] Run full test suite
- [ ] Manual API testing (see Appendix A)
- [ ] Update `MANUAL_VERIFICATION.md`
- [ ] Generate API docs (Swagger)

---

**End of PRD**