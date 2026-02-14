from rest_framework import serializers
from .models import PDFUpload


class UploadURLRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a presigned upload URL (US-006).
    Validates input for PDF upload initiation.
    """
    vault_id = serializers.UUIDField(required=True)
    filename = serializers.CharField(required=True, max_length=255)
    file_size = serializers.IntegerField(required=True, min_value=1, max_value=50 * 1024 * 1024)  # Max 50MB
    content_type = serializers.CharField(required=True, default='application/pdf')

    def validate_content_type(self, value):
        """Ensure only PDF files are accepted."""
        if value != 'application/pdf':
            raise serializers.ValidationError("Only PDF files are supported.")
        return value


class UploadURLResponseSerializer(serializers.Serializer):
    """
    Serializer for presigned upload URL response (US-006).
    Returns the URL and metadata for client-side upload.
    """
    upload_id = serializers.UUIDField()
    upload_url = serializers.URLField()
    expires_in = serializers.IntegerField()
    callback_url = serializers.CharField()


class PDFUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for PDFUpload model (US-009).
    Used for listing and detail views of uploaded PDFs.
    """
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    vault_name = serializers.CharField(source='vault.name', read_only=True)

    class Meta:
        model = PDFUpload
        fields = [
            'id', 'vault', 'vault_name', 'source', 'file', 'original_filename',
            'file_size', 'mime_type', 'uploaded_by', 'uploaded_by_username',
            'uploaded_at', 'processing_status', 'pdf_title', 'pdf_author',
            'page_count', 'thumbnail_url', 'deleted_at'
        ]
        read_only_fields = [
            'id', 'uploaded_by', 'uploaded_at', 'processing_status',
            'pdf_title', 'pdf_author', 'page_count', 'thumbnail_url', 'deleted_at'
        ]
