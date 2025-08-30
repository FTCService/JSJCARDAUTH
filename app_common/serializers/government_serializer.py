from rest_framework import serializers
from ..models import GovernmentUser, GovernmentAuthToken


class GovernmentUserSerializer(serializers.ModelSerializer):
    """Serializer for Government User model"""
    
    class Meta:
        model = GovernmentUser
        fields = [
            'id', 'email', 'full_name', 'mobile_number', 'department',
            'designation', 'is_active', 'is_staff', 'is_government',
            'date_joined', 'last_updated'
        ]
        read_only_fields = ['id', 'date_joined', 'last_updated', 'is_government']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class GovernmentAuthTokenSerializer(serializers.ModelSerializer):
    """Serializer for Government authentication tokens"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = GovernmentAuthToken
        fields = [
            'id', 'user', 'user_email', 'user_full_name', 
            'key', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'key', 'created_at', 'updated_at', 
            'user_email', 'user_full_name'
        ]


class GovernmentUserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for Government User registration"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = GovernmentUser
        fields = [
            'email', 'full_name', 'mobile_number', 'department',
            'designation', 'password', 'confirm_password'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'confirm_password': {'write_only': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = GovernmentUser.objects.create_user(
            password=password, 
            **validated_data
        )
        return user
