from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from .models import User

class UserInfoSerializer(serializers.ModelSerializer):
    profile_photo = serializers.ImageField(source='userprofile.profile_photo', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_photo']

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    def validate(self, attrs):
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password")

        user = get_user_model().objects.filter(email__iexact=email).first()

        if not user or not user.check_password(password):
            raise AuthenticationFailed("Invalid email or password")
        if not user.is_active:
            raise AuthenticationFailed("User account is disabled")

        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

class RegisterUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        return value.strip().lower()
    
    def validate_username(self, value):
        return value.strip().lower()

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)