# Product Requirements Document: File Storage & Cloud Integration

## 1. Overview

### 1.1 Purpose
Implement a robust cloud file storage system for SyncScript that enables secure PDF uploads, downloads, and management within Knowledge Vaults using S3-compatible storage (Cloudflare R2).

### 1.2 Success Metrics
- PDF upload success rate > 99%
- Presigned URL generation < 200ms (p95)
- Post-upload processing completion < 30 seconds for 10MB files
- Zero orphaned multipart uploads after 24 hours
- Storage quota tracking accuracy: 100%

### 1.3 Scope
**In Scope:**
- S3-compatible storage configuration (Cloudflare R2)
- Secure upload/download via presigned URLs
- Multipart upload support for large files
- PDF validation (MIME, magic number, structure parsing)
- Post-upload processing (metadata extraction, thumbnail generation)
- Storage usage tracking per vault and per user
- Soft-delete with audit logging
- Orphaned upload cleanup

**Out of Scope:**
- Storage quota enforcement UI (tracking only)
- Version control for file revisions
- OCR processing for scanned PDFs
- Direct browser-to-R2 uploads (backend-mediated only)

---

## 2. User Stories

### US-1: Secure PDF Upload
**As a** vault contributor  
**I want to** upload PDF files to my vault securely  
**So that** my research materials are stored safely in the cloud

**Acceptance Criteria:**
- Upload endpoint generates presigned PUT URL valid for 1 hour
- File validation rejects non-PDF files before upload
- Files > 20MB trigger multipart upload flow (optional, client-decided)
- Upload completion triggers background processing
- User receives WebSocket notification when processing completes

---

### US-2: Download Vault PDFs
**As a** vault member  
**I want to** download PDFs from my vault  
**So that** I can access research materials offline

**Acceptance Criteria:**
- Download endpoint generates presigned GET URL valid for 15 minutes
- URL includes content-disposition header to force download
- Permission check ensures user has vault access
- Download events logged to audit log
- Rate limiting prevents abuse (10 downloads/minute per user)

---

### US-3: Large File Upload Support
**As a** researcher  
**I want to** upload large PDF files (up to 50MB)  
**So that** I can store comprehensive research papers and books

**Acceptance Criteria:**
- Multipart upload initiation endpoint available (client-optional for files > 20MB)
- Returns upload_id and presigned URLs for each part
- Completion endpoint finalizes multipart upload
- Orphaned multipart uploads cleaned up after 24 hours
- Upload progress trackable via metadata

---

### US-4: Storage Usage Visibility
**As a** vault owner  
**I want to** see how much storage my vault is using  
**So that** I can manage my resources effectively

**Acceptance Criteria:**
- Vault detail API includes `storage_used_bytes` field
- Storage breakdown available by user (who uploaded what)
- Storage recalculated on file upload/deletion
- Cached with Redis (invalidated on write)
- Admin dashboard shows vault storage rankings

---

### US-5: File Deletion & Audit Trail
**As a** vault owner  
**I want to** delete unnecessary PDFs  
**So that** I can keep my vault organized and free up storage

**Acceptance Criteria:**
- Soft-delete marks file as deleted in DB, keeps in storage
- File excluded from listings immediately
- Scheduled Celery task permanently deletes files after 30 days
- Deletion event logged to audit log with user, timestamp, file metadata
- Restore from soft-delete not implemented (future enhancement)

---

## 3. Functional Requirements

### 3.1 Storage Backend Configuration

