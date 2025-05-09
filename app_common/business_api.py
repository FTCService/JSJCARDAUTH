import random
from django.contrib.auth import authenticate, logout, login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import re
from . import serializers, models
from helpers.utils import send_otp_to_mobile
import secrets
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .authentication import CustomTokenAuthentication
from django.contrib.auth.hashers import check_password, make_password
from app_common.models import Business, Member



### ✅ BUSINESS SIGNUP ###
class BusinessSignupApi(APIView):
    """
    API endpoint to initiate Business Signup.
    This view:
    - Accepts mobile_number, email, business_name, and PIN.
    - Validates input.
    - Sends an OTP to the mobile number.
    - Saves data to TempUser for pending verification.
    """

    @swagger_auto_schema(
        request_body=serializers.BusinessSignupSerializer
    )
    def post(self, request):
        serializer = serializers.BusinessSignupSerializer(data=request.data)

        # Step 1: Validate all fields (mobile, pin, email, business_name)
        if serializer.is_valid():
            mobile_number = serializer.validated_data["mobile_number"]
            business_name = serializer.validated_data["business_name"]
            pin = serializer.validated_data["pin"]
            email = serializer.validated_data["email"]

            # Step 2: Generate OTP (6-digit)
            otp = random.randint(100000, 999999)

            # Step 3: Check if already registered
            if models.Business.objects.filter(mobile_number=mobile_number).exists():
                return Response(
                    {"message": "Mobile number already registered. Please log in."},
                    status=status.HTTP_200_OK
                )

            if models.Business.objects.filter(email=email).exists():
                return Response(
                    {"message": "Email already registered. Please log in."},
                    status=status.HTTP_200_OK
                )

            # Step 4: Save or update TempUser entry
            models.TempBusinessUser.objects.update_or_create(
                mobile_number=mobile_number,
                defaults={
                    "business_name": business_name,
                    "pin": pin,
                    "email": email,
                    "otp": otp,
                    "is_active": False
                }
            )

            # Step 5: Send OTP to mobile
            send_otp_to_mobile({
                "mobile_number": mobile_number,
                "otp": otp
            })

            # Step 6: Respond success
            return Response(
                {"message": "OTP sent. Verify to complete signup.", "otp": otp},  # you can remove `otp` in prod
                status=status.HTTP_200_OK
            )

        # Step 7: If validation fails
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
class BusinessVerifyOtpApi(APIView):
    """
    API to verify OTP and complete business user signup.
    """

    @swagger_auto_schema(request_body=serializers.BusinessVerifyOtpSerializer)
    def post(self, request):
        # ✅ Deserialize and validate input
        serializer = serializers.BusinessVerifyOtpSerializer(data=request.data)

        if serializer.is_valid():
            mobile_number = serializer.validated_data["mobile_number"]
            otp_entered = serializer.validated_data["otp"]

            # ✅ Fetch temporary business user
            temp_user = models.TempBusinessUser.objects.filter(
                mobile_number=mobile_number,
                otp=otp_entered
            ).first()

            if not temp_user:
                return Response(
                    {"success": False, "message": "Invalid OTP. Please enter a valid OTP."},
                    status=status.HTTP_200_OK
                )

            # ✅ Create business user from temp_user data
            user = models.Business.objects.create_user(
                mobile_number=mobile_number,
                pin=temp_user.pin,
                business_name=temp_user.business_name,
                email=temp_user.email if temp_user.email else None
            )

            # ✅ Generate and save access token using BusinessAuthToken model
            token = secrets.token_hex(32)
            models.BusinessAuthToken.objects.create(
                user=user,
                key=token
                # `created_at` is automatically set because of auto_now_add=True
            )

            # ✅ Delete temporary user record
            temp_user.delete()

            # ✅ Prepare response
            response_data = {
                "success": True,
                "message": "OTP verified. Signup complete.",
                "token": token,
                "business_name": user.business_name,
                "business_created_at": user.business_created_at.strftime('%Y-%m-%d %H:%M:%S')
            }

            return Response(response_data, status=status.HTTP_200_OK)

        # ❌ Return serializer validation errors
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )




### ✅ BUSINESS LOGIN ###

class BusinessLoginApi(APIView):
    """
    API for business login using mobile number or email and PIN
    """
    @swagger_auto_schema(request_body=serializers.BusinessLoginSerializer)
    def post(self, request):
        if request.user.is_authenticated:
            return Response({"success": False, "message": "You are already logged in."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = serializers.BusinessLoginSerializer(data=request.data)
        if serializer.is_valid():
            contact = serializer.validated_data["contact"]
            pin = serializer.validated_data["pin"]

            # Determine whether contact is mobile or email
            is_mobile = re.fullmatch(r"^\d{10}$", contact)
            lookup_field = "mobile_number" if is_mobile else "email"
            filter_kwargs = {lookup_field: contact}

            try:
                user = Business.objects.get(**filter_kwargs)

                if check_password(pin, user.pin):
                    user.backend = 'django.contrib.auth.backends.ModelBackend'

                    business_kyc = models.BusinessKyc.objects.filter(business=user).first()
                    kyc_status = business_kyc.kycStatus if business_kyc else False

                    # Generate a secure token (32 bytes hex) to be used as access token
                    new_token = secrets.token_hex(32)

                    # Create or update token in DB
                    token, _ = models.BusinessAuthToken.objects.update_or_create(
                        user=user,
                        defaults={"key": new_token}
                    )

                    return Response({
                        "success": True,
                        "message": "Login successful",
                        "token": token.key,
                        "business_id": user.business_id,
                        "business_name": user.business_name,
                        "kyc_status": kyc_status
                    })

                return Response({"success": False, "error": "Invalid PIN"}, status=status.HTTP_401_UNAUTHORIZED)

            except Business.DoesNotExist:
                return Response({"success": False, "error": "Business user not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)