from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate, logout, login
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth.hashers import check_password, make_password
from helpers.utils import send_otp_to_mobile, send_fast2sms
from app_common.authentication import MemberAuthBackend, MemberTokenAuthentication
from drf_yasg import openapi
from app_common.models import User, Member,MemberAuthToken
from . import serializers, models
from admin_dashboard.models import CardPurpose
import secrets
from member.models import JobProfile
from django.utils import timezone
import random
from app_common.email import send_template_email
import csv
import io


import io
import csv
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from urllib.parse import urlparse


class BulkProfileUploadView(APIView):
    def post(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "CSV file is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data_set = file.read().decode("UTF-8")
        except Exception:
            return Response({"error": "Unable to decode CSV file. Make sure it's UTF-8 encoded."}, status=status.HTTP_400_BAD_REQUEST)

        io_string = io.StringIO(data_set)
        csv_reader = csv.DictReader(io_string)

        # Normalize headers (remove leading/trailing whitespace)
        if csv_reader.fieldnames:
            csv_reader.fieldnames = [f.strip() for f in csv_reader.fieldnames]

        created_members = []
        skipped_members = []
        failed_members = []

        for idx, row in enumerate(csv_reader, start=2):  # Line 2 is first data row
            try:
                # Strip all keys and values
                row = {key.strip(): (value.strip() if value else "") for key, value in row.items()}

                mbrcardno = row.get("mbrcardno")
                if not mbrcardno:
                    failed_members.append({"row": idx, "reason": "Missing mbrcardno"})
                    continue

                # Check for duplicate
                if JobProfile.objects.filter(mbrcardno=mbrcardno).exists():
                    skipped_members.append(mbrcardno)
                    continue

                # Create JobProfile
                member = JobProfile(
                    mbrcardno=mbrcardno,
                    # Add other fields here if needed
                    # name=row.get("name"),
                    # contact=row.get("contact"),
                )
                member.save()
                created_members.append(mbrcardno)

            except Exception as e:
                failed_members.append({
                    "row": idx,
                    "error": str(e),
                    "row_data": row
                })

        response_data = {
            "created": len(created_members),
            "skipped": len(skipped_members),
            "failed": len(failed_members),
            "created_members": created_members,
            "skipped_members": skipped_members,
            "failed_details": failed_members,
        }

        status_code = status.HTTP_201_CREATED if created_members else status.HTTP_400_BAD_REQUEST
        return Response(response_data, status=status_code)



class BulkMemberUploadView(APIView):
    
    def post(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "CSV file is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Decode and read the file
        data_set = file.read().decode("UTF-8")
        io_string = io.StringIO(data_set)
        csv_reader = csv.DictReader(io_string)

        created_members = []
        for row in csv_reader:
            try:
                # Skip if mobile number or card number already exists
                if Member.objects.filter(mobile_number=row["mobile_number"]).exists() or Member.objects.filter(mbrcardno=row["mbrcardno"]).exists():
                    continue
                raw_pin = row.get("pin")
                if raw_pin.startswith("pbkdf2_"):
                    pin = raw_pin  # Already hashed
                else:
                    pin = make_password(raw_pin)
                member = Member(
                    id=row.get("id"),
                    full_name=row.get("full_name"),
                    email=row.get("email"),
                    mobile_number=row.get("mobile_number"),
                    pin=pin,
                    first_name=row.get("first_name"),
                    last_name=row.get("last_name"),
                    MbrCountryCode=row.get("MbrCountryCode", "+91"),
                    MbrStatus=row.get("MbrStatus", "True") in ["True", "1", "true"],
                    otp=row.get("otp"),
                    mbrcardno=row.get("mbrcardno"),
                    mbraddress=row.get("mbraddress"),
                    MbrPincode=row.get("MbrPincode"),
                    MbrReferalId=row.get("MbrReferalId"),
                    MbrCreatedBy=row.get("MbrCreatedBy"),
                )
                member.save()
                created_members.append(member.mobile_number)
                # Prepare context for welcome email
                context = {
                    "full_name": member.full_name,
                    "mbrcardno": member.mbrcardno,
                    "otp_code": member.otp,
                    "mobile_number": member.mobile_number,
                    "email": member.email,
                }

                # Send welcome email
                send_template_email(
                    subject="Welcome to JSJ Card - Your Membership Details",
                    template_name="email_template/send_welcome_new_member.html",
                    context=context,
                    recipient_list=[member.email]
                )
            except Exception as e:
                return Response({"error": f"Failed to process row: {row}", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": f"{len(created_members)} members uploaded successfully", "members": created_members}, status=status.HTTP_201_CREATED)
    


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
            mobile_number = serializer.validated_data["mobile_number"]
            password = serializer.validated_data["password"]
            employee_id = serializer.validated_data["employee_id"]

            # Check if the email is already used
            if User.objects.filter(email=email).exists():
                return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

            # Create staff user
            user = User.objects.create(
                email=email,
                password=make_password(password),
                full_name=full_name,
                employee_id=employee_id,
                mobile_number=mobile_number,
                is_staff=True  
            )
            # Send welcome email
            context = {
                "full_name": full_name,
                "email": email,
                "employee_id": employee_id,
                "mobile_number": mobile_number,
                "login_url": "https://www.jsjcard.com/admin/login"
            }

            send_template_email(
                subject="🎉 Welcome to JSJCard Admin Portal",
                template_name="email_template/welcome_staff.html",
                context=context,
                recipient_list=[email]
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
            email = validated_data.get("email") or None
            otp = random.randint(100000, 999999)

            if models.Member.objects.filter(mobile_number=mobile_number).exists():
                return Response({"message": " mobile number already registered. Please log in."}, status=status.HTTP_200_OK)

          
        
            if email and models.Member.objects.filter(email=email).exists():
                
                return Response({"message": "email already registered. Please log in."}, status=status.HTTP_200_OK)
          
            models.TempMemberUser.objects.update_or_create(
                mobile_number=mobile_number,
                defaults={
                    "full_name": full_name,
                    "pin": pin,
                    "otp": otp,
                    "is_active": False,
                    "ref_by": refer_id if refer_id else None,  # Ensuring `refer_id` is saved
                    "email": email  
                }
            )
            send_template_email(
            subject="Your OTP Code",
            template_name="email_template/otp_validation_mail.html",
            context={'otp_code': otp},
            recipient_list=[email]
            )
            # Send SMS with OTP
            send_fast2sms(mobile_number, otp)
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
                # ✅ Handle multiple purpose entries
            purposes_data = request.data.get("card_purposes", [
                {"purpose": "consumer", "features": ["Reward"]}
            ])

            final_purpose_list = []

            for entry in purposes_data:
                purpose_name = entry.get("purpose", "consumer")
                features = entry.get("features", [])

                purpose_obj = CardPurpose.objects.filter(purpose_name=purpose_name).first()
                if purpose_obj:
                    final_purpose_list.append({
                        "id": purpose_obj.id,
                        "purpose": purpose_obj.purpose_name,
                        "features": features or purpose_obj.features  # fallback to default
                    })

            user.card_purposes = final_purpose_list
            user.save()

            # ✅ Create Job Profile
            JobProfile.objects.create(
                MbrCardNo=user,
                BasicInformation={
                    "full_name": user.full_name,
                    "mobile_number": user.mobile_number,
                    "email": user.email or ""
                }
            )
            models.CardMapper.objects.create(
                primary_card=user,
                secondary_card=user.mbrcardno,
                secondary_card_type="digital"
            )
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
                "card_purposes": final_purpose_list,
                "MbrCreatedAt": user.MbrCreatedAt.strftime('%Y-%m-%d %H:%M:%S'),
                "token": token,  # ✅ Return token to client
                "job_profile_created": True
            }
            send_template_email(
                subject="Welcome to JSJCard!",
                template_name="email_template/member_welcome.html",
                context={
                    'full_name': user.full_name,
                    'mbrcardno': user.mbrcardno,
                    'email': user.email,
                    'mobile_number': user.mobile_number,
                    'card_purposes': final_purpose_list,
                    'created_at': user.MbrCreatedAt.strftime('%Y-%m-%d %H:%M:%S'),
                },
                recipient_list=[user.email]
            )
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
            username = serializer.validated_data["mobile_number"]
            pin = serializer.validated_data["pin"]

            # Authenticate using custom backend
            auth_backend = MemberAuthBackend()
            user = auth_backend.authenticate(request, username=username, pin=pin)

            # Check if user is valid and is a Member instance
            if user and isinstance(user, Member):
                user.backend = 'app_common.authentication.MemberAuthBackend'  # Replace with actual path

                # Log the result of password check (useful during development/debug)
                # print("✔ check_password result:", check_password(pin, user.pin))

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


### ✅ MEMBER REGISTRATIONS API (PROFILE) ###
class MemberRegistrationApi(APIView):
    """
    API to get and update the member's full profile information after login/signup.
    """
    authentication_classes = [MemberTokenAuthentication]  # Ensure the user is authenticated
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    @swagger_auto_schema(
        operation_description="Get the current member's profile details",
        responses={200: serializers.MemberRegistrationSerializer()}
    )
    def get(self, request):
        """
        Retrieve the current member's profile details.
        """
        user = request.user  # Get the authenticated user
        serializer = serializers.MemberRegistrationSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=serializers.MemberRegistrationSerializer,
        operation_description="Update the member's profile (excluding contact and pin)."
    )
    def post(self, request):
        """
        Update only specific member fields (full_name, first_name, last_name, Location, MbrPincode, etc.).
        """
        user = request.user  # Get the authenticated user
        serializer = serializers.MemberRegistrationSerializer(user, data=request.data, partial=True)  # partial update

        if serializer.is_valid():
            # Ensure 'contact' and 'pin' are not updated
            serializer.validated_data.pop('contact', None)
            serializer.validated_data.pop('pin', None)

            serializer.save()

            return Response({"message": "Profile updated successfully","updated_profile": serializer.data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    

### ✅================ LOGOUT FOR only member ================ ###
class MemberLogoutApi(APIView):
    """
    API for user logout (removes authentication token).
    """
    authentication_classes = [MemberTokenAuthentication]  # ✅ Ensure token authentication
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



### ✅ CHANGE PIN ###
class MemberChangePinAPI(APIView):
    """
    API for logged-in users (Members & Businesses) to change their PIN.
    """
    authentication_classes = [MemberTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=serializers.MemberChangePinSerializer,
        operation_description="Change PIN for logged-in user (Member or Business).",
    )
    def post(self, request):
        user = request.user  
        serializer = serializers.MemberChangePinSerializer(data=request.data, context={"request": request})  # ✅ Pass `request` context

        if serializer.is_valid():
            current_pin = serializer.validated_data["current_pin"]
            new_pin = serializer.validated_data["new_pin"]
            confirm_pin = serializer.validated_data["confirm_pin"]

            # ✅ Check if the current PIN is correct
            if not check_password(current_pin, user.pin):  
                return Response({"error": "Incorrect current PIN."}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Ensure new PIN and confirm PIN match
            if new_pin != confirm_pin:
                return Response({"error": "New PIN and Confirm PIN do not match."}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Hash and update the new PIN
            user.set_pin(new_pin)  
            user.save()

            return Response({"message": "PIN changed successfully."}, status=status.HTTP_200_OK)

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
    
    
    
    
class MemberDetailsByMobileAPI(APIView):
    def get(self, request):
        mobile = request.GET.get("mobile_number")
        print(mobile)
        if not mobile:
            return Response({"message": "Mobile number is required."}, status=status.HTTP_200_OK)

        member = Member.objects.filter(mobile_number=mobile).first()
        if not member:
            return Response({"message": "Member not found."}, status=status.HTTP_200_OK)

        serializer = serializers.MemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class MemberDetailsByCardNoAPI(APIView):
    def get(self, request):
        card_number = request.GET.get("card_number")
        if not card_number:
            return Response({"message": "card number is required."}, status=status.HTTP_200_OK)

        member = Member.objects.filter(mbrcardno=card_number).first()
        if not member:
            return Response({"message": "Member not found."}, status=status.HTTP_200_OK)

        serializer = serializers.MemberSerializer(member)
        # print(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    

class VerifyMemberTokenApi(APIView):
    """
    Endpoint to verify a memberAuthToken from another service.
    """
    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"detail": "Token required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_token = MemberAuthToken.objects.select_related('user').get(key=token)
            user = user_token.user

            if not isinstance(user, Member):
                return Response({"detail": "Invalid user type."}, status=status.HTTP_401_UNAUTHORIZED)

            return Response({
                "valid": True,
                "mbrcardno": user.mbrcardno,
                "full_name": user.full_name,
                "user_id": user.id,
            })
        except MemberAuthToken.DoesNotExist:
            return Response({"valid": False, "detail": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)
        except Member.DoesNotExist:
            return Response({"valid": False, "detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)




class AdminStaffLoginApi(APIView):
    """
    API to log in Admin and Staff users.
    """
    @swagger_auto_schema(
        request_body=serializers.AdminStaffLoginSerializer,
        tags=["Admin Authentication"]  # ✅ Grouping under "Admin Authentication"
    )
    def post(self, request):
        serializer = serializers.AdminStaffLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            user = authenticate(request, email=email, password=password)
            if user and (user.is_staff or user.is_superuser or user.is_jobmitra):
                login(request, user)
                new_token = secrets.token_hex(32)
                token, created = models.UserAuthToken.objects.update_or_create(
                    user=user,
                    defaults={"key": new_token}
                )

                return Response(
                    {"message": "Login successful",
                    "token": token.key,
                    "user_type": (
                            "admin" if user.is_superuser else
                            "staff" if user.is_staff else
                            "jobmitra"
                        ),
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                    "is_jobmitra": user.is_jobmitra, 
                    "user_id": user.id,
                    "email": user.email,},
                    status=status.HTTP_200_OK
                )

            return Response({"error": "Invalid credentials or not authorized"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
class VerifyAdminStaffTokenApi(APIView):
    """
    Endpoint to verify a UserAuthToken from another service.
    """
    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"detail": "Token required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_token = models.UserAuthToken.objects.get(key=token)
            user = user_token.user
            if not isinstance(user, User):
                return Response({"detail": "Invalid user type."}, status=status.HTTP_401_UNAUTHORIZED)

            return Response({
                "valid": True,
                "employee_id": user.employee_id,
                "full_name": user.full_name,
                "id": user.id,
                "email": user.email,
            })
        except models.UserAuthToken.DoesNotExist:
            return Response({"valid": False, "detail": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)
        