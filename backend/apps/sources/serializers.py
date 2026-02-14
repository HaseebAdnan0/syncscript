from rest_framework import serializers
from .models import PDFUpload, Source
from .services import extract_metadata


class UploadURLRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a presigned upload URL (US-006).
    Validates input for PDF upload initiation.
    """
    vault_id = serializers.UUIDField(required=True)
    filename = serializers.CharField(required=True, max_length=255)
    file_size = serializers.IntegerField(required=True, min_value=1, max_value=50 * 1024 * 1024)  # Max 50MB
    content_type = serializers.CharField(default='application/pdf')

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


class SourceSerializer(serializers.ModelSerializer):
    """
    Serializer for Source model (US-007).
    Handles CRUD operations with automatic metadata extraction for URLs.
    """
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Source
        fields = [
            'id', 'vault', 'url', 'title', 'description', 'source_type',
            'metadata', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        """
        Override create to auto-extract metadata from URL if title not provided.
        Merges extracted metadata into the metadata field.
        """
        # If title is not provided, extract metadata from URL
        if not validated_data.get('title'):
            url = validated_data['url']
            extracted = extract_metadata(url)

            # Use extracted title if available
            if 'title' in extracted:
                validated_data['title'] = extracted['title']

            # Merge extracted metadata into metadata field
            existing_metadata = validated_data.get('metadata', {})
            # Copy all extracted data except 'title' into metadata
            for key, value in extracted.items():
                if key != 'title':
                    existing_metadata[key] = value
            validated_data['metadata'] = existing_metadata

        return super().create(validated_data)
