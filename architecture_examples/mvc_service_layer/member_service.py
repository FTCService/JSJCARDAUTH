# architecture_examples/mvc_service_layer/member_service.py
from typing import Optional, Dict, Any, List
from django.db import transaction
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
import secrets
import random

from ..models.member import Member, TempMemberUser, MemberAuthToken
from ..exceptions import MemberServiceError, MemberNotFoundError


class MemberService:
    """
    Service layer for member-related business operations.
    Contains all business logic separated from HTTP concerns.
    """
    
    @staticmethod
    def initiate_signup(signup_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate member signup process with OTP verification.
        
        Args:
            signup_data: Dictionary containing member signup information
            
        Returns:
            Dictionary with OTP and temporary user information
            
        Raises:
            MemberServiceError: If signup fails due to business rules
        """
        mobile_number = signup_data.get('mobile_number')
        email = signup_data.get('email')
        
        # Business rule: Check if member already exists
        if Member.objects.filter(mobile_number=mobile_number).exists():
            raise MemberServiceError("Member with this mobile number already exists")
            
        if email and Member.objects.filter(email=email).exists():
            raise MemberServiceError("Member with this email already exists")
        
        # Generate OTP
        otp = random.randint(100000, 999999)
        
        try:
            with transaction.atomic():
                # Create temporary user for OTP verification
                temp_user = TempMemberUser.objects.create(
                    full_name=signup_data.get('full_name'),
                    email=email,
                    mobile_number=mobile_number,
                    pin=make_password(signup_data.get('pin')),
                    otp=otp,
                    ref_by=signup_data.get('ref_by')
                )
                
                # Send OTP (integrate with SMS service)
                MemberService._send_otp(mobile_number, otp)
                
                return {
                    'temp_user_id': temp_user.id,
                    'otp_sent': True,
                    'message': 'OTP sent successfully'
                }
                
        except Exception as e:
            raise MemberServiceError(f"Signup initiation failed: {str(e)}")
    
    @staticmethod
    def verify_otp_and_create_member(temp_user_id: int, otp: int) -> Member:
        """
        Verify OTP and create permanent member account.
        
        Args:
            temp_user_id: Temporary user ID
            otp: OTP to verify
            
        Returns:
            Created Member instance
            
        Raises:
            MemberServiceError: If OTP verification fails
        """
        try:
            temp_user = TempMemberUser.objects.get(id=temp_user_id)
        except TempMemberUser.DoesNotExist:
            raise MemberServiceError("Invalid signup session")
        
        if temp_user.otp != otp:
            raise MemberServiceError("Invalid OTP")
        
        try:
            with transaction.atomic():
                # Create permanent member
                member = Member.objects.create(
                    full_name=temp_user.full_name,
                    email=temp_user.email,
                    mobile_number=temp_user.mobile_number,
                    pin=temp_user.pin,
                    MbrReferalId=temp_user.ref_by,
                    MbrCreatedBy="self_registration"
                )
                
                # Generate authentication token
                token = MemberService._generate_auth_token(member)
                
                # Clean up temporary user
                temp_user.delete()
                
                return member, token
                
        except Exception as e:
            raise MemberServiceError(f"Member creation failed: {str(e)}")
    
    @staticmethod
    def authenticate_member(mobile_number: str, pin: str) -> Optional[Member]:
        """
        Authenticate member with mobile number and PIN.
        
        Args:
            mobile_number: Member's mobile number
            pin: Member's PIN
            
        Returns:
            Member instance if authentication successful, None otherwise
        """
        try:
            member = Member.objects.get(mobile_number=mobile_number)
            if check_password(pin, member.pin) and member.MbrStatus:
                return member
        except Member.DoesNotExist:
            pass
        return None
    
    @staticmethod
    def get_member_by_card_number(card_number: str) -> Member:
        """
        Retrieve member by card number.
        
        Args:
            card_number: Member's card number
            
        Returns:
            Member instance
            
        Raises:
            MemberNotFoundError: If member not found
        """
        try:
            return Member.objects.get(mbrcardno=card_number)
        except Member.DoesNotExist:
            raise MemberNotFoundError(f"Member with card number {card_number} not found")
    
    @staticmethod
    def update_member_profile(member: Member, update_data: Dict[str, Any]) -> Member:
        """
        Update member profile information.
        
        Args:
            member: Member instance to update
            update_data: Dictionary containing update information
            
        Returns:
            Updated Member instance
        """
        allowed_fields = [
            'full_name', 'email', 'first_name', 'last_name', 
            'address', 'card_purposes'
        ]
        
        with transaction.atomic():
            for field, value in update_data.items():
                if field in allowed_fields:
                    setattr(member, field, value)
            
            member.MbrUpdatedBy = "profile_update"
            member.save()
            
        return member
    
    @staticmethod
    def change_member_pin(member: Member, old_pin: str, new_pin: str) -> bool:
        """
        Change member's PIN after verifying old PIN.
        
        Args:
            member: Member instance
            old_pin: Current PIN
            new_pin: New PIN
            
        Returns:
            True if PIN changed successfully
            
        Raises:
            MemberServiceError: If old PIN is incorrect
        """
        if not check_password(old_pin, member.pin):
            raise MemberServiceError("Current PIN is incorrect")
        
        member.pin = make_password(new_pin)
        member.save()
        return True
    
    @staticmethod
    def get_members_list(filters: Dict[str, Any] = None, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        Get paginated list of members with optional filtering.
        
        Args:
            filters: Optional filters to apply
            page: Page number
            page_size: Number of items per page
            
        Returns:
            Dictionary containing members list and pagination info
        """
        queryset = Member.objects.all().order_by('-id')
        
        # Apply filters if provided
        if filters:
            if filters.get('status') is not None:
                queryset = queryset.filter(MbrStatus=filters['status'])
            if filters.get('search'):
                search_term = filters['search']
                queryset = queryset.filter(
                    models.Q(full_name__icontains=search_term) |
                    models.Q(mobile_number__icontains=search_term) |
                    models.Q(email__icontains=search_term)
                )
        
        # Pagination
        total_count = queryset.count()
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        members = queryset[start_index:end_index]
        
        return {
            'members': members,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        }
    
    @staticmethod
    def _generate_auth_token(member: Member) -> str:
        """Generate authentication token for member."""
        # Remove existing token if any
        MemberAuthToken.objects.filter(user=member).delete()
        
        # Create new token
        token_key = secrets.token_urlsafe(32)
        MemberAuthToken.objects.create(user=member, key=token_key)
        
        return token_key
    
    @staticmethod
    def _send_otp(mobile_number: str, otp: int):
        """Send OTP to mobile number (integrate with SMS service)."""
        # Implementation depends on your SMS service
        # This is a placeholder - replace with actual SMS service integration
        from helpers.utils import send_otp_to_mobile
        send_otp_to_mobile({
            'mobile_number': mobile_number,
            'otp': otp
        })


# Custom exceptions for better error handling
class MemberServiceError(Exception):
    """Base exception for member service errors."""
    pass


class MemberNotFoundError(MemberServiceError):
    """Exception raised when member is not found."""
    pass
