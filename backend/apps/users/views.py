"""
Views for user authentication and management.
"""
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

from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    EmailVerificationSerializer,
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
)
from .tokens import generate_verification_token, verify_token
from .emails import send_verification_email


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


def send_verification_email(user):
    """
    Send email verification link to user.
    """
    from django.template.loader import render_to_string

    verification_url = f"{settings.SITE_URL}/verify-email?token={user.email_verification_token}"

    context = {
        'user': user,
        'verification_url': verification_url,
    }

    # Render HTML and plain text versions
    html_message = render_to_string('emails/verification_email.html', context)
    plain_message = render_to_string('emails/verification_email.txt', context)

    subject = 'Verify your SyncScript account'

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
        html_message=html_message,
    )


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

        # Generate verification token and send email
        token = generate_verification_token(user)
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

        # Set email_verified = True
        user.email_verified = True
        user.save(update_fields=['email_verified'])

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
            # Create RefreshToken instance from the provided token
            refresh = RefreshToken(refresh_token)

            # Generate new access token
            access = refresh.access_token

            # Prepare response with new access token
            response_data = {
                'access': str(access),
            }

            # If token rotation is enabled, new refresh token is automatically generated
            # The new refresh token is available in the same refresh object
            response_data['refresh'] = str(refresh)

            return Response(response_data, status=status.HTTP_200_OK)

        except TokenError as e:
            return Response({
                'error': f'Invalid or expired refresh token: {str(e)}'
            }, status=status.HTTP_401_UNAUTHORIZED)
