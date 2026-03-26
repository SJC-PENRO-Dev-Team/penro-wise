from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in
    with either their email address or username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            # Try to find user by username or email
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except User.DoesNotExist:
            # Run the default password hasher once to reduce timing
            # difference between existing and non-existing users
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # If multiple users have the same email, fall back to username only
            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                return None

        # Check password and return user if valid
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
