from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from ..models import Member, TempMemberUser
from ..serializers import (
    MemberSerializer, 
    MemberRegistrationSerializer,
    MemberLoginSerializer,
    TempMemberUserSerializer
)
from ..services import MemberService
from ..authentication import MemberAuthentication


class MemberRegistrationView(APIView):
    """View for member registration - Step 1: Send OTP"""
    
    def post(self, request):
        try:
            serializer = TempMemberUserSerializer(data=request.data)
            if serializer.is_valid():
                temp_member, otp = MemberService.create_temp_member(
                    full_name=serializer.validated_data['full_name'],
                    email=serializer.validated_data.get('email'),
                    mobile_number=serializer.validated_data['mobile_number'],
                    pin=request.data.get('pin'),
                    ref_by=serializer.validated_data.get('ref_by')
                )
                
                # TODO: Send OTP via SMS/Email service
                
                return Response({
                    'message': 'OTP sent successfully',
                    'mobile_number': temp_member.mobile_number,
                    'otp': otp  # Remove this in production
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class MemberOTPVerificationView(APIView):
    """View for member registration - Step 2: Verify OTP and create member"""
    
    def post(self, request):
        try:
            mobile_number = request.data.get('mobile_number')
            otp = request.data.get('otp')
            
            if not mobile_number or not otp:
                return Response({
                    'error': 'Mobile number and OTP are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            member = MemberService.verify_otp_and_create_member(mobile_number, otp)
            serializer = MemberSerializer(member)
            
            return Response({
                'message': 'Member created successfully',
                'member': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class MemberLoginView(APIView):
    """View for member login"""
    
    def post(self, request):
        try:
            serializer = MemberLoginSerializer(data=request.data)
            if serializer.is_valid():
                member, token = MemberService.authenticate_member(
                    mobile_number=serializer.validated_data['mobile_number'],
                    pin=serializer.validated_data['pin']
                )
                
                member_serializer = MemberSerializer(member)
                
                return Response({
                    'message': 'Login successful',
                    'token': token,
                    'member': member_serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class MemberProfileView(APIView):
    """View for member profile management"""
    authentication_classes = [MemberAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get member profile"""
        serializer = MemberSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update member profile"""
        try:
            updated_member = MemberService.update_member_profile(
                request.user, 
                **request.data
            )
            serializer = MemberSerializer(updated_member)
            
            return Response({
                'message': 'Profile updated successfully',
                'member': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class MemberPINChangeView(APIView):
    """View for changing member PIN"""
    authentication_classes = [MemberAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            old_pin = request.data.get('old_pin')
            new_pin = request.data.get('new_pin')
            
            if not old_pin or not new_pin:
                return Response({
                    'error': 'Old PIN and new PIN are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            MemberService.change_member_pin(request.user, old_pin, new_pin)
            
            return Response({
                'message': 'PIN changed successfully'
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class MemberListView(generics.ListAPIView):
    """View for listing members (Admin only)"""
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = Member.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter is not None:
            queryset = queryset.filter(MbrStatus=status_filter.lower() == 'true')
        
        # Search by name or mobile
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                models.Q(full_name__icontains=search) |
                models.Q(mobile_number__icontains=search)
            )
        
        return queryset.order_by('-MbrCreatedAt')


class MemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for member detail management (Admin only)"""
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'mbrcardno'
    
    def delete(self, request, *args, **kwargs):
        """Deactivate member instead of deleting"""
        member = self.get_object()
        try:
            MemberService.deactivate_member(member)
            return Response({
                'message': 'Member deactivated successfully'
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class MemberStatsView(APIView):
    """View for member statistics (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        try:
            stats = MemberService.get_member_statistics()
            return Response(stats)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def member_logout(request):
    """Logout member by deleting auth token"""
    try:
        # The authentication class will handle token deletion
        request.user.auth_token.delete()
        return Response({
            'message': 'Logout successful'
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
