from rest_framework import serializers
from ..models import TempMemberUser, Member, MemberAuthToken


class TempMemberUserSerializer(serializers.ModelSerializer):
    """Serializer for temporary member user during registration"""
    
    class Meta:
        model = TempMemberUser
        fields = [
            'id', 'full_name', 'email', 'mobile_number', 
            'otp', 'ref_by', 'is_active'
        ]
        read_only_fields = ['id', 'otp']
        extra_kwargs = {
            'pin': {'write_only': True}
        }


class MemberSerializer(serializers.ModelSerializer):
    """Serializer for Member model"""
    
    class Meta:
        model = Member
        fields = [
            'id', 'full_name', 'email', 'mobile_number', 'first_name',
            'last_name', 'MbrCountryCode', 'MbrStatus', 'card_purposes',
            'mbrcardno', 'MbrReferalId', 'address', 'meta_data',
            'MbrCreatedAt', 'MbrUpdatedAt'
        ]
        read_only_fields = [
            'id', 'mbrcardno', 'MbrCreatedAt', 'MbrUpdatedAt'
        ]
        extra_kwargs = {
            'pin': {'write_only': True},
            'otp': {'write_only': True}
        }


class MemberAuthTokenSerializer(serializers.ModelSerializer):
    """Serializer for Member authentication tokens"""
    
    member_name = serializers.CharField(source='user.full_name', read_only=True)
    member_mobile = serializers.CharField(source='user.mobile_number', read_only=True)
    
    class Meta:
        model = MemberAuthToken
        fields = [
            'user', 'member_name', 'member_mobile', 
            'key', 'created_at'
        ]
        read_only_fields = ['key', 'created_at', 'member_name', 'member_mobile']


class MemberRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for Member registration"""
    
    pin = serializers.CharField(write_only=True, min_length=4, max_length=6)
    confirm_pin = serializers.CharField(write_only=True, min_length=4, max_length=6)
    
    class Meta:
        model = Member
        fields = [
            'full_name', 'email', 'mobile_number', 'first_name',
            'last_name', 'MbrCountryCode', 'pin', 'confirm_pin',
            'card_purposes', 'MbrReferalId', 'address'
        ]
        extra_kwargs = {
            'pin': {'write_only': True},
            'confirm_pin': {'write_only': True}
        }
    
    def validate(self, attrs):
        if attrs['pin'] != attrs['confirm_pin']:
            raise serializers.ValidationError("PINs don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_pin')
        pin = validated_data.pop('pin')
        member = Member.objects.create(**validated_data)
        member.set_pin(pin)
        return member


class MemberLoginSerializer(serializers.Serializer):
    """Serializer for Member login"""
    
    mobile_number = serializers.CharField()
    pin = serializers.CharField()
    
    def validate(self, attrs):
        mobile_number = attrs.get('mobile_number')
        pin = attrs.get('pin')
        
        if mobile_number and pin:
            try:
                member = Member.objects.get(mobile_number=mobile_number)
                if not member.check_password(pin):
                    raise serializers.ValidationError("Invalid credentials")
                if not member.MbrStatus:
                    raise serializers.ValidationError("Account is inactive")
                attrs['member'] = member
            except Member.DoesNotExist:
                raise serializers.ValidationError("Invalid credentials")
        else:
            raise serializers.ValidationError("Must include mobile number and pin")
        
        return attrs
