# PRD 13: Cloudflare R2 File Storage (Production)

## Introduction

Enhance SyncScript's file storage system to production-ready status with Cloudflare R2. This PRD extends the existing PDF upload infrastructure to support additional file types (PNG, JPG), adds full-text extraction for search, implements storage quota warnings, and builds a polished frontend upload experience.

**Existing Infrastructure (already implemented):**
- Presigned URL generation (upload 1hr, download 15min) - `apps/sources/storage.py`
- Multipart upload initiate/complete - `apps/sources/storage.py`
- PDF validation with magic numbers - `apps/sources/validators.py`
- PDF processing (metadata, thumbnails) - `apps/sources/tasks.py`
- VaultStorageUsage model - `apps/sources/models.py`
- Soft-delete cleanup tasks - `apps/sources/tasks.py`

## Goals

- Support image uploads (PNG, JPG) alongside existing PDF support
- Extract full PDF text for future search indexing
- Implement storage quota warnings at 80% of 1GB limit
- Add multipart upload abort endpoint for failed uploads
- Create virus scanning service stub for future ClamAV integration
- Build complete frontend upload UI with drag-drop, progress, and error handling
- Clean up orphaned files (S3 objects without DB records)

## User Stories

### US-001: Add extracted_text field to PDFUpload model
**Description:** As a developer, I need a field to store extracted PDF text so it can be used for search indexing.

**Acceptance Criteria:**
- [x] Add `extracted_text = models.TextField(blank=True, default='')` to PDFUpload model
- [x] Generate migration file
- [x] Run migration successfully
- [x] Typecheck passes

---

### US-002: Extract full text during PDF processing
**Description:** As a user, I want PDF text extracted so my documents can be searched later.

**Acceptance Criteria:**
- [x] Update `process_uploaded_pdf` task in `apps/sources/tasks.py`
- [x] Extract text from all pages using `pypdf` reader
- [x] Concatenate text with page separators (e.g., `\n--- Page X ---\n`)
- [x] Truncate to 500KB max to prevent DB bloat
- [x] Save to `pdf_upload.extracted_text` field
- [x] Log extraction success with character count
- [x] Typecheck passes

---

### US-003: Add image file type constants and validators
**Description:** As a developer, I need validation logic for PNG and JPG files to allow image uploads.

**Acceptance Criteria:**
- [x] Add to `apps/sources/validators.py`:
  - `ALLOWED_IMAGE_TYPES = {'image/png': [b'\x89PNG'], 'image/jpeg': [b'\xff\xd8\xff']}`
  - `MAX_IMAGE_SIZE = 10 * 1024 * 1024` (10MB)
- [x] Create `validate_image_file(file)` function
- [x] Check file size against MAX_IMAGE_SIZE
- [x] Verify MIME type via python-magic
- [x] Verify magic number matches content type
- [x] Raise ValidationError with descriptive messages on failure
- [x] Typecheck passes

---

### US-004: Create FileUpload model for images
**Description:** As a developer, I need a model to store image uploads separate from PDFs.

**Acceptance Criteria:**
- [x] Create `FileUpload` model in `apps/sources/models.py` with fields:
  - `id` (UUIDField, primary key)
  - `vault` (ForeignKey to Vault)
  - `file` (FileField, upload_to path)
  - `original_filename` (CharField)
  - `file_size` (BigIntegerField)
  - `mime_type` (CharField)
  - `file_type` (CharField choices: 'image', 'document')
  - `uploaded_by` (ForeignKey to User)
  - `uploaded_at` (DateTimeField auto_now_add)
  - `thumbnail_url` (URLField, blank)
  - `deleted_at` (DateTimeField, null)
- [x] Generate and run migration
- [x] Typecheck passes

---

### US-005: Create image processing Celery task
**Description:** As a user, I want thumbnails generated for my uploaded images.

**Acceptance Criteria:**
- [x] Create `process_uploaded_image` task in `apps/sources/tasks.py`
- [x] Download image from S3
- [x] Generate 300px wide thumbnail using Pillow
- [x] Upload thumbnail to `vaults/{vault_id}/thumbnails/{uuid}.jpg`
- [x] Update FileUpload record with thumbnail_url
- [x] Handle errors with retry logic (max 3 retries)
- [x] Typecheck passes

---

### US-006: Create ClamAV virus scanning service stub
**Description:** As a developer, I need a virus scanning service interface ready for future ClamAV integration.

**Acceptance Criteria:**
- [x] Create `apps/sources/services/virus_scanner.py`
- [x] Create `VirusScanResult` dataclass with fields: `is_clean`, `threat_name`, `scan_time_ms`
- [x] Create `VirusScanner` class with method `scan_file(file_bytes: bytes) -> VirusScanResult`
- [x] Stub implementation: log "TODO: ClamAV integration", return `is_clean=True`
- [x] Add `CLAMAV_ENABLED = False` setting to `config/settings.py`
- [x] Typecheck passes

---

### US-007: Integrate virus scanner into upload flow
**Description:** As a developer, I want uploads to pass through virus scanning before storage.