**FR-1.1: Django Storages Setup**
- Configure `django-storages` with S3-compatible backend
- Support Cloudflare R2 endpoint URL configuration
- Environment variables:
  - `AWS_S3_ENDPOINT_URL` (R2 endpoint)
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_STORAGE_BUCKET_NAME`
  - `AWS_S3_REGION_NAME` (auto for R2)
  - `AWS_S3_SIGNATURE_VERSION=s3v4`
  - `AWS_DEFAULT_ACL=None` (private by default)

**FR-1.2: File Organization**
- Storage path pattern: `vaults/{vault_id}/pdfs/{uuid}.pdf`
- Use UUID4 for file identifiers (avoid filename collisions)
- Original filename stored in `PDFUpload.original_filename` field

**FR-1.3: Storage Settings**
```python
# backend/config/settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True  # Enable presigned URLs
AWS_QUERYSTRING_EXPIRE = 900  # Default 15 minutes
```

---

### 3.2 Database Models

**FR-2.1: PDFUpload Model**
```python
# backend/apps/sources/models.py
class PDFUpload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    vault = models.ForeignKey('vaults.Vault', on_delete=models.CASCADE, related_name='pdfs')
    source = models.ForeignKey('sources.Source', null=True, blank=True, on_delete=models.SET_NULL)
    
    # File metadata
    file = models.FileField(upload_to='vaults/%Y/%m/', storage=...)  # Custom callable
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  # Bytes
    mime_type = models.CharField(max_length=100, default='application/pdf')
    
    # Upload tracking
    uploaded_by = models.ForeignKey('users.User', on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    # Extracted metadata (populated by Celery task)
    pdf_title = models.CharField(max_length=500, blank=True)
    pdf_author = models.CharField(max_length=500, blank=True)
    page_count = models.IntegerField(null=True)
    thumbnail_url = models.URLField(blank=True)  # Presigned URL to thumbnail
    
    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'pdf_uploads'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['vault', 'deleted_at']),
            models.Index(fields=['uploaded_by', 'deleted_at']),
        ]
```

**FR-2.2: StorageUsage Model (Cache Table)**
```python
class VaultStorageUsage(models.Model):
    vault = models.OneToOneField('vaults.Vault', on_delete=models.CASCADE, related_name='storage_usage')
    total_bytes = models.BigIntegerField(default=0)
    file_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Per-user breakdown (JSONField)
    user_breakdown = models.JSONField(default=dict)  # {user_id: bytes}
    
    class Meta:
        db_table = 'vault_storage_usage'
```

---

### 3.3 File Validation

**FR-3.1: PDF Validation Function**
```python
# backend/apps/sources/validators.py
from django.core.exceptions import ValidationError
import magic
import pypdf

def validate_pdf_file(file_obj):
    """
    Strict PDF validation:
    1. MIME type check
    2. Magic number (file header) verification
    3. PDF structure parsing
    """
    # Check size
    if file_obj.size > 50 * 1024 * 1024:  # 50MB
        raise ValidationError("File size exceeds 50MB limit")
    
    # Check MIME type from request
    if not file_obj.content_type == 'application/pdf':
        raise ValidationError("Only PDF files are allowed")
    
    # Magic number check (file header)
    file_obj.seek(0)
    mime = magic.from_buffer(file_obj.read(2048), mime=True)
    if mime != 'application/pdf':
        raise ValidationError("File header does not match PDF format")
    
    # Attempt to parse PDF structure
    file_obj.seek(0)
    try:
        reader = pypdf.PdfReader(file_obj)
        if len(reader.pages) == 0:
            raise ValidationError("PDF has no pages")
    except Exception as e:
        raise ValidationError(f"Invalid PDF structure: {str(e)}")
    
    file_obj.seek(0)  # Reset for further processing
```

---

### 3.4 Presigned URL Generation

**FR-4.1: Upload URL Endpoint**
```
POST /api/v1/sources/pdfs/upload-url/
Request:
{
  "vault_id": "uuid",
  "filename": "research-paper.pdf",
  "file_size": 1048576,
  "content_type": "application/pdf"
}

Response:
{
  "upload_id": "uuid",
  "upload_url": "https://r2.../presigned-put-url",
  "expires_in": 3600,
  "callback_url": "/api/v1/sources/pdfs/{upload_id}/complete/"
}
```

**FR-4.2: Download URL Endpoint**
```
GET /api/v1/sources/pdfs/{pdf_id}/download-url/

Response:
{
  "download_url": "https://r2.../presigned-get-url",
  "expires_in": 900,
  "filename": "research-paper.pdf",
  "file_size": 1048576
}
```

**FR-4.3: Presigned URL Implementation**
```python
# backend/apps/sources/storage.py
from botocore.client import Config
import boto3
from django.conf import settings

def generate_presigned_upload_url(vault_id, filename, content_type='application/pdf'):
    s3_client = boto3.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4')
    )
    
    file_key = f"vaults/{vault_id}/pdfs/{uuid.uuid4()}.pdf"
    
    presigned_url = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': file_key,
            'ContentType': content_type,
        },
        ExpiresIn=3600,  # 1 hour
        HttpMethod='PUT'
    )
    
    return presigned_url, file_key

def generate_presigned_download_url(file_key, original_filename):
    s3_client = boto3.client('s3', ...)
    
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': file_key,
            'ResponseContentDisposition': f'attachment; filename="{original_filename}"'
        },
        ExpiresIn=900,  # 15 minutes
        HttpMethod='GET'
    )
    
    return presigned_url
