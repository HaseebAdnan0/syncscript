"""
File upload validation utilities for SyncScript.

Provides strict validation for PDF uploads to prevent malicious files.
"""

import magic
from django.core.exceptions import ValidationError
from pypdf import PdfReader
from io import BytesIO


MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
ALLOWED_CONTENT_TYPE = "application/pdf"
PDF_MAGIC_NUMBERS = [
    b"%PDF-1.0",
    b"%PDF-1.1",
    b"%PDF-1.2",
    b"%PDF-1.3",
    b"%PDF-1.4",
    b"%PDF-1.5",
    b"%PDF-1.6",
    b"%PDF-1.7",
    b"%PDF-2.0",
]

# Image validation constants (US-003)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
ALLOWED_IMAGE_TYPES = {
    'image/png': [b'\x89PNG'],
    'image/jpeg': [b'\xff\xd8\xff'],
}


def validate_pdf_file(file) -> None:
    """
    Validate that uploaded file is a legitimate PDF.

    Performs multiple security checks:
    - File size limit (50MB)
    - MIME type verification via content-type
    - Magic number verification (file header)
    - PDF structure validation via pypdf

    Args:
        file: Django UploadedFile instance

    Raises:
        ValidationError: If file fails any validation check
    """
    # Check 1: File size limit
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(
            f"File size ({file.size / 1024 / 1024:.2f}MB) exceeds maximum allowed size of 50MB."
        )

    # Check 2: Content-Type header
    if file.content_type != ALLOWED_CONTENT_TYPE:
        raise ValidationError(
            f"Invalid content type '{file.content_type}'. Only PDF files are allowed."
        )

    # Check 3: Magic number verification
    # Read first 1024 bytes to check magic number
    file.seek(0)
    header = file.read(1024)
    file.seek(0)  # Reset for next read

    # Check if any PDF magic number is present
    has_pdf_magic = any(header.startswith(magic_num) for magic_num in PDF_MAGIC_NUMBERS)
    if not has_pdf_magic:
        raise ValidationError(
            "File does not appear to be a valid PDF (magic number check failed)."
        )

    # Check 4: MIME type via python-magic (reads file content, not just extension)
    mime = magic.Magic(mime=True)
    file.seek(0)
    content = file.read()
    file.seek(0)  # Reset after reading

    detected_mime = mime.from_buffer(content)
    if detected_mime != ALLOWED_CONTENT_TYPE:
        raise ValidationError(
            f"File content does not match PDF format. Detected type: {detected_mime}"
        )

    # Check 5: PDF structure validation via pypdf
    try:
        file.seek(0)
        pdf_reader = PdfReader(BytesIO(content))

        # Try to read page count - will raise exception if PDF is corrupted
        page_count = len(pdf_reader.pages)

        if page_count == 0:
            raise ValidationError("PDF file appears to be empty (0 pages).")

    except Exception as e:
        raise ValidationError(
            f"PDF structure validation failed. File may be corrupted: {str(e)}"
        )
    finally:
        file.seek(0)  # Always reset file pointer

    # All checks passed
    return None
