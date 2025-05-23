from rest_framework import serializers
from app_common.models import Member, Business, User, BusinessKyc
from admin_dashboard.models import CardPurpose



        
        

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
    




