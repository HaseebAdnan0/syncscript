# django-allauth Configuration
# This file should be imported at the end of settings.py

# Add allauth apps to INSTALLED_APPS
ALLAUTH_APPS = [
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
]

# Add allauth backend
ALLAUTH_BACKEND = 'allauth.account.auth_backends.AuthenticationBackend'

# Allauth account settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False
