"""Tests for user serializers."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.users.serializers import (
    RegisterSerializer,
    ProfileUpdateSerializer,
    PasswordResetConfirmSerializer,
)

User = get_user_model()


class RegisterSerializerTests(TestCase):
    """Tests for RegisterSerializer."""

    def test_valid_registration_data(self):
        """Test serializer accepts valid registration data."""
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'username': 'newuser',
            'bio': 'Test bio',
            'institution': 'Test University',
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_password_too_short(self):
        """Test serializer rejects password shorter than 8 characters."""
        data = {
            'email': 'user@example.com',
            'password': 'short',
            'username': 'testuser',
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_weak_password_validation(self):
        """Test serializer rejects weak passwords (too common, numeric only)."""
        # Test common password
        data = {
            'email': 'user@example.com',
            'password': 'password',
            'username': 'testuser',
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_email_uniqueness_validation(self):
        """Test serializer rejects duplicate email addresses."""
        # Create existing user
        User.objects.create_user(
            email='existing@example.com',
            username='existinguser',
            password='SecurePass123!',
        )

        # Try to register with same email
        data = {
            'email': 'existing@example.com',
            'password': 'SecurePass123!',
            'username': 'newuser',
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_email_case_insensitive_uniqueness(self):
        """Test email uniqueness is case-insensitive."""
        # Create existing user
        User.objects.create_user(
            email='user@example.com',
            username='existinguser',
            password='SecurePass123!',
        )

        # Try to register with same email (different case)
        data = {
            'email': 'USER@EXAMPLE.COM',
            'password': 'SecurePass123!',
            'username': 'newuser',
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_create_user_with_hashed_password(self):
        """Test serializer creates user with hashed password."""
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'username': 'newuser',
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        # Check user created
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.username, 'newuser')

        # Check password is hashed (not stored in plain text)
        self.assertNotEqual(user.password, 'SecurePass123!')
        self.assertTrue(user.check_password('SecurePass123!'))

    def test_optional_fields(self):
        """Test bio and institution are optional."""
        data = {
            'email': 'user@example.com',
            'password': 'SecurePass123!',
            'username': 'testuser',
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class ProfileUpdateSerializerTests(TestCase):
    """Tests for ProfileUpdateSerializer."""

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='SecurePass123!',
        )

    def test_valid_profile_update(self):
        """Test serializer accepts valid profile data."""
        data = {
            'avatar_url': 'https://example.com/avatar.jpg',
            'bio': 'Updated bio text',
            'institution': 'New University',
        }
        serializer = ProfileUpdateSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

    def test_bio_max_length_validation(self):
        """Test bio cannot exceed 500 characters."""
        data = {
            'bio': 'x' * 501,  # 501 characters
        }
        serializer = ProfileUpdateSerializer(self.user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('bio', serializer.errors)

    def test_bio_exactly_500_chars_valid(self):
        """Test bio with exactly 500 characters is valid."""
        data = {
            'bio': 'x' * 500,  # exactly 500 characters
        }
        serializer = ProfileUpdateSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

    def test_institution_max_length_validation(self):
        """Test institution cannot exceed 200 characters."""
        data = {
            'institution': 'x' * 201,  # 201 characters
        }
        serializer = ProfileUpdateSerializer(self.user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('institution', serializer.errors)

    def test_institution_exactly_200_chars_valid(self):
        """Test institution with exactly 200 characters is valid."""
        data = {
            'institution': 'x' * 200,  # exactly 200 characters
        }
        serializer = ProfileUpdateSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

    def test_invalid_avatar_url(self):
        """Test invalid URL format is rejected."""
        data = {
            'avatar_url': 'not-a-valid-url',
        }
        serializer = ProfileUpdateSerializer(self.user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('avatar_url', serializer.errors)

    def test_valid_avatar_url(self):
        """Test valid URL is accepted."""
        data = {
            'avatar_url': 'https://example.com/avatar.jpg',
        }
        serializer = ProfileUpdateSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

    def test_all_fields_optional(self):
        """Test all fields are optional (partial update)."""
        data = {}
        serializer = ProfileUpdateSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())


class PasswordResetConfirmSerializerTests(TestCase):
    """Tests for PasswordResetConfirmSerializer."""

    def test_valid_password_reset_data(self):
        """Test serializer accepts valid password reset data."""
        data = {
            'uid': 'somebase64uid',
            'token': 'sometoken',
            'new_password': 'NewSecurePass123!',
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_new_password_too_short(self):
        """Test new password must be at least 8 characters."""
        data = {
            'uid': 'somebase64uid',
            'token': 'sometoken',
            'new_password': 'short',
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)

    def test_weak_new_password_validation(self):
        """Test new password strength validation."""
        data = {
            'uid': 'somebase64uid',
            'token': 'sometoken',
            'new_password': 'password',  # Common password
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)

    def test_numeric_only_password_rejected(self):
        """Test numeric-only password is rejected."""
        data = {
            'uid': 'somebase64uid',
            'token': 'sometoken',
            'new_password': '12345678',
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)

    def test_all_fields_required(self):
        """Test all fields are required."""
        # Missing new_password
        data = {
            'uid': 'somebase64uid',
            'token': 'sometoken',
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)

        # Missing uid
        data = {
            'token': 'sometoken',
            'new_password': 'NewSecurePass123!',
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('uid', serializer.errors)

        # Missing token
        data = {
            'uid': 'somebase64uid',
            'new_password': 'NewSecurePass123!',
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)
