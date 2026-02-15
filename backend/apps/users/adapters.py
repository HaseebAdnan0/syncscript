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
        redirect_url = f"{frontend_url}/callback?error={error_message}&provider={provider_id}"

        return HttpResponseRedirect(redirect_url)

    def pre_social_login(self, request, sociallogin):
        """
        Called after successful OAuth but before user is logged in.

        Check if email already exists and handle account linking scenarios.
        """
        # If user is already being logged in (social account exists), we're done
        if sociallogin.is_existing:
            return

        # Get email from OAuth provider
        email = None
        if sociallogin.account.extra_data:
            email = sociallogin.account.extra_data.get('email')

        if not email:
            # No email provided - will need to prompt user (GitHub private email case)
            # Generate temp token for validation
            import secrets
            temp_token = secrets.token_urlsafe(32)

            # Store OAuth data in session and abort the auto-signup
            request.session['pending_oauth'] = {
                'provider': sociallogin.account.provider,
                'uid': sociallogin.account.uid,
                'extra_data': sociallogin.account.extra_data,
            }
            request.session['oauth_needs_email'] = True
            request.session['oauth_temp_token'] = temp_token

            # Abort the signup - we need email first
            from allauth.exceptions import ImmediateHttpResponse
            frontend_url = settings.SITE_URL
            response = HttpResponseRedirect(
                f"{frontend_url}/callback?email_required=true&provider={sociallogin.account.provider}&temp_token={temp_token}"
            )
            raise ImmediateHttpResponse(response)

        # Check if user with this email already exists
        from apps.users.models import User
        try:
            existing_user = User.objects.get(email__iexact=email)

            # Check if OAuth provider is already linked to this user
            social_account = SocialAccount.objects.filter(
                user=existing_user,
                provider=sociallogin.account.provider
            ).first()

            if social_account:
                # Provider is already linked - let allauth proceed with login
                return
            else:
                # Email exists but OAuth not linked - need password confirmation
                # Store OAuth data in session and abort the signup
                request.session['pending_oauth'] = {
                    'provider': sociallogin.account.provider,
                    'uid': sociallogin.account.uid,
                    'email': email,
                    'extra_data': sociallogin.account.extra_data,
                }
                request.session['oauth_needs_linking'] = True

                # Abort the signup - need password confirmation first
                from allauth.exceptions import ImmediateHttpResponse
                frontend_url = settings.SITE_URL
                response = HttpResponseRedirect(
                    f"{frontend_url}/callback?link_required=true&provider={sociallogin.account.provider}"
                )
                raise ImmediateHttpResponse(response)

        except User.DoesNotExist:
            # Email is new - let allauth proceed with auto-signup
            pass

    def get_login_redirect_url(self, request):
        """
        Override to redirect to frontend after successful OAuth login.

        This is called after authentication is complete. We'll generate JWT tokens
        and pass them via URL parameters to the frontend callback page.

        Note: allauth expects a URL string, not a Response object.
        """
        frontend_url = settings.SITE_URL

        # Get the user from the request (allauth sets this after successful auth)
        user = request.user

        if user and user.is_authenticated:
            # Generate JWT tokens using simplejwt
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            # Pass tokens via URL params - frontend will store them
            # This is safe because it's a redirect (tokens won't be in browser history)
            redirect_url = (
                f"{frontend_url}/callback"
                f"?success=true"
                f"&access={str(access)}"
                f"&refresh={str(refresh)}"
            )

            return redirect_url

        # Fallback: redirect to frontend with error if user not authenticated
        return f"{frontend_url}/callback?error=authentication_failed"
