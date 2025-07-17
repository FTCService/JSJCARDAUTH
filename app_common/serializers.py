from rest_framework import serializers
from app_common.models import User, TempMemberUser, Member, TempBusinessUser, Business, BusinessKyc, PhysicalCard, CardMapper, GovernmentUser
import re
from django.contrib.auth.hashers import check_password

class StaffUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "email", "password", "employee_id", "mobile_number", "is_staff"]
        extra_kwargs = {
            "password": {"write_only": True},
            "is_staff": {"read_only": True},
        }

    def create(self, validated_data):
        validated_data["is_staff"] = True  # Ensure only staff users are created
        user = User.objects.create_user(**validated_data)
        return user
    
    


### 🔹 ADMIN AND STAFF LOGIN SERIALIZER ###
class AdminStaffLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    



class GovermentLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
class BusinessListSerializer(serializers.ModelSerializer):
    job_count = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = ['id', 'business_id', 'business_name', 'job_count']

    def get_job_count(self, obj):
        job_counts = self.context.get("job_counts", {})  # ✅ FIXED
        return job_counts.get(str(obj.business_id), 0)

    
    
    

### 🔹 MEMBER SIGNUP SERIALIZER ###
class MemberSignupSerializer(serializers.ModelSerializer):
    """
    Serializer for Member signup
    """
    refer_id = serializers.CharField(required=False, allow_null=True)
    mobile_number = serializers.CharField(
        required=True,
        min_length=10,
        max_length=10,
        error_messages={
            "min_length": "Mobile number must be exactly 10 digits.",
            "max_length": "Mobile number must be exactly 10 digits.",
        }
    )
    full_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    pin = serializers.CharField(
        write_only=True,
        min_length=4,
        max_length=4,
        error_messages={
            "min_length": "PIN must be exactly 4 digits.",
            "max_length": "PIN must be exactly 4 digits.",
        }
    )

    class Meta:
        model = TempMemberUser
        fields = ["mobile_number", "full_name", "pin","refer_id", "email"]

    def validate_mobile_number(self, value):
        """Ensure the mobile number contains only digits."""
        if not re.fullmatch(r"^\d{10}$", value):
            raise serializers.ValidationError("Mobile number must be exactly 10 digits and contain only numbers.")
        return value

    def validate_pin(self, value):
        """Ensure the PIN contains only digits."""
        if not re.fullmatch(r"^\d{4}$", value):
            raise serializers.ValidationError("PIN must be exactly 4 digits and contain only numbers.")
        return value

    
    def create(self, validated_data):
        # Store 'pin' as 'password' since TempUser uses 'password' instead of 'pin'
        validated_data["password"] = validated_data.pop("pin")
        return TempMemberUser.objects.create(**validated_data)
    
    

### 🔹 VERIFY OTP SERIALIZER ###
class VerifyOtpSerializer(serializers.Serializer):
    """
    Serializer for OTP verification
    """
    mobile_number = serializers.CharField(max_length=10, required=True)
    otp = serializers.CharField(max_length=6, required=True)

    def validate(self, data):
        mobile_number = data.get("mobile_number")
        otp = data.get("otp")

        if not TempMemberUser.objects.filter(mobile_number=mobile_number, otp=otp).exists():
            raise serializers.ValidationError("Invalid OTP or user not found.")
        return data
    
    

### 🔹 MEMBER LOGIN SERIALIZER ###
class MemberLoginSerializer(serializers.Serializer):
    """
    Serializer for Member login using either mobile number or email + pin
    """
    mobile_number = serializers.CharField(required=True)  # can be mobile number or email
    pin = serializers.CharField(
        required=True,
        min_length=4,
        max_length=4,
        write_only=True,
        error_messages={
            "min_length": "PIN must be exactly 4 digits.",
            "max_length": "PIN must be exactly 4 digits.",
        }
    )

    def validate_mobile_number(self, value):
        """
        Check if input is a valid email or a valid 10-digit mobile number.
        """
        if re.fullmatch(r"^\d{10}$", value):  # mobile
            return value
        elif re.fullmatch(r"[^@]+@[^@]+\.[^@]+", value):  # email
            return value
        raise serializers.ValidationError("Enter a valid 10-digit mobile number or email address.")

    def validate_pin(self, value):
        if not re.fullmatch(r"^\d{4}$", value):
            raise serializers.ValidationError("PIN must be exactly 4 digits and contain only numbers.")
        return value
    
    
    

    
