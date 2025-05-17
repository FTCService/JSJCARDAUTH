from rest_framework import serializers
from app_common.models import Member, Business, User, BusinessKyc
from admin_dashboard.models import CardPurpose, JobProfileField, FieldCategory



        
        

class MemberSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=False, write_only=True)
    class Meta:
        model = Member
        fields = '__all__'


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

