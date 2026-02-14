"""
Views for user authentication and management.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from .models import User, EmailPreference
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    EmailVerificationSerializer,
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ProfileUpdateSerializer,
    OnboardingSerializer,
    EmailPreferenceSerializer,
)
from .tokens import generate_verification_token, verify_token
from .emails import send_verification_email, send_password_reset_email
from .tasks import send_verification_email_task, send_password_reset_email_task, send_welcome_email_task

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get the client IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def register(request):
    """
    Register a new user account.

    Rate limited to 5 attempts per minute per IP.
    Sends email verification link upon successful registration.
    """
    serializer = UserRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        user.email_verification_sent_at = timezone.now()
        user.save(update_fields=['email_verification_sent_at'])

        # Send verification email
        send_verification_email(user)

        # Return user data without sensitive fields
        user_data = UserSerializer(user).data

        return Response({
            'message': 'Registration successful. Please check your email to verify your account.',
            'user': user_data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify user email with token from verification link.
    """
    serializer = EmailVerificationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    token = serializer.validated_data['token']

    try:
        user = User.objects.get(email_verification_token=token)

        if user.email_verified:
            return Response({
                'message': 'Email already verified.'
            }, status=status.HTTP_200_OK)

        user.verify_email()

        return Response({
            'message': 'Email verified successfully. You can now log in.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'error': 'Invalid or expired verification token.'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='3/h', method='POST', block=True)
def resend_verification(request):
    """
    Resend verification email.

    Rate limited to 3 attempts per hour per IP.
    """
    email = request.data.get('email')

    if not email:
        return Response({
            'error': 'Email is required.'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email__iexact=email)

        if user.email_verified:
            return Response({
                'message': 'Email already verified.'
            }, status=status.HTTP_200_OK)

        # Generate new token and send email
        user.generate_verification_token()
        user.email_verification_sent_at = timezone.now()
        user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])

        send_verification_email(user)

        return Response({
            'message': 'Verification email sent. Please check your inbox.'
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        # Don't reveal if email exists or not
        return Response({
            'message': 'If the email exists, a verification link has been sent.'
        }, status=status.HTTP_200_OK)


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view with rate limiting and httpOnly cookie support.

    Rate limited to 5 attempts per minute per IP.
    Returns JWT tokens with user ID and email claims.
    Optionally stores refresh token in httpOnly cookie.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Optionally set refresh token as httpOnly cookie.
        """
        response = super().finalize_response(request, response, *args, **kwargs)

        # If login successful and refresh token exists
        if response.status_code == 200 and 'refresh' in response.data:
            # Check if client wants cookie-based refresh token
            use_cookie = request.data.get('use_cookie', False)

            if use_cookie:
                # Set refresh token in httpOnly cookie
                response.set_cookie(
                    key='refresh_token',
                    value=response.data['refresh'],
                    httponly=True,
                    secure=not settings.DEBUG,  # HTTPS only in production
                    samesite='Lax',
                    max_age=60 * 60 * 24 * 7,  # 7 days
                )
                # Remove refresh token from response body for security
                # Keep it in response for backward compatibility
                # response.data.pop('refresh')

        return response


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class RegisterView(APIView):
    """
    Register a new user account (US-014).

    POST /api/v1/auth/register/
    Rate limited to 5 attempts per minute per IP.
    Creates user with email_verified=False and sends verification email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Create new user and send verification email."""
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create user with email_verified=False (default in model)
        user = serializer.save()

        # Generate verification token and save to database before queuing task
        token = generate_verification_token(user)

        # Send verification email asynchronously via Celery
        # Fallback to synchronous if Celery is unavailable
        try:
            send_verification_email_task.delay(user.id, token)
        except Exception as e:
            # Celery not available - send synchronously as fallback
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Celery unavailable, sending verification email synchronously: {str(e)}")
            send_verification_email(user, token)

        # Return user data with message
        user_data = UserSerializer(user).data

        return Response({
            'user': user_data,
            'message': 'Registration successful. Please check your email to verify your account.'
        }, status=status.HTTP_201_CREATED)


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='dispatch')
class VerifyEmailView(APIView):
    """
    Verify user email address with token (US-015).

    POST /api/v1/auth/verify-email/
    Rate limited to 10 attempts per minute per IP.
    Accepts token in request body and validates it.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Verify email using token from verification link."""
        token = request.data.get('token')

        if not token:
            return Response({
                'error': 'Token is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate token using tokens.py logic
        user = verify_token(token)

        if user is None:
            return Response({
                'error': 'Invalid or expired verification token.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if this is first-time verification
        is_first_verification = not user.email_verified

        # Set email_verified = True
        user.email_verified = True
        user.save(update_fields=['email_verified'])

        # Send welcome email only on first-time verification
        if is_first_verification:
            try:
                send_welcome_email_task.delay(user.id)
            except Exception as e:
                # Log error but don't fail verification if Celery unavailable
                logger.warning(f"Failed to queue welcome email for user {user.id}: {str(e)}")

        return Response({
            'message': 'Email verified successfully. You can now log in.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class LoginView(APIView):
    """
    Login with email and password to receive JWT tokens (US-016).

    POST /api/v1/auth/login/
    Rate limited to 5 attempts per minute per IP.
    Authenticates user and checks email_verified status before issuing tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Authenticate user and return JWT tokens."""
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                'error': 'Email and password are required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate using Django's authenticate()
        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response({
                'error': 'Invalid email or password.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Check email_verified status
        if not user.email_verified:
            return Response({
                'error': 'Email not verified. Please check your email for the verification link.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Generate access and refresh tokens using SimpleJWT
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # Return tokens and user data
        return Response({
            'access': str(access),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Logout user by blacklisting refresh token (US-017).

    POST /api/v1/auth/logout/
    Requires authentication.
    Accepts refresh token in request body and blacklists it.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Blacklist the refresh token to invalidate it."""
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({
                'error': 'Refresh token is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Blacklist the refresh token using SimpleJWT
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                'message': 'Logout successful.'
            }, status=status.HTTP_200_OK)

        except TokenError as e:
            return Response({
                'error': f'Invalid token: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ratelimit(key='ip', rate='20/m', method='POST', block=True), name='dispatch')
class RefreshTokenView(APIView):
    """
    Refresh access token using refresh token (US-018).

    POST /api/v1/auth/refresh/
    Rate limited to 20 attempts per minute per IP.
    Accepts refresh token and returns new access token.
    If ROTATE_REFRESH_TOKENS is enabled, also returns new refresh token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Generate new access token from refresh token."""
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({
                'error': 'Refresh token is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create RefreshToken instance from the provided token to validate it
            old_refresh = RefreshToken(refresh_token)

            # Get the user from the token
            user_id = old_refresh['user_id']
            from apps.users.models import User
            user = User.objects.get(id=user_id)

            # Blacklist the old refresh token (token rotation)
            old_refresh.blacklist()

            # Generate new refresh and access tokens
            new_refresh = RefreshToken.for_user(user)
            access = new_refresh.access_token

            # Prepare response with new tokens
            response_data = {
                'access': str(access),
                'refresh': str(new_refresh),
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except TokenError as e:
            return Response({
                'error': f'Invalid or expired refresh token: {str(e)}'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid refresh token: User not found.'
            }, status=status.HTTP_401_UNAUTHORIZED)


@method_decorator(ratelimit(key='user_or_ip', rate='3/h', method='POST', block=True), name='dispatch')
class PasswordResetRequestView(APIView):
    """
    Request password reset email (US-019).

    POST /api/v1/auth/password-reset/
    Rate limited to 3 attempts per hour per email.
    Generates reset token and sends email if user exists.
    Always returns success to prevent user enumeration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Generate password reset token and send email."""
        serializer = PasswordResetRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']

        # Get request metadata for security notice in email
        request_ip = get_client_ip(request)
        request_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')

        # Try to find user by email
        try:
            user = User.objects.get(email__iexact=email)

            # Generate reset token using Django's PasswordResetTokenGenerator
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)

            # Encode user ID in base64
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Send password reset email asynchronously via Celery
            try:
                send_password_reset_email_task.delay(user.id, uid, token, request_ip, request_time)
            except Exception as e:
                # Fallback to sync if Celery unavailable
                logger.warning(f"Celery unavailable, falling back to sync email: {str(e)}")
                send_password_reset_email(user, uid, token, request_ip, request_time)

        except User.DoesNotExist:
            # Don't reveal if email exists or not - just continue
            pass

        # Always return success (no user enumeration)
        return Response({
            'message': 'If an account exists with this email, a password reset link has been sent.'
        }, status=status.HTTP_200_OK)


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='dispatch')
class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token and set new password (US-021).

    POST /api/v1/auth/password-reset-confirm/
    Rate limited to 10 attempts per minute per IP.
    Accepts uid, token, and new_password to complete password reset.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Validate reset token and update user password."""
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            # Decode uid and fetch user
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)

            # Validate token using PasswordResetTokenGenerator
            token_generator = PasswordResetTokenGenerator()
            if not token_generator.check_token(user, token):
                return Response({
                    'error': 'Invalid or expired reset token.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update user password (hashed)
            user.set_password(new_password)
            user.save(update_fields=['password'])

            return Response({
                'message': 'Password reset successful. You can now log in with your new password.'
            }, status=status.HTTP_200_OK)

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Invalid reset link.'
            }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """
    View and update user profile (US-022).

    GET /api/v1/users/profile/ returns current user's profile.
    PATCH /api/v1/users/profile/ updates avatar_url, bio, institution.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return current user's profile data."""
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Update current user's profile fields."""
        user = request.user
        serializer = ProfileUpdateSerializer(user, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Reject attempts to change email or password
        if 'email' in request.data or 'password' in request.data:
            return Response({
                'error': 'Email and password cannot be changed through this endpoint.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response({
            'message': 'Profile updated successfully.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class OnboardingView(APIView):
    """
    View and update onboarding progress (US-002).

    GET /api/v1/users/me/onboarding/ returns current onboarding state.
    PATCH /api/v1/users/me/onboarding/ updates onboarding progress.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return current user's onboarding state."""
        from django.conf import settings

        # Check if onboarding is enabled
        if not settings.ONBOARDING_ENABLED:
            return Response(
                {'detail': 'Onboarding feature is currently disabled.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user

        return Response({
            'step': user.onboarding_step,
            'completed': user.onboarding_completed,
            'path': user.onboarding_path,
            'data': user.onboarding_data or {}
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        """Update current user's onboarding progress."""
        from django.utils import timezone
        from django.conf import settings
        import logging

        # Check if onboarding is enabled
        if not settings.ONBOARDING_ENABLED:
            return Response(
                {'detail': 'Onboarding feature is currently disabled.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        serializer = OnboardingSerializer(data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Update onboarding fields
        update_fields = []

        # Set onboarding_started_at on first step (if not already set)
        if not user.onboarding_started_at and 'step' in serializer.validated_data:
            user.onboarding_started_at = timezone.now()
            update_fields.append('onboarding_started_at')

        if 'step' in serializer.validated_data:
            user.onboarding_step = serializer.validated_data['step']
            update_fields.append('onboarding_step')

        if 'completed' in serializer.validated_data:
            user.onboarding_completed = serializer.validated_data['completed']
            update_fields.append('onboarding_completed')

            # Set onboarding_completed_at when completing onboarding
            if serializer.validated_data['completed'] and not user.onboarding_completed_at:
                user.onboarding_completed_at = timezone.now()
                update_fields.append('onboarding_completed_at')

                # Log completion metrics
                logger = logging.getLogger(__name__)
                time_to_complete = None
                if user.onboarding_started_at:
                    time_to_complete = (timezone.now() - user.onboarding_started_at).total_seconds()

                logger.info(
                    f"Onboarding completed | "
                    f"user={user.email} | "
                    f"path={user.onboarding_path or 'unknown'} | "
                    f"time_to_complete={time_to_complete}s"
                )

        if 'path' in serializer.validated_data:
            user.onboarding_path = serializer.validated_data['path']
            update_fields.append('onboarding_path')

            # Log path selection
            logger = logging.getLogger(__name__)
            logger.info(
                f"Onboarding path selected | "
                f"user={user.email} | "
                f"path={serializer.validated_data['path']}"
            )

        if 'data' in serializer.validated_data:
            # Merge with existing data if it exists
            existing_data = user.onboarding_data or {}
            new_data = serializer.validated_data['data']
            user.onboarding_data = {**existing_data, **new_data}
            update_fields.append('onboarding_data')

        if update_fields:
            user.save(update_fields=update_fields)

        return Response({
            'step': user.onboarding_step,
            'completed': user.onboarding_completed,
            'path': user.onboarding_path,
            'data': user.onboarding_data or {}
        }, status=status.HTTP_200_OK)


class DemoVaultResetView(APIView):
    """
    Reset demo vault to its original state (US-005).

    POST /api/v1/users/me/demo-vault/reset/
    Deletes existing demo vault and creates a fresh one from template.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Delete existing demo vault and create fresh one."""
        from apps.vaults.models import Vault, VaultMembership
        from apps.vaults.serializers import VaultSerializer
        from .services.onboarding import create_demo_vault
        from django.db.models.signals import post_delete
        from apps.vaults import signals as vault_signals
        from django.conf import settings

        # Check if onboarding is enabled
        if not settings.ONBOARDING_ENABLED:
            return Response(
                {'detail': 'Onboarding feature is currently disabled.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user

        # Delete existing demo vault if it exists
        # Use the same name as in create_demo_vault function
        demo_vault = Vault.objects.filter(
            owner=user,
            name="AI Research Papers 2025"
        ).first()

        if demo_vault:
            # Temporarily disconnect the membership deletion signal to avoid
            # audit log FK constraint violations during cascade deletion
            post_delete.disconnect(vault_signals.log_membership_removed, sender=VaultMembership)

            try:
                # Delete vault (cascade will delete sources, annotations, memberships, audit logs)
                demo_vault.delete()
            finally:
                # Reconnect the signal
                post_delete.connect(vault_signals.log_membership_removed, sender=VaultMembership)

        # Create fresh demo vault from template
        new_vault = create_demo_vault(user)

        # Serialize and return vault data
        serializer = VaultSerializer(new_vault, context={'request': request})

        return Response({
            'message': 'Demo vault reset successfully.',
            'vault': serializer.data
        }, status=status.HTTP_200_OK)


class DemoVaultStatusView(APIView):
    """
    Check demo vault status (US-006).

    GET /api/v1/users/me/demo-vault/status/
    Returns whether demo vault exists and its ID if present.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return demo vault existence status."""
        from apps.vaults.models import Vault
        from django.conf import settings

        # Check if onboarding is enabled
        if not settings.ONBOARDING_ENABLED:
            return Response(
                {'detail': 'Onboarding feature is currently disabled.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user

        # Check if demo vault exists
        demo_vault = Vault.objects.filter(
            owner=user,
            name="AI Research Papers 2025"
        ).first()

        if demo_vault:
            return Response({
                'exists': True,
                'vault_id': str(demo_vault.id)
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'exists': False,
                'vault_id': None
            }, status=status.HTTP_200_OK)


class DemoVaultCreateView(APIView):
    """
    Create demo vault if it doesn't exist (US-006).

    POST /api/v1/users/me/demo-vault/create/
    Creates demo vault from template if it doesn't already exist.
    Returns error if demo vault already exists.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create demo vault if it doesn't exist."""
        from apps.vaults.models import Vault
        from apps.vaults.serializers import VaultSerializer
        from .services.onboarding import create_demo_vault
        from django.conf import settings

        # Check if onboarding is enabled
        if not settings.ONBOARDING_ENABLED:
            return Response(
                {'detail': 'Onboarding feature is currently disabled.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user

        # Check if demo vault already exists
        existing_vault = Vault.objects.filter(
            owner=user,
            name="AI Research Papers 2025"
        ).first()

        if existing_vault:
            return Response({
                'error': 'Demo vault already exists.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create demo vault from template
        new_vault = create_demo_vault(user)

        # Serialize and return vault data
        serializer = VaultSerializer(new_vault, context={'request': request})

        return Response({
            'message': 'Demo vault created successfully.',
            'vault': serializer.data
        }, status=status.HTTP_201_CREATED)


# OAuth Views (PRD12)

class GoogleOAuthRedirectView(APIView):
    """
    Initiate Google OAuth flow (US-005).

    GET /api/v1/auth/google/
    Accepts optional 'next' query parameter for post-auth redirect.
    Redirects user to Google's consent screen.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Redirect to Google OAuth consent screen."""
        # Check if Google OAuth is configured
        google_client_id = settings.SOCIALACCOUNT_PROVIDERS.get('google', {}).get('APP', {}).get('client_id')

        if not google_client_id:
            return Response({
                'error': 'Google OAuth is not configured. Please contact support.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Store 'next' URL in session for post-auth redirect
        next_url = request.GET.get('next', '')
        if next_url:
            request.session['oauth_next_url'] = next_url

        # Use allauth's Google OAuth view to redirect to consent screen
        from allauth.socialaccount.providers.google.views import oauth2_login
        return oauth2_login(request)


class GitHubOAuthRedirectView(APIView):
    """
    Initiate GitHub OAuth flow (US-007).

    GET /api/v1/auth/github/
    Accepts optional 'next' query parameter for post-auth redirect.
    Redirects user to GitHub's authorization screen.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Redirect to GitHub OAuth authorization screen."""
        # Check if GitHub OAuth is configured
        github_client_id = settings.SOCIALACCOUNT_PROVIDERS.get('github', {}).get('APP', {}).get('client_id')

        if not github_client_id:
            return Response({
                'error': 'GitHub OAuth is not configured. Please contact support.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Store 'next' URL in session for post-auth redirect
        next_url = request.GET.get('next', '')
        if next_url:
            request.session['oauth_next_url'] = next_url

        # Use allauth's GitHub OAuth view to redirect to authorization screen
        from allauth.socialaccount.providers.github.views import oauth2_login
        return oauth2_login(request)


class LinkOAuthAccountView(APIView):
    """
    Link OAuth provider to existing account with password confirmation (US-009).

    POST /api/v1/auth/oauth/link/
    Body: { password: string, provider: 'google' | 'github' }

    Links pending OAuth provider (stored in session) to existing user account
    after validating password.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Link OAuth provider to existing account."""
        password = request.data.get('password')
        provider = request.data.get('provider')

        # Validate inputs
        if not password or not provider:
            return Response({
                'error': 'Password and provider are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if provider not in ['google', 'github']:
            return Response({
                'error': 'Invalid provider. Must be "google" or "github"'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check for pending OAuth data in session
        pending_oauth = request.session.get('pending_oauth')
        oauth_needs_linking = request.session.get('oauth_needs_linking', False)

        if not pending_oauth or not oauth_needs_linking:
            return Response({
                'error': 'No pending OAuth data found. Please restart the OAuth flow'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify provider matches
        if pending_oauth.get('provider') != provider:
            return Response({
                'error': 'Provider mismatch'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get email from pending OAuth data
        email = pending_oauth.get('email')
        if not email:
            return Response({
                'error': 'No email found in OAuth data'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get user by email
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify password
        if not user.check_password(password):
            return Response({
                'error': 'Incorrect password'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Create SocialAccount linking OAuth provider to user
        from allauth.socialaccount.models import SocialAccount

        # Check if social account already exists
        social_account = SocialAccount.objects.filter(
            user=user,
            provider=provider
        ).first()

        if social_account:
            # Already linked - just clear session and login
            pass
        else:
            # Create new SocialAccount
            social_account = SocialAccount.objects.create(
                user=user,
                provider=provider,
                uid=pending_oauth.get('uid'),
                extra_data=pending_oauth.get('extra_data', {})
            )

        # Clear OAuth session data
        request.session.pop('pending_oauth', None)
        request.session.pop('oauth_needs_linking', None)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # Build response with tokens
        response = Response({
            'message': 'OAuth provider linked successfully',
            'access_token': str(access),
            'refresh_token': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

        # Set tokens in httpOnly cookies
        response.set_cookie(
            key='access_token',
            value=str(access),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=60 * 15,  # 15 minutes
        )

        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=60 * 60 * 24 * 7,  # 7 days
        )

        return response


class CompleteOAuthEmailView(APIView):
    """
    Submit email to complete GitHub OAuth registration (US-010).

    POST /api/v1/auth/oauth/complete-email/
    Body: { email: string, temp_token: string }

    For GitHub users with private email, completes registration by accepting email.
    Validates email uniqueness and creates User + SocialAccount.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Complete OAuth registration with user-provided email."""
        email = request.data.get('email')
        temp_token = request.data.get('temp_token')

        # Validate inputs
        if not email or not temp_token:
            return Response({
                'error': 'Email and temp_token are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate email format
        from django.core.validators import EmailValidator
        from django.core.exceptions import ValidationError as DjangoValidationError
        validator = EmailValidator()
        try:
            validator(email)
        except DjangoValidationError:
            return Response({
                'error': 'Invalid email format'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check for pending OAuth data in session
        pending_oauth = request.session.get('pending_oauth')
        oauth_needs_email = request.session.get('oauth_needs_email', False)

        if not pending_oauth or not oauth_needs_email:
            return Response({
                'error': 'No pending OAuth data found. Please restart the OAuth flow'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate temp_token matches (simple check - in production use signed tokens)
        session_token = request.session.get('oauth_temp_token')
        if session_token != temp_token:
            return Response({
                'error': 'Invalid or expired temp_token'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if email already exists
        existing_user = User.objects.filter(email__iexact=email).first()

        if existing_user:
            # Email exists - need to link instead
            # Store email in pending_oauth for linking flow
            pending_oauth['email'] = email
            request.session['pending_oauth'] = pending_oauth
            request.session['oauth_needs_linking'] = True
            request.session['oauth_needs_email'] = False

            return Response({
                'link_required': True,
                'provider': pending_oauth.get('provider'),
                'message': 'An account with this email already exists. Please link your account.'
            }, status=status.HTTP_200_OK)

        # Email is new - create User + SocialAccount
        provider = pending_oauth.get('provider')
        uid = pending_oauth.get('uid')
        extra_data = pending_oauth.get('extra_data', {})

        # Extract username from extra_data (for GitHub)
        username = extra_data.get('login') or email.split('@')[0]

        # Create new user
        user = User.objects.create_user(
            email=email,
            username=username,
            email_verified=True  # OAuth providers verify email
        )

        # Create SocialAccount
        from allauth.socialaccount.models import SocialAccount
        SocialAccount.objects.create(
            user=user,
            provider=provider,
            uid=uid,
            extra_data=extra_data
        )

        # Clear OAuth session data
        request.session.pop('pending_oauth', None)
        request.session.pop('oauth_needs_email', None)
        request.session.pop('oauth_temp_token', None)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # Build response with tokens
        response = Response({
            'message': 'Registration completed successfully',
            'access_token': str(access),
            'refresh_token': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

        # Set tokens in httpOnly cookies
        response.set_cookie(
            key='access_token',
            value=str(access),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=60 * 15,  # 15 minutes
        )

        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=60 * 60 * 24 * 7,  # 7 days
        )

        return response


class ConnectedAccountsListView(APIView):
    """
    List connected OAuth providers for authenticated user (US-011).

    GET /api/v1/auth/oauth/connected/
    Returns list of OAuth providers linked to user's account with metadata.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve list of connected OAuth providers."""
        from allauth.socialaccount.models import SocialAccount

        user = request.user

        # Get all SocialAccounts for this user
        social_accounts = SocialAccount.objects.filter(user=user).select_related('user')

        # Build response list with provider-specific data
        connected_accounts = []
        for account in social_accounts:
            provider_data = {
                'provider': account.provider,
                'connected_at': account.date_joined,
                'email': account.extra_data.get('email', ''),
            }

            # Add provider-specific data
            if account.provider == 'google':
                provider_data['profile_picture'] = account.extra_data.get('picture', '')
            elif account.provider == 'github':
                provider_data['username'] = account.extra_data.get('login', '')
                provider_data['avatar_url'] = account.extra_data.get('avatar_url', '')

            connected_accounts.append(provider_data)

        return Response(connected_accounts, status=status.HTTP_200_OK)


class DisconnectOAuthProviderView(APIView):
    """
    Disconnect an OAuth provider from authenticated user's account (US-012).

    DELETE /api/v1/auth/oauth/connected/{provider}/
    Removes OAuth provider link. Requires at least one other auth method to prevent lockout.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, provider):
        """Disconnect OAuth provider from user account."""
        from allauth.socialaccount.models import SocialAccount

        # Validate provider is valid
        if provider not in ['google', 'github']:
            return Response({
                'error': f'Invalid provider. Must be "google" or "github", got "{provider}"'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # Check if user has this provider connected
        try:
            social_account = SocialAccount.objects.get(user=user, provider=provider)
        except SocialAccount.DoesNotExist:
            return Response({
                'error': f'No {provider} account connected to your profile'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if user has at least one other auth method
        # User must have either:
        # - A usable password (has_usable_password = True), OR
        # - At least one other OAuth provider
        has_password = user.has_usable_password()
        other_oauth_count = SocialAccount.objects.filter(user=user).exclude(provider=provider).count()

        if not has_password and other_oauth_count == 0:
            return Response({
                'error': 'Cannot disconnect your only authentication method. Please set a password first or connect another OAuth provider.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Safe to delete - user has another way to login
        social_account.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class UnsubscribeView(APIView):
    """
    Unsubscribe from email notifications via token link (US-011).

    GET /api/v1/auth/unsubscribe/{token}/
    Validates unsubscribe token and sets collaboration_notifications to False.
    Returns success message (could also redirect to a frontend success page).
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        """Unsubscribe user from collaboration notifications."""
        try:
            # Find EmailPreference by unsubscribe token
            email_pref = EmailPreference.objects.get(unsubscribe_token=token)

            # Set collaboration_notifications to False
            email_pref.collaboration_notifications = False
            email_pref.save(update_fields=['collaboration_notifications'])

            return Response({
                'message': 'You have been unsubscribed from collaboration notifications.',
                'email': email_pref.user.email
            }, status=status.HTTP_200_OK)

        except EmailPreference.DoesNotExist:
            return Response({
                'error': 'Invalid unsubscribe token.'
            }, status=status.HTTP_400_BAD_REQUEST)


class EmailPreferenceUpdateView(APIView):
    """
    Update email preferences for authenticated user (US-011).

    POST /api/v1/users/email-preferences/
    Allows users to update their email notification settings.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Update email preferences for current user."""
        user = request.user

        # Get or create EmailPreference (should exist from signal, but safety check)
        email_pref, created = EmailPreference.objects.get_or_create(user=user)

        # Validate and update preferences
        serializer = EmailPreferenceSerializer(email_pref, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response({
            'message': 'Email preferences updated successfully.',
            'preferences': {
                'collaboration_notifications': email_pref.collaboration_notifications,
                'marketing_emails': email_pref.marketing_emails,
            }
        }, status=status.HTTP_200_OK)
