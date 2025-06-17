from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Member, MemberAuthToken, BusinessAuthToken, Business, User, UserAuthToken

class MemberAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, pin=None):  # mobile_number can be email too
        print("✅ MemberAuthBackend called with", username, pin)

        try:
            if '@' in username:
                user = Member.objects.get(email=username)
            else:
                user = Member.objects.get(mobile_number=username)

            if check_password(pin, user.pin):
                return user
        except Member.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Member.objects.get(pk=user_id)
        except Member.DoesNotExist:
            return None


class AdminAuthBackend(BaseBackend):
    """
    Custom authentication backend for Admin and Staff users (Login via email & password).
    """

    def authenticate(self, request, email=None, password=None):
        try:
            user = User.objects.get(email=email)
            if user.is_staff or user.is_superuser or user.is_jobmitra:  # ✅ Ensure only staff & admin can log in
                if user.check_password(password):  # ✅ Correct password validation
                    return user
        except User.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None



class UserTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Token "):
            return None

        token_key = auth_header.split("Token ")[1]
        print(token_key,"user_token")

        try:
            user_token = UserAuthToken.objects.get(key=token_key)
            # print(user_token,"+++++++++++++++++++++++")
            user = user_token.user

            if not isinstance(user, User):
                raise AuthenticationFailed("Invalid user type.")

            return (user, None)
        except UserAuthToken.DoesNotExist:
            raise AuthenticationFailed("Invalid token.")



class MemberTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Token "):
            return None

        token_key = auth_header.split("Token ")[1]
        print(token_key,"user_token")

        try:
            user_token = MemberAuthToken.objects.get(key=token_key)
            print(user_token,"+++++++++++++++++++++++")
            user = user_token.user

            if not isinstance(user, Member):
                raise AuthenticationFailed("Invalid user type.")

            return (user, None)
        except MemberAuthToken.DoesNotExist:
            raise AuthenticationFailed("Invalid token.")



class BusinessTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Token "):
            return None

        token_key = auth_header.split("Token ")[1]

        try:
            user_token = BusinessAuthToken.objects.get(key=token_key)
            user = user_token.user

            if not isinstance(user, Business):
                raise AuthenticationFailed("Invalid user type.")

            return (user, None)
        except BusinessAuthToken.DoesNotExist:
            raise AuthenticationFailed("Invalid token.")