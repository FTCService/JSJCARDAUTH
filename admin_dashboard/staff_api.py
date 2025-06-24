from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from app_common.models import Member,Business,User, BusinessKyc
from . import serializers
from admin_dashboard.models import CardPurpose
from helpers.utils import send_otp_to_mobile
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from app_common.authentication import UserTokenAuthentication
from app_common.models import PhysicalCard, Business, TempBusinessUser
from collections import defaultdict
import random



class StaffDashboard(APIView):
    """
    API to get the total count of registered businesses.
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve the total count of registered businesses.",
        responses={200: openapi.Response("Total number of businesses", schema=openapi.Schema(type=openapi.TYPE_INTEGER))}
    )
    def get(self, request):
        total_businesses = Business.objects.count()  # Get the total count of businesses
        total_members = Member.objects.count() # Get the total count of

        return Response(
            {
                "success": True,
                "total_businesses": total_businesses,
                "total_members": total_members
            },
            status=status.HTTP_200_OK
        )
        
        
        
class AddJobMitraApi(APIView):
    """
    API to add a new Job Mitra user (Admin Only).
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=serializers.JobMitraUserSerializer,
        tags=["Job Mitra"]  # ✅ Grouping under "Job Mitra"
    )
   
    def post(self, request):
        serializer = serializers.JobMitraUserSerializer(data=request.data)
        if serializer.is_valid():
            full_name = serializer.validated_data["full_name"]
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]
            employee_id = serializer.validated_data["employee_id"]

            state = serializer.validated_data.get("state")
            district = serializer.validated_data.get("district")
            block = serializer.validated_data.get("block")
            village = serializer.validated_data.get("village")
            pincode = serializer.validated_data.get("pincode")
            # Check if the email is already used
            if User.objects.filter(email=email).exists():
                return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

            # Build meta_data dict
            meta_data = {
                "state": state,
                "district": district,
                "block": block,
                "village": village,
                "pincode": pincode
            }
            # Create staff user
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                employee_id=employee_id,
                is_jobmitra=True,
                meta_data=meta_data
            )

            return Response({"message": "Job Mitra user added successfully"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(
        responses={200: serializers.JobMitraUserSerializer(many=True)},
        tags=["Job Mitra"]
    )
    def get(self, request):
        """Retrieve all job mitra users."""
        staff_users = User.objects.filter(is_jobmitra=True)
        serializer = serializers.JobMitraUserSerializer(staff_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class InstituteSignupApi(APIView):
    """
    API endpoint to initiate Business Signup.
    This view:
    - Accepts mobile_number, email, business_name, and PIN.
    - Validates input.
    - Sends an OTP to the mobile number.
    - Saves data to TempUser for pending verification.
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
    operation_description="Get a list of all registered institute businesses.",
    responses={200: serializers.InstituteSignupSerializer(many=True)}
    )
    def get(self, request):
        """
        Returns a list of all registered institutes.
        """
        institutes = Business.objects.filter(is_institute=True)
        serializer = serializers.InstituteSignupSerializer(institutes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    @swagger_auto_schema(
        request_body=serializers.InstituteSignupSerializer
    )
    def post(self, request):
        serializer = serializers.InstituteSignupSerializer(data=request.data)

        # Step 1: Validate all fields (mobile, pin, email, business_name)
        if serializer.is_valid():
            mobile_number = serializer.validated_data["mobile_number"]
            business_name = serializer.validated_data["business_name"]
            pin = serializer.validated_data["pin"]
            email = serializer.validated_data["email"]

            # # Step 2: Generate OTP (6-digit)
            # otp = random.randint(100000, 999999)

            # Step 3: Check if already registered
            if Business.objects.filter(mobile_number=mobile_number).exists():
                return Response(
                    {"message": "Mobile number already registered. Please log in."},
                    status=status.HTTP_200_OK
                )

            if Business.objects.filter(email=email).exists():
                return Response(
                    {"message": "Email already registered. Please log in."},
                    status=status.HTTP_200_OK
                )

            # Step 4: Save or update TempUser entry
            user = Business.objects.create_user(
                mobile_number=mobile_number,
                pin=pin,
                business_name=business_name,
                email=email,
                is_institute=True
            )

        
            # Step 6: Respond success
            return Response(
                {"message": "institute add successfuly", },  
                status=status.HTTP_200_OK
            )

        # Step 7: If validation fails
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)