```

---

### 3.5 Multipart Upload Support

**FR-5.1: Initiate Multipart Upload**
```
POST /api/v1/sources/pdfs/multipart-upload/initiate/
Request:
{
  "vault_id": "uuid",
  "filename": "large-research-paper.pdf",
  "file_size": 52428800,  # 50MB
  "part_size": 5242880,    # 5MB parts
  "content_type": "application/pdf"
}

Response:
{
  "upload_id": "s3-multipart-upload-id",
  "pdf_upload_id": "uuid",
  "file_key": "vaults/{vault_id}/pdfs/{uuid}.pdf",
  "part_urls": [
    {"part_number": 1, "upload_url": "https://..."},
    {"part_number": 2, "upload_url": "https://..."},
    ...
  ],
  "expires_in": 3600
}
```

**FR-5.2: Complete Multipart Upload**
```
POST /api/v1/sources/pdfs/multipart-upload/{upload_id}/complete/
Request:
{
  "parts": [
    {"part_number": 1, "etag": "etag-from-s3"},
    {"part_number": 2, "etag": "etag-from-s3"},
    ...
  ]
}

Response:
{
  "pdf_id": "uuid",
  "status": "processing",
  "message": "Upload completed, processing PDF metadata"
}
```

**FR-5.3: Implementation**
```python
# backend/apps/sources/views.py
class MultipartUploadInitiateView(APIView):
    def post(self, request):
        # Validate permissions
        # Create PDFUpload record with status='pending'
        # Initiate S3 multipart upload
        # Generate presigned URLs for each part
        # Return part URLs and upload_id
        
class MultipartUploadCompleteView(APIView):
    def post(self, request, upload_id):
        # Complete S3 multipart upload
        # Update PDFUpload status to 'processing'
        # Trigger Celery task for post-processing
        # Send WebSocket notification
```

---

### 3.6 Upload Completion & Processing

**FR-6.1: Upload Completion Callback**
```
POST /api/v1/sources/pdfs/{upload_id}/complete/
Request:
{
  "file_key": "vaults/{vault_id}/pdfs/{uuid}.pdf"
}

Response:
{
  "pdf_id": "uuid",
  "status": "processing",
  "message": "PDF uploaded successfully, processing metadata"
}
```

**FR-6.2: Post-Upload Celery Task**
```python
# backend/apps/sources/tasks.py
from celery import shared_task
from .models import PDFUpload
import pypdf
from PIL import Image
import io

@shared_task(bind=True, max_retries=3)
def process_uploaded_pdf(self, pdf_upload_id):
    """
    Post-upload processing:
    1. Extract metadata (title, author, page count)
    2. Generate first-page thumbnail
    3. Update PDFUpload record
    4. Send WebSocket notification
    """
    try:
        pdf_upload = PDFUpload.objects.get(id=pdf_upload_id)
        pdf_upload.processing_status = 'processing'
        pdf_upload.save()
        
        # Download file from S3 temporarily
        file_obj = pdf_upload.file.open('rb')
        
        # Extract metadata
        reader = pypdf.PdfReader(file_obj)
        metadata = reader.metadata
        
        pdf_upload.pdf_title = metadata.get('/Title', '')
        pdf_upload.pdf_author = metadata.get('/Author', '')
        pdf_upload.page_count = len(reader.pages)
        
        # Generate thumbnail (first page)
        first_page = reader.pages[0]
        # Convert to image using pdf2image or PyMuPDF
        # Upload thumbnail to S3 with key: vaults/{vault_id}/thumbnails/{uuid}.jpg
        # Generate presigned URL for thumbnail (expires in 7 days)
        
        pdf_upload.thumbnail_url = generate_presigned_download_url(thumbnail_key, ...)
        pdf_upload.processing_status = 'completed'
        pdf_upload.save()
        
        # Update storage usage
        update_vault_storage_usage(pdf_upload.vault_id)
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"vault_{pdf_upload.vault_id}",
            {
                "type": "pdf.uploaded",
                "data": {
                    "pdf_id": str(pdf_upload.id),
                    "filename": pdf_upload.original_filename,
                    "uploaded_by": pdf_upload.uploaded_by.username,
                }
            }
        )
        
        # Log to audit log
        AuditLog.objects.create(
            vault=pdf_upload.vault,
            user=pdf_upload.uploaded_by,
            action='pdf.uploaded',
            details={'pdf_id': str(pdf_upload.id), 'filename': pdf_upload.original_filename}
        )
        
    except Exception as exc:
        pdf_upload.processing_status = 'failed'
        pdf_upload.save()
        raise self.retry(exc=exc, countdown=60)  # Retry after 1 minute
