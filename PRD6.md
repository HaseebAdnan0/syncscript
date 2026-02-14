# PRD: File Storage & Cloud Integration

## Introduction

Implement cloud file storage for SyncScript using Cloudflare R2 (S3-compatible). Researchers can securely upload, download, and manage PDFs within Knowledge Vaults. Files are validated, processed for metadata extraction, and tracked for storage usage.

## Goals

- Enable secure PDF upload/download via presigned URLs
- Support multipart uploads for large files (up to 50MB)
- Validate PDFs strictly (MIME, magic number, structure)
- Extract metadata and generate thumbnails post-upload
- Track storage usage per vault and per user
- Implement soft-delete with 30-day retention
- Clean up orphaned multipart uploads automatically
- Notify users via WebSocket on upload/delete events
- Log all file operations to audit trail

## User Stories

### US-001: Create PDFUpload database model
**Description:** As a developer, I need to store PDF upload records so file metadata persists.

**Acceptance Criteria:**
- [x] Create `PDFUpload` model in `backend/apps/sources/models.py`
- [x] Fields: id (UUID), vault (FK), source (FK nullable), file (FileField), original_filename, file_size (BigInt), mime_type
- [x] Fields: uploaded_by (FK), uploaded_at, processing_status (pending/processing/completed/failed)
- [x] Fields: pdf_title, pdf_author, page_count, thumbnail_url, deleted_at (nullable)
- [x] Add indexes on (vault, deleted_at) and (uploaded_by, deleted_at)
- [x] Run makemigrations and migrate successfully
- [x] Typecheck passes

### US-002: Create VaultStorageUsage database model
**Description:** As a developer, I need to cache storage usage per vault for fast retrieval.

**Acceptance Criteria:**
- [x] Create `VaultStorageUsage` model in `backend/apps/sources/models.py`
- [x] Fields: vault (OneToOne), total_bytes (BigInt), file_count (Int), user_breakdown (JSONField), last_updated
- [x] Run makemigrations and migrate successfully
- [x] Typecheck passes

### US-003: Configure django-storages with Cloudflare R2
**Description:** As a developer, I need S3-compatible storage configured so files can be stored in the cloud.

**Acceptance Criteria:**
- [x] Add `django-storages[s3]` and `boto3` to requirements.txt
- [x] Configure `DEFAULT_FILE_STORAGE` in settings.py
- [x] Add settings: AWS_S3_FILE_OVERWRITE=False, AWS_QUERYSTRING_AUTH=True, AWS_QUERYSTRING_EXPIRE=900
- [x] Document required env vars in `.planning/USER_SETUP.md`: AWS_S3_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME
- [x] Typecheck passes

### US-004: Create PDF validation function
**Description:** As a developer, I need strict PDF validation so malicious files are rejected.

**Acceptance Criteria:**
- [x] Create `backend/apps/sources/validators.py`
- [x] Add `python-magic` and `pypdf` to requirements.txt
- [x] Implement `validate_pdf_file()` that checks: size <= 50MB, content_type == application/pdf, magic number matches PDF, pypdf can parse structure
- [x] Raise ValidationError with descriptive message on failure
- [x] Typecheck passes

### US-005: Create presigned URL generation utilities
**Description:** As a developer, I need utility functions to generate presigned S3 URLs.

**Acceptance Criteria:**
- [x] Create `backend/apps/sources/storage.py`
- [x] Implement `generate_presigned_upload_url(vault_id, filename, content_type)` returning (url, file_key)
- [x] Implement `generate_presigned_download_url(file_key, original_filename)` with content-disposition header
- [x] Upload URLs expire in 1 hour, download URLs expire in 15 minutes
- [x] Use SigV4 signature version
- [x] Typecheck passes

### US-006: Create upload URL endpoint
**Description:** As a vault contributor, I want to request a presigned upload URL so I can upload PDFs directly to storage.

**Acceptance Criteria:**
- [x] Add `POST /api/v1/sources/pdfs/upload-url/` endpoint
- [x] Request body: vault_id, filename, file_size, content_type
- [x] Validate user has contributor/owner permission on vault
- [x] Create PDFUpload record with status='pending'
- [x] Return: upload_id, upload_url, expires_in, callback_url
- [x] Add URL route to `backend/apps/sources/urls.py`
- [x] Typecheck passes

### US-007: Create upload completion endpoint
**Description:** As a client, I need to notify the backend when upload completes so processing can start.

**Acceptance Criteria:**
- [x] Add `POST /api/v1/sources/pdfs/{upload_id}/complete/` endpoint
- [x] Request body: file_key
- [x] Update PDFUpload status to 'processing'
- [x] Trigger Celery task for post-processing (placeholder call for now)
- [x] Return: pdf_id, status, message
- [x] Typecheck passes

### US-008: Create download URL endpoint
**Description:** As a vault member, I want to download PDFs from my vault so I can access materials offline.

**Acceptance Criteria:**
- [x] Add `GET /api/v1/sources/pdfs/{pdf_id}/download-url/` endpoint
- [x] Validate user has viewer/contributor/owner permission on vault
- [x] Generate presigned GET URL with content-disposition attachment
- [x] Return: download_url, expires_in, filename, file_size
- [x] Typecheck passes

