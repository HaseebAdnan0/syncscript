from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import PDFUpload
from .serializers import (
    UploadURLRequestSerializer,
    UploadURLResponseSerializer,
    PDFUploadSerializer
)
from .storage import generate_presigned_upload_url
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
