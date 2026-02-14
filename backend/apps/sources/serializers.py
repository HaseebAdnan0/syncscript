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


class MultipartUploadRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting multipart upload initiation (US-012).
    Validates input for large PDF upload via S3 multipart upload.
    """
    vault_id = serializers.UUIDField(required=True)
    filename = serializers.CharField(required=True, max_length=255)
    file_size = serializers.IntegerField(required=True, min_value=1, max_value=50 * 1024 * 1024)  # Max 50MB
    part_size = serializers.IntegerField(required=True, min_value=5 * 1024 * 1024)  # Minimum 5MB per part
    content_type = serializers.CharField(default='application/pdf')

    def validate_content_type(self, value):
        """Ensure only PDF files are accepted."""
        if value != 'application/pdf':
            raise serializers.ValidationError("Only PDF files are supported.")
        return value

    def validate(self, attrs):
        """Validate that file_size and part_size are compatible."""
        file_size = attrs['file_size']
        part_size = attrs['part_size']

        # Calculate number of parts
        num_parts = (file_size + part_size - 1) // part_size  # Ceiling division

        # AWS S3 allows maximum 10,000 parts
        if num_parts > 10000:
            raise serializers.ValidationError(
                f"Part size too small. Would result in {num_parts} parts (max 10,000)."
            )

        return attrs


class MultipartUploadResponseSerializer(serializers.Serializer):
    """
    Serializer for multipart upload initiation response (US-012).
    Returns upload ID, file key, and presigned URLs for each part.
    """
    upload_id = serializers.CharField()
    pdf_upload_id = serializers.UUIDField()
    file_key = serializers.CharField()
    part_urls = serializers.ListField(child=serializers.DictField())
    expires_in = serializers.IntegerField()


class MultipartUploadCompleteRequestSerializer(serializers.Serializer):
    """
    Serializer for multipart upload completion request (US-013).
    Validates the parts array with part_number and ETag for each uploaded part.
    """
    pdf_upload_id = serializers.UUIDField(
        required=True,
        help_text="PDFUpload record ID from initiate endpoint"
    )
    parts = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        min_length=1,
        help_text="Array of objects with 'part_number' (int) and 'etag' (str)"
    )

    def validate_parts(self, value):
        """Ensure each part has required fields."""
        for part in value:
            if 'part_number' not in part:
                raise serializers.ValidationError("Each part must have 'part_number' field.")
            if 'etag' not in part:
                raise serializers.ValidationError("Each part must have 'etag' field.")

            # Validate types
            if not isinstance(part['part_number'], int):
                raise serializers.ValidationError("'part_number' must be an integer.")
            if not isinstance(part['etag'], str):
                raise serializers.ValidationError("'etag' must be a string.")

            # Validate range
            if part['part_number'] < 1 or part['part_number'] > 10000:
                raise serializers.ValidationError("'part_number' must be between 1 and 10,000.")

        return value


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
