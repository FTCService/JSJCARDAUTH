from rest_framework import serializers
from app_common.models import Member, Business, User, BusinessKyc, PhysicalCard, TempBusinessUser
from admin_dashboard.models import CardPurpose, JobProfileField, FieldCategory
import re


        
class BusinessShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ['business_id', 'business_name']

class MemberDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = [
            "id",
            "full_name",
            "email",
            "mobile_number",
            "first_name",
            "last_name",
            "MbrCountryCode",
            "MbrStatus",
            "mbrcardno",
            "MbrReferalId",
            "MbrCreatedBy",
            "card_purposes",
            "address",
        ]
        read_only_fields = ["id", "mbrcardno"]


class BusinessSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Business details.
    """
    class Meta:
        model = Business
        fields = ['id','business_id', 'business_name', 'mobile_number', 'email', 'business_type','business_address','business_pincode','business_is_active']


class CardPurposeSerializer(serializers.ModelSerializer):
    """
    Serializer for CardPurpose model
    """

    class Meta:
        model = CardPurpose
        fields = ["id", "purpose_name", "features"]
        read_only_fields = ["id"]
        
        
        
class VerifyKycSerializer(serializers.ModelSerializer):
    """
    Serializer for verifying Business KYC.
    """
    class Meta:
        model = BusinessKyc
        fields = ["id", "kycStatus"]  

    def validate_kyc_status(self, value):
        """Ensure only 'True' can be set."""
        if value is not True:
            raise serializers.ValidationError("KYC can only be marked as Verified (True).")
        return value
    




class PhysicalCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicalCard
        fields = ['id', 'card_number', 'business', 'issued', 'created_at']
        
        
class GenerateCardSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=1)
    business_id = serializers.PrimaryKeyRelatedField(
        queryset=Business.objects.all(),
        help_text="Select a business to generate cards for"
    )



class JobMitraUserSerializer(serializers.ModelSerializer):
    state = serializers.CharField(required=False)
    district = serializers.CharField(required=False)
    block = serializers.CharField(required=False)
    village = serializers.CharField(required=False)
    pincode = serializers.CharField(required=False)
    class Meta:
        model = User
        fields = ["id", "full_name", "email", "password", "employee_id", "mobile_number", "is_jobmitra",'state', 'district', 'block', 'village', 'pincode']
        extra_kwargs = {
            "password": {"write_only": True},
            "is_jobmitra": {"read_only": True},
        }
    
    
    
class JobMitraUserListSerializer(serializers.ModelSerializer):
    state = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    block = serializers.SerializerMethodField()
    village = serializers.SerializerMethodField()
    pincode = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "full_name", "email", "mobile_number", "employee_id",
            "is_jobmitra", "state", "district", "block", "village", "pincode"
        ]

    def get_state(self, obj):
        return obj.address.get("state") if obj.address else None

    def get_district(self, obj):
        return obj.address.get("district") if obj.address else None

    def get_block(self, obj):
        return obj.address.get("block") if obj.address else None

    def get_village(self, obj):
        return obj.address.get("village") if obj.address else None

    def get_pincode(self, obj):
        return obj.address.get("pincode") if obj.address else None
    
    
    
    
    
class InstituteSignupSerializer(serializers.ModelSerializer):
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
        error_messages={"blank": "institute name is required."}
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
        model = Business
        fields = ["mobile_number", "business_name", "pin", "email", "business_profile_image"]

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


class InstituteListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = [
            "id",
            "business_id",
            "email",
            "mobile_number",
            "business_name",
            "business_type",
            "business_profile_image",
        ]
        read_only_fields = fields     
    
    
class InstituteUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = [
            'business_name',
            'email',
            'business_profile_image',
            'business_address',
            'business_type'
        ]
        extra_kwargs = {
            'email': {'required': False},
            'business_name': {'required': False},
            'business_profile_image': {'required': False},
        }



class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category"""

    class Meta:
        model = FieldCategory
        fields = ["id", "name", "description"]
        
        

class JobProfileFieldSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=FieldCategory.objects.all())
    option = serializers.ListField(child=serializers.CharField(), default=list(), required=False)

    class Meta:
        model = JobProfileField
        fields = "__all__"
        extra_fields = ["category_name"]

    def create(self, validated_data):
        options = validated_data.pop('option', [])
        field = JobProfileField.objects.create(option=options, **validated_data)
        return field

    def update(self, instance, validated_data):
        options = validated_data.pop('option', None)
        if options is not None:
            instance.option = options
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure options are correctly represented from the instance
        data["option"] = instance.option if instance.option is not None else []
        return data
    
    
class JobMitraAddMemberSerializer(serializers.ModelSerializer):
    state = serializers.CharField(required=False)
    district = serializers.CharField(required=False)
    block = serializers.CharField(required=False)
    village = serializers.CharField(required=False)
    pincode = serializers.CharField(required=False)
    class Meta:
        model = Member
        fields = ["id","MbrReferalId", "full_name", "email", "pin", "mobile_number",'state', 'district', 'block', 'village', 'pincode']
        extra_kwargs = {
            "pin": {"write_only": True},
            "id": {"read_only": True},
        }

    
    
class JobMitraMemberListSerializer(serializers.ModelSerializer):
    state = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    block = serializers.SerializerMethodField()
    village = serializers.SerializerMethodField()
    pincode = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            "id", "full_name", "email", "mobile_number",
            "MbrStatus", "mbrcardno", "MbrCreatedAt", "MbrUpdatedAt",
            "state", "district", "block", "village", "pincode",
            "MbrReferalId"
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




class BulkAssignInstituteSerializer(serializers.Serializer):
    institutes = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
