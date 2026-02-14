"""
Unit tests for PDF validation.

Tests the validate_pdf_file() function to ensure it properly validates
PDFs and rejects invalid or malicious files.
"""

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.sources.validators import validate_pdf_file, MAX_FILE_SIZE


class TestPDFValidation(TestCase):
    """Test PDF file validation."""

    def test_valid_pdf_passes_validation(self):
        """Test that a valid PDF file passes all validation checks."""
        # Minimal valid PDF (single blank page)
        valid_pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
299
%%EOF
"""

        pdf_file = SimpleUploadedFile(
            "test.pdf",
            valid_pdf_content,
            content_type="application/pdf"
        )

        # Should not raise ValidationError
        try:
            validate_pdf_file(pdf_file)
        except ValidationError:
            self.fail("validate_pdf_file() raised ValidationError for valid PDF")

    def test_non_pdf_file_raises_validation_error(self):
        """Test that a non-PDF file (txt) is rejected."""
        txt_content = b"This is a plain text file, not a PDF."

        txt_file = SimpleUploadedFile(
            "test.txt",
            txt_content,
            content_type="text/plain"
        )

        with self.assertRaises(ValidationError) as context:
            validate_pdf_file(txt_file)

        self.assertIn("Invalid content type", str(context.exception))

    def test_file_exceeding_size_limit_raises_validation_error(self):
        """Test that files larger than 50MB are rejected."""
        # Create a file larger than MAX_FILE_SIZE
        # We'll create a minimal PDF header and pad with zeros
        oversized_content = b"%PDF-1.4\n" + b"0" * (MAX_FILE_SIZE + 1000)

        oversized_file = SimpleUploadedFile(
            "oversized.pdf",
            oversized_content,
            content_type="application/pdf"
        )

        with self.assertRaises(ValidationError) as context:
            validate_pdf_file(oversized_file)

        self.assertIn("exceeds maximum allowed size", str(context.exception))

    def test_corrupted_pdf_raises_validation_error(self):
        """Test that a corrupted PDF file is rejected."""
        # PDF with correct magic number but invalid structure
        corrupted_pdf = b"%PDF-1.4\nThis is corrupted data that won't parse as a PDF\n%%EOF"

        corrupted_file = SimpleUploadedFile(
            "corrupted.pdf",
            corrupted_pdf,
            content_type="application/pdf"
        )

        with self.assertRaises(ValidationError) as context:
            validate_pdf_file(corrupted_file)

        # Should fail either magic detection or pypdf parsing
        error_msg = str(context.exception)
        self.assertTrue(
            "structure validation failed" in error_msg or
            "does not match PDF format" in error_msg or
            "magic number check failed" in error_msg,
            f"Unexpected error message: {error_msg}"
        )


class TestImageValidation(TestCase):
    """Test image file validation (US-023)."""

    def test_valid_png_passes_validation(self):
        """Test that a valid PNG file passes all validation checks."""
        # Minimal valid PNG (1x1 pixel, transparent)
        valid_png_content = (
            b'\x89PNG\r\n\x1a\n'  # PNG signature
            b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'  # IHDR chunk
            b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
            b'\r\n-\xb4'  # IDAT chunk
            b'\x00\x00\x00\x00IEND\xaeB`\x82'  # IEND chunk
        )

        png_file = SimpleUploadedFile(
            "test.png",
            valid_png_content,
            content_type="image/png"
        )

        # Should not raise ValidationError
        from apps.sources.validators import validate_image_file
        try:
            validate_image_file(png_file)
        except ValidationError:
            self.fail("validate_image_file() raised ValidationError for valid PNG")

    def test_valid_jpg_passes_validation(self):
        """Test that a valid JPG file passes all validation checks."""
        # Minimal valid JPEG (1x1 pixel, black)
        valid_jpg_content = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c'
            b'\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c'
            b'\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342'
            b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
            b'\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\t'
            b'\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00'
            b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00T\xdf'
            b'\xff\xd9'  # EOI marker
        )

        jpg_file = SimpleUploadedFile(
            "test.jpg",
            valid_jpg_content,
            content_type="image/jpeg"
        )

        # Should not raise ValidationError
        from apps.sources.validators import validate_image_file
        try:
            validate_image_file(jpg_file)
        except ValidationError:
            self.fail("validate_image_file() raised ValidationError for valid JPG")

    def test_non_image_file_raises_validation_error(self):
        """Test that a non-image file is rejected."""
        txt_content = b"This is a plain text file, not an image."

        txt_file = SimpleUploadedFile(
            "test.txt",
            txt_content,
            content_type="text/plain"
        )

        from apps.sources.validators import validate_image_file
        with self.assertRaises(ValidationError) as context:
            validate_image_file(txt_file)

        self.assertIn("Invalid content type", str(context.exception))

    def test_image_exceeding_size_limit_raises_validation_error(self):
        """Test that images larger than 10MB are rejected."""
        from apps.sources.validators import MAX_IMAGE_SIZE

        # Create oversized content with PNG header
        oversized_content = b'\x89PNG\r\n\x1a\n' + b"0" * (MAX_IMAGE_SIZE + 1000)

        oversized_file = SimpleUploadedFile(
            "oversized.png",
            oversized_content,
            content_type="image/png"
        )

        from apps.sources.validators import validate_image_file
        with self.assertRaises(ValidationError) as context:
            validate_image_file(oversized_file)

        self.assertIn("exceeds maximum allowed size", str(context.exception))