### 🔹 FORGOT PIN SERIALIZER ###
class MemberForgotPinSerializer(serializers.Serializer):
    """
    Serializer for requesting OTP for PIN reset.
    """
    mobile_number = serializers.CharField(
        required=True,
        min_length=10,
        max_length=10,
        error_messages={
            "min_length": "Mobile number must be exactly 10 digits.",
            "max_length": "Mobile number must be exactly 10 digits.",
        }
    )

    def validate_mobile_number(self, value):
        """
        Validate that the mobile number:
        - Contains only numbers.
        - Exists in  Member table.
        """
        if not re.fullmatch(r"^\d{10}$", value):
            raise serializers.ValidationError("Mobile number must be exactly 10 digits and contain only numbers.")

        if not Member.objects.filter(mobile_number=value).exists():
            raise serializers.ValidationError("No user found with this mobile number.")

        return value
    
    
    
### 🔹 RESET PIN SERIALIZER ###
class MemberResetPinSerializer(serializers.Serializer):
    """
    Serializer for resetting PIN using OTP.
    """
    otp = serializers.CharField(
        max_length=6, 
        min_length=6, 
        required=True, 
        error_messages={
            "min_length": "OTP must be exactly 6 digits.",
            "max_length": "OTP must be exactly 6 digits."
        }
    )
    new_pin = serializers.CharField(
        write_only=True, 
        required=True, 
        min_length=4, 
        max_length=4,  # ✅ Ensuring PIN is exactly 4 digits
        error_messages={
            "min_length": "PIN must be exactly 4 digits.",
            "max_length": "PIN must be exactly 4 digits."
        }
    )

    def validate_otp(self, value):
        """
        Validate OTP:
        - Must be exactly 6 digits.
        - Must exist in either `Member` or `Business` table.
        """
        if not re.fullmatch(r"^\d{6}$", value):
            raise serializers.ValidationError("OTP must be exactly 6 digits.")

        if not Member.objects.filter(otp=value).exists():
            raise serializers.ValidationError("Invalid OTP. Please enter a valid OTP.")

        return value

    def validate_new_pin(self, value):
        """
        Validate new PIN:
        - Must be exactly 4 digits.
        - Must contain only numbers.
        """
        if not re.fullmatch(r"^\d{4}$", value):
            raise serializers.ValidationError("PIN must be exactly 4 digits and contain only numbers.")

        return value
    
    
    
### 🔹 CHANGE PIN SERIALIZER ###
class MemberChangePinSerializer(serializers.Serializer):
    """
    Serializer for changing the user's PIN.
    """
    current_pin = serializers.CharField(
        write_only=True, 
        required=True, 
        min_length=4, 
        max_length=4,
        error_messages={"required": "Current PIN is required."}
    )
    new_pin = serializers.CharField(
        write_only=True, 
        required=True, 
        min_length=4, 
        max_length=4,
        error_messages={"required": "New PIN is required."}
    )
    confirm_pin = serializers.CharField(
        write_only=True, 
        required=True, 
        min_length=4, 
        max_length=4,
        error_messages={"required": "Confirm PIN is required."}
    )

    def validate_current_pin(self, value):
        """
        Validate that the current PIN matches the stored PIN.
        """
        user = self.context["request"].user  

        if not check_password(value, user.pin):  # ✅ Ensure `check_password()` is used
            raise serializers.ValidationError("Incorrect current PIN.")

        return value

    def validate_new_pin(self, value):
        """
        Ensure new PIN is 4 digits and different from current PIN.
        """
        if not re.fullmatch(r"^\d{4}$", value):
            raise serializers.ValidationError("New PIN must contain exactly 4 digits.")

        if "current_pin" in self.initial_data and value == self.initial_data["current_pin"]:
            raise serializers.ValidationError("New PIN cannot be the same as the current PIN.")

        return value

    def validate(self, data):
        """
        Ensure new PIN and confirm PIN match.
        """
        if data["new_pin"] != data["confirm_pin"]:
            raise serializers.ValidationError({"confirm_pin": "New PIN and Confirm PIN must match."})

        return data



