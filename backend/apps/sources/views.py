from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers as drf_serializers
from django.shortcuts import get_object_or_404
from .models import PDFUpload, Source
from .serializers import (
    UploadURLRequestSerializer,
    UploadURLResponseSerializer,
    PDFUploadSerializer,
    SourceSerializer,
    MultipartUploadRequestSerializer,
    MultipartUploadResponseSerializer,
)
from .storage import (
    generate_presigned_upload_url,
    generate_presigned_download_url,
    initiate_multipart_upload,
)
from .permissions import VaultSourcePermission
from .filters import SourceFilter
from apps.vaults.models import Vault, VaultMembership, RoleChoices


class PDFUploadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PDF upload operations (US-006).
    Handles presigned URL generation, upload completion, and downloads.
    """
    queryset = PDFUpload.objects.filter(deleted_at__isnull=True)
    serializer_class = PDFUploadSerializer
    permission_classes = [IsAuthenticated]

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
        """
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()
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

        # Return serialized source
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
