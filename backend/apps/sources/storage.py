"""
Storage utilities for generating presigned S3 URLs for file uploads and downloads.

This module provides helper functions to generate secure, time-limited URLs for:
- Direct browser uploads to S3/R2 storage
- Secure downloads with proper content-disposition headers
"""

import uuid
from typing import Tuple
from django.conf import settings
import boto3
from botocore.client import Config


def get_s3_client():
    """
    Get configured boto3 S3 client with credentials from settings.

    Returns:
        boto3 S3 client configured with Cloudflare R2 or AWS S3 endpoint.

    Raises:
        ValueError: If S3 is not configured (USE_S3=False).
    """
    if not settings.USE_S3:
        raise ValueError("S3 storage is not configured. Set AWS credentials in environment variables.")

    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        region_name=settings.AWS_S3_REGION_NAME,
        config=Config(signature_version='s3v4')
    )


def generate_presigned_upload_url(
    vault_id: str,
    filename: str,
    content_type: str
) -> Tuple[str, str]:
    """
    Generate a presigned URL for uploading a PDF file directly to S3.

    Args:
        vault_id: UUID of the vault (used in S3 key path)
        filename: Original filename (used to generate unique key)
        content_type: MIME type of the file (should be 'application/pdf')

    Returns:
        Tuple of (presigned_url, file_key):
            - presigned_url: Time-limited URL for PUT upload (expires in 1 hour)
            - file_key: S3 object key where file will be stored

    Example:
        >>> url, key = generate_presigned_upload_url(
        ...     vault_id='abc123',
        ...     filename='research.pdf',
        ...     content_type='application/pdf'
        ... )
        >>> # Client uploads file to `url` via PUT request
        >>> # File is stored at `vaults/abc123/pdfs/{uuid}.pdf`
    """
    s3_client = get_s3_client()

    # Generate unique file key using UUID to prevent collisions
    file_extension = filename.split('.')[-1] if '.' in filename else 'pdf'
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_key = f"vaults/{vault_id}/pdfs/{unique_filename}"

    # Generate presigned URL for PUT operation (upload)
    # Expires in 1 hour (3600 seconds) as per acceptance criteria
    presigned_url = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': file_key,
            'ContentType': content_type,
        },
        ExpiresIn=3600,  # 1 hour expiration
    )

    return presigned_url, file_key


def generate_presigned_download_url(
    file_key: str,
    original_filename: str
) -> str:
    """
    Generate a presigned URL for downloading a file from S3.

    Args:
        file_key: S3 object key (e.g., 'vaults/abc123/pdfs/file.pdf')
        original_filename: Original filename to use in Content-Disposition header

    Returns:
        Presigned URL for GET download (expires in 15 minutes).
        Includes Content-Disposition header to trigger browser download with original filename.

    Example:
        >>> url = generate_presigned_download_url(
        ...     file_key='vaults/abc123/pdfs/uuid.pdf',
        ...     original_filename='My Research Paper.pdf'
        ... )
        >>> # Client downloads file from `url` via GET request
        >>> # Browser saves file as 'My Research Paper.pdf'
    """
    s3_client = get_s3_client()

    # Generate presigned URL for GET operation (download)
    # Expires in 15 minutes (900 seconds) as per acceptance criteria
    # Content-Disposition=attachment triggers download instead of inline display
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': file_key,
            'ResponseContentDisposition': f'attachment; filename="{original_filename}"',
        },
        ExpiresIn=900,  # 15 minutes expiration
    )

    return presigned_url


def initiate_multipart_upload(
    vault_id: str,
    filename: str,
    file_size: int,
    part_size: int,
    content_type: str
) -> Tuple[str, str, list]:
    """
    Initiate a multipart upload to S3 and generate presigned URLs for each part.

    Args:
        vault_id: UUID of the vault (used in S3 key path)
        filename: Original filename (used to generate unique key)
        file_size: Total file size in bytes
        part_size: Size of each part in bytes (minimum 5MB except last part)
        content_type: MIME type of the file (should be 'application/pdf')

    Returns:
        Tuple of (upload_id, file_key, part_urls):
            - upload_id: S3 multipart upload ID (required for completion)
            - file_key: S3 object key where file will be stored
            - part_urls: List of dicts with {part_number, upload_url} for each part

    Example:
        >>> upload_id, key, parts = initiate_multipart_upload(
        ...     vault_id='abc123',
        ...     filename='large.pdf',
        ...     file_size=30000000,  # 30MB
        ...     part_size=10000000,  # 10MB per part
        ...     content_type='application/pdf'
        ... )
        >>> # Client uploads each part to corresponding part_url
        >>> # Then calls complete endpoint with upload_id and ETags
    """
    s3_client = get_s3_client()

    # Generate unique file key using UUID to prevent collisions
    file_extension = filename.split('.')[-1] if '.' in filename else 'pdf'
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_key = f"vaults/{vault_id}/pdfs/{unique_filename}"

    # Initiate multipart upload
    response = s3_client.create_multipart_upload(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=file_key,
        ContentType=content_type
    )
    upload_id = response['UploadId']

    # Calculate number of parts needed
    num_parts = (file_size + part_size - 1) // part_size  # Ceiling division

    # Generate presigned URL for each part
    part_urls = []
    for part_number in range(1, num_parts + 1):
        presigned_url = s3_client.generate_presigned_url(
            'upload_part',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': file_key,
                'PartNumber': part_number,
                'UploadId': upload_id,
            },
            ExpiresIn=3600,  # 1 hour expiration (same as regular upload)
        )
        part_urls.append({
            'part_number': part_number,
            'upload_url': presigned_url
        })

    return upload_id, file_key, part_urls


def complete_multipart_upload(
    file_key: str,
    upload_id: str,
    parts: list
) -> None:
    """
    Complete a multipart upload to S3 by combining all uploaded parts.

    Args:
        file_key: S3 object key where file is being stored
        upload_id: S3 multipart upload ID from initiate_multipart_upload
        parts: List of dicts with {part_number, etag} for each uploaded part

    Raises:
        Exception: If S3 multipart upload completion fails

    Example:
        >>> complete_multipart_upload(
        ...     file_key='vaults/abc123/pdfs/uuid.pdf',
        ...     upload_id='xyz789',
        ...     parts=[
        ...         {'part_number': 1, 'etag': 'etag1'},
        ...         {'part_number': 2, 'etag': 'etag2'}
        ...     ]
        ... )
        >>> # File is now available at file_key in S3
    """
    s3_client = get_s3_client()

    # Format parts for S3 API (expects 'PartNumber' and 'ETag' capitalized)
    formatted_parts = [
        {
            'PartNumber': part['part_number'],
            'ETag': part['etag']
        }
        for part in parts
    ]

    # Sort parts by part number (S3 requires this)
    formatted_parts.sort(key=lambda x: x['PartNumber'])

    # Complete the multipart upload
    s3_client.complete_multipart_upload(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=file_key,
        UploadId=upload_id,
        MultipartUpload={'Parts': formatted_parts}
    )
