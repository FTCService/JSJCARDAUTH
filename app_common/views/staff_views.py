from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from ..models import User
from ..serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    StaffProfileSerializer
)
from ..services import StaffService, MemberService, BusinessService, GovernmentService
from ..authentication import StaffAuthentication


class StaffRegistrationView(APIView):
    """View for staff registration (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                staff_user = StaffService.create_staff_user(
                    full_name=serializer.validated_data['full_name'],
                    employee_id=serializer.validated_data['employee_id'],
                    email=serializer.validated_data['email'],
                    mobile_number=serializer.validated_data['mobile_number'],
                    password=serializer.validated_data['password'],
                    is_staff=serializer.validated_data.get('is_staff', True),
                    is_jobmitra=serializer.validated_data.get('is_jobmitra', False)
                )
                
                user_serializer = UserSerializer(staff_user)
                
                return Response({
                    'message': 'Staff user created successfully',
                    'user': user_serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class StaffLoginView(APIView):
    """View for staff login"""
    
    def post(self, request):
        try:
            serializer = UserLoginSerializer(data=request.data)
            if serializer.is_valid():
                staff_user, token = StaffService.authenticate_staff_user(
                    email=serializer.validated_data['email'],
                    password=serializer.validated_data['password']
                )
                
                user_serializer = UserSerializer(staff_user)
                
                return Response({
                    'message': 'Login successful',
                    'token': token,
                    'user': user_serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class StaffProfileView(APIView):
    """View for staff profile management"""
    authentication_classes = [StaffAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get staff profile"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update staff profile"""
        try:
            updated_user = StaffService.update_staff_profile(
                request.user, 
                **request.data
            )
            serializer = UserSerializer(updated_user)
            
            return Response({
                'message': 'Profile updated successfully',
                'user': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class StaffPasswordChangeView(APIView):
    """View for changing staff password"""
    authentication_classes = [StaffAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            old_password = request.data.get('old_password')
            new_password = request.data.get('new_password')
            
            if not old_password or not new_password:
                return Response({
                    'error': 'Old password and new password are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            StaffService.change_staff_password(request.user, old_password, new_password)
            
            return Response({
                'message': 'Password changed successfully'
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class StaffListView(generics.ListAPIView):
    """View for listing staff users (Admin only)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = User.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter is not None:
            queryset = queryset.filter(is_active=status_filter.lower() == 'true')
        
        # Filter by role
        role_filter = self.request.query_params.get('role', None)
        if role_filter == 'admin':
            queryset = queryset.filter(is_superuser=True)
        elif role_filter == 'staff':
            queryset = queryset.filter(is_staff=True, is_superuser=False)
        elif role_filter == 'jobmitra':
            queryset = queryset.filter(is_jobmitra=True)
        
        # Search by name, email, or employee ID
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                models.Q(full_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(employee_id__icontains=search)
            )
        
        return queryset.order_by('-date_joined')


class StaffDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for staff detail management (Admin only)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'employee_id'
    
    def delete(self, request, *args, **kwargs):
        """Deactivate staff user instead of deleting"""
        staff_user = self.get_object()
        try:
            reason = request.data.get('reason', 'Deactivated by admin')
            deactivated_by = request.user.email
            StaffService.deactivate_staff_user(staff_user, reason, deactivated_by)
            return Response({
                'message': 'Staff user deactivated successfully'
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class StaffPromotionView(APIView):
    """View for promoting/demoting staff users (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, employee_id):
        try:
            staff_user = StaffService.get_user_by_employee_id(employee_id)
            action = request.data.get('action')  # 'promote' or 'demote'
            
            if action == 'promote':
                StaffService.promote_to_admin(staff_user, request.user.email)
                message = 'User promoted to admin successfully'
            elif action == 'demote':
                StaffService.demote_from_admin(staff_user, request.user.email)
                message = 'User demoted from admin successfully'
            else:
                return Response({
                    'error': 'Invalid action. Use "promote" or "demote"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = UserSerializer(staff_user)
            return Response({
                'message': message,
                'user': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class JobMitraToggleView(APIView):
    """View for toggling JobMitra access (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, employee_id):
        try:
            staff_user = StaffService.get_user_by_employee_id(employee_id)
            StaffService.toggle_jobmitra_access(staff_user, request.user.email)
            
            serializer = UserSerializer(staff_user)
            return Response({
                'message': f'JobMitra access {"enabled" if staff_user.is_jobmitra else "disabled"} successfully',
                'user': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class StaffPasswordResetView(APIView):
    """View for resetting staff password (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, employee_id):
        try:
            staff_user = StaffService.get_user_by_employee_id(employee_id)
            new_password = request.data.get('new_password')
            
            if not new_password:
                return Response({
                    'error': 'New password is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            StaffService.reset_user_password(staff_user, new_password, request.user.email)
            
            return Response({
                'message': 'Password reset successfully'
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class StaffDashboardView(APIView):
    """View for staff dashboard with statistics"""
    authentication_classes = [StaffAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            # Gather statistics from all services
            member_stats = MemberService.get_member_statistics()
            business_stats = BusinessService.get_business_statistics()
            government_stats = GovernmentService.get_government_user_statistics()
            staff_stats = StaffService.get_staff_statistics()
            
            dashboard_data = {
                'overview': {
                    'total_members': member_stats['total_members'],
                    'total_businesses': business_stats['total_businesses'],
                    'total_government_users': government_stats['total_users'],
                    'total_staff': staff_stats['total_staff']
                },
                'member_stats': member_stats,
                'business_stats': business_stats,
                'government_stats': government_stats,
                'staff_stats': staff_stats,
                'user_info': {
                    'name': request.user.full_name,
                    'email': request.user.email,
                    'employee_id': request.user.employee_id,
                    'is_admin': request.user.is_superuser,
                    'is_jobmitra': request.user.is_jobmitra
                }
            }
            
            return Response(dashboard_data)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class StaffActivationView(APIView):
    """View for activating/deactivating staff users (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, employee_id):
        try:
            staff_user = StaffService.get_user_by_employee_id(employee_id)
            action = request.data.get('action')  # 'activate' or 'deactivate'
            
            if action == 'activate':
                StaffService.activate_staff_user(staff_user, request.user.email)
                message = 'Staff user activated successfully'
            elif action == 'deactivate':
                reason = request.data.get('reason', 'Deactivated by admin')
                StaffService.deactivate_staff_user(staff_user, reason, request.user.email)
                message = 'Staff user deactivated successfully'
            else:
                return Response({
                    'error': 'Invalid action. Use "activate" or "deactivate"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = UserSerializer(staff_user)
            return Response({
                'message': message,
                'user': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def staff_logout(request):
    """Logout staff user by deleting auth token"""
    try:
        StaffService.logout_staff_user(request.user)
        return Response({
            'message': 'Logout successful'
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
