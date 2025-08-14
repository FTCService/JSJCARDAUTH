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
from helpers.utils import send_otp_to_mobile, send_fast2sms, get_member_active_in_marchant
import secrets
from django.utils import timezone
from .authentication import BusinessTokenAuthentication
from django.contrib.auth.hashers import check_password, make_password
from app_common.models import Business, BusinessKyc
import csv, io
from app_common.email import send_template_email
from admin_dashboard.models import CardPurpose
from member.models import JobProfile

class BulkBusinessUploadView(APIView):
    def post(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "CSV file is required"}, status=status.HTTP_400_BAD_REQUEST)

        data_set = file.read().decode("UTF-8")
        io_string = io.StringIO(data_set)
        csv_reader = csv.DictReader(io_string)

        created_businesses = []
        for row in csv_reader:
            try:
                if Business.objects.filter(mobile_number=row["mobile_number"]).exists():
                    continue  # Skip duplicates

                raw_pin = row.get("pin")
                if raw_pin.startswith("pbkdf2_"):  # Already hashed
                    pin = raw_pin
                else:
                    pin = make_password(raw_pin)

                business = Business(
                    id=row.get("id"),
                    business_id =row.get("business_id"),
                    email=row.get("email"),
                    mobile_number=row.get("mobile_number"),
                    pin=pin,
                    business_name=row.get("business_name"),
                    business_type=row.get("business_type"),
                    otp=row.get("otp"),
                    business_country_code=row.get("business_country_code", "+91"),
                    business_is_active=row.get("business_is_active", "True") in ["True", "1", "true"],
                    business_address=row.get("business_address"),
                    business_pincode=row.get("business_pincode"),
                    business_created_by=row.get("business_created_by"),
                    business_updated_by=row.get("business_updated_by"),
                    business_notes=row.get("business_notes"),
                )
                business.save()
                created_businesses.append(business.mobile_number)

            except Exception as e:
                return Response({
                    "error": f"Failed to process row: {row}",
                    "details": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": f"{len(created_businesses)} businesses uploaded successfully",
            "businesses": created_businesses
        }, status=status.HTTP_201_CREATED)



