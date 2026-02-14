"""
Unit tests for storage utilities (presigned URL generation and storage tracking).
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from apps.vaults.models import Vault
from apps.sources.models import PDFUpload, VaultStorageUsage
from apps.sources.storage import (
    generate_presigned_upload_url,
    generate_presigned_download_url,
    get_s3_client,
)
from apps.sources.utils import update_vault_storage_usage

User = get_user_model()


class GeneratePresignedUploadURLTests(TestCase):
    """Tests for generate_presigned_upload_url function."""

    @override_settings(USE_S3=True, AWS_STORAGE_BUCKET_NAME='test-bucket')
    @patch('apps.sources.storage.get_s3_client')
    def test_generate_presigned_upload_url_returns_valid_url_and_key(self, mock_get_s3_client):
        """Test that generate_presigned_upload_url returns valid URL and key with correct parameters."""
        # Mock boto3 S3 client
        mock_s3 = MagicMock()
        mock_get_s3_client.return_value = mock_s3
        mock_s3.generate_presigned_url.return_value = 'https://s3.example.com/presigned-upload-url?signature=abc123'

        # Generate presigned upload URL
        vault_id = 'test-vault-123'
        filename = 'research.pdf'
        content_type = 'application/pdf'

        url, file_key = generate_presigned_upload_url(vault_id, filename, content_type)

        # Verify URL was returned
        self.assertEqual(url, 'https://s3.example.com/presigned-upload-url?signature=abc123')

        # Verify file_key follows expected pattern: vaults/{vault_id}/pdfs/{uuid}.pdf
        self.assertTrue(file_key.startswith(f'vaults/{vault_id}/pdfs/'))
        self.assertTrue(file_key.endswith('.pdf'))

        # Verify boto3 client was called with correct parameters
        mock_s3.generate_presigned_url.assert_called_once()
        call_args = mock_s3.generate_presigned_url.call_args

        # Check operation type
        self.assertEqual(call_args[0][0], 'put_object')

        # Check parameters
        params = call_args[1]['Params']
        self.assertIn('Bucket', params)
        self.assertEqual(params['Key'], file_key)
        self.assertEqual(params['ContentType'], content_type)

        # Check expiration (should be 1 hour = 3600 seconds)
        self.assertEqual(call_args[1]['ExpiresIn'], 3600)

    @override_settings(USE_S3=True, AWS_STORAGE_BUCKET_NAME='test-bucket')
    @patch('apps.sources.storage.get_s3_client')
    def test_generate_presigned_upload_url_handles_filename_without_extension(self, mock_get_s3_client):
        """Test that generate_presigned_upload_url handles filenames without extensions."""
        mock_s3 = MagicMock()
        mock_get_s3_client.return_value = mock_s3
        mock_s3.generate_presigned_url.return_value = 'https://s3.example.com/presigned-url'

        # Generate URL with filename without extension
        url, file_key = generate_presigned_upload_url('vault-123', 'research', 'application/pdf')

        # Should default to .pdf extension
        self.assertTrue(file_key.endswith('.pdf'))

    @override_settings(USE_S3=False)
    def test_generate_presigned_upload_url_raises_error_when_s3_disabled(self):
        """Test that generate_presigned_upload_url raises error when S3 is not configured."""
        with self.assertRaises(ValueError) as context:
            generate_presigned_upload_url('vault-123', 'research.pdf', 'application/pdf')

        self.assertIn('S3 storage is not configured', str(context.exception))


class GeneratePresignedDownloadURLTests(TestCase):
    """Tests for generate_presigned_download_url function."""

    @override_settings(USE_S3=True, AWS_STORAGE_BUCKET_NAME='test-bucket')
    @patch('apps.sources.storage.get_s3_client')
    def test_generate_presigned_download_url_includes_content_disposition(self, mock_get_s3_client):
        """Test that generate_presigned_download_url includes Content-Disposition header."""
        # Mock boto3 S3 client
        mock_s3 = MagicMock()
        mock_get_s3_client.return_value = mock_s3
        mock_s3.generate_presigned_url.return_value = 'https://s3.example.com/presigned-download-url?signature=xyz789'

        # Generate presigned download URL
        file_key = 'vaults/vault-123/pdfs/uuid.pdf'
        original_filename = 'My Research Paper.pdf'

        url = generate_presigned_download_url(file_key, original_filename)

        # Verify URL was returned
        self.assertEqual(url, 'https://s3.example.com/presigned-download-url?signature=xyz789')

        # Verify boto3 client was called with correct parameters
        mock_s3.generate_presigned_url.assert_called_once()
        call_args = mock_s3.generate_presigned_url.call_args

        # Check operation type
        self.assertEqual(call_args[0][0], 'get_object')

        # Check parameters
        params = call_args[1]['Params']
        self.assertIn('Bucket', params)
        self.assertEqual(params['Key'], file_key)

        # Check Content-Disposition header includes original filename
        self.assertIn('ResponseContentDisposition', params)
        self.assertIn(original_filename, params['ResponseContentDisposition'])
        self.assertTrue(params['ResponseContentDisposition'].startswith('attachment'))

        # Check expiration (should be 15 minutes = 900 seconds)
        self.assertEqual(call_args[1]['ExpiresIn'], 900)


class UpdateVaultStorageUsageTests(TestCase):
    """Tests for update_vault_storage_usage function."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test users with unique emails
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='pass123')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='pass123')

        # Create test vault
        self.vault = Vault.objects.create(
            name='Test Vault',
            description='Test vault for storage tests',
            owner=self.user1
        )

    def test_update_vault_storage_usage_calculates_correct_totals(self):
        """Test that update_vault_storage_usage calculates correct total bytes and file count."""
        # Create test PDFUploads with mock file paths (skip actual file creation)
        pdf1 = PDFUpload(
            vault=self.vault,
            uploaded_by=self.user1,
            original_filename='file1.pdf',
            file_size=1000000,  # 1MB
            mime_type='application/pdf',
            processing_status='completed'
        )
        pdf1.file.name = 'vaults/test/file1.pdf'  # Set file path without saving to storage
        pdf1.save()

        pdf2 = PDFUpload(
            vault=self.vault,
            uploaded_by=self.user1,
            original_filename='file2.pdf',
            file_size=2000000,  # 2MB
            mime_type='application/pdf',
            processing_status='completed'
        )
        pdf2.file.name = 'vaults/test/file2.pdf'
        pdf2.save()

        pdf3 = PDFUpload(
            vault=self.vault,
            uploaded_by=self.user2,
            original_filename='file3.pdf',
            file_size=3000000,  # 3MB
            mime_type='application/pdf',
            processing_status='completed'
        )
        pdf3.file.name = 'vaults/test/file3.pdf'
        pdf3.save()

        # Calculate storage usage
        storage_usage = update_vault_storage_usage(self.vault.id)

        # Verify totals
        self.assertEqual(storage_usage.total_bytes, 6000000)  # 1MB + 2MB + 3MB
        self.assertEqual(storage_usage.file_count, 3)

    def test_update_vault_storage_usage_calculates_per_user_breakdown(self):
        """Test that update_vault_storage_usage calculates correct per-user breakdown."""
        # Create test PDFUploads with mock file paths
        pdf1 = PDFUpload(
            vault=self.vault,
            uploaded_by=self.user1,
            original_filename='file1.pdf',
            file_size=1500000,  # 1.5MB
            mime_type='application/pdf',
            processing_status='completed'
        )
        pdf1.file.name = 'vaults/test/file1.pdf'
        pdf1.save()

        pdf2 = PDFUpload(
            vault=self.vault,
            uploaded_by=self.user1,
            original_filename='file2.pdf',
            file_size=2500000,  # 2.5MB
            mime_type='application/pdf',
            processing_status='completed'
        )
        pdf2.file.name = 'vaults/test/file2.pdf'
        pdf2.save()

        pdf3 = PDFUpload(
            vault=self.vault,
            uploaded_by=self.user2,
            original_filename='file3.pdf',
            file_size=3000000,  # 3MB
            mime_type='application/pdf',
            processing_status='completed'
        )
        pdf3.file.name = 'vaults/test/file3.pdf'
        pdf3.save()

        # Calculate storage usage
        storage_usage = update_vault_storage_usage(self.vault.id)

        # Verify user breakdown
        self.assertEqual(storage_usage.user_breakdown[str(self.user1.id)], 4000000)  # 1.5MB + 2.5MB
        self.assertEqual(storage_usage.user_breakdown[str(self.user2.id)], 3000000)  # 3MB

    def test_update_vault_storage_usage_excludes_deleted_files(self):
        """Test that update_vault_storage_usage excludes soft-deleted PDFs."""
        from django.utils import timezone

        # Create test PDFUploads (one deleted) with mock file paths
        pdf1 = PDFUpload(
            vault=self.vault,
            uploaded_by=self.user1,
            original_filename='file1.pdf',
            file_size=1000000,  # 1MB
            mime_type='application/pdf',
            processing_status='completed'
        )
        pdf1.file.name = 'vaults/test/file1.pdf'
        pdf1.save()

        pdf2 = PDFUpload(
            vault=self.vault,
            uploaded_by=self.user1,
            original_filename='file2.pdf',
            file_size=2000000,  # 2MB (DELETED)
            mime_type='application/pdf',
            processing_status='completed',
            deleted_at=timezone.now()  # Soft-deleted
        )
        pdf2.file.name = 'vaults/test/file2.pdf'
        pdf2.save()

        # Calculate storage usage
        storage_usage = update_vault_storage_usage(self.vault.id)

        # Verify only non-deleted file is counted
        self.assertEqual(storage_usage.total_bytes, 1000000)  # Only 1MB
        self.assertEqual(storage_usage.file_count, 1)

    def test_update_vault_storage_usage_handles_empty_vault(self):
        """Test that update_vault_storage_usage handles vaults with no PDFs."""
        # Calculate storage usage for empty vault
        storage_usage = update_vault_storage_usage(self.vault.id)

        # Verify zero values
        self.assertEqual(storage_usage.total_bytes, 0)
        self.assertEqual(storage_usage.file_count, 0)
        self.assertEqual(storage_usage.user_breakdown, {})

    @patch('apps.sources.utils.cache.delete')
    def test_update_vault_storage_usage_invalidates_cache(self, mock_cache_delete):
        """Test that update_vault_storage_usage invalidates Redis cache."""
        # Create a test PDFUpload with mock file path
        pdf1 = PDFUpload(
            vault=self.vault,
            uploaded_by=self.user1,
            original_filename='file1.pdf',
            file_size=1000000,
            mime_type='application/pdf',
            processing_status='completed'
        )
        pdf1.file.name = 'vaults/test/file1.pdf'
        pdf1.save()

        # Calculate storage usage
        update_vault_storage_usage(self.vault.id)

        # Verify cache was invalidated with correct key
        mock_cache_delete.assert_called_once_with(f'vault_storage:{self.vault.id}')
