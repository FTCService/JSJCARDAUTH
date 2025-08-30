# architecture_examples/mvc_service_layer/member_controller.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .member_service import MemberService, MemberServiceError, MemberNotFoundError
from .serializers.member_serializer import (
    MemberSignupSerializer, 
    MemberOTPVerificationSerializer,
    MemberLoginSerializer,
    MemberProfileSerializer,
    MemberListSerializer
)


class MemberSignupController(APIView):
    """
    Controller for member signup process.
    Handles HTTP concerns only - business logic delegated to service layer.
    """
    
    @swagger_auto_schema(
        operation_summary="Initiate Member Signup",
        request_body=MemberSignupSerializer,
        responses={
            201: openapi.Response(
                description="Signup initiated successfully",
                examples={
                    "application/json": {
                        "status": 201,
                        "message": "OTP sent successfully",
                        "temp_user_id": 123
                    }
                }
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        """Initiate member signup with OTP verification."""
        serializer = MemberSignupSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                result = MemberService.initiate_signup(serializer.validated_data)
                
                return Response({
                    "status": 201,
                    "message": result['message'],
                    "temp_user_id": result['temp_user_id']
                }, status=status.HTTP_201_CREATED)
                
            except MemberServiceError as e:
                return Response({
                    "status": 400,
                    "message": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            "status": 400,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MemberOTPVerificationController(APIView):
    """Controller for OTP verification and member creation."""
    
    @swagger_auto_schema(
        operation_summary="Verify OTP and Create Member",
        request_body=MemberOTPVerificationSerializer,
        responses={
            201: openapi.Response(
                description="Member created successfully",
                examples={
                    "application/json": {
                        "status": 201,
                        "message": "Member created successfully",
                        "token": "abc123...",
                        "member": {
                            "id": 1,
                            "full_name": "John Doe",
                            "mobile_number": "9876543210"
                        }
                    }
                }
            ),
            400: "Invalid OTP or request"
        }
    )
    def post(self, request):
        """Verify OTP and create permanent member account."""
        serializer = MemberOTPVerificationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                member, token = MemberService.verify_otp_and_create_member(
                    serializer.validated_data['temp_user_id'],
                    serializer.validated_data['otp']
                )
                
                member_data = MemberProfileSerializer(member).data
                
                return Response({
                    "status": 201,
                    "message": "Member created successfully",
                    "token": token,
                    "member": member_data
                }, status=status.HTTP_201_CREATED)
                
            except MemberServiceError as e:
                return Response({
                    "status": 400,
                    "message": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            "status": 400,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MemberLoginController(APIView):
    """Controller for member authentication."""
    
    @swagger_auto_schema(
        operation_summary="Member Login",
        request_body=MemberLoginSerializer,
        responses={
            200: "Login successful",
            401: "Invalid credentials"
        }
    )
    def post(self, request):
        """Authenticate member and return token."""
        serializer = MemberLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            member = MemberService.authenticate_member(
                serializer.validated_data['mobile_number'],
                serializer.validated_data['pin']
            )
            
            if member:
                token = MemberService._generate_auth_token(member)
                member_data = MemberProfileSerializer(member).data
                
                return Response({
                    "status": 200,
                    "message": "Login successful",
                    "token": token,
                    "member": member_data
                }, status=status.HTTP_200_OK)
            
            return Response({
                "status": 401,
                "message": "Invalid credentials"
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        return Response({
            "status": 400,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MemberProfileController(APIView):
    """Controller for member profile operations."""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get Member Profile",
        responses={200: MemberProfileSerializer}
    )
    def get(self, request):
        """Get current member's profile."""
        serializer = MemberProfileSerializer(request.user)
        return Response({
            "status": 200,
            "member": serializer.data
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_summary="Update Member Profile",
        request_body=MemberProfileSerializer,
        responses={200: MemberProfileSerializer}
    )
    def put(self, request):
        """Update member profile."""
        serializer = MemberProfileSerializer(data=request.data, partial=True)
        
        if serializer.is_valid():
            try:
                updated_member = MemberService.update_member_profile(
                    request.user, 
                    serializer.validated_data
                )
                
                response_data = MemberProfileSerializer(updated_member).data
                
                return Response({
                    "status": 200,
                    "message": "Profile updated successfully",
                    "member": response_data
                }, status=status.HTTP_200_OK)
                
            except MemberServiceError as e:
                return Response({
                    "status": 400,
                    "message": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "status": 400,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MemberDetailController(APIView):
    """Controller for retrieving specific member details."""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get Member by Card Number",
        manual_parameters=[
            openapi.Parameter(
                'card_number',
                openapi.IN_PATH,
                description="Member's card number",
                type=openapi.TYPE_STRING
            )
        ],
        responses={
            200: MemberProfileSerializer,
            404: "Member not found"
        }
    )
    def get(self, request, card_number):
        """Get member details by card number."""
        try:
            member = MemberService.get_member_by_card_number(card_number)
            serializer = MemberProfileSerializer(member)
            
            return Response({
                "status": 200,
                "member": serializer.data
            }, status=status.HTTP_200_OK)
            
        except MemberNotFoundError as e:
            return Response({
                "status": 404,
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)


class MemberListController(APIView):
    """Controller for listing members with pagination and filtering."""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="List Members",
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page", type=openapi.TYPE_INTEGER),
            openapi.Parameter('status', openapi.IN_QUERY, description="Member status filter", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search term", type=openapi.TYPE_STRING),
        ],
        responses={200: MemberListSerializer}
    )
    def get(self, request):
        """Get paginated list of members with optional filtering."""
        # Extract query parameters
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        filters = {}
        if request.query_params.get('status') is not None:
            filters['status'] = request.query_params.get('status').lower() == 'true'
        if request.query_params.get('search'):
            filters['search'] = request.query_params.get('search')
        
        try:
            result = MemberService.get_members_list(filters, page, page_size)
            
            # Serialize members
            members_data = MemberListSerializer(result['members'], many=True).data
            
            return Response({
                "status": 200,
                "data": members_data,
                "pagination": {
                    "page": result['page'],
                    "page_size": result['page_size'],
                    "total_count": result['total_count'],
                    "total_pages": result['total_pages']
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": 500,
                "message": f"Internal server error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
