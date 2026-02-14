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
    ProfileView,
)

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', RefreshTokenView.as_view(), name='refresh'),

    # Password reset endpoints
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # User profile endpoint
    path('users/profile/', ProfileView.as_view(), name='profile'),
]
