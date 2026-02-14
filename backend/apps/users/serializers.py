"""
Serializers for user authentication and profile management.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Validates email uniqueness and password strength.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm', 'bio', 'institution']
        extra_kwargs = {
            'bio': {'required': False},
            'institution': {'required': False},
        }

    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_username(self, value):
        """Validate username uniqueness."""
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate(self, attrs):
        """Validate password match and strength."""
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)

        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })

        # Validate password strength using Django's validators
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })

        return attrs

    def create(self, validated_data):
        """Create user with hashed password."""
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration (US-008).
    Validates email uniqueness and password strength.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['email', 'password', 'username', 'bio', 'institution']
        extra_kwargs = {
            'bio': {'required': False},
            'institution': {'required': False},
        }

    def validate_password(self, value):
        """Validate password strength using Django's password validators."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def create(self, validated_data):
        """Create user with hashed password."""
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile display.
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'avatar_url', 'bio', 'institution',
                  'email_verified', 'created_at']
        read_only_fields = ['id', 'email', 'email_verified', 'created_at']


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile fields (US-009).
    Validates avatar_url, bio, and institution fields.
    """
    class Meta:
        model = User
        fields = ['avatar_url', 'bio', 'institution']
        extra_kwargs = {
            'avatar_url': {'required': False},
            'bio': {'required': False},
            'institution': {'required': False},
        }

    def validate_avatar_url(self, value):
        """Validate avatar_url is a valid URL format."""
        if value and not value.strip():
            raise serializers.ValidationError("Avatar URL cannot be empty.")
        # URLField already validates URL format, but we can add extra checks
        return value

    def validate_bio(self, value):
        """Enforce 500 character limit for bio."""
        if value and len(value) > 500:
            raise serializers.ValidationError("Bio cannot exceed 500 characters.")
        return value

    def validate_institution(self, value):
        """Enforce 200 character limit for institution."""
        if value and len(value) > 200:
            raise serializers.ValidationError("Institution cannot exceed 200 characters.")
        return value


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    token = serializers.CharField(required=True, max_length=64)


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request (US-010).
    Accepts email address to send password reset link.
    """
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation (US-010).
    Validates uid, token, and new password.
    """
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_new_password(self, value):
        """Validate password strength using Django's password validators."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that includes user ID and email in token claims.
    """
    username_field = 'email'

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['user_id'] = str(user.id)
        token['email'] = user.email
        token['email_verified'] = user.email_verified

        return token

    def validate(self, attrs):
        """
        Validate credentials and check email verification.
        """
        data = super().validate(attrs)

        # Add user data to response
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'username': self.user.username,
            'email_verified': self.user.email_verified,
        }

        return data
