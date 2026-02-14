"""
Custom allauth adapters for JWT-based OAuth authentication.

Overrides default session-based authentication to use JWT tokens instead.
"""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework_simplejwt.tokens import RefreshToken


class JWTSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter that generates JWT tokens after successful OAuth authentication.

    Instead of creating a session, this adapter:
    1. Generates JWT access and refresh tokens using simplejwt
    2. Sets tokens in httpOnly cookies for security
    3. Redirects to frontend with success indicator
    """

    def authentication_error(
        self,
        request,  # noqa: ARG002
        provider_id,
        error=None,
        exception=None,  # noqa: ARG002
        extra_context=None,  # noqa: ARG002
    ):
        """
        Handle OAuth authentication errors by redirecting to frontend with error info.
        """
        # Build frontend URL with error parameter
        frontend_url = settings.SITE_URL
        error_message = str(error) if error else 'authentication_failed'
        redirect_url = f"{frontend_url}/auth/callback?error={error_message}&provider={provider_id}"

        return HttpResponseRedirect(redirect_url)

    def pre_social_login(self, request, sociallogin):  # noqa: ARG002
        """
        Called after successful OAuth but before user is logged in.

        This is where we can check for existing accounts and handle linking logic.
        The actual linking logic will be handled in the callback view.
        """
        # Let allauth handle the basic social login flow
        # We'll override the response generation in get_login_redirect_url
        pass

    def get_login_redirect_url(self, request):
        """
        Override to redirect to frontend after successful OAuth login.

        This is called after authentication is complete. We'll generate JWT tokens
        and redirect to the frontend callback page.
        """
        # Get the user from the request (allauth sets this after successful auth)
        user = request.user

        if user and user.is_authenticated:
            # Generate JWT tokens using simplejwt
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            # Build redirect response to frontend
            frontend_url = settings.SITE_URL
            redirect_url = f"{frontend_url}/auth/callback?success=true"

            # Create response with redirect
            response = HttpResponseRedirect(redirect_url)

            # Set tokens in httpOnly cookies (same pattern as regular login)
            response.set_cookie(
                key='access_token',
                value=str(access),
                httponly=True,
                secure=not settings.DEBUG,  # HTTPS only in production
                samesite='Lax',
                max_age=60 * 15,  # 15 minutes (matches ACCESS_TOKEN_LIFETIME)
            )

            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=not settings.DEBUG,  # HTTPS only in production
                samesite='Lax',
                max_age=60 * 60 * 24 * 7,  # 7 days (matches REFRESH_TOKEN_LIFETIME)
            )

            return response

        # Fallback: redirect to frontend with error if user not authenticated
        frontend_url = settings.SITE_URL
        return HttpResponseRedirect(f"{frontend_url}/auth/callback?error=authentication_failed")
