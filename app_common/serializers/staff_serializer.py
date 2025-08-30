from rest_framework import serializers
from ..models import User, UserAuthToken


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User (Admin & Staff) model"""
    
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'employee_id', 'email', 'mobile_number',
            'is_active', 'is_superuser', 'is_staff', 'is_jobmitra',
            'address', 'meta_data'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'password': {'write_only': True},
            'token': {'write_only': True}
        }


class UserAuthTokenSerializer(serializers.ModelSerializer):
    """Serializer for User authentication tokens"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = UserAuthToken
        fields = [
            'user', 'user_email', 'user_full_name', 
            'key', 'created_at'
        ]
        read_only_fields = ['key', 'created_at', 'user_email', 'user_full_name']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for User registration"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'full_name', 'employee_id', 'email', 'mobile_number',
            'password', 'confirm_password', 'is_staff', 'is_jobmitra',
            'address', 'meta_data'
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
        user = User.objects.create_user(
            password=password, 
            **validated_data
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for User login"""
    
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
                if not user.check_password(password):
                    raise serializers.ValidationError("Invalid credentials")
                if not user.is_active:
                    raise serializers.ValidationError("Account is inactive")
                attrs['user'] = user
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid credentials")
        else:
            raise serializers.ValidationError("Must include email and password")
        
        return attrs


class StaffProfileSerializer(serializers.ModelSerializer):
    """Serializer for Staff profile updates"""
    
    class Meta:
        model = User
        fields = [
            'full_name', 'mobile_number', 'address', 'meta_data'
        ]
