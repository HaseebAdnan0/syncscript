"""
Celery tasks for processing uploaded PDFs.

This module contains background tasks for extracting metadata,
generating thumbnails, and processing PDF files after upload.
"""
import io
import logging
import uuid
from datetime import timedelta
from typing import Any

import boto3
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from pdf2image import convert_from_bytes
from PIL import Image
from pypdf import PdfReader

from apps.sources.models import PDFUpload
from apps.vaults.models import AuditLog
from core.websocket_utils import broadcast_to_vault

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_uploaded_pdf(self, pdf_upload_id: str) -> dict[str, Any]:
    """
    Process an uploaded PDF: extract metadata and generate thumbnail.

    This task downloads the PDF from S3, extracts title, author, and page count
    from the PDF metadata, generates a thumbnail from the first page, and updates
    the PDFUpload record.

    Args:
        self: Celery task instance (bound task)
        pdf_upload_id: UUID of the PDFUpload record to process

    Returns:
        dict with processing results:
            - pdf_id: UUID of the processed PDF
            - status: 'completed' or 'failed'
            - metadata: Extracted metadata (title, author, page_count)
            - thumbnail_url: URL to the generated thumbnail
            - error: Error message if failed

    Raises:
        Retry exception on transient failures (network, S3 errors)
    """
    try:
        # Fetch the PDFUpload record
        pdf_upload = PDFUpload.objects.get(id=pdf_upload_id)

        # Download PDF from S3
        s3_client = boto3.client(
            's3',
            endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'auto'),
        )

        # Get the file key (path in S3)
        file_key = pdf_upload.file.name

        # Download file into memory
        pdf_bytes = io.BytesIO()
        s3_client.download_fileobj(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=file_key,
            Fileobj=pdf_bytes,
        )
        pdf_bytes.seek(0)  # Reset to beginning

        # Parse PDF and extract metadata
        reader = PdfReader(pdf_bytes)

        # Extract metadata
        metadata = reader.metadata or {}
        pdf_title = metadata.get('/Title') or metadata.get('/Subject') or pdf_upload.original_filename
        pdf_author = metadata.get('/Author')
        page_count = len(reader.pages)

        # Extract full text from all pages (US-002)
        extracted_text_parts = []
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text:
                    extracted_text_parts.append(f"\n--- Page {page_num} ---\n{page_text}")
            except Exception as page_exc:
                logger.warning(
                    f"Failed to extract text from page {page_num} of PDF {pdf_upload_id}: {page_exc}"
                )
                continue

        # Concatenate all text
        extracted_text = ''.join(extracted_text_parts)

        # Truncate to 500KB max to prevent DB bloat
        max_text_size = 500 * 1024  # 500KB
        if len(extracted_text) > max_text_size:
            extracted_text = extracted_text[:max_text_size]
            logger.info(
                f"Truncated extracted text for PDF {pdf_upload_id} from "
                f"{len(extracted_text)} to {max_text_size} bytes"
            )

        logger.info(
            f"Extracted {len(extracted_text)} characters of text from "
            f"{page_count} pages of PDF {pdf_upload_id}"
        )

        # Generate thumbnail from first page
        thumbnail_url = None
        try:
            # Reset pdf_bytes to beginning for thumbnail generation
            pdf_bytes.seek(0)

            # Convert first page to image (max 300px width)
            images = convert_from_bytes(
                pdf_bytes.read(),
                first_page=1,
                last_page=1,
                dpi=72,  # Lower DPI for thumbnails
                size=(300, None),  # Width 300px, height proportional
            )

            if images:
                # Get first (and only) page
                thumbnail = images[0]

                # Convert to JPEG with 80% quality
                thumb_bytes = io.BytesIO()
                thumbnail.save(thumb_bytes, format='JPEG', quality=80, optimize=True)
                thumb_bytes.seek(0)

                # Upload thumbnail to S3
                thumb_uuid = uuid.uuid4()
                thumb_key = f"vaults/{pdf_upload.vault_id}/thumbnails/{thumb_uuid}.jpg"

                s3_client.upload_fileobj(
                    thumb_bytes,
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=thumb_key,
                    ExtraArgs={
                        'ContentType': 'image/jpeg',
                    }
                )

                # Generate presigned URL for thumbnail (7-day expiry)
                thumbnail_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                        'Key': thumb_key,
                    },
                    ExpiresIn=7 * 24 * 60 * 60,  # 7 days
                )

                logger.info(f"Generated thumbnail for PDF {pdf_upload_id} at {thumb_key}")

        except Exception as thumb_exc:
            # Log thumbnail generation error but don't fail the entire task
            logger.warning(
                f"Failed to generate thumbnail for PDF {pdf_upload_id}: {thumb_exc}",
                exc_info=True,
            )

        # Update PDFUpload record
        pdf_upload.pdf_title = str(pdf_title) if pdf_title else pdf_upload.original_filename
        pdf_upload.pdf_author = str(pdf_author) if pdf_author else None
        pdf_upload.page_count = page_count
        pdf_upload.thumbnail_url = thumbnail_url
        pdf_upload.processing_status = 'completed'
        pdf_upload.save(update_fields=['pdf_title', 'pdf_author', 'page_count', 'thumbnail_url', 'processing_status'])

        logger.info(
            f"Successfully processed PDF {pdf_upload_id}: "
            f"title={pdf_upload.pdf_title}, pages={page_count}"
        )

        # Send WebSocket notification to vault (US-020)
        try:
            broadcast_to_vault(
                vault_id=pdf_upload.vault_id,
                event_type='pdf.uploaded',
                payload={
                    'pdf_id': str(pdf_upload.id),
                    'filename': pdf_upload.original_filename,
                    'pdf_title': pdf_upload.pdf_title,
                    'page_count': page_count,
                    'thumbnail_url': thumbnail_url,
                },
                user=pdf_upload.uploaded_by,
            )
        except Exception as ws_exc:
            # Log but don't fail the task if WebSocket broadcast fails
            logger.warning(
                f"Failed to send WebSocket notification for PDF {pdf_upload_id}: {ws_exc}",
                exc_info=True,
            )

        # Log pdf.uploaded event to audit log (US-021)
        try:
            AuditLog.objects.create(
                vault=pdf_upload.vault,
                actor=pdf_upload.uploaded_by,
                action='pdf.uploaded',
                metadata={
                    'pdf_id': str(pdf_upload.id),
                    'filename': pdf_upload.original_filename,
                    'pdf_title': pdf_upload.pdf_title,
                    'file_size': pdf_upload.file_size,
                    'page_count': page_count,
                }
            )
        except Exception as audit_exc:
            # Log but don't fail the task if audit logging fails
            logger.warning(
                f"Failed to create audit log for PDF {pdf_upload_id}: {audit_exc}",
                exc_info=True,
            )

        return {
            'pdf_id': str(pdf_upload.id),
            'status': 'completed',
            'metadata': {
                'title': pdf_upload.pdf_title,
                'author': pdf_upload.pdf_author,
                'page_count': page_count,
            },
            'thumbnail_url': thumbnail_url,
        }

    except PDFUpload.DoesNotExist:
        logger.error(f"PDFUpload {pdf_upload_id} not found")
        return {
            'pdf_id': pdf_upload_id,
            'status': 'failed',
            'error': 'PDFUpload record not found',
        }

    except Exception as exc:
        # Log the error
        logger.error(
            f"Error processing PDF {pdf_upload_id}: {exc}",
            exc_info=True,
        )

        # Mark as failed in database and log to audit
        try:
            pdf_upload = PDFUpload.objects.get(id=pdf_upload_id)
            pdf_upload.processing_status = 'failed'
            pdf_upload.save(update_fields=['processing_status'])

            # Log pdf.processing_failed event to audit log (US-021)
            try:
                AuditLog.objects.create(
                    vault=pdf_upload.vault,
                    actor=pdf_upload.uploaded_by,
                    action='pdf.processing_failed',
                    metadata={
                        'pdf_id': str(pdf_upload.id),
                        'filename': pdf_upload.original_filename,
                        'error': str(exc),
                        'retries': self.request.retries,
                    }
                )
            except Exception as audit_exc:
                # Log but don't fail further if audit logging fails
                logger.warning(
                    f"Failed to create audit log for failed PDF {pdf_upload_id}: {audit_exc}",
                    exc_info=True,
                )
        except Exception:
            pass

        # Retry with exponential backoff
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries * 60)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for PDF {pdf_upload_id}")
            return {
                'pdf_id': pdf_upload_id,
                'status': 'failed',
                'error': str(exc),
            }


