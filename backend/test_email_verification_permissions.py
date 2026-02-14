"""Test script for US-023 email verification permissions."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied
from apps.vaults.permissions import _check_email_verified

User = get_user_model()

print("Testing email verification permission check...\n")

# Create verified user
verified_user = User(username="verified", email="verified@test.com", email_verified=True)
print(f"1. Testing verified user ({verified_user.email}):")
try:
    _check_email_verified(verified_user)
    print("   PASS - No exception raised for verified user")
except PermissionDenied:
    print("   FAIL - Exception raised for verified user")

# Create unverified user
unverified_user = User(username="unverified", email="unverified@test.com", email_verified=False)
print(f"\n2. Testing unverified user ({unverified_user.email}):")
try:
    _check_email_verified(unverified_user)
    print("   FAIL - No exception raised for unverified user")
except PermissionDenied as e:
    print(f"   PASS - PermissionDenied raised: {e.detail}")
    if hasattr(e, 'email_verification_required'):
        print(f"   PASS - email_verification_required flag set: {e.email_verification_required}")
    else:
        print("   FAIL - email_verification_required flag not set")

print("\nAll tests completed!")
