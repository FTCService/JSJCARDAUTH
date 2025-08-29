from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .manager import MyAccountManager, MemberManager, BusinessManager, GovernmentUserManager
from django.contrib.auth.hashers import make_password
from django.utils import timezone
import random

# ✅ TempMemberUser (for OTP verification)
class TempMemberUser(models.Model):
    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    pin = models.CharField(max_length=128, null=True, blank=True)
    mobile_number = models.CharField(max_length=10, null=True, blank=True)
    otp = models.IntegerField(null=True, blank=True)
    
    ref_by = models.CharField(max_length=6, null=True, blank=True)

    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.full_name} - {self.mobile_number}"
    
    

# ✅ Main User Model (for Admin & Staff)
class User(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=255, null=True, blank=True)
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    password = models.CharField(max_length=128, null=True, blank=True)  
    mobile_number = models.CharField(max_length=10, null=True, blank=True, unique=True)
    
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    # ✅ New Role Field
    is_jobmitra = models.BooleanField(default=False)
    token = models.CharField(max_length=100, null=True, blank=True)
    address = models.JSONField(default=dict)
    meta_data = models.JSONField(default=dict)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "employee_id"] 

    objects = MyAccountManager()

    def __str__(self):
        return self.email if self.email else "No Email"


class UserAuthToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="admin_auth_token")
    key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User {self.user} - {self.key}"

class GovernmentUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=15, unique=True)
    department = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_government = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    objects = GovernmentUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'mobile_number']
    

    def __str__(self):
        return f"{self.full_name} ({self.email})"

class GovernmentAuthToken(models.Model):
    user = models.ForeignKey(GovernmentUser, on_delete=models.CASCADE)
    key = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# ✅ Member Model
class Member(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True)
    mobile_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    pin = models.CharField(max_length=128)  # Store hashed PIN
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    
    MbrCountryCode = models.CharField(
        max_length=5,
        choices=[
            ("+91", "India"),
            ("+1", "USA"),
            ("+44", "UK"),
            # Add more country codes as necessary
        ],
        default="+91"
    )
    MbrStatus = models.BooleanField(default=True)  
    otp = models.CharField(max_length=6, null=True, blank=True)  

    card_purposes = models.JSONField(default=list)
    
    mbrcardno = models.BigIntegerField(unique=True, null=True, blank=True,)  
    MbrReferalId = models.CharField(max_length=50, null=True, blank=True)  
    
    MbrCreatedBy = models.CharField(max_length=255, null=True, blank=True)  
    MbrCreatedAt = models.DateTimeField(default=timezone.now)  
    MbrUpdatedBy = models.CharField(max_length=255, null=True, blank=True)  
    MbrUpdatedAt = models.DateTimeField(auto_now=True)
    address = models.JSONField(default=dict) 
    meta_data = models.JSONField(default=dict)  
    

    objects = MemberManager()

    USERNAME_FIELD = "mobile_number"
    REQUIRED_FIELDS = ["full_name"]
   
    groups = models.ManyToManyField('auth.Group', related_name='custom_member_set', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='custom_member_permissions', blank=True)

    def generate_unique_cardno(self):
        while True:
            cardno = random.randint(1000000000000000, 9999999999999999)
            if not Member.objects.filter(mbrcardno=cardno).exists():
                return cardno

    def save(self, *args, **kwargs):
        if not self.mbrcardno:
            self.mbrcardno = self.generate_unique_cardno()
                       
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.mobile_number}"
    
    def set_pin(self, pin):
        self.pin = make_password(pin)  # ✅ Hash PIN before storing
        self.save()

  
  
### 🔹 OPTIMIZED TOKEN MODEL ###
class MemberAuthToken(models.Model):
    user = models.OneToOneField(Member, on_delete=models.CASCADE, related_name="auth_token")
    key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Member {self.user} - {self.key}"

    class Meta:
        db_table = "member_auth_token"
        verbose_name = "Member Auth Token"
        verbose_name_plural = "Member Auth Tokens"
        
        



#  TempUser (for OTP verification)
class TempBusinessUser(models.Model):
    business_name = models.CharField(max_length=255, null=True)
    email = models.EmailField(null=True, blank=True)
    pin = models.CharField(max_length=128, null=True, blank=True)
    mobile_number = models.CharField(max_length=10, null=True, blank=True)
    otp = models.IntegerField(null=True, blank=True)
   
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_institute = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.business_name} - {self.mobile_number}"
        