### 🔹 MEMBER RESEND OTP SERIALIZER ###
class MemberResendOtpSerializer(serializers.Serializer):
    """
    Serializer for resending OTP.
    """
    mobile_number = serializers.CharField(
        max_length=10, required=True,
        error_messages={"required": "Mobile number is required."}
    )

    def validate_mobile_number(self, value):
        """
        Ensure the mobile number exists in the TempUser table.
        """
        if not TempMemberUser.objects.filter(mobile_number=value).exists():
            raise serializers.ValidationError("Mobile number is not registered.")
        return value




# this serializer for send to business all details of member 
class MemberSerializer(serializers.ModelSerializer):
    state = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    block = serializers.SerializerMethodField()
    village = serializers.SerializerMethodField()
    pincode = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            "full_name",
            "email",
            "mobile_number",
            "first_name",
            "last_name",
            "MbrCountryCode",
            "MbrStatus",
            "card_purposes",
            "mbrcardno",
            "MbrReferalId",
            "MbrCreatedAt",
            "MbrUpdatedAt",

            # From meta_data
            "state",
            "district",
            "block",
            "village",
            "pincode",
        ]

    def get_state(self, obj):
        return obj.address.get("state")

    def get_district(self, obj):
        return obj.address.get("district")

    def get_block(self, obj):
        return obj.address.get("block")

    def get_village(self, obj):
        return obj.address.get("village")

    def get_pincode(self, obj):
        return obj.address.get("pincode")

        

class MemberListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = [
            "full_name",
            "mbrcardno",
          
        ]        


class BusinessDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = [
            "business_id",
            "business_name",
            "email",
            "mobile_number",
        ]



class MemberRegistrationSerializer(serializers.ModelSerializer):
    contact_with_country = serializers.SerializerMethodField()

    # Add meta fields (read from meta_data)
    state = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    block = serializers.SerializerMethodField()
    village = serializers.SerializerMethodField()
    pincode = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            'full_name', 'first_name', 'last_name',
            'mbrcardno', 'email', 'contact_with_country', 'MbrStatus',
            'state', 'district', 'block', 'village', 'pincode'
        ]
        read_only_fields = ['mobile_number', 'pin', 'contact_with_country']

    def get_contact_with_country(self, obj):
        return f"{obj.MbrCountryCode} {obj.mobile_number}" if obj.mobile_number else None

    def get_state(self, obj):
        return obj.address.get('state')

    def get_district(self, obj):
        return obj.address.get('district')

    def get_block(self, obj):
        return obj.address.get('block')

    def get_village(self, obj):
        return obj.address.get('village')

    def get_pincode(self, obj):
        return obj.address.get('pincode')

    def update(self, instance, validated_data):
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.MbrStatus = validated_data.get('MbrStatus', instance.MbrStatus)

        # Update meta_data
        meta = instance.address or {}
        meta["state"] = validated_data.get("state", meta.get("state"))
        meta["district"] = validated_data.get("district", meta.get("district"))
        meta["block"] = validated_data.get("block", meta.get("block"))
        meta["village"] = validated_data.get("village", meta.get("village"))
        meta["pincode"] = validated_data.get("pincode", meta.get("pincode"))
        instance.address = meta

        instance.save()
        return instance









#=================== Business authentication serializers ============================





### 🔹 BUSINESS SIGNUP SERIALIZER ###
class BusinessSignupSerializer(serializers.ModelSerializer):
    """
    Serializer for Business signup, includes validations for:
    - Mobile number (must be exactly 10 digits)
    - Business name (required)
    - PIN (must be exactly 4 numeric digits)
    - Email (valid format, must be unique across TempUser and Business)
    """

    mobile_number = serializers.CharField(
        required=True,
        min_length=10,
        max_length=10,
        error_messages={
            "min_length": "Mobile number must be exactly 10 digits.",
            "max_length": "Mobile number must be exactly 10 digits.",
            "blank": "Mobile number is required.",
        }
    )

    business_name = serializers.CharField(
        required=True,
        error_messages={"blank": "Business name is required."}
    )

    pin = serializers.CharField(
        write_only=True,
        min_length=4,
        max_length=4,
        error_messages={
            "min_length": "PIN must be exactly 4 digits.",
            "max_length": "PIN must be exactly 4 digits.",
            "blank": "PIN is required.",
        }
    )

    email = serializers.EmailField(
        required=True,
        error_messages={
            "invalid": "Enter a valid email address.",
            "blank": "Email is required.",
        }
    )

    class Meta:
        model = TempBusinessUser
        fields = ["mobile_number", "business_name", "pin", "email"]

    def validate_mobile_number(self, value):
        """
        Validate that the mobile number contains exactly 10 digits.
        """
        if not re.fullmatch(r"^\d{10}$", value):
            raise serializers.ValidationError("Mobile number must be exactly 10 digits and contain only numbers.")
        return value

    def validate_pin(self, value):
        """
        Validate that the PIN contains exactly 4 numeric digits.
        """
        if not re.fullmatch(r"^\d{4}$", value):
            raise serializers.ValidationError("PIN must be exactly 4 digits and contain only numbers.")
        return value

    

    def create(self, validated_data):
        """
        Create and return a new TempUser instance.
        """
        return TempBusinessUser.objects.create(**validated_data)