class BulkBusinessKycUpload(APIView):
    def post(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "CSV file is required"}, status=status.HTTP_400_BAD_REQUEST)

        data_set = file.read().decode("UTF-8")
        io_string = io.StringIO(data_set)
        csv_reader = csv.DictReader(io_string)

        created_kyc = []

        for row in csv_reader:
            try:
                business_id = row.get("business_id")
                if not business_id:
                    raise ValueError("Missing business_id in row.")

                business = Business.objects.get(business_id=business_id)

                kyc = BusinessKyc.objects.create(
                    business=business,
                    kycStatus=row.get("kycStatus", "False").lower() in ["true", "1"],
                    kycAdharCard=row.get("kycAdharCard"),
                    kycGst=row.get("kycGst"),
                    kycPanCard=row.get("kycPanCard"),
                    kycOthers=row.get("kycOthers")
                )
                created_kyc.append(kyc.business.business_id)

            except Business.DoesNotExist:
                return Response({
                    "error": f"Business with ID '{row.get('business_id')}' does not exist."
                }, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                return Response({
                    "error": f"Failed to process row: {row}",
                    "details": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": f"{len(created_kyc)} KYC records uploaded successfully.",
            "businesses": created_kyc
        }, status=status.HTTP_201_CREATED)




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

            # # Step 5: Send OTP to mobile
            # send_otp_to_mobile({
            #     "mobile_number": mobile_number,
            #     "otp": otp
            # })
            send_fast2sms(mobile_number, otp)
            send_template_email(
            subject="Your OTP Code",
            template_name="email_template/otp_validation_mail.html",
            context={'otp_code': otp},
            recipient_list=[email]
            )
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
                        "kyc_status": kyc_status,
                        "is_business":user.is_business,
                        "is_institute":user.is_institute,
                        "user_type": "institute" if user.is_institute else "business",
                    })

                return Response({"success": False, "error": "Invalid PIN"}, status=status.HTTP_401_UNAUTHORIZED)

            except Business.DoesNotExist:
                return Response({"success": False, "error": "Business user not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



class BusinessLogoutApi(APIView):
    """
    API for business logout (removes authentication token and ends session).
    """
    authentication_classes = [BusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Logs out the currently authenticated business.",
        responses={
            200: openapi.Response(description="Logout Successful", examples={"application/json": {"message": "Logout Successful"}}),
            401: openapi.Response(description="Unauthorized - Invalid or missing token"),
            500: openapi.Response(description="Internal Server Error", examples={"application/json": {"error": "Something went wrong.", "details": "Error message"}})
        },
    )
    def post(self, request):
        try:
            models.BusinessAuthToken.objects.filter(user=request.user.id).delete()
            logout(request)
            return Response({"message": "Logout Successful"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": "Something went wrong.", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


### ✅ BUSINESS FORGOT PIN ###
class BusinessForgotPinAPI(APIView):
    @swagger_auto_schema(request_body=serializers.BusinessForgotPinSerializer)
    def post(self, request):
        serializer = serializers.BusinessForgotPinSerializer(data=request.data)
        if serializer.is_valid():
            mobile_number = serializer.validated_data["mobile_number"]
            otp = random.randint(100000, 999999)

            user = models.Business.objects.filter(mobile_number=mobile_number).first()
            if not user:
                return Response({"message": "User not found."}, status=status.HTTP_200_OK)

            user.otp = otp
            user.save()

            send_otp_to_mobile({"mobile_number": mobile_number, "otp": otp})
            return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





### ✅ BUSINESS RESET PIN ###
class BusinessResetPinAPI(APIView):
    @swagger_auto_schema(request_body=serializers.BusinessResetPinSerializer)
    
    def post(self, request):
        serializer = serializers.BusinessResetPinSerializer(data=request.data)
        if serializer.is_valid():
            otp_entered = serializer.validated_data["otp"]
            new_pin = serializer.validated_data["new_pin"]

            user = models.Business.objects.filter(otp=otp_entered).first()
            if not user:
                return Response({"message": "Wrong OTP, enter a valid OTP."}, status=status.HTTP_200_OK) 

            user.set_pin(new_pin)
            user.otp = None
            user.save()

            return Response({"message": "PIN reset successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    

        
### ✅ BUSINESS REGISTRATIONS API ###
class BusinessRegistrationApi(APIView):
    """
    API to get and update the business's full profile information after login/signup.
    """
    authentication_classes = [BusinessTokenAuthentication]  # Ensure the user is authenticated
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    @swagger_auto_schema(
        operation_description="Get the current business profile details",
        responses={200: serializers.BusinessRegistrationSerializer()}
    )
    def get(self, request):
        """
        Retrieve the current business profile details.
        """
        user = request.user  # Get the authenticated business user
        print(user,"Business")
        serializer = serializers.BusinessRegistrationSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=serializers.BusinessRegistrationSerializer,
        operation_description="Update the business profile (excluding contact and pin)."
    )
    def post(self, request):
        """
        Update only specific business fields (business_name, business_type, address, etc.).
        """
        user = request.user # Get the authenticated business user
        serializer = serializers.BusinessRegistrationSerializer(user, data=request.data, partial=True)  # Partial update

        if serializer.is_valid():
            # Ensure 'contact' and 'pin' are not updated
            serializer.validated_data.pop('contact', None)
            serializer.validated_data.pop('pin', None)

            serializer.save()

            return Response({
                "message": "Business profile updated successfully",
                "updated_data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    

class BusinessKycApi(APIView):
    authentication_classes = [BusinessTokenAuthentication]  
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve Business KYC details",
        responses={200: serializers.BusinessKycSerializer()}
    )
    def get(self, request):
        user = request.user.business_id
       
        try:
            business = Business.objects.get(business_id=user)
        except Business.DoesNotExist:
            return Response({"error": "Invalid business."}, status=status.HTTP_403_FORBIDDEN)
        
        kyc_data = models.BusinessKyc.objects.filter(business=business).first()
        if not kyc_data:
            return Response({"message": "No KYC details found. Please submit your KYC."}, status=status.HTTP_200_OK)

        serializer =serializers.BusinessKycSerializer(kyc_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=serializers.BusinessKycSerializer,
        operation_description="Submit Business KYC documents (Send URLs for Aadhar, PAN, etc.)."
    )
    def post(self, request):
        business_id = request.user.business_id

        try:
            business = Business.objects.get(business_id=business_id)
        except Business.DoesNotExist:
            return Response({"error": "Invalid business."}, status=status.HTTP_403_FORBIDDEN)
        # ✅ Auto-assign `business` field from `request.user`
        kyc_instance, created = models.BusinessKyc.objects.get_or_create(business=business)

        mutable_data = request.data.copy()
        mutable_data["business"] = business.id  # Assign user ID to business field
        mutable_data["kycStatus"] = True

        serializer = serializers.BusinessKycSerializer(kyc_instance, data=mutable_data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "KYC submitted successfully.", "kycDetails": serializer.data},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
class VerifyBusinessTokenApi(APIView):
    """
    Endpoint to verify a BusinessAuthToken from another service.
    """
    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"detail": "Token required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_token = models.BusinessAuthToken.objects.get(key=token)
            user = user_token.user
            if not isinstance(user, Business):
                return Response({"detail": "Invalid user type."}, status=status.HTTP_401_UNAUTHORIZED)

            return Response({
                "valid": True,
                "business_id": user.business_id,
                "business_name": user.business_name,
                "user_id": user.id,
            })
        except models.BusinessAuthToken.DoesNotExist:
            return Response({"valid": False, "detail": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)
        
        
        
class BusinessDetailsByIdAPI(APIView):
    def get(self, request):
        business_id = request.GET.get("business_id")
        print(business_id)
        if not business_id:
            return Response({"message": "business_id number is required."}, status=status.HTTP_200_OK)

        member = Business.objects.filter(business_id=business_id).first()
        if not member:
            return Response({"message": "Business not found."}, status=status.HTTP_200_OK)

        serializer = serializers.BusinessDetailsSerializer(member)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    

class InitiateCardAssignmentView(APIView):
    authentication_classes = [BusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=serializers.InitiateCardAssignmentSerializer,
        operation_description="Initiate assignment of a physical card to a member.",
        responses={200: "Card activated successfully", 400: "Validation Error"}
    )
    def post(self, request):
        serializer = serializers.InitiateCardAssignmentSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            card_number = data['card_number']
            mobile_number = data['mobile_number']
            full_name = data['full_name']
            pin = data.get('pin')

            # Get the Business instance
            try:
                business = models.Business.objects.get(business_id=request.user.business_id)
            except models.Business.DoesNotExist:
                return Response({"message": "Business not found."}, status=status.HTTP_200_OK)

            # Check if physical card exists and is not already issued
            physical_card_qs = models.PhysicalCard.objects.filter(card_number=card_number, business=business.business_id)
            if not physical_card_qs.exists():
                return Response({"message": "Card not found."}, status=status.HTTP_200_OK)

            physical_card = physical_card_qs.first()

            # Check if this card is already mapped
            card_mapper_qs = models.CardMapper.objects.filter(secondary_card=physical_card.card_number)
            if card_mapper_qs.exists():
                existing_mapping = card_mapper_qs.first()
                return Response({
                    "message": "Card already issued.",
                    "mbrcardno": existing_mapping.primary_card.mbrcardno
                }, status=status.HTTP_200_OK)

            # Check if member with this mobile number exists
            member_qs = models.Member.objects.filter(mobile_number=mobile_number)
            if member_qs.exists():
                member = member_qs.first()

                # Existing member, map as secondary card
                models.CardMapper.objects.create(
                    business_id=business.business_id,
                    primary_card=member,
                    secondary_card=physical_card.card_number,
                    secondary_card_type='physical'
                )
                physical_card.issued = True
                physical_card.save()

                return Response({
                    "message": "Existing member found. Secondary card assigned.",
                    "mbrcardno": member.mbrcardno,
                }, status=status.HTTP_200_OK)
            else:
                # Create new member
                new_member = models.Member.objects.create(
                    mobile_number=mobile_number,
                    full_name=full_name
                )
                new_member.set_pin(pin)  # Securely hash pin
                new_member.save()

                # Map card as secondary to new member
                models.CardMapper.objects.create(
                    business_id=business.business_id,
                    primary_card=new_member,
                    secondary_card=physical_card.card_number,
                    secondary_card_type='physical'
                )
                physical_card.issued = True
                physical_card.save()

                return Response({
                    "message": "New member created and card assigned.",
                    "mbrcardno": new_member.mbrcardno
                }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    

class AllCardMappingsByBusiness(APIView):
    authentication_classes = [BusinessTokenAuthentication]  
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve Business CardMapper list",
        responses={200: serializers.CardMapperSerializer()}
    )
    def get(self, request):
        mappings = models.CardMapper.objects.filter(business_id=request.user.business_id)
        serializer = serializers.CardMapperSerializer(mappings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    

class PhysicalCardsByBusinessID(APIView):
    authentication_classes = [BusinessTokenAuthentication]  
    permission_classes = [IsAuthenticated]

    # @swagger_auto_schema(
    #     operation_description="Retrieve Business PhysicalCard list",
    #     responses={200: openapi.Response(
    #         description="List of Physical Cards",
    #         schema=serializers.PhysicalCardSerializer(many=True)
    #     )}
    # )
    def get(self, request):
        physical_cards = models.PhysicalCard.objects.filter(business__business_id=request.user.business_id)
        serializer = serializers.PhysicalCardSerializer(physical_cards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    

class MemberExitsApi(APIView):
    authentication_classes = [BusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Check if a member exists in the business and return their details",
        manual_parameters=[
            openapi.Parameter(
                'mobile_number',
                openapi.IN_QUERY,
                description="Mobile number of the member",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Member exists and details are returned",
                schema=serializers.MemberSerializer()
            ),
            404: openapi.Response(
                description="Member not found",
                schema=serializers.MemberExistenceSerializer()
            )
        }
    )
    def get(self, request):
        mobile_number = request.GET.get("mobile_number")
        if not mobile_number:
            return Response(
                {"success": False, "message": "Mobile number is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            member = models.Member.objects.get(mobile_number=mobile_number)
        except models.Member.DoesNotExist:
            return Response(
                {"success": False,"is_present":False, "message": "Member does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = serializers.MemberSerializer(member)
        return Response(
            {"success": True,"is_present":True, "data": serializer.data},
            status=status.HTTP_200_OK
        )
        

class AddMemberBybusinessEntrypassApi(APIView):
    """
    API to add a new member user for entry passs.
    """
    authentication_classes = [BusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=serializers.EntryPassMemberSerializer,
        tags=["Institute"]  # ✅ Grouping under "Job Mitra"
    )
   
    def post(self, request):
        referal_id = request.user.business_id
        data = request.data

        # ✅ Check for existing mobile/email BEFORE serializer validation
        email = data.get("email")
        mobile_number = data.get("mobile_number")

        if models.Member.objects.filter(email=email).exists():
            return Response({
                "success": False,
                "message": "Member with this email already exists."
            }, status=status.HTTP_200_OK)

        if models.Member.objects.filter(mobile_number=mobile_number).exists():
            return Response({
                "success": False,
                "message": "Member with this mobile number already exists."
            }, status=status.HTTP_200_OK)

        # Now validate the rest
        serializer = serializers.EntryPassMemberSerializer(data=data)
        if serializer.is_valid():
            full_name = serializer.validated_data["full_name"]
            email = serializer.validated_data["email"]
            pin = serializer.validated_data["pin"]
            mobile_number = serializer.validated_data["mobile_number"]
          
           
            # Create staff user
            user = models.Member.objects.create(
                email=email,
                pin=make_password(pin),
                full_name=full_name,
                mobile_number=mobile_number,
                MbrReferalId=referal_id,
               
            )
            
            try:
                business = models.Business.objects.get(business_id=referal_id)
            except models.Business.DoesNotExist:
                return Response({"error": "Invalid Referral ID"}, status=status.HTTP_404_NOT_FOUND)

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
            
            JobProfile.objects.create(
                MbrCardNo=user,
                BasicInformation={
                    "full_name": user.full_name,
                    "mobile_number": user.mobile_number,
                    "email": user.email or ""
                },
              
            )
            models.CardMapper.objects.create(
                business_id=business.business_id,
                primary_card=user,
                secondary_card=user.mbrcardno,
                secondary_card_type="digital"
            )
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
            return Response({"success": True,"message": "member added successfully","member": {
                "mbrcardno": user.mbrcardno,
                "full_name": user.full_name,
                "email": user.email,
                "mobile_number": user.mobile_number,
                "address": user.address
            }}, status=status.HTTP_201_CREATED)
           
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(
        responses={200: serializers.EntryPassMemberSerializer(many=True)},
        tags=["Institute"]
    )
    def get(self, request):
        """Retrieve all referred members and return total count."""

        referal_id = request.user.business_id
        staff_users = models.Member.objects.filter(MbrReferalId=referal_id)
        total_students = staff_users.count()
        serializer = serializers.EntryPassMemberSerializer(staff_users, many=True)

        return Response({
            "success": True,
            "total_students": total_students,
            "members": serializer.data
        }, status=status.HTTP_200_OK)