# WebSocket broadcast tasks (implemented in US-013)
@shared_task
def broadcast_source_created(source_id: int) -> None:
    """
    Broadcast source.created event to vault collaborators.

    Args:
        source_id: ID of the newly created Source
    """
    from apps.sources.models import Source  # type: ignore[import-not-found]
    from core.websocket_utils import broadcast_to_vault  # type: ignore[import-not-found]

    try:
        source = Source.objects.select_related('created_by', 'vault').get(id=source_id)

        payload = {
            'id': source.id,  # type: ignore[attr-defined]
            'url': source.url,
            'title': source.title,
            'description': source.description,
            'source_type': source.source_type,
            'created_by': {
                'id': source.created_by.id if source.created_by else None,  # type: ignore[attr-defined]
                'username': source.created_by.username if source.created_by else None,  # type: ignore[attr-defined]
            },
            'created_at': source.created_at.isoformat(),
        }

        broadcast_to_vault(
            vault_id=source.vault.id,  # type: ignore[attr-defined]
            event_type='source.created',
            payload=payload,
            user=source.created_by,
        )
        logger.info(f"Broadcasted source.created for source {source_id} in vault {source.vault.id}")  # type: ignore[attr-defined]

    except Source.DoesNotExist:
        logger.error(f"Source {source_id} not found for broadcast")


