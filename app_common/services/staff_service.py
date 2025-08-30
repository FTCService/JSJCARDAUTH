from django.core.exceptions import ValidationError
from django.db import transaction
from ..models import User, UserAuthToken
import secrets


class StaffService:
    """Service class for Staff/Admin User-related business logic"""
    
    @staticmethod
    def create_staff_user(full_name, employee_id, email, mobile_number, password, is_staff=True, is_jobmitra=False):
        """Create a new staff/admin user"""
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    full_name=full_name,
                    employee_id=employee_id,
                    email=email,
                    mobile_number=mobile_number,
                    password=password,
                    is_staff=is_staff,
                    is_jobmitra=is_jobmitra
                )
                return user
        except Exception as e:
            raise ValidationError(f"Error creating staff user: {str(e)}")
    
    @staticmethod
    def authenticate_staff_user(email, password):
        """Authenticate staff user and return auth token"""
        try:
            user = User.objects.get(email=email)
            
            if not user.check_password(password):
                raise ValidationError("Invalid credentials")
            
            if not user.is_active:
                raise ValidationError("Account is inactive")
            
            # Generate or get auth token
            auth_token, created = UserAuthToken.objects.get_or_create(
                user=user,
                defaults={'key': secrets.token_urlsafe(32)}
            )
            
            if not created:
                # Regenerate token for security
                auth_token.key = secrets.token_urlsafe(32)
                auth_token.save()
            
            return user, auth_token.key
            
        except User.DoesNotExist:
            raise ValidationError("Invalid credentials")
        except Exception as e:
            raise ValidationError(f"Authentication failed: {str(e)}")
    
    @staticmethod
    def update_staff_profile(user, **kwargs):
        """Update staff user profile information"""
        try:
            allowed_fields = [
                'full_name', 'mobile_number', 'address', 'meta_data'
            ]
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(user, field, value)
            
            user.save()
            return user
            
        except Exception as e:
            raise ValidationError(f"Error updating profile: {str(e)}")
    
    @staticmethod
    def change_staff_password(user, old_password, new_password):
        """Change staff user password after verifying old password"""
        try:
            if not user.check_password(old_password):
                raise ValidationError("Invalid current password")
            
            user.set_password(new_password)
            user.save()
            
            # Invalidate all existing tokens for security
            UserAuthToken.objects.filter(user=user).delete()
            
            return True
            
        except Exception as e:
            raise ValidationError(f"Error changing password: {str(e)}")
    
    @staticmethod
    def promote_to_admin(user, promoted_by):
        """Promote staff user to admin"""
        try:
            user.is_superuser = True
            if not user.meta_data:
                user.meta_data = {}
            user.meta_data['promoted_by'] = promoted_by
            user.meta_data['promoted_at'] = str(timezone.now())
            user.save()
            
            return user
            
        except Exception as e:
            raise ValidationError(f"Error promoting user: {str(e)}")
    
    @staticmethod
    def demote_from_admin(user, demoted_by):
        """Demote admin user to staff"""
        try:
            user.is_superuser = False
            if not user.meta_data:
                user.meta_data = {}
            user.meta_data['demoted_by'] = demoted_by
            user.meta_data['demoted_at'] = str(timezone.now())
            user.save()
            
            return user
            
        except Exception as e:
            raise ValidationError(f"Error demoting user: {str(e)}")
    
    @staticmethod
    def toggle_jobmitra_access(user, enabled_by):
        """Toggle JobMitra access for user"""
        try:
            user.is_jobmitra = not user.is_jobmitra
            if not user.meta_data:
                user.meta_data = {}
            user.meta_data['jobmitra_toggled_by'] = enabled_by
            user.meta_data['jobmitra_toggled_at'] = str(timezone.now())
            user.save()
            
            return user
            
        except Exception as e:
            raise ValidationError(f"Error toggling JobMitra access: {str(e)}")
    
    @staticmethod
    def deactivate_staff_user(user, reason=None, deactivated_by=None):
        """Deactivate staff user account"""
        try:
            user.is_active = False
            if not user.meta_data:
                user.meta_data = {}
            if reason:
                user.meta_data['deactivation_reason'] = reason
            if deactivated_by:
                user.meta_data['deactivated_by'] = deactivated_by
            user.meta_data['deactivated_at'] = str(timezone.now())
            user.save()
            
            # Remove all auth tokens
            UserAuthToken.objects.filter(user=user).delete()
            
            return True
            
        except Exception as e:
            raise ValidationError(f"Error deactivating staff user: {str(e)}")
    
    @staticmethod
    def activate_staff_user(user, activated_by=None):
        """Activate staff user account"""
        try:
            user.is_active = True
            if not user.meta_data:
                user.meta_data = {}
            if activated_by:
                user.meta_data['activated_by'] = activated_by
            user.meta_data['activated_at'] = str(timezone.now())
            user.save()
            
            return True
            
        except Exception as e:
            raise ValidationError(f"Error activating staff user: {str(e)}")
    
    @staticmethod
    def get_staff_statistics():
        """Get staff user statistics"""
        try:
            total_staff = User.objects.count()
            active_staff = User.objects.filter(is_active=True).count()
            admin_users = User.objects.filter(is_superuser=True, is_active=True).count()
            jobmitra_users = User.objects.filter(is_jobmitra=True, is_active=True).count()
            staff_only = User.objects.filter(is_staff=True, is_superuser=False, is_active=True).count()
            
            return {
                'total_staff': total_staff,
                'active_staff': active_staff,
                'inactive_staff': total_staff - active_staff,
                'admin_users': admin_users,
                'jobmitra_users': jobmitra_users,
                'staff_only': staff_only,
                'activation_rate': round((active_staff / total_staff * 100), 2) if total_staff > 0 else 0
            }
        except Exception as e:
            raise ValidationError(f"Error getting statistics: {str(e)}")
    
    @staticmethod
    def logout_staff_user(user):
        """Logout staff user by removing auth tokens"""
        try:
            UserAuthToken.objects.filter(user=user).delete()
            return True
        except Exception as e:
            raise ValidationError(f"Error during logout: {str(e)}")
    
    @staticmethod
    def get_user_by_employee_id(employee_id):
        """Get staff user by employee ID"""
        try:
            return User.objects.get(employee_id=employee_id, is_active=True)
        except User.DoesNotExist:
            raise ValidationError("User not found with this employee ID")
        except Exception as e:
            raise ValidationError(f"Error getting user: {str(e)}")
    
    @staticmethod
    def reset_user_password(user, new_password, reset_by):
        """Reset user password (admin function)"""
        try:
            user.set_password(new_password)
            if not user.meta_data:
                user.meta_data = {}
            user.meta_data['password_reset_by'] = reset_by
            user.meta_data['password_reset_at'] = str(timezone.now())
            user.save()
            
            # Invalidate all existing tokens
            UserAuthToken.objects.filter(user=user).delete()
            
            return True
            
        except Exception as e:
            raise ValidationError(f"Error resetting password: {str(e)}")
