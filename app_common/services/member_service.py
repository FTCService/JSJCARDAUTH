from django.core.exceptions import ValidationError
from django.db import transaction
from ..models import Member, MemberAuthToken, TempMemberUser
import secrets
import random


class MemberService:
    """Service class for Member-related business logic"""
    
    @staticmethod
    def create_temp_member(full_name, email, mobile_number, pin, ref_by=None):
        """Create a temporary member user for OTP verification"""
        try:
            # Generate OTP
            otp = random.randint(100000, 999999)
            
            temp_member = TempMemberUser.objects.create(
                full_name=full_name,
                email=email,
                mobile_number=mobile_number,
                pin=pin,
                ref_by=ref_by,
                otp=otp
            )
            return temp_member, otp
        except Exception as e:
            raise ValidationError(f"Error creating temporary member: {str(e)}")
    
    @staticmethod
    def verify_otp_and_create_member(mobile_number, otp):
        """Verify OTP and create permanent member from temp member"""
        try:
            with transaction.atomic():
                temp_member = TempMemberUser.objects.get(
                    mobile_number=mobile_number,
                    otp=otp,
                    is_active=False
                )
                
                # Create permanent member
                member = Member.objects.create(
                    full_name=temp_member.full_name,
                    email=temp_member.email,
                    mobile_number=temp_member.mobile_number,
                    MbrReferalId=temp_member.ref_by
                )
                member.set_pin(temp_member.pin)
                
                # Delete temp member
                temp_member.delete()
                
                return member
        except TempMemberUser.DoesNotExist:
            raise ValidationError("Invalid OTP or mobile number")
        except Exception as e:
            raise ValidationError(f"Error creating member: {str(e)}")
    
    @staticmethod
    def authenticate_member(mobile_number, pin):
        """Authenticate member and return auth token"""
        try:
            member = Member.objects.get(mobile_number=mobile_number)
            
            if not member.check_password(pin):
                raise ValidationError("Invalid credentials")
            
            if not member.MbrStatus:
                raise ValidationError("Account is inactive")
            
            # Generate or get auth token
            auth_token, created = MemberAuthToken.objects.get_or_create(
                user=member,
                defaults={'key': secrets.token_urlsafe(32)}
            )
            
            if not created:
                # Regenerate token for security
                auth_token.key = secrets.token_urlsafe(32)
                auth_token.save()
            
            return member, auth_token.key
            
        except Member.DoesNotExist:
            raise ValidationError("Invalid credentials")
        except Exception as e:
            raise ValidationError(f"Authentication failed: {str(e)}")
    
    @staticmethod
    def update_member_profile(member, **kwargs):
        """Update member profile information"""
        try:
            allowed_fields = [
                'full_name', 'email', 'first_name', 'last_name',
                'card_purposes', 'address', 'meta_data'
            ]
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(member, field, value)
            
            member.save()
            return member
            
        except Exception as e:
            raise ValidationError(f"Error updating profile: {str(e)}")
    
    @staticmethod
    def change_member_pin(member, old_pin, new_pin):
        """Change member PIN after verifying old PIN"""
        try:
            if not member.check_password(old_pin):
                raise ValidationError("Invalid current PIN")
            
            member.set_pin(new_pin)
            return True
            
        except Exception as e:
            raise ValidationError(f"Error changing PIN: {str(e)}")
    
    @staticmethod
    def deactivate_member(member):
        """Deactivate member account"""
        try:
            member.MbrStatus = False
            member.save()
            
            # Remove auth tokens
            MemberAuthToken.objects.filter(user=member).delete()
            
            return True
            
        except Exception as e:
            raise ValidationError(f"Error deactivating member: {str(e)}")
    
    @staticmethod
    def get_member_by_card_number(card_number):
        """Get member by card number"""
        try:
            return Member.objects.get(mbrcardno=card_number)
        except Member.DoesNotExist:
            raise ValidationError("Member not found with this card number")
    
    @staticmethod
    def get_member_statistics():
        """Get member statistics"""
        try:
            total_members = Member.objects.count()
            active_members = Member.objects.filter(MbrStatus=True).count()
            inactive_members = total_members - active_members
            
            return {
                'total_members': total_members,
                'active_members': active_members,
                'inactive_members': inactive_members,
                'activation_rate': round((active_members / total_members * 100), 2) if total_members > 0 else 0
            }
        except Exception as e:
            raise ValidationError(f"Error getting statistics: {str(e)}")