```

---

### 3.7 Storage Usage Tracking

**FR-7.1: Update Storage Usage Function**
```python
# backend/apps/sources/utils.py
from django.db.models import Sum
from .models import PDFUpload, VaultStorageUsage

def update_vault_storage_usage(vault_id):
    """
    Recalculate storage usage for vault:
    - Total bytes
    - File count
    - Per-user breakdown
    """
    # Aggregate total (exclude soft-deleted)
    stats = PDFUpload.objects.filter(
        vault_id=vault_id,
        deleted_at__isnull=True
    ).aggregate(
        total_bytes=Sum('file_size'),
        file_count=Count('id')
    )
    
    # Per-user breakdown
    user_breakdown = {}
    user_stats = PDFUpload.objects.filter(
        vault_id=vault_id,
        deleted_at__isnull=True
    ).values('uploaded_by').annotate(total=Sum('file_size'))
    
    for stat in user_stats:
        user_breakdown[str(stat['uploaded_by'])] = stat['total']
    
    # Update or create VaultStorageUsage
    VaultStorageUsage.objects.update_or_create(
        vault_id=vault_id,
        defaults={
            'total_bytes': stats['total_bytes'] or 0,
            'file_count': stats['file_count'] or 0,
            'user_breakdown': user_breakdown
        }
    )
    
    # Invalidate cache
    cache.delete(f'vault_storage:{vault_id}')
```

**FR-7.2: Vault API Integration**
```python
# backend/apps/vaults/serializers.py
class VaultDetailSerializer(serializers.ModelSerializer):
    storage_used_bytes = serializers.IntegerField(source='storage_usage.total_bytes', read_only=True)
    storage_file_count = serializers.IntegerField(source='storage_usage.file_count', read_only=True)
    storage_user_breakdown = serializers.JSONField(source='storage_usage.user_breakdown', read_only=True)
    
    class Meta:
        model = Vault
        fields = ['id', 'name', 'description', 'storage_used_bytes', ...]
```

---

### 3.8 Soft Delete & Cleanup

**FR-8.1: Soft Delete Endpoint**
```
DELETE /api/v1/sources/pdfs/{pdf_id}/

Response:
{
  "message": "PDF marked for deletion",
  "pdf_id": "uuid",
  "permanent_deletion_date": "2026-03-16T00:00:00Z"
}
```

**FR-8.2: Soft Delete Implementation**
```python
# backend/apps/sources/views.py
class PDFUploadDeleteView(APIView):
    def delete(self, request, pdf_id):
        pdf_upload = get_object_or_404(PDFUpload, id=pdf_id)
        
        # Permission check
        if not request.user.has_vault_permission(pdf_upload.vault, 'delete_pdf'):
            return Response({'error': 'Permission denied'}, status=403)
        
        # Soft delete
        pdf_upload.deleted_at = timezone.now()
        pdf_upload.save()
        
        # Update storage usage
        update_vault_storage_usage(pdf_upload.vault_id)
        
        # Audit log
        AuditLog.objects.create(
            vault=pdf_upload.vault,
            user=request.user,
            action='pdf.deleted',
            details={'pdf_id': str(pdf_id), 'filename': pdf_upload.original_filename}
        )
        
        # WebSocket notification
        # ...
        
        return Response({'message': 'PDF marked for deletion', ...})
```

**FR-8.3: Scheduled Cleanup Task**
```python
# backend/apps/sources/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task
def cleanup_deleted_pdfs():
    """
    Permanently delete PDFs that were soft-deleted > 30 days ago.
    Run daily via Celery Beat.
    """
    cutoff_date = timezone.now() - timedelta(days=30)
    
    pdfs_to_delete = PDFUpload.objects.filter(
        deleted_at__isnull=False,
        deleted_at__lt=cutoff_date
    )
    
    for pdf in pdfs_to_delete:
        # Delete from S3
        pdf.file.delete(save=False)
        
        # Delete thumbnail if exists
        # ...
        
        # Delete DB record
        pdf.delete()
        
        logger.info(f"Permanently deleted PDF {pdf.id}")
