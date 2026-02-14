"""
Celery tasks for processing uploaded PDFs.

This module contains background tasks for extracting metadata,
generating thumbnails, and processing PDF files after upload.
"""
import io
import logging
import uuid
from typing import Any

import boto3
from celery import shared_task
from django.conf import settings
from pdf2image import convert_from_bytes
from PIL import Image
from pypdf import PdfReader

from apps.sources.models import PDFUpload

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

        # Mark as failed in database
        try:
            pdf_upload = PDFUpload.objects.get(id=pdf_upload_id)
            pdf_upload.processing_status = 'failed'
            pdf_upload.save(update_fields=['processing_status'])
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