**Acceptance Criteria:**
- [x] Import VirusScanner in upload view/serializer
- [x] Call `virus_scanner.scan_file()` before saving file
- [x] If `is_clean=False`, reject upload with 400 error
- [x] Log scan results (clean/threat) with file info
- [x] Typecheck passes

---

### US-008: Add abort_multipart_upload function
**Description:** As a developer, I need to abort failed multipart uploads to free S3 resources.

**Acceptance Criteria:**
- [x] Add `abort_multipart_upload(file_key: str, upload_id: str) -> None` to `apps/sources/storage.py`
- [x] Call `s3_client.abort_multipart_upload()` with bucket, key, upload_id
- [x] Log abort action
- [x] Handle and log S3 errors gracefully
- [x] Typecheck passes

---

### US-009: Create multipart abort API endpoint
**Description:** As a frontend developer, I need an endpoint to abort failed uploads.

**Acceptance Criteria:**
- [x] Add `POST /api/v1/uploads/abort/` endpoint
- [x] Request body: `{ "upload_id": str, "file_key": str }`
- [x] Validate user has permission to abort (owns the upload or vault admin)
- [x] Call `abort_multipart_upload()` function
- [x] Return 200 on success, 400/404 on error
- [x] Typecheck passes

---

### US-010: Add storage quota warning logic
**Description:** As a vault owner, I want warnings when storage approaches the 1GB limit.

**Acceptance Criteria:**
- [x] Add `VAULT_STORAGE_LIMIT = 1 * 1024 * 1024 * 1024` (1GB) to settings
- [x] Add `VAULT_STORAGE_WARNING_THRESHOLD = 0.8` (80%) to settings
- [x] Create `check_storage_quota(vault_id) -> dict` in `apps/sources/services/storage_quota.py`
- [x] Returns: `{ "used_bytes", "limit_bytes", "percentage", "warning": bool, "exceeded": bool }`
- [x] Warning is True when usage >= 80%
- [x] Typecheck passes

---

### US-011: Block uploads when storage quota exceeded
**Description:** As a system, I need to prevent uploads when vault storage is full.

**Acceptance Criteria:**
- [x] Check storage quota before accepting uploads in upload view
- [x] If `exceeded=True`, return 413 with message "Storage quota exceeded"
- [x] Include `used_bytes` and `limit_bytes` in error response
- [x] Typecheck passes

---

### US-012: Add storage quota to vault API response
**Description:** As a frontend developer, I need storage info in the vault API to display usage.

**Acceptance Criteria:**
- [x] Add `storage_usage` field to VaultSerializer
- [x] Include: `used_bytes`, `limit_bytes`, `percentage`, `warning`, `file_count`
- [x] Retrieve from VaultStorageUsage model (create if not exists)
- [x] Typecheck passes

---

### US-013: Create orphan file cleanup task
**Description:** As a system admin, I want orphaned S3 files cleaned up to save storage costs.

**Acceptance Criteria:**
- [ ] Create `cleanup_orphaned_files` Celery task in `apps/sources/tasks.py`
- [ ] List S3 objects in `vaults/` prefix
- [ ] For each object, check if corresponding PDFUpload or FileUpload exists
- [ ] If no DB record and file older than 24 hours, delete from S3
- [ ] Log deleted files with keys
- [ ] Return `{ "deleted_count": int, "errors": list }`
- [ ] Typecheck passes

---

### US-014: Create FileUploadZone component
**Description:** As a user, I want to drag and drop files to upload them easily.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/uploads/FileUploadZone.tsx`
- [ ] Accept `onFilesSelected: (files: File[]) => void` prop
- [ ] Accept `accept` prop for allowed MIME types (default: PDF, PNG, JPG)
- [ ] Drag-over visual state with dashed border highlight (Bitcoin orange)
- [ ] Click to open file picker
- [ ] Display drop hint text: "Drop files here or click to browse"
- [ ] Validate file types client-side before calling callback
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-015: Create UploadProgressBar component
**Description:** As a user, I want to see upload progress so I know how long to wait.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/uploads/UploadProgressBar.tsx`
- [ ] Props: `filename: string`, `progress: number (0-100)`, `status: 'uploading' | 'processing' | 'complete' | 'error'`
- [ ] Show filename truncated to 30 chars with ellipsis
- [ ] Animated progress bar with gradient (orange to gold)
- [ ] Show percentage text
- [ ] Different colors for status: orange=uploading, blue=processing, green=complete, red=error
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-016: Create FileTypeIcon component
**Description:** As a user, I want visual icons to identify file types at a glance.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/uploads/FileTypeIcon.tsx`
- [ ] Props: `mimeType: string`, `size?: 'sm' | 'md' | 'lg'`
- [ ] Return appropriate Lucide icon: `FileText` (PDF), `Image` (PNG/JPG), `File` (other)
- [ ] Size variants: sm=16px, md=24px, lg=32px
- [ ] Color: muted gray, or primary orange when active
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-017: Create useFileUpload hook
**Description:** As a developer, I need a hook to manage file upload state and progress.

**Acceptance Criteria:**
- [ ] Create `frontend/src/hooks/useFileUpload.ts`
- [ ] State: `uploads: Map<string, { file, progress, status, error }>`
- [ ] Methods: `uploadFile(file, vaultId)`, `retryUpload(uploadId)`, `cancelUpload(uploadId)`
- [ ] Get presigned URL from backend, then PUT file with XMLHttpRequest for progress
- [ ] Update progress via `xhr.upload.onprogress`
- [ ] Handle multipart for files > 20MB (call initiate, upload parts, complete)
- [ ] Typecheck passes

---

### US-018: Create StorageUsageIndicator component
**Description:** As a vault owner, I want to see storage usage in vault settings.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/vaults/StorageUsageIndicator.tsx`
- [ ] Props: `usedBytes: number`, `limitBytes: number`, `warning?: boolean`
- [ ] Display progress bar showing percentage used
- [ ] Show text: "X.XX GB / 1 GB used"
- [ ] Yellow/orange color when warning=true (>80%)
- [ ] Red color when >95%
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-019: Create UploadErrorState component
**Description:** As a user, I want to see clear error messages and retry failed uploads.