### US-009: Create PDF serializers
**Description:** As a developer, I need serializers for PDF upload API responses.

**Acceptance Criteria:**
- [x] Create `backend/apps/sources/serializers.py` (or add to existing)
- [x] Add `UploadURLRequestSerializer` with vault_id, filename, file_size, content_type
- [x] Add `UploadURLResponseSerializer` with upload_id, upload_url, expires_in, callback_url
- [x] Add `PDFUploadSerializer` for listing/detail views
- [x] Typecheck passes

### US-010: Create post-upload Celery task for metadata extraction
**Description:** As a user, I want PDF metadata extracted automatically so I don't have to enter it manually.

**Acceptance Criteria:**
- [x] Create `process_uploaded_pdf` task in `backend/apps/sources/tasks.py`
- [x] Download file from S3, parse with pypdf
- [x] Extract: title, author, page_count from PDF metadata
- [x] Update PDFUpload record with extracted fields
- [x] Set processing_status to 'completed' on success, 'failed' on error
- [x] Add max_retries=3 with exponential backoff
- [x] Typecheck passes

### US-011: Add thumbnail generation to processing task
**Description:** As a user, I want to see PDF thumbnails so I can visually identify files.

**Acceptance Criteria:**
- [x] Add `pdf2image` and `Pillow` to requirements.txt
- [x] In `process_uploaded_pdf`, generate JPEG thumbnail from first page (max 300px width, 80% quality)
- [x] Upload thumbnail to S3 at `vaults/{vault_id}/thumbnails/{uuid}.jpg`
- [x] Generate presigned URL for thumbnail (7-day expiry)
- [x] Store thumbnail_url in PDFUpload record
- [x] Document system dependencies (poppler-utils) in `.planning/USER_SETUP.md`
- [x] Typecheck passes

### US-012: Create multipart upload initiate endpoint
**Description:** As a researcher, I want to upload large PDFs (>20MB) reliably via multipart upload.

**Acceptance Criteria:**
- [x] Add `POST /api/v1/sources/pdfs/multipart-upload/initiate/` endpoint
- [x] Request body: vault_id, filename, file_size, part_size, content_type
- [x] Initiate S3 multipart upload via boto3
- [x] Calculate number of parts and generate presigned URL for each
- [x] Return: upload_id, pdf_upload_id, file_key, part_urls array, expires_in
- [x] Typecheck passes

### US-013: Create multipart upload complete endpoint
**Description:** As a client, I need to finalize multipart upload after all parts are uploaded.

**Acceptance Criteria:**
- [x] Add `POST /api/v1/sources/pdfs/multipart-upload/{upload_id}/complete/` endpoint
- [x] Request body: parts array with part_number and etag
- [x] Complete S3 multipart upload via boto3
- [x] Update PDFUpload status and trigger processing task
- [x] Return: pdf_id, status, message
- [x] Typecheck passes

### US-014: Create storage usage calculation utility
**Description:** As a developer, I need to recalculate vault storage usage when files change.

**Acceptance Criteria:**
- [x] Create `update_vault_storage_usage(vault_id)` in `backend/apps/sources/utils.py`
- [x] Aggregate total_bytes and file_count from non-deleted PDFUploads
- [x] Calculate per-user breakdown as JSON
- [x] Update or create VaultStorageUsage record
- [x] Invalidate Redis cache key `vault_storage:{vault_id}`
- [x] Typecheck passes

### US-015: Add storage fields to Vault API
**Description:** As a vault owner, I want to see storage usage in vault details so I can manage resources.

**Acceptance Criteria:**
- [x] Add `storage_used_bytes`, `storage_file_count`, `storage_user_breakdown` to VaultDetailSerializer
- [x] Source from related VaultStorageUsage model
- [x] Handle case where VaultStorageUsage doesn't exist (return 0/empty)
- [x] Typecheck passes

### US-016: Create soft-delete endpoint
**Description:** As a vault owner, I want to delete PDFs so I can keep my vault organized.

**Acceptance Criteria:**
- [x] Add `DELETE /api/v1/sources/pdfs/{pdf_id}/` endpoint
- [x] Validate user has owner permission or is the uploader
- [x] Set deleted_at timestamp (soft-delete)
- [x] Update vault storage usage
- [x] Return: message, pdf_id, permanent_deletion_date (30 days later)
- [x] Typecheck passes

### US-017: Create cleanup_deleted_pdfs Celery task
**Description:** As a system, I need to permanently delete soft-deleted files after 30 days.

**Acceptance Criteria:**
- [x] Create `cleanup_deleted_pdfs` task in `backend/apps/sources/tasks.py`
- [x] Query PDFUploads where deleted_at < 30 days ago
- [x] Delete file from S3 via `pdf.file.delete(save=False)`
- [x] Delete thumbnail if exists
- [x] Delete database record
- [x] Log each permanent deletion
- [x] Typecheck passes

