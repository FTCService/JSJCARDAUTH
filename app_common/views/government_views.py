from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from ..models import GovernmentUser
from ..serializers import (
    GovernmentUserSerializer,
    GovernmentUserRegistrationSerializer
)
from ..services import GovernmentService
from ..authentication import GovernmentAuthentication


class GovernmentUserRegistrationView(APIView):
    """View for government user registration (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        try:
            serializer = GovernmentUserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                government_user = GovernmentService.create_government_user(
                    email=serializer.validated_data['email'],
                    full_name=serializer.validated_data['full_name'],
                    mobile_number=serializer.validated_data['mobile_number'],
                    department=serializer.validated_data['department'],
                    designation=serializer.validated_data['designation'],
                    password=serializer.validated_data['password']
                )
                
                user_serializer = GovernmentUserSerializer(government_user)
                
                return Response({
                    'message': 'Government user created successfully',
                    'user': user_serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class GovernmentUserLoginView(APIView):
    """View for government user login"""
    
    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            
            if not email or not password:
                return Response({
                    'error': 'Email and password are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            government_user, token = GovernmentService.authenticate_government_user(email, password)
            user_serializer = GovernmentUserSerializer(government_user)
            
            return Response({
                'message': 'Login successful',
                'token': token,
                'user': user_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class GovernmentUserProfileView(APIView):
    """View for government user profile management"""
    authentication_classes = [GovernmentAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get government user profile"""
        serializer = GovernmentUserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update government user profile"""
        try:
            updated_user = GovernmentService.update_government_user_profile(
                request.user, 
                **request.data
            )
            serializer = GovernmentUserSerializer(updated_user)
            
            return Response({
                'message': 'Profile updated successfully',
                'user': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class GovernmentUserPasswordChangeView(APIView):
    """View for changing government user password"""
    authentication_classes = [GovernmentAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            old_password = request.data.get('old_password')
            new_password = request.data.get('new_password')
            
            if not old_password or not new_password:
                return Response({
                    'error': 'Old password and new password are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            GovernmentService.change_government_user_password(
                request.user, old_password, new_password
            )
            
            return Response({
                'message': 'Password changed successfully'
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class GovernmentUserListView(generics.ListAPIView):
    """View for listing government users (Admin only)"""
    queryset = GovernmentUser.objects.all()
    serializer_class = GovernmentUserSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = GovernmentUser.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter is not None:
            queryset = queryset.filter(is_active=status_filter.lower() == 'true')
        
        # Filter by department
        department = self.request.query_params.get('department', None)
        if department is not None:
            queryset = queryset.filter(department__icontains=department)
        
        # Search by name or email
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                models.Q(full_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(mobile_number__icontains=search)
            )
        
        return queryset.order_by('-date_joined')


class GovernmentUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for government user detail management (Admin only)"""
    queryset = GovernmentUser.objects.all()
    serializer_class = GovernmentUserSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def delete(self, request, *args, **kwargs):
        """Deactivate government user instead of deleting"""
        government_user = self.get_object()
        try:
            reason = request.data.get('reason', 'Deactivated by admin')
            GovernmentService.deactivate_government_user(government_user, reason)
            return Response({
                'message': 'Government user deactivated successfully'
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class GovernmentUserActivationView(APIView):
    """View for activating/deactivating government users (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, pk):
        try:
            government_user = get_object_or_404(GovernmentUser, pk=pk)
            action = request.data.get('action')  # 'activate' or 'deactivate'
            
            if action == 'activate':
                GovernmentService.activate_government_user(government_user)
                message = 'Government user activated successfully'
            elif action == 'deactivate':
                reason = request.data.get('reason', 'Deactivated by admin')
                GovernmentService.deactivate_government_user(government_user, reason)
                message = 'Government user deactivated successfully'
            else:
                return Response({
                    'error': 'Invalid action. Use "activate" or "deactivate"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = GovernmentUserSerializer(government_user)
            return Response({
                'message': message,
                'user': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class GovernmentUserStatsView(APIView):
    """View for government user statistics (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        try:
            stats = GovernmentService.get_government_user_statistics()
            return Response(stats)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class DepartmentUsersView(APIView):
    """View for getting users by department"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, department):
        try:
            users = GovernmentService.get_users_by_department(department)
            serializer = GovernmentUserSerializer(users, many=True)
            return Response({
                'department': department,
                'users': serializer.data,
                'count': len(serializer.data)
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class RecentLoginsView(APIView):
    """View for getting recent government user logins (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 10))
            recent_logins = GovernmentService.get_recent_logins(limit)
            return Response({
                'recent_logins': recent_logins
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def government_user_logout(request):
    """Logout government user by deleting auth token"""
    try:
        GovernmentService.logout_government_user(request.user)
        return Response({
            'message': 'Logout successful'
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
