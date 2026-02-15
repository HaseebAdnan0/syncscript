import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from dirtyfields import DirtyFieldsMixin

User = get_user_model()


class SourceType(models.TextChoices):
    URL = 'URL', 'URL'
    PDF = 'PDF', 'PDF'
    BOOK = 'BOOK', 'Book'
    JOURNAL = 'JOURNAL', 'Journal'
    DATASET = 'DATASET', 'Dataset'


class Source(DirtyFieldsMixin, models.Model):
    id: int  # Auto-generated primary key
    vault = models.ForeignKey(
        'vaults.Vault',
        on_delete=models.CASCADE,
        related_name='sources'
    )
    url = models.URLField(max_length=2048)
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True)
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.URL
    )
    metadata = models.JSONField(default=dict)
    ai_summary = models.JSONField(
        null=True,
        blank=True,
        help_text='AI-generated summary: {abstract, key_findings[], methodology, limitations, keywords[], generated_at}'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_sources'
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vault', 'is_deleted']),
            models.Index(fields=['source_type']),
            models.Index(fields=['created_at']),
            GinIndex(fields=['search_vector'], name='source_search_vector_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['vault', 'url'],
                condition=models.Q(is_deleted=False),
                name='unique_active_source_per_vault'
            )
        ]

    def __str__(self):
        return f"{self.title} ({self.source_type})"


class PDFUpload(models.Model):
    """
    Stores PDF file uploads within Knowledge Vaults.
    Tracks metadata, processing status, and supports soft-delete with 30-day retention.
    """
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vault = models.ForeignKey(
        'vaults.Vault',
        on_delete=models.CASCADE,
        related_name='pdf_uploads',
        db_index=True
    )
    source = models.ForeignKey(
        Source,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pdf_uploads'
    )
    file = models.FileField(upload_to='vaults/%Y/%m/%d/', max_length=500)
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text='File size in bytes')
    mime_type = models.CharField(max_length=100, default='application/pdf')

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_pdfs'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    # Extracted metadata
    pdf_title = models.CharField(max_length=500, blank=True)
    pdf_author = models.CharField(max_length=255, blank=True)
    page_count = models.IntegerField(null=True, blank=True)
    thumbnail_url = models.URLField(max_length=500, blank=True, null=True)
    extracted_text = models.TextField(blank=True, default='')

    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'pdf_uploads'
        indexes = [
            models.Index(fields=['vault', 'deleted_at']),
            models.Index(fields=['uploaded_by', 'deleted_at']),
        ]
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_filename}"


class FileUpload(models.Model):
    """
    Stores image and document file uploads within Knowledge Vaults.
    Supports PNG and JPG images with thumbnail generation.
    """
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('document', 'Document'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vault = models.ForeignKey(
        'vaults.Vault',
        on_delete=models.CASCADE,
        related_name='file_uploads',
        db_index=True
    )
    file = models.FileField(upload_to='vaults/%Y/%m/%d/', max_length=500)
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text='File size in bytes')
    mime_type = models.CharField(max_length=100)
    file_type = models.CharField(
        max_length=20,
        choices=FILE_TYPE_CHOICES,
        default='image'
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_files'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    thumbnail_url = models.URLField(max_length=500, blank=True, null=True)

    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'file_uploads'
        indexes = [
            models.Index(fields=['vault', 'deleted_at']),
            models.Index(fields=['uploaded_by', 'deleted_at']),
            models.Index(fields=['file_type']),
        ]
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_filename}"


class VaultStorageUsage(models.Model):
    """
    Caches storage usage statistics per vault for fast retrieval.
    Updated when files are uploaded or deleted.
    """
    vault = models.OneToOneField(
        'vaults.Vault',
        on_delete=models.CASCADE,
        related_name='storage_usage',
        primary_key=True
    )
    total_bytes = models.BigIntegerField(default=0, help_text='Total storage used in bytes')
    file_count = models.IntegerField(default=0, help_text='Number of non-deleted files')
    user_breakdown = models.JSONField(
        default=dict,
        help_text='Storage breakdown by user ID: {user_id: bytes}'
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vault_storage_usage'

    def __str__(self):
        return f"Storage for vault {self.vault.id if self.vault else 'Unknown'}: {self.total_bytes} bytes"
