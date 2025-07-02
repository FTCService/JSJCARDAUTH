from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from app_common.models import Member,Business,User, UserAuthToken, GovernmentUser
from . import serializers
from app_common.authentication import UserTokenAuthentication
from django.contrib.auth import logout
from app_common.serializers import GovernmentUserSerializer
from django.db.models import Q



class UserLogoutApi(APIView):
    """
    API for business logout (removes authentication token and ends session).
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Logs out the currently authenticated member.",
        responses={
            200: openapi.Response(description="Logout Successful", examples={"application/json": {"message": "Logout Successful"}}),
            401: openapi.Response(description="Unauthorized - Invalid or missing token"),
            500: openapi.Response(description="Internal Server Error", examples={"application/json": {"error": "Something went wrong.", "details": "Error message"}})
        },
    )
    def post(self, request):
        try:
            UserAuthToken.objects.filter(user=request.user.id).delete()
            logout(request)
            return Response({"message": "Logout Successful"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": "Something went wrong.", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
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
            mobile_number = serializer.validated_data["mobile_number"]
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
            address = {
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
                mobile_number=mobile_number,
                employee_id=employee_id,
                is_jobmitra=True,
                address=address
            )

            return Response({"message": "Job Mitra user added successfully"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(
        responses={200: serializers.JobMitraUserListSerializer(many=True)},
        tags=["Job Mitra"]
    )
    def get(self, request):
        """Retrieve all job mitra users."""
        staff_users = User.objects.filter(is_jobmitra=True)
        serializer = serializers.JobMitraUserListSerializer(staff_users, many=True)
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
    responses={200: serializers.InstituteListSerializer(many=True)}
    )
    def get(self, request):
        """
        Returns a list of all registered institutes.
        """
        institutes = Business.objects.filter(is_institute=True)
        serializer = serializers.InstituteListSerializer(institutes, many=True)
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
    
    
    
class AddGovernmentUserApi(APIView):
    """
    API to add and list Government users.
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=GovernmentUserSerializer,
        tags=["Government"]
    )
    def post(self, request):
        serializer = GovernmentUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Government user created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses={200: GovernmentUserSerializer(many=True)},
        tags=["Government"]
    )
    def get(self, request):
        users = GovernmentUser.objects.filter(is_government=True, is_active=True)
        serializer = GovernmentUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    
    
class BusinessSearchAPIView(APIView):
    """
    API to search businesses by business_id or business_name (partial match).
    """

    @swagger_auto_schema(
        operation_summary="Search Businesses",
        operation_description="Search businesses by partial business_id or business_name as a query parameter.",
        manual_parameters=[
            openapi.Parameter(
                'query',
                openapi.IN_QUERY,
                description="Search keyword (partial business ID or name)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        tags=["Business"],
        responses={
            200: openapi.Response(
                description="Matching businesses",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "business_id": openapi.Schema(type=openapi.TYPE_STRING),
                                    "business_name": openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            )
                        )
                    }
                )
            ),
            400: "Query parameter missing"
        }
    )
    def get(self, request):
        query = request.query_params.get("query")

        if not query:
            return Response({
                "success": False,
                "message": "Please provide a 'query' parameter."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Search by partial business_id or name
        businesses = Business.objects.filter(
            Q(business_id__icontains=query) | Q(business_name__icontains=query)
        )

        serializer = serializers.BusinessShortSerializer(businesses, many=True)
        return Response({
            "success": True,
            "message": "Matching businesses found.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)