```

**FR-8.4: Orphaned Multipart Upload Cleanup**
```python
@shared_task
def cleanup_orphaned_multipart_uploads():
    """
    Abort multipart uploads that were initiated > 24 hours ago
    but never completed.
    Run daily via Celery Beat.
    """
    s3_client = boto3.client('s3', ...)
    
    # List all multipart uploads
    response = s3_client.list_multipart_uploads(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME
    )
    
    cutoff_date = timezone.now() - timedelta(hours=24)
    
    for upload in response.get('Uploads', []):
        if upload['Initiated'] < cutoff_date:
            s3_client.abort_multipart_upload(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=upload['Key'],
                UploadId=upload['UploadId']
            )
            logger.info(f"Aborted orphaned multipart upload: {upload['UploadId']}")
```

---

### 3.9 Error Handling & Retry Logic

**FR-9.1: Upload Failure Handling**
- Client receives 4xx/5xx error from presigned URL upload
- Client retries up to 3 times with exponential backoff (1s, 2s, 4s)
- If all retries fail, client calls `/api/v1/sources/pdfs/{upload_id}/abort/`
- Backend marks PDFUpload as failed, logs to audit log

**FR-9.2: Processing Failure Handling**
```python
@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,))
def process_uploaded_pdf(self, pdf_upload_id):
    try:
        # Processing logic
        pass
    except Exception as exc:
        # Log detailed error
        logger.error(f"PDF processing failed: {exc}", exc_info=True)
        
        # Update status
        pdf_upload = PDFUpload.objects.get(id=pdf_upload_id)
        pdf_upload.processing_status = 'failed'
        pdf_upload.save()
        
        # Send WebSocket notification
        # ...
        
        # Audit log
        AuditLog.objects.create(
            vault=pdf_upload.vault,
            user=pdf_upload.uploaded_by,
            action='pdf.processing_failed',
            details={'pdf_id': str(pdf_upload_id), 'error': str(exc)}
        )
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

---

## 4. Non-Functional Requirements

### 4.1 Performance
- Presigned URL generation: < 200ms (p95)
- Upload completion callback: < 500ms (p95)
- Post-upload processing: < 30s for 10MB files
- Storage usage cache TTL: 5 minutes
- Download URL generation: < 100ms (p95)

### 4.2 Security
- All presigned URLs use Signature Version 4 (SigV4)
- Upload URLs expire after 1 hour
- Download URLs expire after 15 minutes
- No public read ACLs (all files private by default)
- CSRF protection on all endpoints
- Rate limiting: 10 uploads/minute per user, 30 downloads/minute per user

### 4.3 Scalability
- Support 1000 concurrent uploads
- Handle vaults with 10,000+ PDFs
- Multipart uploads for files > 20MB (client-optional)
- Horizontal scaling via stateless API servers
- Celery workers auto-scale based on queue depth

### 4.4 Reliability
- 99.9% upload success rate
- Automatic retry on transient S3 errors (3 attempts)
- Dead letter queue for failed processing tasks
- Monitoring alerts for:
  - Failed uploads (> 5/minute)
  - Processing task queue depth (> 100)
  - S3 error rate (> 1%)

---

## 5. Technical Architecture

### 5.1 Component Diagram
```
[Client] 
  ↓ POST /pdfs/upload-url/
[Django API]
  ↓ boto3.generate_presigned_url()
[Cloudflare R2]
  ← presigned PUT URL (1hr expiry)
[Client]
  ↑ PUT {file} to presigned URL
[Cloudflare R2]
  ↓ POST /pdfs/{id}/complete/
[Django API]
  ↓ trigger Celery task
[Celery Worker]
  ↓ download file, extract metadata, generate thumbnail
  ↓ upload thumbnail to R2
  ↓ update PDFUpload record
  ↓ send WebSocket notification
[Client] ← "pdf.uploaded" event
```

### 5.2 File Flow

**Upload Flow:**
1. Client requests upload URL with vault_id, filename, file_size
2. Django validates permissions, creates PDFUpload record (status='pending')
3. Django generates presigned PUT URL (1hr expiry)
4. Client uploads file directly to R2 using presigned URL
5. Client calls completion callback with file_key
6. Django updates PDFUpload status to 'processing', triggers Celery task
7. Celery task extracts metadata, generates thumbnail, updates record
8. Celery task sends WebSocket notification, logs to audit log
9. Client receives "pdf.uploaded" event

**Download Flow:**
1. Client requests download URL for pdf_id
2. Django validates permissions
3. Django generates presigned GET URL (15min expiry)
4. Client downloads file directly from R2 using presigned URL
5. Django logs download event to audit log

