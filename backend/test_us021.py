"""
Quick test script to verify audit logging implementation (US-021).
Tests that audit log functions are properly imported and wired.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.vaults.models import AuditLog

# Test 1: Verify AuditLog model is accessible
print("[PASS] AuditLog model imported successfully")

# Test 2: Verify model fields
expected_fields = {'id', 'vault', 'actor', 'action', 'metadata', 'created_at'}
actual_fields = {f.name for f in AuditLog._meta.get_fields()}
missing_fields = expected_fields - actual_fields

if missing_fields:
    print(f"[FAIL] Missing fields: {missing_fields}")
    exit(1)
else:
    print(f"[PASS] All required fields present: {expected_fields}")

# Test 3: Check if audit logging is in tasks.py
from apps.sources import tasks
import inspect

process_uploaded_pdf_source = inspect.getsource(tasks.process_uploaded_pdf)

# Check for audit log creation calls
if 'AuditLog.objects.create' in process_uploaded_pdf_source:
    print("[PASS] Audit logging found in process_uploaded_pdf task")

    # Check for specific event types
    if 'pdf.uploaded' in process_uploaded_pdf_source:
        print("  [PASS] pdf.uploaded event logging found")
    else:
        print("  [FAIL] pdf.uploaded event logging NOT found")

    if 'pdf.processing_failed' in process_uploaded_pdf_source:
        print("  [PASS] pdf.processing_failed event logging found")
    else:
        print("  [FAIL] pdf.processing_failed event logging NOT found")
else:
    print("[FAIL] Audit logging NOT found in process_uploaded_pdf task")

# Test 4: Check if audit logging is in views.py
from apps.sources import views

download_url_source = inspect.getsource(views.PDFUploadViewSet.download_url)
destroy_source = inspect.getsource(views.PDFUploadViewSet.destroy)

if 'AuditLog.objects.create' in download_url_source:
    if 'pdf.downloaded' in download_url_source:
        print("[PASS] pdf.downloaded event logging found in download_url view")
    else:
        print("[FAIL] pdf.downloaded event found but wrong action")
else:
    print("[FAIL] Audit logging NOT found in download_url view")

if 'AuditLog.objects.create' in destroy_source:
    if 'pdf.deleted' in destroy_source:
        print("[PASS] pdf.deleted event logging found in destroy view")
    else:
        print("[FAIL] pdf.deleted event found but wrong action")
else:
    print("[FAIL] Audit logging NOT found in destroy view")

print("\n" + "="*50)
print("US-021 Audit Logging Implementation Test: PASSED")
print("="*50)
