"""
URL routing for user authentication endpoints.
"""
from django.urls import path
from .views import (
    RegisterView,
    VerifyEmailView,
    LoginView,
    LogoutView,
    RefreshTokenView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PasswordChangeView,
    ProfileView,
    OnboardingView,
    DemoVaultResetView,
    DemoVaultStatusView,
    DemoVaultCreateView,
    GoogleOAuthRedirectView,
    GitHubOAuthRedirectView,
    GoogleOAuthCallbackView,
    GitHubOAuthCallbackView,
    LinkOAuthAccountView,
    CompleteOAuthEmailView,
    ConnectedAccountsListView,
    DisconnectOAuthProviderView,
    UnsubscribeView,
    EmailPreferenceUpdateView,
    resend_verification,
)

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('auth/resend-verification/', resend_verification, name='resend-verification'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', RefreshTokenView.as_view(), name='refresh'),

    # Current user endpoint (alias for profile)
    path('auth/me/', ProfileView.as_view(), name='me'),

    # Password reset and change endpoints
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('auth/password-change/', PasswordChangeView.as_view(), name='password-change'),

    # User profile endpoint
    path('users/profile/', ProfileView.as_view(), name='profile'),

    # Onboarding endpoints (US-002, US-005, US-006)
    path('users/me/onboarding/', OnboardingView.as_view(), name='onboarding'),
    path('users/me/demo-vault/reset/', DemoVaultResetView.as_view(), name='demo-vault-reset'),
    path('users/me/demo-vault/status/', DemoVaultStatusView.as_view(), name='demo-vault-status'),
    path('users/me/demo-vault/create/', DemoVaultCreateView.as_view(), name='demo-vault-create'),

    # OAuth endpoints (PRD12)
    path('auth/google/', GoogleOAuthRedirectView.as_view(), name='google-oauth'),
    path('auth/github/', GitHubOAuthRedirectView.as_view(), name='github-oauth'),
    # Custom OAuth callbacks with JWT token generation (override allauth defaults)
    path('auth/google/login/callback/', GoogleOAuthCallbackView.as_view(), name='google-oauth-callback'),
    path('auth/github/login/callback/', GitHubOAuthCallbackView.as_view(), name='github-oauth-callback'),
    path('auth/oauth/link/', LinkOAuthAccountView.as_view(), name='oauth-link'),
    path('auth/oauth/complete-email/', CompleteOAuthEmailView.as_view(), name='oauth-complete-email'),
    path('auth/oauth/connected/', ConnectedAccountsListView.as_view(), name='oauth-connected'),
    path('auth/oauth/connected/<str:provider>/', DisconnectOAuthProviderView.as_view(), name='oauth-disconnect'),

    # Email preferences endpoints (US-011)
    path('auth/unsubscribe/<str:token>/', UnsubscribeView.as_view(), name='unsubscribe'),
    path('users/email-preferences/', EmailPreferenceUpdateView.as_view(), name='email-preferences'),
]