**Deletion Flow:**
1. Client calls DELETE /pdfs/{id}/
2. Django validates permissions
3. Django sets deleted_at timestamp (soft-delete)
4. Django updates storage usage, logs to audit log
5. Scheduled Celery task (daily) permanently deletes files after 30 days

---

### 5.3 Database Schema

```sql
-- PDFUploads table
CREATE TABLE pdf_uploads (
    id UUID PRIMARY KEY,
    vault_id UUID NOT NULL REFERENCES vaults(id) ON DELETE CASCADE,
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    
    file VARCHAR(255) NOT NULL,  -- S3 key
    original_filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) DEFAULT 'application/pdf',
    
    uploaded_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    processing_status VARCHAR(20) DEFAULT 'pending',
    
    pdf_title VARCHAR(500),
    pdf_author VARCHAR(500),
    page_count INTEGER,
    thumbnail_url TEXT,
    
    deleted_at TIMESTAMP,
    
    INDEX idx_vault_deleted (vault_id, deleted_at),
    INDEX idx_user_deleted (uploaded_by, deleted_at)
);

-- VaultStorageUsage table
CREATE TABLE vault_storage_usage (
    vault_id UUID PRIMARY KEY REFERENCES vaults(id) ON DELETE CASCADE,
    total_bytes BIGINT DEFAULT 0,
    file_count INTEGER DEFAULT 0,
    user_breakdown JSONB DEFAULT '{}',
    last_updated TIMESTAMP DEFAULT NOW()
);
```

---

### 5.4 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/sources/pdfs/upload-url/` | Generate presigned upload URL | JWT |
| POST | `/api/v1/sources/pdfs/{id}/complete/` | Mark upload as complete | JWT |
| GET | `/api/v1/sources/pdfs/{id}/download-url/` | Generate presigned download URL | JWT |
| DELETE | `/api/v1/sources/pdfs/{id}/` | Soft-delete PDF | JWT |
| POST | `/api/v1/sources/pdfs/multipart-upload/initiate/` | Initiate multipart upload | JWT |
| POST | `/api/v1/sources/pdfs/multipart-upload/{id}/complete/` | Complete multipart upload | JWT |
| GET | `/api/v1/vaults/{id}/storage/` | Get vault storage usage | JWT |

---

### 5.5 Celery Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `process_uploaded_pdf` | On-demand | Extract metadata, generate thumbnail |
| `cleanup_deleted_pdfs` | Daily 2am | Permanently delete soft-deleted files after 30 days |
| `cleanup_orphaned_multipart_uploads` | Daily 3am | Abort multipart uploads > 24hrs old |
| `recalculate_vault_storage` | Weekly | Audit and recalculate storage usage for all vaults |

---

## 6. Dependencies

### 6.1 Python Packages
```txt
# Add to backend/requirements.txt
django-storages[s3]>=1.14
boto3>=1.35
python-magic>=0.4.27
pypdf>=5.3.1
Pillow>=11.2.0  # For thumbnail generation
pdf2image>=1.17  # Alternative for thumbnail
```

### 6.2 System Dependencies
```bash
# Ubuntu/Debian
apt-get install libmagic1 poppler-utils

# macOS
brew install libmagic poppler
```

### 6.3 External Services
- **Cloudflare R2**: S3-compatible object storage
- **Redis**: Celery broker, cache backend
- **PostgreSQL**: Primary database

---

## 7. Configuration

### 7.1 Environment Variables
```bash
# backend/.env
AWS_S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
AWS_ACCESS_KEY_ID=<r2-access-key>
AWS_SECRET_ACCESS_KEY=<r2-secret-key>
AWS_STORAGE_BUCKET_NAME=syncscript-pdfs
AWS_S3_REGION_NAME=auto  # R2 uses 'auto'
AWS_S3_SIGNATURE_VERSION=s3v4
AWS_DEFAULT_ACL=None  # Private by default
```

### 7.2 Django Settings
```python
# backend/config/settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 900  # 15 minutes default

# Custom upload path function
def pdf_upload_path(instance, filename):
    return f"vaults/{instance.vault_id}/pdfs/{instance.id}.pdf"
```

