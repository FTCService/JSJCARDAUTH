from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Member, MemberAuthToken

class MemberAuthBackend(BaseBackend):
    def authenticate(self, request, mobile_number=None, pin=None):
        print("✅ MemberAuthBackend called with", mobile_number, pin)
        
        try:
            user = Member.objects.get(mobile_number=mobile_number)
            
            print("✔ check_password result:", check_password(pin, user.pin))
            if check_password(pin, user.pin):  # ✅ Correct way to check hashed PIN
                return user
        except Member.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            print(user_id)
            return Member.objects.get(pk=user_id)
        except Member.DoesNotExist:
            return None


class CustomTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Token "):
            return None

        token_key = auth_header.split("Token ")[1]

        try:
            user_token = MemberAuthToken.objects.get(key=token_key)
            user = user_token.user

            if not isinstance(user, Member):
                raise AuthenticationFailed("Invalid user type.")

            return (user, None)
        except MemberAuthToken.DoesNotExist:
            raise AuthenticationFailed("Invalid token.")