**Acceptance Criteria:**
- [ ] Create `frontend/src/components/features/uploads/UploadErrorState.tsx`
- [ ] Props: `filename: string`, `error: string`, `onRetry: () => void`, `onDismiss: () => void`
- [ ] Display error icon, filename, error message
- [ ] "Retry" button calls onRetry
- [ ] "X" dismiss button calls onDismiss
- [ ] Red accent color for error state
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-020: Integrate upload components into SourcesList
**Description:** As a user, I want to upload files directly from the sources list view.

**Acceptance Criteria:**
- [ ] Add FileUploadZone to top of SourcesList component
- [ ] Use useFileUpload hook to manage uploads
- [ ] Show UploadProgressBar for each active upload
- [ ] Show UploadErrorState for failed uploads
- [ ] Refresh sources list when upload completes
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-021: Add storage usage to vault settings page
**Description:** As a vault owner, I want to see storage usage in my vault settings.

**Acceptance Criteria:**
- [ ] Fetch vault data with storage_usage field
- [ ] Add StorageUsageIndicator component to vault settings section
- [ ] Show warning message when approaching limit
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-022: Register Celery beat schedule for cleanup tasks
**Description:** As a system admin, I want cleanup tasks to run automatically on schedule.

**Acceptance Criteria:**
- [ ] Add to `config/celery.py` beat schedule:
  - `cleanup_orphaned_files`: daily at 3 AM
  - `cleanup_orphaned_multipart_uploads`: daily at 4 AM (already exists, verify)
  - `cleanup_deleted_pdfs`: daily at 5 AM (already exists, verify)
- [ ] Typecheck passes

---

### US-023: Add upload API tests
**Description:** As a developer, I need tests for the new upload functionality.

**Acceptance Criteria:**
- [ ] Test image validation (valid PNG, valid JPG, invalid file)
- [ ] Test abort multipart endpoint
- [ ] Test storage quota check (under limit, warning, exceeded)
- [ ] Test virus scanner stub returns clean
- [ ] All tests pass
- [ ] Typecheck passes

---

### US-024: Update presigned URL generation for images
**Description:** As a developer, I need presigned URLs to support image content types.

**Acceptance Criteria:**
- [ ] Update `generate_presigned_upload_url` to accept `file_type` parameter ('pdf', 'image')
- [ ] Set correct content-type based on file type
- [ ] Store in correct path: `vaults/{vault_id}/images/{uuid}.{ext}` for images
- [ ] Typecheck passes

---

## Non-Goals

- Full ClamAV integration (stub only for now)
- DOCX file support (PDF and images only in this PRD)
- Full-text search implementation (text extraction only, search is separate)
- Custom CDN domain setup (presigned URLs work without CDN)
- Real-time upload collaboration (single user uploads)
- Resumable uploads after browser close

## Technical Considerations

- **Existing Code:** Build on `apps/sources/storage.py`, `validators.py`, `tasks.py`, `models.py`
- **File Paths:** Use pattern `vaults/{vault_id}/{type}/{uuid}.{ext}` where type is `pdfs`, `images`, `thumbnails`
- **Multipart Threshold:** 20MB (already configured)
- **Storage Limits:** 1GB per vault, warning at 80%
- **Dependencies:** pypdf (exists), Pillow (exists), python-magic (exists), boto3 (exists)

## File Locations

| Component | Location |
|-----------|----------|
| Validators | `backend/apps/sources/validators.py` |
| Storage utils | `backend/apps/sources/storage.py` |
| Celery tasks | `backend/apps/sources/tasks.py` |
| Models | `backend/apps/sources/models.py` |
| Virus scanner | `backend/apps/sources/services/virus_scanner.py` |
| Storage quota | `backend/apps/sources/services/storage_quota.py` |
| Upload views | `backend/apps/sources/views.py` |
| Frontend uploads | `frontend/src/components/features/uploads/` |
| Upload hook | `frontend/src/hooks/useFileUpload.ts` |
