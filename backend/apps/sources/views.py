from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers as drf_serializers
from django.shortcuts import get_object_or_404
from django.db import transaction
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from .models import PDFUpload, Source
from .serializers import (
    UploadURLRequestSerializer,
    UploadURLResponseSerializer,
    PDFUploadSerializer,
    SourceSerializer,
    BulkSourceSerializer,
    MultipartUploadRequestSerializer,
    MultipartUploadResponseSerializer,
    MultipartUploadCompleteRequestSerializer,
    MultipartUploadAbortRequestSerializer,
)
from .storage import (
    generate_presigned_upload_url,
    generate_presigned_download_url,
    initiate_multipart_upload,
    complete_multipart_upload,
    abort_multipart_upload,
)
from .services import extract_metadata
from .services.storage_quota import check_storage_quota
from .permissions import VaultSourcePermission
from .filters import SourceFilter
from .utils import update_vault_storage_usage
from apps.vaults.models import Vault, VaultMembership, RoleChoices, AuditLog
from datetime import datetime, timedelta
from django.utils import timezone
from core.websocket_utils import broadcast_to_vault
import logging

logger = logging.getLogger(__name__)


class PDFUploadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PDF upload operations (US-006).
    Handles presigned URL generation, upload completion, and downloads.
    Also provides nested route for listing vault PDFs (US-023).
    """
    queryset = PDFUpload.objects.filter(deleted_at__isnull=True)
    serializer_class = PDFUploadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Override get_queryset to filter by vault when accessed via nested route (US-023).

        For nested route /api/v1/vaults/{vault_id}/pdfs/:
        - Filters PDFs by vault_id
        - Excludes soft-deleted PDFs
        - Orders by uploaded_at descending

        For standard route /api/v1/sources/pdfs/:
        - Returns all accessible PDFs
        """
        user = self.request.user

        # Check if this is a nested route from /vaults/{vault_id}/pdfs/
        vault_pk = self.kwargs.get('vault_pk')

        if vault_pk:
            # Nested route: Verify permission and filter by specific vault
            self._check_vault_permission(
                vault_pk,
                user,
                required_roles=[RoleChoices.VIEWER, RoleChoices.CONTRIBUTOR, RoleChoices.OWNER]
            )

            return PDFUpload.objects.filter(
                vault_id=vault_pk,
                deleted_at__isnull=True
            ).order_by('-uploaded_at')

        # Standard route: Return all PDFs from accessible vaults
        # Get vaults where user is owner
        owned_vault_ids = Vault.objects.filter(owner=user).values_list('id', flat=True)

        # Get vaults where user is a member
        member_vault_ids = VaultMembership.objects.filter(user=user).values_list('vault_id', flat=True)

        # Combine both sets of vault IDs
        accessible_vault_ids = list(owned_vault_ids) + list(member_vault_ids)

        return PDFUpload.objects.filter(
            vault_id__in=accessible_vault_ids,
            deleted_at__isnull=True
        ).order_by('-uploaded_at')

    def _check_vault_permission(self, vault_id, user, required_roles=None):
        """
        Check if user has required permission on vault.

        Args:
            vault_id: UUID of the vault
            user: User instance
            required_roles: List of acceptable roles (defaults to [OWNER, CONTRIBUTOR])

        Returns:
            Vault instance if permission granted

        Raises:
            PermissionDenied if user doesn't have required permission
        """
        if required_roles is None:
            required_roles = [RoleChoices.OWNER, RoleChoices.CONTRIBUTOR]

        vault = get_object_or_404(Vault, id=vault_id)

        # Check if user is owner
        if vault.owner == user:
            return vault

        # Check if user has membership with required role
        membership = VaultMembership.objects.filter(
            vault=vault,
            user=user,
            role__in=required_roles
        ).first()

        if not membership:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to access this vault.")

        return vault

    @action(detail=False, methods=['post'], url_path='upload-url')
    @method_decorator(ratelimit(key='user', rate='10/m', method='POST'))
    def upload_url(self, request):
        """
        POST /api/v1/sources/pdfs/upload-url/

        Generate a presigned URL for uploading a PDF directly to S3/R2.
        Creates a pending PDFUpload record and returns upload credentials.

        Request body:
        - vault_id (UUID): Target vault
        - filename (str): Original filename
        - file_size (int): File size in bytes
        - content_type (str): MIME type (must be application/pdf)

        Response:
        - upload_id (UUID): PDFUpload record ID
        - upload_url (str): Presigned S3 URL for PUT upload
        - expires_in (int): URL expiration time in seconds
        - callback_url (str): Endpoint to call after upload completes
        """
        # Validate request data
        request_serializer = UploadURLRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        vault_id = request_serializer.validated_data['vault_id']
        filename = request_serializer.validated_data['filename']
        file_size = request_serializer.validated_data['file_size']
        content_type = request_serializer.validated_data['content_type']

        # Check user has contributor or owner permission on vault
        vault = self._check_vault_permission(vault_id, request.user)

        # Check storage quota before allowing upload
        quota_result = check_storage_quota(vault_id)
        if quota_result['exceeded']:
            return Response({
                'error': 'Storage quota exceeded',
                'used_bytes': quota_result['used_bytes'],
                'limit_bytes': quota_result['limit_bytes'],
                'percentage': round(quota_result['percentage'] * 100, 2)
            }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        # Generate presigned upload URL
        upload_url, file_key = generate_presigned_upload_url(
            vault_id=str(vault_id),
            filename=filename,
            content_type=content_type
        )

        # Create PDFUpload record with status='pending'
        pdf_upload = PDFUpload.objects.create(
            vault=vault,
            file=file_key,  # Store the S3 key in the file field
            original_filename=filename,
            file_size=file_size,
            mime_type=content_type,
            uploaded_by=request.user,
            processing_status='pending'
        )

        # Prepare response
        response_data = {
            'upload_id': pdf_upload.id,
            'upload_url': upload_url,
            'file_key': file_key,
            'expires_in': 3600,  # 1 hour
            'callback_url': f'/api/v1/sources/pdfs/{pdf_upload.id}/complete/'
        }

        response_serializer = UploadURLResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """
        POST /api/v1/sources/pdfs/{upload_id}/complete/

        Mark upload as complete and trigger post-processing.
        Called by client after successfully uploading file to S3.

        Request body:
        - file_key (str): S3 object key where file was uploaded

        Response:
        - pdf_id (UUID): PDFUpload record ID
        - status (str): Processing status
        - message (str): Success message
        """
        # Validate request
        class CompletionRequestSerializer(drf_serializers.Serializer):
            file_key = drf_serializers.CharField(required=True)

        request_serializer = CompletionRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        file_key = request_serializer.validated_data['file_key']

        # Get PDFUpload record
        pdf_upload = get_object_or_404(PDFUpload, id=pk)

        # Verify user has permission (must be uploader or vault owner/contributor)
        self._check_vault_permission(pdf_upload.vault.id, request.user)

        # Update status to 'processing'
        pdf_upload.processing_status = 'processing'
        pdf_upload.file = file_key  # Update with actual S3 key if different
        pdf_upload.save()

        # Trigger Celery task for post-processing
        from .tasks import process_uploaded_pdf
        process_uploaded_pdf.delay(str(pdf_upload.id))

        return Response({
            'pdf_id': pdf_upload.id,
            'status': pdf_upload.processing_status,
            'message': 'Upload marked as complete. Processing will begin shortly.'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='download-url')
    @method_decorator(ratelimit(key='user', rate='30/m', method='GET'))
    def download_url(self, request, pk=None):
        """
        GET /api/v1/sources/pdfs/{pdf_id}/download-url/

        Generate a presigned URL for downloading a PDF from S3/R2.
        Validates user has vault viewer/contributor/owner permission.

        Response:
        - download_url (str): Presigned S3 URL for GET download
        - expires_in (int): URL expiration time in seconds
        - filename (str): Original filename
        - file_size (int): File size in bytes
        """
        # Get PDFUpload record
        pdf_upload = get_object_or_404(PDFUpload, id=pk)

        # Verify user has permission (viewer, contributor, or owner)
        self._check_vault_permission(
            pdf_upload.vault.id,
            request.user,
            required_roles=[RoleChoices.VIEWER, RoleChoices.CONTRIBUTOR, RoleChoices.OWNER]
        )

        # Generate presigned download URL with content-disposition attachment
        download_url = generate_presigned_download_url(
            file_key=pdf_upload.file.name,  # S3 object key
            original_filename=pdf_upload.original_filename
        )

        # Log pdf.downloaded event to audit log (US-021)
        try:
            AuditLog.objects.create(
                vault=pdf_upload.vault,
                actor=request.user,
                action='pdf.downloaded',
                metadata={
                    'pdf_id': str(pdf_upload.id),
                    'filename': pdf_upload.original_filename,
                }
            )
        except Exception as audit_exc:
            # Log but don't fail the request if audit logging fails
            logger.warning(
                f"Failed to create audit log for PDF download {pdf_upload.id}: {audit_exc}",
                exc_info=True,
            )

        return Response({
            'download_url': download_url,
            'expires_in': 900,  # 15 minutes
            'filename': pdf_upload.original_filename,
            'file_size': pdf_upload.file_size
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='multipart-upload/initiate')
    def multipart_upload_initiate(self, request):
        """
        POST /api/v1/sources/pdfs/multipart-upload/initiate/

        Initiate a multipart upload for large PDF files (>20MB).
        Returns presigned URLs for each part that the client uploads individually.

        Request body:
        - vault_id (UUID): Target vault
        - filename (str): Original filename
        - file_size (int): Total file size in bytes
        - part_size (int): Size of each part in bytes (minimum 5MB)
        - content_type (str): MIME type (must be application/pdf)

        Response:
        - upload_id (str): S3 multipart upload ID (required for completion)
        - pdf_upload_id (UUID): PDFUpload record ID
        - file_key (str): S3 object key where file will be stored
        - part_urls (list): Array of {part_number, upload_url} for each part
        - expires_in (int): URL expiration time in seconds
        """
        # Validate request data
        request_serializer = MultipartUploadRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        vault_id = request_serializer.validated_data['vault_id']
        filename = request_serializer.validated_data['filename']
        file_size = request_serializer.validated_data['file_size']
        part_size = request_serializer.validated_data['part_size']
        content_type = request_serializer.validated_data['content_type']

        # Check user has contributor or owner permission on vault
        vault = self._check_vault_permission(vault_id, request.user)

        # Check storage quota before allowing upload
        quota_result = check_storage_quota(vault_id)
        if quota_result['exceeded']:
            return Response({
                'error': 'Storage quota exceeded',
                'used_bytes': quota_result['used_bytes'],
                'limit_bytes': quota_result['limit_bytes'],
                'percentage': round(quota_result['percentage'] * 100, 2)
            }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        # Initiate S3 multipart upload
        upload_id, file_key, part_urls = initiate_multipart_upload(
            vault_id=str(vault_id),
            filename=filename,
            file_size=file_size,
            part_size=part_size,
            content_type=content_type
        )

        # Create PDFUpload record with status='pending'
        # Store upload_id in metadata for later completion
        pdf_upload = PDFUpload.objects.create(
            vault=vault,
            file=file_key,  # Store the S3 key in the file field
            original_filename=filename,
            file_size=file_size,
            mime_type=content_type,
            uploaded_by=request.user,
            processing_status='pending'
        )

        # Prepare response
        response_data = {
            'upload_id': upload_id,
            'pdf_upload_id': pdf_upload.id,
            'file_key': file_key,
            'part_urls': part_urls,
            'expires_in': 3600,  # 1 hour
        }

        response_serializer = MultipartUploadResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path=r'multipart-upload/(?P<upload_id>[^/.]+)/complete')
    def multipart_upload_complete(self, request, upload_id=None):
        """
        POST /api/v1/sources/pdfs/multipart-upload/{upload_id}/complete/

        Complete a multipart upload after all parts have been uploaded.
        Combines uploaded parts into final file and triggers post-processing.

        URL Parameters:
        - upload_id (str): S3 multipart upload ID from initiate endpoint

        Request body:
        - parts (array): List of {part_number: int, etag: str} for each uploaded part

        Response:
        - pdf_id (UUID): PDFUpload record ID
        - status (str): Processing status
        - message (str): Success message
        """
        # Validate request
        request_serializer = MultipartUploadCompleteRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        parts = request_serializer.validated_data['parts']
        pdf_upload_id = request_serializer.validated_data['pdf_upload_id']

        # Get PDFUpload record
        pdf_upload = get_object_or_404(PDFUpload, id=pdf_upload_id)

        # Verify user has permission
        self._check_vault_permission(pdf_upload.vault.id, request.user)

        # Complete the multipart upload on S3
        try:
            complete_multipart_upload(
                file_key=pdf_upload.file.name,
                upload_id=upload_id,
                parts=parts
            )
        except Exception as e:
            # If completion fails, update status to failed
            pdf_upload.processing_status = 'failed'
            pdf_upload.save()
            return Response(
                {'error': f'Multipart upload completion failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Update status to 'processing'
        pdf_upload.processing_status = 'processing'
        pdf_upload.save()

        # Trigger Celery task for post-processing
        from .tasks import process_uploaded_pdf
        process_uploaded_pdf.delay(str(pdf_upload.id))

        return Response({
            'pdf_id': pdf_upload.id,
            'status': pdf_upload.processing_status,
            'message': 'Multipart upload completed. Processing will begin shortly.'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='multipart-upload/abort')
    def multipart_upload_abort(self, request):
        """
        POST /api/v1/sources/pdfs/multipart-upload/abort/

        Abort a failed multipart upload to free S3 resources.
        Called by client when upload fails or is cancelled.

        Request body:
        - upload_id (str): S3 multipart upload ID from initiate endpoint
        - file_key (str): S3 object key where file was being uploaded

        Response:
        - message (str): Success message
        """
        # Validate request
        request_serializer = MultipartUploadAbortRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        upload_id = request_serializer.validated_data['upload_id']
        file_key = request_serializer.validated_data['file_key']

        # Extract vault_id from file_key (format: vaults/{vault_id}/pdfs/{uuid}.pdf)
        try:
            parts = file_key.split('/')
            if len(parts) >= 2 and parts[0] == 'vaults':
                vault_id = parts[1]
            else:
                return Response(
                    {'error': 'Invalid file_key format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception:
            return Response(
                {'error': 'Invalid file_key format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify user has permission to abort (owns the vault or is contributor)
        try:
            vault = get_object_or_404(Vault, id=vault_id)
            self._check_vault_permission(vault_id, request.user)
        except Exception:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to abort this upload.")

        # Abort the multipart upload
        try:
            abort_multipart_upload(file_key=file_key, upload_id=upload_id)
            logger.info(f"User {request.user.id} aborted multipart upload {upload_id} for {file_key}")
        except Exception as e:
            logger.error(f"Failed to abort multipart upload {upload_id}: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to abort upload: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'message': 'Multipart upload aborted successfully.'
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/v1/sources/pdfs/{pdf_id}/

        Soft-delete a PDF upload by setting deleted_at timestamp.
        Only vault owner or the uploader can delete PDFs.
        Files are permanently deleted after 30 days.

        Response:
        - message (str): Success message
        - pdf_id (UUID): PDFUpload record ID
        - permanent_deletion_date (str): ISO 8601 date when file will be permanently deleted
        """
        # Get PDFUpload record
        pdf_upload = self.get_object()

        # Verify user has permission: must be owner or uploader
        is_owner = pdf_upload.vault.owner == request.user
        is_uploader = pdf_upload.uploaded_by == request.user

        # Also allow vault owner with owner role via membership
        is_vault_admin = False
        if not is_owner:
            membership = VaultMembership.objects.filter(
                vault=pdf_upload.vault,
                user=request.user,
                role=RoleChoices.OWNER
            ).first()
            is_vault_admin = membership is not None

        if not (is_owner or is_uploader or is_vault_admin):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only the vault owner or the uploader can delete this PDF.")

        # Set deleted_at timestamp (soft-delete)
        pdf_upload.deleted_at = timezone.now()
        pdf_upload.save()

        # Update vault storage usage
        update_vault_storage_usage(pdf_upload.vault.id)

        # Send WebSocket notification to vault (US-020)
        try:
            broadcast_to_vault(
                vault_id=pdf_upload.vault.id,
                event_type='pdf.deleted',
                payload={
                    'pdf_id': str(pdf_upload.id),
                    'filename': pdf_upload.original_filename,
                },
                user=request.user,
            )
        except Exception as ws_exc:
            # Log but don't fail the request if WebSocket broadcast fails
            logger.warning(
                f"Failed to send WebSocket notification for deleted PDF {pdf_upload.id}: {ws_exc}",
                exc_info=True,
            )

        # Log pdf.deleted event to audit log (US-021)
        try:
            AuditLog.objects.create(
                vault=pdf_upload.vault,
                actor=request.user,
                action='pdf.deleted',
                metadata={
                    'pdf_id': str(pdf_upload.id),
                    'filename': pdf_upload.original_filename,
                }
            )
        except Exception as audit_exc:
            # Log but don't fail the request if audit logging fails
            logger.warning(
                f"Failed to create audit log for PDF deletion {pdf_upload.id}: {audit_exc}",
                exc_info=True,
            )

        # Calculate permanent deletion date (30 days from now)
        permanent_deletion_date = pdf_upload.deleted_at + timedelta(days=30)

        return Response({
            'message': 'PDF has been deleted. It will be permanently removed in 30 days.',
            'pdf_id': pdf_upload.id,
            'permanent_deletion_date': permanent_deletion_date.isoformat()
        }, status=status.HTTP_200_OK)


class SourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Source CRUD operations (US-008).
    Provides list, retrieve, create, update functionality for sources.
    """
    queryset = Source.objects.filter(is_deleted=False)
    serializer_class = SourceSerializer
    permission_classes = [IsAuthenticated, VaultSourcePermission]
    filterset_class = SourceFilter

    def perform_create(self, serializer):
        """
        Override perform_create to set created_by from request.user (US-008).
        Also handles nested creation from /vaults/{vault_id}/sources/ (US-015).
        """
        # Check if this is a nested creation from /vaults/{vault_id}/sources/
        vault_pk = self.kwargs.get('vault_pk')

        if vault_pk:
            # Nested route: /api/v1/vaults/{vault_id}/sources/
            # Validate user has Owner/Contributor role on vault
            vault = get_object_or_404(Vault, id=vault_pk)

            # Check if user is owner
            if vault.owner == self.request.user:
                serializer.save(created_by=self.request.user, vault=vault)
                return

            # Check if user has membership with Contributor or Owner role
            membership = VaultMembership.objects.filter(
                vault=vault,
                user=self.request.user,
                role__in=[RoleChoices.OWNER, RoleChoices.CONTRIBUTOR]
            ).first()

            if not membership:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You must be an Owner or Contributor to add sources to this vault.")

            serializer.save(created_by=self.request.user, vault=vault)
        else:
            # Standard route: /api/v1/sources/
            serializer.save(created_by=self.request.user)

    def get_queryset(self):
        """
        Override get_queryset to filter by vaults user has access to (US-008).
        Returns only sources from vaults where user is owner or member.
        Also handles nested listing from /vaults/{vault_id}/sources/ (US-015).
        """
        user = self.request.user

        # Check if this is a nested route from /vaults/{vault_id}/sources/
        vault_pk = self.kwargs.get('vault_pk')

        if vault_pk:
            # Nested route: Filter by specific vault only
            # Permission is already checked by VaultSourcePermission
            return Source.objects.filter(
                vault_id=vault_pk,
                is_deleted=False
            )

        # Standard route: Get all accessible sources
        # Get vaults where user is owner
        owned_vault_ids = Vault.objects.filter(owner=user).values_list('id', flat=True)

        # Get vaults where user is a member (through VaultMembership)
        member_vault_ids = VaultMembership.objects.filter(user=user).values_list('vault_id', flat=True)

        # Combine both sets of vault IDs
        accessible_vault_ids = list(owned_vault_ids) + list(member_vault_ids)

        # Filter sources by accessible vaults and not deleted
        return Source.objects.filter(
            vault_id__in=accessible_vault_ids,
            is_deleted=False
        )

    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to soft-delete sources instead of hard delete (US-010).
        Sets is_deleted=True rather than removing from database.
        Creates audit log for source.soft_deleted action (US-038).
        """
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()

        # Create audit log for soft delete (US-038)
        AuditLog.objects.create(
            vault=instance.vault,
            actor=request.user,
            action='source.soft_deleted',
            metadata={
                'source_id': str(instance.id),
                'vault_id': str(instance.vault_id),
            }
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """
        POST /api/v1/sources/{id}/restore/

        Restore a soft-deleted source (US-011).
        Only vault OWNER role can restore sources.
        """
        # Override get_queryset to include soft-deleted sources
        # We need to fetch from all sources, including is_deleted=True
        user = request.user

        # Get vaults where user is owner
        owned_vault_ids = Vault.objects.filter(owner=user).values_list('id', flat=True)

        # Get vaults where user is a member (through VaultMembership)
        member_vault_ids = VaultMembership.objects.filter(user=user).values_list('vault_id', flat=True)

        # Combine both sets of vault IDs
        accessible_vault_ids = list(owned_vault_ids) + list(member_vault_ids)

        # Get the source including soft-deleted ones
        instance = get_object_or_404(
            Source,
            pk=pk,
            vault_id__in=accessible_vault_ids,
            is_deleted=True  # Only allow restoring soft-deleted sources
        )

        # Check permission: Only OWNER can restore
        # Use VaultSourcePermission's logic manually since get_object() not used
        try:
            membership = VaultMembership.objects.get(
                vault=instance.vault,
                user=user
            )
            if membership.role != RoleChoices.OWNER:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Only vault owners can restore sources.")
        except VaultMembership.DoesNotExist:
            # Check if user is vault owner directly
            if instance.vault.owner != user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Only vault owners can restore sources.")

        # Restore the source
        instance.is_deleted = False
        instance.save()

        # Create audit log for restore (US-038)
        AuditLog.objects.create(
            vault=instance.vault,
            actor=request.user,
            action='source.restored',
            metadata={
                'source_id': str(instance.id),
                'vault_id': str(instance.vault_id),
            }
        )

        # Return serialized source
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    @method_decorator(ratelimit(key='user', rate='30/m', method='POST'))
    def preview(self, request):
        """
        POST /api/v1/sources/preview/

        Preview URL metadata without creating a source.
        Returns extracted title, authors, abstract, and publication date.

        Request body:
        - url (str): URL to extract metadata from

        Response:
        - url (str): Original URL
        - title (str): Extracted title
        - authors (list): List of author names
        - abstract (str): First 500 chars of content
        - publication_date (str|null): ISO date if available
        - error (str|null): Error message if extraction failed
        """
        url = request.data.get('url')

        if not url:
            return Response(
                {'error': 'URL is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract metadata using existing service
        metadata = extract_metadata(url)

        return Response({
            'url': url,
            'title': metadata.get('title', url),
            'authors': metadata.get('authors', []),
            'abstract': metadata.get('abstract', ''),
            'publication_date': metadata.get('publication_date'),
            'error': metadata.get('error'),
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        """
        POST /api/v1/sources/bulk_import/

        Bulk import multiple source URLs (US-017).
        Creates multiple sources with auto metadata extraction.
        Detects duplicates and returns created/skipped/errors.

        Request body:
        - urls (list): List of URLs to import (max 50)

        Response:
        - created (list): Successfully created sources
        - skipped (list): URLs that already exist in vault
        - errors (list): URLs that failed validation or creation
        """
        # Validate request data
        request_serializer = BulkSourceSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        urls = request_serializer.validated_data['urls']

        # Check if this is a nested route from /vaults/{vault_id}/sources/bulk_import/
        vault_pk = self.kwargs.get('vault_pk')

        if not vault_pk:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("bulk_import must be called via nested route: /api/v1/vaults/{vault_id}/sources/bulk_import/")

        # Get vault and check permissions
        vault = get_object_or_404(Vault, id=vault_pk)

        # Check if user is owner or contributor
        if vault.owner != request.user:
            membership = VaultMembership.objects.filter(
                vault=vault,
                user=request.user,
                role__in=[RoleChoices.OWNER, RoleChoices.CONTRIBUTOR]
            ).first()

            if not membership:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You must be an Owner or Contributor to bulk import sources.")

        # Check for existing sources in vault
        existing_urls = set(
            Source.objects.filter(
                vault=vault,
                is_deleted=False
            ).values_list('url', flat=True)
        )

        created = []
        skipped = []
        errors = []

        # Process each URL in a transaction
        with transaction.atomic():
            for url in urls:
                # Skip if URL already exists in vault
                if url in existing_urls:
                    skipped.append({
                        'url': url,
                        'reason': 'URL already exists in vault'
                    })
                    continue

                try:
                    # Extract metadata for each URL
                    metadata = extract_metadata(url)

                    # Use extracted title or fall back to URL
                    title = metadata.get('title', url)

                    # Create source
                    source = Source.objects.create(
                        vault=vault,
                        url=url,
                        title=title,
                        source_type='URL',
                        metadata=metadata,
                        created_by=request.user,
                        is_deleted=False
                    )

                    # Serialize and add to created list
                    source_serializer = SourceSerializer(source)
                    created.append(source_serializer.data)

                except Exception as e:
                    # Capture any errors during creation
                    errors.append({
                        'url': url,
                        'error': str(e)
                    })

        return Response({
            'created': created,
            'skipped': skipped,
            'errors': errors
        }, status=status.HTTP_200_OK)
