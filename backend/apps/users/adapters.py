"""
Custom allauth adapters for JWT-based OAuth authentication.

Overrides default session-based authentication to use JWT tokens instead.
"""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework_simplejwt.tokens import RefreshToken


class JWTSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter that generates JWT tokens after successful OAuth authentication.

    Instead of creating a session, this adapter:
    1. Detects if account linking is required
    2. Generates JWT access and refresh tokens using simplejwt
    3. Sets tokens in httpOnly cookies for security
    4. Redirects to frontend with appropriate indicators
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

    def pre_social_login(self, request, sociallogin):
        """
        Called after successful OAuth but before user is logged in.

        Check if email already exists and handle account linking scenarios.
        """
        # If user is already being logged in, we're done
        if sociallogin.is_existing:
            return

        # Get email from OAuth provider
        email = None
        if sociallogin.account.extra_data:
            email = sociallogin.account.extra_data.get('email')

        if not email:
            # No email provided - will need to prompt user (GitHub private email case)
            # Store OAuth data in session for later
            request.session['pending_oauth'] = {
                'provider': sociallogin.account.provider,
                'uid': sociallogin.account.uid,
                'extra_data': sociallogin.account.extra_data,
            }
            request.session['oauth_needs_email'] = True
            return

        # Check if user with this email already exists
        from apps.users.models import User
        try:
            existing_user = User.objects.get(email__iexact=email)

            # Check if OAuth provider is already linked to this user
            social_account = SocialAccount.objects.filter(
                user=existing_user,
                provider=sociallogin.account.provider
            ).first()

            if not social_account:
                # Email exists but OAuth not linked - need password confirmation
                # Store OAuth data in session for linking flow
                request.session['pending_oauth'] = {
                    'provider': sociallogin.account.provider,
                    'uid': sociallogin.account.uid,
                    'email': email,
                    'extra_data': sociallogin.account.extra_data,
                }
                request.session['oauth_needs_linking'] = True

        except User.DoesNotExist:
            # Email is new - allauth will create the user automatically
            pass

    def get_login_redirect_url(self, request):
        """
        Override to redirect to frontend after successful OAuth login.

        This is called after authentication is complete. We'll generate JWT tokens
        and redirect to the frontend callback page.
        """
        frontend_url = settings.SITE_URL

        # Check if account linking is required
        if request.session.get('oauth_needs_linking'):
            provider = request.session.get('pending_oauth', {}).get('provider', 'unknown')
            request.session.pop('oauth_needs_linking', None)
            return HttpResponseRedirect(
                f"{frontend_url}/auth/callback?link_required=true&provider={provider}"
            )

        # Check if email is required (GitHub private email case)
        if request.session.get('oauth_needs_email'):
            provider = request.session.get('pending_oauth', {}).get('provider', 'unknown')
            # Don't pop yet - need the data for email submission
            return HttpResponseRedirect(
                f"{frontend_url}/auth/callback?email_required=true&provider={provider}"
            )

        # Get the user from the request (allauth sets this after successful auth)
        user = request.user

        if user and user.is_authenticated:
            # Generate JWT tokens using simplejwt
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            # Build redirect response to frontend
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
        return HttpResponseRedirect(f"{frontend_url}/auth/callback?error=authentication_failed")
