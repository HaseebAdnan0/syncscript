"""
Custom authentication backends for SyncScript.
"""
from django.contrib.auth.backends import ModelBackend
from .models import User


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows login with email (case-insensitive).
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user with email (case-insensitive) and password.
        """
        # Support both 'username' and 'email' parameters
        email = kwargs.get('email', username)

        if email is None or password is None:
            return None

        try:
            # Case-insensitive email lookup
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