@shared_task
def broadcast_source_updated(source_id: int, changed_fields: list[str]) -> None:
    """
    Broadcast source.updated event to vault collaborators.

    Args:
        source_id: ID of the updated Source
        changed_fields: List of field names that were changed
    """
    from apps.sources.models import Source  # type: ignore[import-not-found]
    from core.websocket_utils import broadcast_to_vault  # type: ignore[import-not-found]

    try:
        source = Source.objects.select_related('created_by', 'vault').get(id=source_id)

        payload = {
            'id': source.id,  # type: ignore[attr-defined]
            'url': source.url,
            'title': source.title,
            'description': source.description,
            'source_type': source.source_type,
            'changed_fields': changed_fields,
            'updated_at': source.updated_at.isoformat(),
        }

        broadcast_to_vault(
            vault_id=source.vault.id,  # type: ignore[attr-defined]
            event_type='source.updated',
            payload=payload,
            user=None,  # Updated by might not be tracked
        )
        logger.info(f"Broadcasted source.updated for source {source_id} in vault {source.vault.id}")  # type: ignore[attr-defined]

    except Source.DoesNotExist:
        logger.error(f"Source {source_id} not found for broadcast")


@shared_task
def broadcast_source_deleted(source_id: int, vault_id: int, deleted_by_id: int | None) -> None:
    """
    Broadcast source.deleted event to vault collaborators.

    Args:
        source_id: ID of the deleted Source
        vault_id: ID of the vault the source belonged to
        deleted_by_id: ID of the user who deleted the source (optional)
    """
    from django.contrib.auth import get_user_model
    from core.websocket_utils import broadcast_to_vault  # type: ignore[import-not-found]

    User = get_user_model()

    payload: dict[str, Any] = {
        'id': source_id,
        'vault_id': vault_id,
    }

    # Fetch user if deleted_by_id provided
    deleted_by = None
    if deleted_by_id:
        try:
            deleted_by = User.objects.get(id=deleted_by_id)
            payload['deleted_by'] = {
                'id': deleted_by.id,  # type: ignore[attr-defined]
                'username': deleted_by.username,  # type: ignore[attr-defined]
            }
        except User.DoesNotExist:
            logger.warning(f"User {deleted_by_id} not found for source deletion broadcast")

    broadcast_to_vault(
        vault_id=vault_id,
        event_type='source.deleted',
        payload=payload,
        user=deleted_by,
    )
    logger.info(f"Broadcasted source.deleted for source {source_id} in vault {vault_id}")


