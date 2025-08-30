from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from ..models import GovernmentUser, GovernmentAuthToken
import secrets


class GovernmentService:
    """Service class for Government User-related business logic"""
    
    @staticmethod
    def create_government_user(email, full_name, mobile_number, department, designation, password):
        """Create a new government user"""
        try:
            with transaction.atomic():
                government_user = GovernmentUser.objects.create_user(
                    email=email,
                    full_name=full_name,
                    mobile_number=mobile_number,
                    department=department,
                    designation=designation,
                    password=password
                )
                return government_user
        except Exception as e:
            raise ValidationError(f"Error creating government user: {str(e)}")
    
    @staticmethod
    def authenticate_government_user(email, password):
        """Authenticate government user and return auth token"""
        try:
            government_user = GovernmentUser.objects.get(email=email)
            
            if not government_user.check_password(password):
                raise ValidationError("Invalid credentials")
            
            if not government_user.is_active:
                raise ValidationError("Account is inactive")
            
            # Generate or get auth token
            auth_token, created = GovernmentAuthToken.objects.get_or_create(
                user=government_user,
                defaults={'key': secrets.token_urlsafe(32)}
            )
            
            if not created:
                # Update existing token
                auth_token.key = secrets.token_urlsafe(32)
                auth_token.save()
            
            return government_user, auth_token.key
            
        except GovernmentUser.DoesNotExist:
            raise ValidationError("Invalid credentials")
        except Exception as e:
            raise ValidationError(f"Authentication failed: {str(e)}")
    
    @staticmethod
    def update_government_user_profile(government_user, **kwargs):
        """Update government user profile information"""
        try:
            allowed_fields = [
                'full_name', 'mobile_number', 'department', 'designation'
            ]
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(government_user, field, value)
            
            government_user.last_updated = timezone.now()
            government_user.save()
            return government_user
            
        except Exception as e:
            raise ValidationError(f"Error updating profile: {str(e)}")
    
    @staticmethod
    def change_government_user_password(government_user, old_password, new_password):
        """Change government user password after verifying old password"""
        try:
            if not government_user.check_password(old_password):
                raise ValidationError("Invalid current password")
            
            government_user.set_password(new_password)
            government_user.save()
            
            # Invalidate all existing tokens
            GovernmentAuthToken.objects.filter(user=government_user).delete()
            
            return True
            
        except Exception as e:
            raise ValidationError(f"Error changing password: {str(e)}")
    
    @staticmethod
    def deactivate_government_user(government_user, reason=None):
        """Deactivate government user account"""
        try:
            government_user.is_active = False
            government_user.last_updated = timezone.now()
            government_user.save()
            
            # Remove all auth tokens
            GovernmentAuthToken.objects.filter(user=government_user).delete()
            
            return True
            
        except Exception as e:
            raise ValidationError(f"Error deactivating government user: {str(e)}")
    
    @staticmethod
    def activate_government_user(government_user):
        """Activate government user account"""
        try:
            government_user.is_active = True
            government_user.last_updated = timezone.now()
            government_user.save()
            
            return True
            
        except Exception as e:
            raise ValidationError(f"Error activating government user: {str(e)}")
    
    @staticmethod
    def get_users_by_department(department):
        """Get all government users by department"""
        try:
            return GovernmentUser.objects.filter(
                department__icontains=department,
                is_active=True
            ).order_by('full_name')
        except Exception as e:
            raise ValidationError(f"Error getting users by department: {str(e)}")
    
    @staticmethod
    def get_government_user_statistics():
        """Get government user statistics"""
        try:
            total_users = GovernmentUser.objects.count()
            active_users = GovernmentUser.objects.filter(is_active=True).count()
            inactive_users = total_users - active_users
            
            # Department-wise breakdown
            departments = GovernmentUser.objects.values_list('department', flat=True).distinct()
            department_stats = {}
            for dept in departments:
                dept_count = GovernmentUser.objects.filter(department=dept, is_active=True).count()
                department_stats[dept] = dept_count
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': inactive_users,
                'department_breakdown': department_stats,
                'activation_rate': round((active_users / total_users * 100), 2) if total_users > 0 else 0
            }
        except Exception as e:
            raise ValidationError(f"Error getting statistics: {str(e)}")
    
    @staticmethod
    def logout_government_user(government_user):
        """Logout government user by removing auth tokens"""
        try:
            GovernmentAuthToken.objects.filter(user=government_user).delete()
            return True
        except Exception as e:
            raise ValidationError(f"Error during logout: {str(e)}")
    
    @staticmethod
    def get_recent_logins(limit=10):
        """Get recent government user logins"""
        try:
            recent_tokens = GovernmentAuthToken.objects.select_related('user').order_by('-created_at')[:limit]
            return [
                {
                    'user': token.user.full_name,
                    'email': token.user.email,
                    'department': token.user.department,
                    'login_time': token.created_at
                }
                for token in recent_tokens
            ]
        except Exception as e:
            raise ValidationError(f"Error getting recent logins: {str(e)}")