### 🔹 VERIFY OTP SERIALIZER ###
class BusinessVerifyOtpSerializer(serializers.Serializer):
    """
    Serializer for OTP verification
    """
    mobile_number = serializers.CharField(max_length=10, required=True)
    otp = serializers.CharField(max_length=6, required=True)

    def validate(self, data):
        mobile_number = data.get("mobile_number")
        otp = data.get("otp")

        if not TempBusinessUser.objects.filter(mobile_number=mobile_number, otp=otp).exists():
            raise serializers.ValidationError("Invalid OTP or user not found.")
        return data
    
    

### 🔹 BUSINESS LOGIN SERIALIZER ###
class BusinessLoginSerializer(serializers.Serializer):
    """
    Serializer for Business login (via mobile number or email + PIN)
    """
    contact = serializers.CharField(
        required=True,
        help_text="Enter either a 10-digit mobile number or an email address"
    )
    pin = serializers.CharField(
        required=True,
        min_length=4,
        max_length=4,
        write_only=True,
        error_messages={
            "min_length": "PIN must be exactly 4 digits.",
            "max_length": "PIN must be exactly 4 digits.",
        }
    )

    def validate_contact(self, value):
        """Ensure contact is a valid 10-digit mobile number or email address."""
        if re.fullmatch(r"^\d{10}$", value):  # Valid mobile
            return value
        elif re.fullmatch(r"[^@]+@[^@]+\.[^@]+", value):  # Valid email
            return value
        raise serializers.ValidationError("Enter a valid 10-digit mobile number or a valid email address.")

    def validate_pin(self, value):
        """Ensure the PIN contains only digits."""
        if not re.fullmatch(r"^\d{4}$", value):
            raise serializers.ValidationError("PIN must be exactly 4 digits and contain only numbers.")
        return value
    

### 🔹 BUSINESS SERIALIZER SERIALIZER ###
class BusinessRegistrationSerializer(serializers.ModelSerializer):
    contact_with_country = serializers.SerializerMethodField()  # Custom field for formatted contact

    class Meta:
        model = Business
        fields = [
            'business_name', 'business_type', 'business_is_active',
            'business_address', 'business_pincode', 'business_created_by', 'business_created_at',
            'business_updated_by', 'business_updated_at', 'business_notes', 'email', 'contact_with_country','business_profile_image'
        ]
        read_only_fields = ['mobile_number', 'pin', 'contact_with_country', 'business_created_at', 'business_updated_at']

    def get_contact_with_country(self, obj):
        """
        Format contact with country code (e.g., +91 7462982798).
        """
        return f"{obj.business_country_code} {obj.mobile_number}" if obj.mobile_number else None

    def update(self, instance, validated_data):
        """
        Update all allowed fields for business registration.
        """
        instance.business_name = validated_data.get('business_name', instance.business_name)
        instance.business_type = validated_data.get('business_type', instance.business_type)
        instance.business_is_active = validated_data.get('business_is_active', instance.business_is_active)
        instance.business_address = validated_data.get('business_address', instance.business_address)
        instance.business_pincode = validated_data.get('business_pincode', instance.business_pincode)
        instance.email = validated_data.get('email', instance.email)
        instance.business_notes = validated_data.get('business_notes', instance.business_notes)
        instance.business_updated_by = validated_data.get('business_updated_by', instance.business_updated_by)
        instance.business_profile_image = validated_data.get('business_profile_image', instance.business_profile_image)

        instance.save()
        return instance
    
    
    