### 7.3 Celery Beat Schedule
```python
# backend/config/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-deleted-pdfs': {
        'task': 'apps.sources.tasks.cleanup_deleted_pdfs',
        'schedule': crontab(hour=2, minute=0),  # 2am daily
    },
    'cleanup-orphaned-multipart-uploads': {
        'task': 'apps.sources.tasks.cleanup_orphaned_multipart_uploads',
        'schedule': crontab(hour=3, minute=0),  # 3am daily
    },
    'recalculate-vault-storage': {
        'task': 'apps.sources.tasks.recalculate_vault_storage',
        'schedule': crontab(day_of_week=0, hour=4, minute=0),  # Sunday 4am
    },
}
```

---

## 8. Testing Strategy

### 8.1 Unit Tests
```python
# backend/apps/sources/tests/test_storage.py
class PDFUploadTests(TestCase):
    def test_generate_presigned_upload_url(self):
        # Test URL generation with valid vault
        
    def test_generate_presigned_download_url(self):
        # Test URL generation with permissions
        
    def test_pdf_validation_rejects_non_pdf(self):
        # Test validator rejects .txt file
        
    def test_pdf_validation_rejects_corrupted_pdf(self):
        # Test validator rejects corrupted PDF
        
    def test_soft_delete_excludes_from_listings(self):
        # Test soft-deleted PDFs not in queryset
        
    def test_storage_usage_calculation(self):
        # Test accurate byte calculation per vault
```

### 8.2 Integration Tests
```python
class PDFUploadIntegrationTests(TestCase):
    def test_complete_upload_flow(self):
        # 1. Request upload URL
        # 2. Simulate S3 upload (mock)
        # 3. Call completion callback
        # 4. Verify Celery task triggered
        # 5. Verify WebSocket notification sent
        
    def test_multipart_upload_flow(self):
        # 1. Initiate multipart upload
        # 2. Upload parts (mock)
        # 3. Complete multipart upload
        # 4. Verify file assembled correctly
```

### 8.3 Load Tests
- Upload 100 PDFs concurrently
- Generate 1000 presigned URLs/second
- Test Celery worker throughput (PDFs processed/minute)

---

## 9. Monitoring & Observability

### 9.1 Metrics to Track
- **Upload Success Rate**: `(completed_uploads / initiated_uploads) * 100`
- **Processing Time**: p50, p95, p99 for Celery task duration
- **Storage Growth**: Bytes added per day
- **Error Rate**: Failed uploads, failed processing tasks
- **Presigned URL Generation Time**: p95 latency

### 9.2 Alerts
- Upload success rate < 95% (5 min window)
- Processing task queue depth > 100
- S3 error rate > 1% (1 min window)
- Orphaned multipart uploads > 50

### 9.3 Logging
```python
import logging
logger = logging.getLogger(__name__)

# Log all upload events
logger.info(f"PDF upload initiated: vault={vault_id}, file={filename}, user={user_id}")

# Log processing events
logger.info(f"PDF processing started: pdf_id={pdf_id}")
logger.info(f"PDF processing completed: pdf_id={pdf_id}, duration={duration}s")

# Log errors with context
logger.error(f"PDF processing failed: pdf_id={pdf_id}, error={exc}", exc_info=True)
```

---

## 10. Security Considerations

### 10.1 Threat Model
- **Threat**: Unauthorized file access
  - **Mitigation**: All files private by default, presigned URLs with short expiry, permission checks before URL generation
  
- **Threat**: Malicious file upload (malware, XSS payloads)
  - **Mitigation**: Strict PDF validation (magic number, structure parsing), content-type enforcement, no direct execution
  
- **Threat**: Storage quota abuse
  - **Mitigation**: File size limit (50MB), rate limiting on uploads, storage tracking (no enforcement initially, future enhancement)
  
- **Threat**: Presigned URL leakage
  - **Mitigation**: Short expiry times, HTTPS-only, no logging of full URLs

### 10.2 Access Control
- Upload URL generation: Requires vault CONTRIBUTOR or OWNER role
- Download URL generation: Requires vault VIEWER, CONTRIBUTOR, or OWNER role
- Delete: Requires vault OWNER role or uploaded_by match

---

## 11. Future Enhancements (Out of Scope)

- **Storage Quota Enforcement**: Hard limits per vault with upgrade paths
- **File Versioning**: Track PDF revisions with restore functionality
- **OCR Processing**: Extract text from scanned PDFs
- **Full-Text Search**: Elasticsearch integration for PDF content search
- **Batch Operations**: Bulk upload, bulk delete, zip downloads
- **Virus Scanning**: ClamAV integration for malware detection
- **CDN Integration**: CloudFlare CDN for faster global access
- **Collaborative Annotations**: Real-time PDF annotation sync

---

## 12. Acceptance Criteria Summary

