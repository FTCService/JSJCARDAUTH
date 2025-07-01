import random
from django.contrib.auth import authenticate, logout, login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from . import serializers, models
from helpers.utils import send_otp_to_mobile
import secrets
from django.utils import timezone
from .authentication import GovernmentTokenAuthentication
from django.contrib.auth.hashers import check_password, make_password




class GovermentLoginApi(APIView):
    """
    API to log in Government users using email and password.
    """

    @swagger_auto_schema(
        request_body=serializers.GovermentLoginSerializer,
        tags=["Government"]
    )
    def post(self, request):
        serializer = serializers.GovermentLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            from django.contrib.auth import authenticate
            user = authenticate(request, email=email, password=password)

            if user and isinstance(user, models.GovernmentUser):
                login(request, user)

                token_key = secrets.token_hex(32)
                token, created = models.GovernmentAuthToken.objects.update_or_create(
                    user=user,
                    defaults={"key": token_key}
                )

                return Response({
                    "message": "Login successful",
                    "token": token.key,
                    "user_type": "government",
                    "user_id": user.id,
                    "email": user.email,
                    "full_name": user.full_name
                }, status=status.HTTP_200_OK)

            return Response({"error": "Invalid credentials or not authorized"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class GovernmentLogoutApi(APIView):
    """
    API for government user logout (removes authentication token and ends session).
    """
    authentication_classes = [GovernmentTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Logs out the currently authenticated government user.",
        responses={
            200: openapi.Response(description="Logout Successful", examples={
                "application/json": {"message": "Logout Successful"}
            }),
            401: openapi.Response(description="Unauthorized - Invalid or missing token"),
            500: openapi.Response(description="Internal Server Error", examples={
                "application/json": {"error": "Something went wrong.", "details": "Error message"}
            })
        },
        tags=["Government"]
    )
    def post(self, request):
        try:
            models.GovernmentAuthToken.objects.filter(user=request.user).delete()
            logout(request)
            return Response({"message": "Logout Successful"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": "Something went wrong.",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            


class VerifyGovernmentTokenApi(APIView):
    """
    Endpoint to verify a GovernmentAuthToken from another service.
    """

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"detail": "Token required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            gov_token = models.GovernmentAuthToken.objects.get(key=token)
            user = gov_token.user

            if not isinstance(user, models.GovernmentUser):
                return Response({"detail": "Invalid user type."}, status=status.HTTP_401_UNAUTHORIZED)

            return Response({
                "valid": True,
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "mobile_number": user.mobile_number,
                "department": user.department,
                "designation": user.designation
            })

        except models.GovernmentAuthToken.DoesNotExist:
            return Response({
                "valid": False,
                "detail": "Invalid or expired token."
            }, status=status.HTTP_401_UNAUTHORIZED)
            
            
            

class BusinessSummaryAPIView(APIView):
    """
    Returns total of registered institutes and companies counts.
    """

    @swagger_auto_schema(
        operation_description="Get total of registered institutes  counts.",
        responses={
            200: openapi.Response(description="Business summary fetched successfully"),
            500: openapi.Response(description="Server error")
        },
        tags=["Government"]
    )
    def get(self, request):
        try:
            # Institutes
            institutes = models.Business.objects.filter(is_institute=True).count()
           
            # Companies
            companies = models.Business.objects.filter(is_business=True, is_institute=False).count()
            

            return Response({
                "success": True,
                "institutes": institutes,
                "companies": companies
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to fetch business summary.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BusinessListgovernmentApi(APIView):
    """
    API to list all registered businesses.
    """
    authentication_classes = [GovernmentTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve a list of all registered businesses.",
        responses={200: serializers.BusinessListSerializer(many=True)},tags=["Government"]
    )
    def get(self, request):
        businesses = models.Business.objects.filter(is_business=True,is_institute=False)
        serializer = serializers.BusinessListSerializer(businesses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class InstituteListgovernmentApi(APIView):
    """
    API to list all registered businesses.
    """
    authentication_classes = [GovernmentTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve a list of all registered businesses.",
        responses={200: serializers.BusinessListSerializer(many=True)},
        tags=["Government"]
    )
    def get(self, request):
        businesses = models.Business.objects.filter(is_institute=False)
        serializer = serializers.BusinessListSerializer(businesses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class StudentListgovernmentApi(APIView):
    """
    API to list all registered members.
    """
    authentication_classes = [GovernmentTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve a list of all registered members.",
        responses={200: serializers.MemberListSerializer(many=True)},
        tags=["Government"]
    )
    def get(self, request):
        members = models.Member.objects.all()
        serializer = serializers.MemberListSerializer(members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    
    
    
# class BusinessSummaryAPIView(APIView):
#     """
#     Returns list of registered institutes and companies with job counts.
#     """

#     @swagger_auto_schema(
#         operation_description="Get list of registered institutes and companies with job counts.",
#         responses={
#             200: openapi.Response(description="Business summary fetched successfully"),
#             500: openapi.Response(description="Server error")
#         },
#         tags=["Government"]
#     )
#     def get(self, request):
#         try:
#             # Institutes
#             institutes = models.Business.objects.filter(is_institute=True)
#             institute_list = [{"name": i.business_name} for i in institutes]

#             # Companies
#             companies = models.Business.objects.filter(is_business=True, is_institute=False)
#             company_list = []

#             # Call external job service to fetch job counts
#             for c in companies:
#                 job_count = 0
#                 try:
#                     response = requests.get(
#                         f"{settings.JOB_SERVER_URL}/job/count-by-business/",
#                         params={"business_id": c.id},
#                         timeout=5
#                     )
#                     if response.status_code == 200:
#                         job_count = response.json().get("job_count", 0)
#                 except requests.RequestException:
#                     job_count = 0  # fallback

#                 company_list.append({
#                     "name": c.business_name,
#                     "job_count": job_count
#                 })

#             return Response({
#                 "success": True,
#                 "institutes": institute_list,
#                 "companies": company_list
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({
#                 "success": False,
#                 "message": "Failed to fetch business summary.",
#                 "error": str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