### 🔹 BUSINESS MODEL ###
class Business(AbstractBaseUser, PermissionsMixin):
    
    business_id = models.CharField(max_length=6, unique=True, editable=False, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    mobile_number = models.CharField(max_length=15, unique=True, null=True, blank=True) 
    pin = models.CharField(max_length=128, null=True, blank=True)  
    business_name = models.CharField(max_length=55, null=True, blank=True)
    business_type = models.CharField(max_length=100 , null=True, blank=True)  
    otp = models.CharField(max_length=6, null=True, blank=True)  

    business_country_code = models.CharField(
        max_length=6,
        choices=[
            ("+91", "India"),
            ("+1", "USA"),
            ("+44", "UK"),
            # Add more country codes as necessary
        ],
        default="+91"
    ) 
    business_is_active = models.BooleanField(default=True)  
    business_address = models.TextField(null=True, blank=True)  
    business_pincode = models.CharField(max_length=10, null=True, blank=True) 
     
    business_created_by = models.CharField(max_length=255, null=True, blank=True)  
    business_created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  
    business_updated_by = models.CharField(max_length=255, null=True, blank=True)  
    business_updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)  
    business_notes = models.TextField(null=True, blank=True)  
    business_profile_image = models.TextField(null=True, blank=True)
    
    is_business = models.BooleanField(default=True)     # Regular business
    is_institute = models.BooleanField(default=False)   # If true, user is an institute
    
    objects = BusinessManager()

    USERNAME_FIELD = "mobile_number"  
    REQUIRED_FIELDS = ["business_name", "pin"]
    
    groups = models.ManyToManyField('auth.Group', related_name='custom_business_set', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='custom_business_permissions', blank=True)

    def __str__(self):
        return f"{self.business_name} ({self.business_id})"

    def save(self, *args, **kwargs):
        """
        Auto-generate a unique 6-digit business_id before saving.
        """
        if not self.business_id:
            while True:
                new_id = str(random.randint(100000, 999999))  # Generate a random 6-digit number
                if not Business.objects.filter(business_id=new_id).exists():
                    self.business_id = new_id
                    break
        super().save(*args, **kwargs)

    def set_pin(self, raw_pin):
        """
        Hash and save the PIN securely.
        """
        self.pin = make_password(raw_pin)
        self.save()


### 🔹 OPTIMIZED TOKEN MODEL ###
class BusinessAuthToken(models.Model):
    user = models.OneToOneField(Business, on_delete=models.CASCADE, related_name="business_auth_token")
    key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Business {self.user} - {self.key}"

    class Meta:
        db_table = "business_auth_token"  # ✅ Updated table name
        verbose_name = "Business Auth Token"  # ✅ Updated verbose name
        verbose_name_plural = "Business Auth Tokens"



class BusinessKyc(models.Model):

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="kyc", verbose_name="Business", to_field="business_id"
    )
    kycStatus = models.BooleanField(default=False, null=True, blank=True, verbose_name="KYC Status"
    )
    kycAdharCard = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Aadhar Card URL"
    )
    kycGst = models.CharField(
        max_length=15, null=True, blank=True, verbose_name="GST Number"
    )
    kycPanCard = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="PAN Card URL"
    )
    kycOthers = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Other Documents URL"
    )

    def __str__(self):
        return f"KYC for {self.business.business_name} - Status: {'Verified' if self.kycStatus else 'Not Verified'}"



class PhysicalCard(models.Model):
    card_number = models.BigIntegerField(unique=True)  # 16-digit unique card number
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='physical_cards', to_field="business_id")
    issued = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.card_number)
    


class CardMapper(models.Model):
    SECONDARY_CARD_TYPE_CHOICES = [
        ('physical', 'Physical Card'),
        ('prepaid', 'Prepaid Card'),
        ('digital', 'Digital Card'),
        
    ]
    business_id = models.IntegerField(null=True, blank=True)
    primary_card = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='primary_card_mappings',to_field='mbrcardno')
    secondary_card = models.BigIntegerField(verbose_name="Secondary Card")
    secondary_card_type = models.CharField(max_length=20,choices=SECONDARY_CARD_TYPE_CHOICES,default='physical')
    created_at = models.DateTimeField(auto_now_add=True)

   
   