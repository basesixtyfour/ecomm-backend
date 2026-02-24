from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from .models import User

class UserInfoSerializer(serializers.ModelSerializer):
    profile_photo = serializers.ImageField(source='userprofile.profile_photo', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_photo', 'is_staff']

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
        access = refresh.access_token
        access["is_staff"] = user.is_staff
        return {
            "refresh": str(refresh),
            "access": str(access),
        }

class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = RefreshToken(attrs["refresh"])
        access = refresh.access_token

        user_id = access.get("user_id")
        if user_id:
            try:
                user = get_user_model().objects.get(id=user_id)
                access["is_staff"] = user.is_staff
            except Exception:
                pass

        data = {"access": str(access)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    refresh.blacklist()
                except AttributeError:
                    pass
            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()
            data["refresh"] = str(refresh)

        return data


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