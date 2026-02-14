from django.test import TestCase
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User, EmailVerificationToken


class UserModelTestCase(TestCase):
    """Test suite for User model"""

    def test_user_creation_with_all_fields(self):
        """Test creating a user with all fields"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            avatar_url='https://example.com/avatar.jpg',
            bio='Test bio for user',
            institution='Test University'
        )

        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.avatar_url, 'https://example.com/avatar.jpg')
        self.assertEqual(user.bio, 'Test bio for user')
        self.assertEqual(user.institution, 'Test University')
        self.assertFalse(user.email_verified)  # Default is False
        self.assertTrue(user.check_password('testpass123'))
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)

    def test_email_uniqueness_constraint(self):
        """Test that email must be unique"""
        User.objects.create_user(
            email='duplicate@example.com',
            username='user1',
            password='testpass123'
        )

        # Attempting to create another user with same email should fail
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='duplicate@example.com',
                username='user2',
                password='testpass123'
            )

    def test_email_verified_default_is_false(self):
        """Test that email_verified defaults to False"""
        user = User.objects.create_user(
            email='newuser@example.com',
            username='newuser',
            password='testpass123'
        )

        self.assertFalse(user.email_verified)

    def test_user_string_representation(self):
        """Test __str__ method returns email"""
        user = User.objects.create_user(
            email='stringtest@example.com',
            username='stringtest',
            password='testpass123'
        )

        self.assertEqual(str(user), 'stringtest@example.com')

    def test_username_field_is_email(self):
        """Test that USERNAME_FIELD is set to email"""
        self.assertEqual(User.USERNAME_FIELD, 'email')

    def test_user_creation_with_minimal_fields(self):
        """Test creating a user with only required fields"""
        user = User.objects.create_user(
            email='minimal@example.com',
            username='minimal',
            password='testpass123'
        )

        self.assertEqual(user.email, 'minimal@example.com')
        self.assertEqual(user.username, 'minimal')
        self.assertEqual(user.avatar_url, '')  # blank=True defaults to empty string
        self.assertEqual(user.bio, '')
        self.assertEqual(user.institution, '')


class EmailVerificationTokenModelTestCase(TestCase):
    """Test suite for EmailVerificationToken model"""

    def setUp(self):
        """Create a test user for token tests"""
        self.user = User.objects.create_user(
            email='tokentest@example.com',
            username='tokentest',
            password='testpass123'
        )

    def test_token_creation_with_all_fields(self):
        """Test creating a verification token"""
        expires_at = timezone.now() + timedelta(hours=24)
        token = EmailVerificationToken.objects.create(
            user=self.user,
            token='test_token_123456',
            expires_at=expires_at
        )

        self.assertEqual(token.user, self.user)
        self.assertEqual(token.token, 'test_token_123456')
        self.assertIsNotNone(token.created_at)
        self.assertEqual(token.expires_at, expires_at)

    def test_token_user_relationship(self):
        """Test ForeignKey relationship to User"""
        expires_at = timezone.now() + timedelta(hours=24)
        token = EmailVerificationToken.objects.create(
            user=self.user,
            token='relationship_test_token',
            expires_at=expires_at
        )

        # Access token from user (related_name='verification_tokens')
        user_tokens = self.user.verification_tokens.all()
        self.assertEqual(user_tokens.count(), 1)
        self.assertEqual(user_tokens.first(), token)

    def test_token_uniqueness(self):
        """Test that token must be unique"""
        expires_at = timezone.now() + timedelta(hours=24)
        EmailVerificationToken.objects.create(
            user=self.user,
            token='unique_token_123',
            expires_at=expires_at
        )

        # Create another user
        user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='testpass123'
        )

        # Attempting to create token with same token string should fail
        with self.assertRaises(IntegrityError):
            EmailVerificationToken.objects.create(
                user=user2,
                token='unique_token_123',
                expires_at=expires_at
            )

    def test_token_deletion_on_user_deletion(self):
        """Test that tokens are deleted when user is deleted"""
        expires_at = timezone.now() + timedelta(hours=24)
        token = EmailVerificationToken.objects.create(
            user=self.user,
            token='cascade_test_token',
            expires_at=expires_at
        )

        token_id = token.id

        # Delete the user
        self.user.delete()

        # Token should be deleted too (CASCADE)
        self.assertFalse(
            EmailVerificationToken.objects.filter(id=token_id).exists()
        )

    def test_token_string_representation(self):
        """Test __str__ method returns formatted string with user email"""
        expires_at = timezone.now() + timedelta(hours=24)
        token = EmailVerificationToken.objects.create(
            user=self.user,
            token='string_repr_token',
            expires_at=expires_at
        )

        self.assertIn('tokentest@example.com', str(token))
        self.assertEqual(str(token), f'Token for {self.user.email}')
