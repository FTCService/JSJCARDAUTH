from rest_framework import serializers
from ..models import (
    TempBusinessUser, 
    Business, 
    BusinessAuthToken, 
    BusinessKyc, 
    PhysicalCard, 
    CardMapper
)


class TempBusinessUserSerializer(serializers.ModelSerializer):
    """Serializer for temporary business user during registration"""
    
    class Meta:
        model = TempBusinessUser
        fields = [
            'id', 'business_name', 'email', 'mobile_number', 
            'otp', 'is_active', 'is_institute'
        ]
        read_only_fields = ['id', 'otp']
        extra_kwargs = {
            'pin': {'write_only': True}
        }


class BusinessSerializer(serializers.ModelSerializer):
    """Serializer for Business model"""
    
    class Meta:
        model = Business
        fields = [
            'id', 'business_id', 'email', 'mobile_number', 'business_name',
            'business_type', 'business_country_code', 'business_is_active',
            'business_address', 'business_pincode', 'business_profile_image',
            'is_business', 'is_institute', 'business_created_at', 'business_updated_at'
        ]
        read_only_fields = [
            'id', 'business_id', 'business_created_at', 'business_updated_at'
        ]
        extra_kwargs = {
            'pin': {'write_only': True},
            'otp': {'write_only': True}
        }


class BusinessAuthTokenSerializer(serializers.ModelSerializer):
    """Serializer for Business authentication tokens"""
    
    class Meta:
        model = BusinessAuthToken
        fields = ['key', 'created_at']
        read_only_fields = ['key', 'created_at']


class BusinessKycSerializer(serializers.ModelSerializer):
    """Serializer for Business KYC information"""
    
    business_name = serializers.CharField(source='business.business_name', read_only=True)
    business_id = serializers.CharField(source='business.business_id', read_only=True)
    
    class Meta:
        model = BusinessKyc
        fields = [
            'id', 'business', 'business_name', 'business_id', 'kycStatus',
            'kycAdharCard', 'kycGst', 'kycPanCard', 'kycOthers'
        ]
        read_only_fields = ['id', 'business_name', 'business_id']


class PhysicalCardSerializer(serializers.ModelSerializer):
    """Serializer for Physical Card model"""
    
    business_name = serializers.CharField(source='business.business_name', read_only=True)
    
    class Meta:
        model = PhysicalCard
        fields = [
            'id', 'card_number', 'business', 'business_name', 
            'issued', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'business_name']


class CardMapperSerializer(serializers.ModelSerializer):
    """Serializer for Card Mapper model"""
    
    primary_card_holder = serializers.CharField(source='primary_card.full_name', read_only=True)
    primary_card_number = serializers.CharField(source='primary_card.mbrcardno', read_only=True)
    
    class Meta:
        model = CardMapper
        fields = [
            'id', 'business_id', 'primary_card', 'primary_card_holder',
            'primary_card_number', 'secondary_card', 'secondary_card_type',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'primary_card_holder', 'primary_card_number']