class BusinessKycSerializer(serializers.ModelSerializer):
    businessName = serializers.CharField(source="business.business_name", read_only=True)

    kycAdharCard = serializers.CharField(required=False)  # ✅ Accepts String (URL)
    kycPanCard = serializers.CharField(required=False)  # ✅ Accepts String (URL)
    kycOthers = serializers.CharField(required=False, allow_null=True, allow_blank=True)   # ✅ Optional

    class Meta:
        model = BusinessKyc
        fields = [
            "id",
            "business",  # ✅ Auto-filled from request.user
            "businessName",
            "kycStatus",
            "kycAdharCard",
            "kycGst",
            "kycPanCard",
            "kycOthers",
        ]
        read_only_fields = ["business", "businessName"]
        
        
        
        

### 🔹 Business FORGOT PIN SERIALIZER ###
class BusinessForgotPinSerializer(serializers.Serializer):
    """
    Serializer for requesting OTP for PIN reset.
    """
    mobile_number = serializers.CharField(
        required=True,
        min_length=10,
        max_length=10,
        error_messages={
            "min_length": "Mobile number must be exactly 10 digits.",
            "max_length": "Mobile number must be exactly 10 digits.",
        }
    )

    def validate_mobile_number(self, value):
        """
        Validate that the mobile number:
        - Contains only numbers.
        - Exists in either Member or Business table.
        """
        if not re.fullmatch(r"^\d{10}$", value):
            raise serializers.ValidationError("Mobile number must be exactly 10 digits and contain only numbers.")

        if not Business.objects.filter(mobile_number=value).exists():
            raise serializers.ValidationError("No user found with this mobile number.")

        return value


### 🔹 RESET PIN SERIALIZER ###
class BusinessResetPinSerializer(serializers.Serializer):
    """
    Serializer for resetting PIN using OTP.
    """
    otp = serializers.CharField(
        max_length=6, 
        min_length=6, 
        required=True, 
        error_messages={
            "min_length": "OTP must be exactly 6 digits.",
            "max_length": "OTP must be exactly 6 digits."
        }
    )
    new_pin = serializers.CharField(
        write_only=True, 
        required=True, 
        min_length=4, 
        max_length=4,  # ✅ Ensuring PIN is exactly 4 digits
        error_messages={
            "min_length": "PIN must be exactly 4 digits.",
            "max_length": "PIN must be exactly 4 digits."
        }
    )

    def validate_otp(self, value):
        """
        Validate OTP:
        - Must be exactly 6 digits.
        - Must exist in either `Member` or `Business` table.
        """
        if not re.fullmatch(r"^\d{6}$", value):
            raise serializers.ValidationError("OTP must be exactly 6 digits.")

        if not Business.objects.filter(otp=value).exists():
            raise serializers.ValidationError("Invalid OTP. Please enter a valid OTP.")

        return value

    def validate_new_pin(self, value):
        """
        Validate new PIN:
        - Must be exactly 4 digits.
        - Must contain only numbers.
        """
        if not re.fullmatch(r"^\d{4}$", value):
            raise serializers.ValidationError("PIN must be exactly 4 digits and contain only numbers.")

        return value
    
    

class InitiateCardAssignmentSerializer(serializers.Serializer):
    card_number = serializers.CharField(max_length=16)
    full_name = serializers.CharField(max_length=100, required = False)
    mobile_number = serializers.CharField(max_length=15,required = False)
    pin = serializers.CharField(max_length=6,required = False, allow_blank=True)
    
    def validate_card_number(self, value):
        if not PhysicalCard.objects.filter(card_number=value).exists():
            raise serializers.ValidationError("Invalid card number.")
        return value



class CardMapperSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardMapper
        fields = [
            'business',
            'primary_card',
            'secondary_card',
            'secondary_card_type',
            'created_at'
        ]


class PhysicalCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicalCard
        fields = ['card_number', 'business', 'issued', 'created_at']



#============================ govermnet users ========================

class GovernmentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovernmentUser
        fields = [
            "id", "email", "full_name", "mobile_number",
            "department", "designation", "is_government", "password"
        ]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = GovernmentUser(**validated_data)
        user.set_password(password)
        user.save()
        return user