@shared_task
def cleanup_deleted_pdfs() -> dict[str, Any]:
    """
    Permanently delete PDFs that were soft-deleted more than 30 days ago.

    This task runs daily to clean up storage by:
    1. Querying PDFUploads where deleted_at < 30 days ago
    2. Deleting the PDF file from S3
    3. Deleting the thumbnail file from S3 (if exists)
    4. Deleting the database record

    Returns:
        dict with cleanup results:
            - deleted_count: Number of PDFs permanently deleted
            - errors: List of errors encountered during cleanup
    """
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Query soft-deleted PDFs older than 30 days
    pdfs_to_delete = PDFUpload.objects.filter(
        deleted_at__isnull=False,
        deleted_at__lt=thirty_days_ago,
    ).select_related('vault')

    deleted_count = 0
    errors = []

    # Initialize S3 client if we have PDFs to delete
    s3_client = None
    if pdfs_to_delete.exists() and getattr(settings, 'USE_S3', False):
        s3_client = boto3.client(
            's3',
            endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'auto'),
        )

    for pdf in pdfs_to_delete:
        try:
            # Delete PDF file from S3
            if s3_client and pdf.file:
                try:
                    s3_client.delete_object(
                        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                        Key=pdf.file.name,
                    )
                    logger.info(f"Deleted PDF file from S3: {pdf.file.name}")
                except Exception as s3_exc:
                    logger.warning(
                        f"Failed to delete PDF file {pdf.file.name} from S3: {s3_exc}",
                        exc_info=True,
                    )
                    errors.append({
                        'pdf_id': str(pdf.id),
                        'error': f"S3 delete failed: {s3_exc}",
                    })

            # Delete thumbnail from S3 if exists
            if s3_client and pdf.thumbnail_url:
                try:
                    # Extract thumbnail key from URL or construct it
                    # Thumbnail path: vaults/{vault_id}/thumbnails/{uuid}.jpg
                    # We need to extract the key from the file.name pattern
                    # The thumbnail key should be in the same vault folder
                    file_name = pdf.file.name if pdf.file else ''
                    if file_name:
                        # Extract vault_id and construct thumbnail path
                        # Assuming file_name is like: vaults/{vault_id}/pdfs/{uuid}.pdf
                        parts = file_name.split('/')
                        if len(parts) >= 3 and parts[0] == 'vaults':
                            vault_id_str = parts[1]
                            # Extract UUID from filename (without .pdf extension)
                            pdf_uuid = parts[-1].rsplit('.', 1)[0]
                            thumbnail_key = f"vaults/{vault_id_str}/thumbnails/{pdf_uuid}.jpg"

                            s3_client.delete_object(
                                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                Key=thumbnail_key,
                            )
                            logger.info(f"Deleted thumbnail from S3: {thumbnail_key}")
                except Exception as thumb_exc:
                    # Thumbnail deletion is best-effort, log but don't fail
                    logger.warning(
                        f"Failed to delete thumbnail for PDF {pdf.id}: {thumb_exc}",
                        exc_info=True,
                    )

            # Delete database record
            pdf_id = str(pdf.id)
            pdf_filename = pdf.original_filename
            pdf.delete()
            deleted_count += 1

            logger.info(
                f"Permanently deleted PDF {pdf_id} ({pdf_filename}) "
                f"from vault {pdf.vault_id}"
            )

        except Exception as exc:
            logger.error(
                f"Failed to delete PDF {pdf.id}: {exc}",
                exc_info=True,
            )
            errors.append({
                'pdf_id': str(pdf.id),
                'error': str(exc),
            })

    logger.info(
        f"Cleanup completed: {deleted_count} PDFs permanently deleted, "
        f"{len(errors)} errors"
    )

    return {
        'deleted_count': deleted_count,
        'errors': errors,
    }


@shared_task
def cleanup_orphaned_multipart_uploads() -> dict[str, Any]:
    """
    Clean up abandoned S3 multipart uploads to prevent storage waste.

    This task runs daily to abort multipart uploads that were initiated
    more than 24 hours ago and never completed. This prevents storage
    accumulation from abandoned uploads.

    Returns:
        dict with cleanup results:
            - aborted_count: Number of multipart uploads aborted
            - errors: List of errors encountered during cleanup
    """
    # Only run if S3 is enabled
    if not getattr(settings, 'USE_S3', False):
        logger.info("S3 not enabled, skipping multipart upload cleanup")
        return {
            'aborted_count': 0,
            'errors': [],
        }

    aborted_count = 0
    errors = []

    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'auto'),
        )

        # Calculate threshold (24 hours ago)
        threshold = timezone.now() - timedelta(hours=24)

        # List all in-progress multipart uploads
        # Note: list_multipart_uploads returns uploads for the entire bucket
        response = s3_client.list_multipart_uploads(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        )

        # Get uploads that are older than 24 hours
        uploads = response.get('Uploads', [])

        for upload in uploads:
            initiated = upload.get('Initiated')
            upload_id = upload.get('UploadId')
            key = upload.get('Key')

            # Skip if missing required fields
            if not initiated or not upload_id or not key:
                continue

            # Convert initiated datetime to timezone-aware datetime
            # boto3 returns timezone-aware datetime from S3 API
            if initiated < threshold:
                try:
                    # Abort the multipart upload
                    s3_client.abort_multipart_upload(
                        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                        Key=key,
                        UploadId=upload_id,
                    )

                    aborted_count += 1
                    logger.info(
                        f"Aborted orphaned multipart upload: "
                        f"key={key}, upload_id={upload_id}, "
                        f"initiated={initiated.isoformat()}"
                    )

                except Exception as abort_exc:
                    logger.error(
                        f"Failed to abort multipart upload {upload_id} for key {key}: {abort_exc}",
                        exc_info=True,
                    )
                    errors.append({
                        'upload_id': upload_id,
                        'key': key,
                        'error': str(abort_exc),
                    })

        logger.info(
            f"Multipart upload cleanup completed: {aborted_count} uploads aborted, "
            f"{len(errors)} errors"
        )

    except Exception as exc:
        logger.error(
            f"Error during multipart upload cleanup: {exc}",
            exc_info=True,
        )
        errors.append({
            'error': f"Cleanup failed: {exc}",
        })

    return {
        'aborted_count': aborted_count,
        'errors': errors,
    }
