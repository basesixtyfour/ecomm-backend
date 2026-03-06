from urllib.parse import urlencode

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from ..serializers import EmailTokenObtainPairSerializer, CustomTokenRefreshSerializer
from ..token_blacklist import blacklist_token
from .mixins import RefreshCookieMixin


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
    serializer_class = CustomTokenRefreshSerializer
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


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        cookie_name = getattr(settings, "JWT_REFRESH_COOKIE_NAME", "refresh_token")
        raw_token = request.COOKIES.get(cookie_name)

        if raw_token:
            try:
                token = RefreshToken(raw_token)
                remaining = int(token["exp"] - token.current_time.timestamp())
                ttl = max(remaining, 0)
                blacklist_token(token["jti"], ttl_seconds=ttl)
            except TokenError:
                pass

        auth0_logout = request.data.get("auth0", False)
        domain = settings.AUTH0_DOMAIN
        client_id = settings.AUTH0_CLIENT_ID
        frontend_url = settings.FRONTEND_URL

        if auth0_logout and domain and client_id:
            auth0_params = urlencode({
                "client_id": client_id,
                "returnTo": f"{frontend_url}/login",
            })
            response = Response(
                {"detail": "Logged out.", "auth0_logout_url": f"https://{domain}/v2/logout?{auth0_params}"},
                status=status.HTTP_200_OK,
            )
        else:
            response = Response({"detail": "Logged out."}, status=status.HTTP_200_OK)

        response.delete_cookie(
            key=cookie_name,
            path=getattr(settings, "JWT_REFRESH_COOKIE_PATH", "/"),
            samesite=getattr(settings, "JWT_REFRESH_COOKIE_SAMESITE", "None"),
        )
        return response
