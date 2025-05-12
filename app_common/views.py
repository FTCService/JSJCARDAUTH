from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import logout
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth.hashers import check_password
from helpers.utils import send_otp_to_mobile
from app_common.authentication import MemberAuthBackend, CustomTokenAuthentication
from drf_yasg import openapi
from app_common.models import User, Member
from . import serializers, models
import secrets
from django.utils import timezone
import random

# ================ admin add staff ================ ##.
class AddStaffApi(APIView):
    """
    API to add a new staff user (Admin Only).
    """
   

    @swagger_auto_schema(
        request_body=serializers.StaffUserSerializer,
        tags=["Admin Authentication"]  # ✅ Grouping under "Admin Authentication"
    )
   
    def post(self, request):
        serializer = serializers.StaffUserSerializer(data=request.data)
        if serializer.is_valid():
            full_name = serializer.validated_data["full_name"]
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]
            employee_id = serializer.validated_data["employee_id"]

            # Check if the email is already used
            if User.objects.filter(email=email).exists():
                return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

            # Create staff user
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                employee_id=employee_id,
                is_staff=True  
            )

            return Response({"message": "Staff user added successfully"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(
        responses={200: serializers.StaffUserSerializer(many=True)},
        tags=["Admin Authentication"]
    )
    def get(self, request):
        """Retrieve all staff users."""
        staff_users = User.objects.filter(is_staff=True)
        serializer = serializers.StaffUserSerializer(staff_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    
### ✅================ MEMBER SIGNUP ================ ###
class MemberSignupApi(APIView):
    @swagger_auto_schema(request_body=serializers.MemberSignupSerializer)
    def post(self, request):
        # Get query parameters from URL
        refer_id = request.query_params.get("referId")  # Correctly extract referId
        full_name = request.query_params.get("name")
        mobile_number = request.query_params.get("phone")

        # Get request body data
        request_data = request.data.copy()

        # Use query params if the request body does not contain values
        if not request_data.get("refer_id"):
            request_data["refer_id"] = refer_id
        if not request_data.get("full_name"):
            request_data["full_name"] = full_name
        if not request_data.get("mobile_number"):
            request_data["mobile_number"] = mobile_number

        # Validate merged data
        serializer = serializers.MemberSignupSerializer(data=request_data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            refer_id = validated_data.get("refer_id")  # This now properly maps refer_id
            full_name = validated_data["full_name"]
            mobile_number = validated_data["mobile_number"]
            pin = validated_data["pin"]

            otp = random.randint(100000, 999999)

            if models.Member.objects.filter(mobile_number=mobile_number).exists():
                return Response({"error": "User already registered. Please log in."}, status=status.HTTP_400_BAD_REQUEST)

            models.TempMemberUser.objects.update_or_create(
                mobile_number=mobile_number,
                defaults={
                    "full_name": full_name,
                    "pin": pin,
                    "otp": otp,
                    "is_active": False,
                    "ref_by": refer_id if refer_id else None  # Ensuring `refer_id` is saved
                }
            )

            # send_otp_to_mobile({"mobile_number": mobile_number, "otp": otp})
            return Response({"message": "OTP sent. Verify to complete registration.", "otp": otp}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



### ========= VERIFY OTP FOR SIGNUP ###==============
class MemberVerifyOtpApi(APIView):
    @swagger_auto_schema(request_body=serializers.VerifyOtpSerializer)
    def post(self, request):
        serializer = serializers.VerifyOtpSerializer(data=request.data)
       
        if serializer.is_valid():
            mobile_number = serializer.validated_data["mobile_number"]
            otp_entered = serializer.validated_data["otp"]
            
            temp_user = models.TempMemberUser.objects.filter(
                mobile_number=mobile_number, otp=otp_entered
            ).first()

            if not temp_user:
                return Response(
                    {"success": False, "message": "Invalid OTP. Please enter a valid OTP."},
                    status=status.HTTP_200_OK
                )

            refer_id = temp_user.ref_by
            email = temp_user.email if temp_user.email else None
            
            # ✅ Create Member user
            user = models.Member.objects.create_user(
                mobile_number=mobile_number,
                pin=temp_user.pin,
                full_name=temp_user.full_name,
                email=email,
            )

            if refer_id:
                user.MbrCreatedBy = refer_id
                user.save()

            # ✅ Generate Token
            token = secrets.token_hex(32)  # Or use uuid.uuid4().hex
            models.MemberAuthToken.objects.create(
                user=user,
                key=token,
                created_at=timezone.now()
            )

            # ✅ Delete TempUser
            temp_user.delete()

            # ✅ Prepare response
            response_data = {
                "success": True,
                "message": "OTP verified. Signup complete.",
                "full_name": user.full_name,
                "cardno": user.mbrcardno,
                "MbrCreatedAt": user.MbrCreatedAt.strftime('%Y-%m-%d %H:%M:%S'),
                "token": token  # ✅ Return token to client
            }

            return Response(response_data, status=status.HTTP_200_OK)

        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



# ======== member login and access dashboard ================
class MemberLoginApi(APIView):
    """
    API for Member Login using mobile number and PIN.
    Generates and returns a custom access token on successful authentication.
    """

    @swagger_auto_schema(
        request_body=serializers.MemberLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "message": "Login successful",
                        "token": "abcdef123456...",
                        "full_name": "John Doe",
                        "mbrcardno": "MBR0001"
                    }
                }
            ),
            401: openapi.Response(description="Invalid credentials"),
            400: openapi.Response(description="Validation error")
        },
    )
    def post(self, request):
        # Deserialize and validate request data
        serializer = serializers.MemberLoginSerializer(data=request.data)
        if serializer.is_valid():
            mobile_number = serializer.validated_data["mobile_number"]
            pin = serializer.validated_data["pin"]

            # Authenticate using custom backend
            auth_backend = MemberAuthBackend()
            user = auth_backend.authenticate(request, mobile_number=mobile_number, pin=pin)

            # Check if user is valid and is a Member instance
            if user and isinstance(user, Member):
                user.backend = 'app_common.authentication.MemberAuthBackend'  # Replace with actual path

                # Log the result of password check (useful during development/debug)
                print("✔ check_password result:", check_password(pin, user.pin))

                # Generate a secure token (32 bytes hex) to be used as access token
                new_token = secrets.token_hex(32)

                # Create or update token in DB
                token, _ = models.MemberAuthToken.objects.update_or_create(
                    user=user,
                    defaults={"key": new_token}
                )

                # Return login success response with access token and user details
                return Response({
                    "message": "Login successful",
                    "token": token.key,  # This is your access token
                    "full_name": user.full_name,
                    "mbrcardno": user.mbrcardno
                }, status=status.HTTP_200_OK)

            # If credentials are invalid
            return Response({"Message": "Invalid mobile number or PIN"}, status=status.HTTP_401_UNAUTHORIZED)

        # Return validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
### ✅================ LOGOUT FOR only member ================ ###
class MemberLogoutApi(APIView):
    """
    API for user logout (removes authentication token).
    """
    authentication_classes = [CustomTokenAuthentication]  # ✅ Ensure token authentication
    permission_classes = [IsAuthenticated]  

    @swagger_auto_schema(
        operation_description="Logs out the currently authenticated member.",
        responses={
            200: openapi.Response(description="Logout Successful", examples={"application/json": {"message": "Logout Successful"}}),
            401: openapi.Response(description="Unauthorized - Invalid or missing token"),
            500: openapi.Response(description="Internal Server Error", examples={"application/json": {"error": "Something went wrong.", "details": "Error message"}})
        },
        
    )
    def post(self, request):  # ✅ Use POST instead of GET for logout
        try:
            # ✅ Delete the user's authentication token
            models.MemberAuthToken.objects.filter(user=request.user.id).delete()
            
            # ✅ Logout user session
            logout(request)

            return Response({"message": "Logout Successful"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": "Something went wrong.", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    
### ✅================ MEMBER FORGOT  ================ ###
class MemberForgotPinAPI(APIView):
    @swagger_auto_schema(request_body=serializers.MemberForgotPinSerializer)
    def post(self, request):
        serializer = serializers.MemberForgotPinSerializer(data=request.data)
        if serializer.is_valid():
            mobile_number = serializer.validated_data["mobile_number"]
            otp = random.randint(100000, 999999)

            user = models.Member.objects.filter(mobile_number=mobile_number).first() 
            if not user:
                return Response({"message": "User not found."}, status=status.HTTP_200_OK)

            user.otp = otp
            user.save()

            send_otp_to_mobile({"mobile_number": mobile_number, "otp": otp})
            return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


### ✅ ================MEMBER RESET PIN ================ ###
class MemberResetPinAPI(APIView):
    """
    API for resetting member's PIN using OTP verification.
    """

    @swagger_auto_schema(request_body=serializers.MemberResetPinSerializer)
    def post(self, request):
        # Deserialize and validate the incoming data using MemberResetPinSerializer
        serializer = serializers.MemberResetPinSerializer(data=request.data)
        if serializer.is_valid():
            # Extract validated OTP and new PIN from the serializer
            otp_entered = serializer.validated_data["otp"]
            new_pin = serializer.validated_data["new_pin"]

            # Search for the user with the provided OTP
            user = models.Member.objects.filter(otp=otp_entered).first()
            if not user:
                # Return message if no user found with the provided OTP
                return Response({"message": "Wrong OTP, enter a valid OTP."}, status=status.HTTP_200_OK)

            # Set the new PIN for the user
            user.set_pin(new_pin)

            # Clear the OTP after successful verification
            user.otp = None

            # Save the updated user information to the database
            user.save()

            # Return a success message
            return Response({"message": "PIN reset successfully."}, status=status.HTTP_200_OK)

        # If serializer validation fails, return the error messages
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




### ✅ MEMBER RESEND OTP FOR VERYFIED OTP  ###
class MemberResendOtpApi(APIView):
    """
    API to resend OTP to a registered mobile number.
    """
    @swagger_auto_schema(request_body=serializers.MemberResendOtpSerializer)
    def post(self, request):
        serializer = serializers.MemberResendOtpSerializer(data=request.data)

        if serializer.is_valid():
            mobile_number = serializer.validated_data["mobile_number"]
            
            # Generate a new OTP
            new_otp = random.randint(100000, 999999)

            # Update OTP in TempUser
            temp_user = models.TempMemberUser.objects.filter(mobile_number=mobile_number).first()
            temp_user.otp = new_otp
            temp_user.save()

            # Send OTP to user
            send_otp_to_mobile({"mobile_number": mobile_number, "otp": new_otp})

            return Response({"message": "OTP resent successfully.", "mobile_number": mobile_number}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)