### US-018: Create cleanup_orphaned_multipart_uploads Celery task
**Description:** As a system, I need to clean up abandoned multipart uploads to prevent storage waste.

**Acceptance Criteria:**
- [x] Create `cleanup_orphaned_multipart_uploads` task in `backend/apps/sources/tasks.py`
- [x] List multipart uploads via boto3 `list_multipart_uploads`
- [x] Abort uploads initiated > 24 hours ago
- [x] Log each aborted upload
- [x] Typecheck passes

### US-019: Configure Celery Beat schedule for cleanup tasks
**Description:** As a developer, I need cleanup tasks to run on schedule.

**Acceptance Criteria:**
- [x] Add `cleanup_deleted_pdfs` to Celery Beat: daily at 2am
- [x] Add `cleanup_orphaned_multipart_uploads` to Celery Beat: daily at 3am
- [x] Update `backend/config/celery.py` with beat_schedule
- [x] Typecheck passes

### US-020: Add WebSocket notifications for PDF events
**Description:** As a user, I want real-time notifications when PDFs are uploaded or deleted.

**Acceptance Criteria:**
- [x] In `process_uploaded_pdf` task, send WebSocket message to `vault_{vault_id}` group
- [x] Event type: `pdf.uploaded` with pdf_id, filename, uploaded_by
- [x] In soft-delete view, send `pdf.deleted` event
- [x] Use existing channel_layer infrastructure
- [x] Typecheck passes

### US-021: Add audit logging for file operations
**Description:** As a researcher, I need file operations logged for research integrity.

**Acceptance Criteria:**
- [x] Log `pdf.uploaded` event after processing completes (in Celery task)
- [x] Log `pdf.deleted` event in soft-delete view
- [x] Log `pdf.downloaded` event in download-url view
- [x] Log `pdf.processing_failed` event on task failure
- [x] Include: vault, user, action, details (pdf_id, filename)
- [x] Typecheck passes

### US-022: Add rate limiting to PDF endpoints
**Description:** As a system, I need rate limiting to prevent abuse.

**Acceptance Criteria:**
- [x] Add rate limit to upload-url endpoint: 10/minute per user
- [x] Add rate limit to download-url endpoint: 30/minute per user
- [x] Use django-ratelimit decorator
- [x] Typecheck passes

### US-023: Create PDF list endpoint for vault
**Description:** As a vault member, I want to list all PDFs in my vault.

**Acceptance Criteria:**
- [x] Add `GET /api/v1/vaults/{vault_id}/pdfs/` endpoint
- [x] Filter out soft-deleted PDFs (deleted_at is null)
- [x] Return paginated list using PDFUploadSerializer
- [x] Validate user has vault access
- [x] Order by uploaded_at descending
- [x] Typecheck passes

### US-024: Write unit tests for PDF validation
**Description:** As a developer, I need tests to verify PDF validation works correctly.

**Acceptance Criteria:**
- [x] Create `backend/apps/sources/tests/test_validators.py`
- [x] Test: valid PDF passes validation
- [x] Test: non-PDF file (txt) raises ValidationError
- [x] Test: file > 50MB raises ValidationError
- [x] Test: corrupted PDF raises ValidationError
- [x] All tests pass

### US-025: Write unit tests for storage utilities
**Description:** As a developer, I need tests for presigned URL generation and storage tracking.

**Acceptance Criteria:**
- [ ] Create `backend/apps/sources/tests/test_storage.py`
- [ ] Test: generate_presigned_upload_url returns valid URL and key
- [ ] Test: generate_presigned_download_url includes content-disposition
- [ ] Test: update_vault_storage_usage calculates correct totals
- [ ] Mock boto3 client for S3 operations
- [ ] All tests pass

### US-026: Write integration tests for upload flow
**Description:** As a developer, I need end-to-end tests for the upload workflow.

**Acceptance Criteria:**
- [ ] Create `backend/apps/sources/tests/test_views.py`
- [ ] Test: upload-url endpoint returns presigned URL for authorized user
- [ ] Test: upload-url endpoint rejects unauthorized user
- [ ] Test: completion endpoint triggers processing
- [ ] Test: download-url endpoint works for vault members
- [ ] Test: delete endpoint soft-deletes and updates storage
- [ ] All tests pass

## Non-Goals

- Storage quota enforcement (tracking only, no hard limits)
- File versioning / revision history
- OCR processing for scanned PDFs
- Direct browser-to-R2 uploads (backend-mediated only)
- Restore from soft-delete (future enhancement)
- Virus scanning with ClamAV (future enhancement)
- CDN integration (evaluate after load testing)

## Technical Considerations

- **Storage Path:** `vaults/{vault_id}/pdfs/{uuid}.pdf`
- **Thumbnail Path:** `vaults/{vault_id}/thumbnails/{uuid}.jpg`
- **System Dependencies:** libmagic1, poppler-utils (document in USER_SETUP.md)
- **Existing Models:** Vault, Source, User, AuditLog already exist
- **Existing Infra:** Redis for cache/Celery, Django Channels for WebSocket
- **Permission System:** Reuse existing vault permission checks