**Sprint Goal**: Researchers can securely upload, download, and manage PDFs in their Knowledge Vaults with automatic metadata extraction.

**Definition of Done:**
- [ ] Django models created and migrated (PDFUpload, VaultStorageUsage)
- [ ] django-storages configured with Cloudflare R2
- [ ] Presigned URL endpoints implemented (upload, download)
- [ ] PDF validation enforces MIME type, magic number, structure parsing
- [ ] Multipart upload endpoints functional (initiate, complete)
- [ ] Post-upload Celery task extracts metadata and generates thumbnail
- [ ] Soft-delete implementation with 30-day retention
- [ ] Storage usage tracking per vault and per user
- [ ] Orphaned multipart upload cleanup scheduled task
- [ ] WebSocket notifications on upload/delete events
- [ ] Audit logging for all file operations
- [ ] Unit tests > 80% coverage
- [ ] Integration tests for full upload/download flows
- [ ] API documentation updated (OpenAPI/Swagger)
- [ ] Manual verification tasks documented in `.planning/MANUAL_VERIFICATION.md`
- [ ] Environment variable setup documented in `.planning/USER_SETUP.md`

---

## 13. Implementation Notes

### 13.1 File Locations
```
backend/
├── apps/sources/
│   ├── models.py              # PDFUpload, VaultStorageUsage models
│   ├── serializers.py         # PDF serializers
│   ├── views.py               # Upload/download/delete endpoints
│   ├── storage.py             # Presigned URL generation utilities
│   ├── validators.py          # PDF validation logic
│   ├── tasks.py               # Celery tasks (processing, cleanup)
│   ├── urls.py                # PDF API routes
│   └── tests/
│       ├── test_storage.py    # Storage utility tests
│       ├── test_views.py      # API endpoint tests
│       └── test_tasks.py      # Celery task tests
├── config/
│   ├── settings.py            # Django storages config
│   └── celery.py              # Celery Beat schedule
```

### 13.2 Migration Order
1. Create PDFUpload model migration
2. Create VaultStorageUsage model migration
3. Run migrations: `python manage.py migrate`
4. Configure R2 credentials in `.env`
5. Test presigned URL generation locally
6. Deploy Celery worker with new tasks
7. Configure Celery Beat schedule

### 13.3 Testing Checklist
- [ ] Upload PDF < 50MB via presigned URL
- [ ] Upload PDF > 50MB via multipart upload
- [ ] Download PDF with valid permissions
- [ ] Reject non-PDF file upload
- [ ] Reject corrupted PDF upload
- [ ] Verify metadata extraction (title, author, page count)
- [ ] Verify thumbnail generation
- [ ] Soft-delete PDF and confirm exclusion from listings
- [ ] Verify storage usage calculation accuracy
- [ ] Test orphaned multipart upload cleanup
- [ ] Test WebSocket notification on upload
- [ ] Test audit log entries for all operations

---

## 14. Rollout Plan

### Phase 1: Core Upload/Download (Week 1)
- Implement PDFUpload model and migrations
- Configure django-storages with R2
- Build presigned URL endpoints (upload, download)
- Basic PDF validation (MIME type only)
- Manual testing with Postman

### Phase 2: Processing & Metadata (Week 2)
- Implement post-upload Celery task
- Add metadata extraction (pypdf)
- Generate first-page thumbnails
- WebSocket notifications
- Unit tests for processing logic

### Phase 3: Advanced Features (Week 3)
- Multipart upload support
- Strict PDF validation (magic number, structure)
- Storage usage tracking
- Soft-delete with scheduled cleanup
- Integration tests

### Phase 4: Monitoring & Optimization (Week 4)
- Add logging and metrics
- Configure alerts
- Load testing (100 concurrent uploads)
- Performance optimization (caching, query optimization)
- Documentation and deployment

---

## 15. Open Questions

1. **Storage Quota Limits**: Should we enforce hard limits now or just track usage? (Decision: Track only, no enforcement initially)
2. **Thumbnail Format**: JPEG or PNG for thumbnails? (Decision: JPEG, 80% quality, max 300px width)
3. **Virus Scanning**: Integrate ClamAV now or later? (Decision: Future enhancement, out of scope for MVP)
4. **CDN**: Use CloudFlare CDN in front of R2? (Decision: Not initially, evaluate after load testing)

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-14  
**Author**: SyncScript Team  
**Reviewers**: Backend Lead, DevOps Lead  
**Status**: Ready for Review