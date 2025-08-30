from django.core.exceptions import ValidationError
from django.db import transaction
from ..models import Business, BusinessAuthToken, TempBusinessUser, BusinessKyc, PhysicalCard, CardMapper
import secrets
import random


class BusinessService:
    """Service class for Business-related business logic"""
    
    @staticmethod
    def create_temp_business(business_name, email, mobile_number, pin, is_institute=False):
        """Create a temporary business user for OTP verification"""
        try:
            # Generate OTP
            otp = random.randint(100000, 999999)
            
            temp_business = TempBusinessUser.objects.create(
                business_name=business_name,
                email=email,
                mobile_number=mobile_number,
                pin=pin,
                otp=otp,
                is_institute=is_institute
            )
            return temp_business, otp
        except Exception as e:
            raise ValidationError(f"Error creating temporary business: {str(e)}")
    
    @staticmethod
    def verify_otp_and_create_business(mobile_number, otp):
        """Verify OTP and create permanent business from temp business"""
        try:
            with transaction.atomic():
                temp_business = TempBusinessUser.objects.get(
                    mobile_number=mobile_number,
                    otp=otp,
                    is_active=False
                )
                
                # Create permanent business
                business = Business.objects.create(
                    business_name=temp_business.business_name,
                    email=temp_business.email,
                    mobile_number=temp_business.mobile_number,
                    is_institute=temp_business.is_institute
                )
                business.set_pin(temp_business.pin)
                
                # Delete temp business
                temp_business.delete()
                
                return business
        except TempBusinessUser.DoesNotExist:
            raise ValidationError("Invalid OTP or mobile number")
        except Exception as e:
            raise ValidationError(f"Error creating business: {str(e)}")
    
    @staticmethod
    def authenticate_business(mobile_number, pin):
        """Authenticate business and return auth token"""
        try:
            business = Business.objects.get(mobile_number=mobile_number)
            
            if not business.check_password(pin):
                raise ValidationError("Invalid credentials")
            
            if not business.business_is_active:
                raise ValidationError("Account is inactive")
            
            # Generate or get auth token
            auth_token, created = BusinessAuthToken.objects.get_or_create(
                user=business,
                defaults={'key': secrets.token_urlsafe(32)}
            )
            
            if not created:
                # Regenerate token for security
                auth_token.key = secrets.token_urlsafe(32)
                auth_token.save()
            
            return business, auth_token.key
            
        except Business.DoesNotExist:
            raise ValidationError("Invalid credentials")
        except Exception as e:
            raise ValidationError(f"Authentication failed: {str(e)}")
    
    @staticmethod
    def update_business_profile(business, **kwargs):
        """Update business profile information"""
        try:
            allowed_fields = [
                'business_name', 'email', 'business_type', 'business_address',
                'business_pincode', 'business_notes', 'business_profile_image'
            ]
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(business, field, value)
            
            business.save()
            return business
            
        except Exception as e:
            raise ValidationError(f"Error updating profile: {str(e)}")
    
    @staticmethod
    def submit_kyc_documents(business_id, kyc_data):
        """Submit KYC documents for business"""
        try:
            business = Business.objects.get(business_id=business_id)
            
            kyc, created = BusinessKyc.objects.get_or_create(
                business=business,
                defaults=kyc_data
            )
            
            if not created:
                # Update existing KYC
                for field, value in kyc_data.items():
                    setattr(kyc, field, value)
                kyc.save()
            
            return kyc
            
        except Business.DoesNotExist:
            raise ValidationError("Business not found")
        except Exception as e:
            raise ValidationError(f"Error submitting KYC: {str(e)}")
    
    @staticmethod
    def approve_kyc(business_id, approved_by):
        """Approve business KYC"""
        try:
            business = Business.objects.get(business_id=business_id)
            kyc = BusinessKyc.objects.get(business=business)
            
            kyc.kycStatus = True
            kyc.save()
            
            # Update business metadata
            if not business.meta_data:
                business.meta_data = {}
            business.meta_data['kyc_approved_by'] = approved_by
            business.meta_data['kyc_approved_at'] = str(timezone.now())
            business.save()
            
            return kyc
            
        except (Business.DoesNotExist, BusinessKyc.DoesNotExist):
            raise ValidationError("Business or KYC not found")
        except Exception as e:
            raise ValidationError(f"Error approving KYC: {str(e)}")
    
    @staticmethod
    def generate_physical_cards(business_id, quantity):
        """Generate physical cards for business"""
        try:
            business = Business.objects.get(business_id=business_id)
            
            cards = []
            for _ in range(quantity):
                while True:
                    card_number = random.randint(1000000000000000, 9999999999999999)
                    if not PhysicalCard.objects.filter(card_number=card_number).exists():
                        break
                
                card = PhysicalCard.objects.create(
                    card_number=card_number,
                    business=business
                )
                cards.append(card)
            
            return cards
            
        except Business.DoesNotExist:
            raise ValidationError("Business not found")
        except Exception as e:
            raise ValidationError(f"Error generating cards: {str(e)}")
    
    @staticmethod
    def map_cards(primary_card_number, secondary_card_number, card_type, business_id=None):
        """Map primary member card to secondary card"""
        try:
            from ..models import Member
            
            primary_card = Member.objects.get(mbrcardno=primary_card_number)
            
            card_mapping = CardMapper.objects.create(
                primary_card=primary_card,
                secondary_card=secondary_card_number,
                secondary_card_type=card_type,
                business_id=business_id
            )
            
            return card_mapping
            
        except Member.DoesNotExist:
            raise ValidationError("Primary card not found")
        except Exception as e:
            raise ValidationError(f"Error mapping cards: {str(e)}")
    
    @staticmethod
    def get_business_statistics():
        """Get business statistics"""
        try:
            total_businesses = Business.objects.count()
            active_businesses = Business.objects.filter(business_is_active=True).count()
            institutes = Business.objects.filter(is_institute=True).count()
            kyc_approved = BusinessKyc.objects.filter(kycStatus=True).count()
            
            return {
                'total_businesses': total_businesses,
                'active_businesses': active_businesses,
                'institutes': institutes,
                'regular_businesses': total_businesses - institutes,
                'kyc_approved': kyc_approved,
                'kyc_pending': total_businesses - kyc_approved
            }
        except Exception as e:
            raise ValidationError(f"Error getting statistics: {str(e)}")
    
    @staticmethod
    def deactivate_business(business, reason=None):
        """Deactivate business account"""
        try:
            business.business_is_active = False
            if reason and not business.meta_data:
                business.meta_data = {}
            if reason:
                business.meta_data['deactivation_reason'] = reason
            business.save()
            
            # Remove auth tokens
            BusinessAuthToken.objects.filter(user=business).delete()
            
            return True
            
        except Exception as e:
            raise ValidationError(f"Error deactivating business: {str(e)}")
