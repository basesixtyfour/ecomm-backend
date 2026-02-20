from rest_framework import generics
from django.conf import settings
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .serializers import UserInfoSerializer, EmailTokenObtainPairSerializer, RegisterUserSerializer


class RefreshCookieMixin:
    def set_refresh_cookie(self, response, refresh_token):
        response.set_cookie(
            key=getattr(settings, "JWT_REFRESH_COOKIE_NAME", "refresh_token"),
            value=refresh_token,
            httponly=getattr(settings, "JWT_REFRESH_COOKIE_HTTP_ONLY", True),
            secure=getattr(settings, "JWT_REFRESH_COOKIE_SECURE", True),
            samesite=getattr(settings, "JWT_REFRESH_COOKIE_SAMESITE", "None"),
            path=getattr(settings, "JWT_REFRESH_COOKIE_PATH", "/"),
        )


class EmailTokenObtainPairView(RefreshCookieMixin, TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            refresh_token = response.data.pop("refresh", None)
            if refresh_token:
                self.set_refresh_cookie(response, refresh_token)

        return response


class CookieTokenRefreshView(RefreshCookieMixin, TokenRefreshView):
    serializer_class = TokenRefreshSerializer
    permission_classes = [AllowAny]

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get('data', {})
        
        if not data.get("refresh"):
            cookie_name = getattr(settings, "JWT_REFRESH_COOKIE_NAME", "refresh_token")
            refresh_from_cookie = self.request.COOKIES.get(cookie_name)
            if refresh_from_cookie:
                data = dict(data)
                data["refresh"] = refresh_from_cookie
                kwargs['data'] = data
        
        return super().get_serializer(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            refresh_token = response.data.pop("refresh", None)
            if refresh_token:
                self.set_refresh_cookie(response, refresh_token)

        return response


class UserInfoView(generics.RetrieveAPIView):
    serializer_class = UserInfoSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class RegisterUserView(generics.CreateAPIView):
    serializer_class = RegisterUserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(
            response.data,
            status=response.status_code,
            headers=response.headers,
        )