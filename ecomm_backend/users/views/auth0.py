import logging
import secrets
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from ..services.auth0 import (
    Auth0IDTokenError,
    Auth0TokenExchangeError,
    exchange_code_for_tokens,
    get_or_create_user,
    verify_id_token,
)
from .mixins import RefreshCookieMixin

logger = logging.getLogger(__name__)


class Auth0LoginView(APIView):
    """Redirect the user to Auth0's /authorize endpoint."""

    permission_classes = [AllowAny]

    def get(self, request):
        domain = settings.AUTH0_DOMAIN
        client_id = settings.AUTH0_CLIENT_ID
        callback = settings.AUTH0_CALLBACK_URL

        if not domain or not client_id:
            return Response(
                {"detail": "Auth0 is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        state = secrets.token_urlsafe(32)
        next_url = request.GET.get("next", "/")

        params = urlencode({
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": callback,
            "scope": "openid profile email",
            "state": state,
        })

        secure = settings.FRONTEND_URL.startswith("https://")
        response = HttpResponseRedirect(f"https://{domain}/authorize?{params}")
        response.set_cookie("auth0_state", state, max_age=300, httponly=True, samesite="Lax", secure=secure)
        response.set_cookie("auth0_next", next_url, max_age=300, httponly=True, samesite="Lax", secure=secure)
        return response


class Auth0CallbackView(RefreshCookieMixin, APIView):
    """Handle the callback from Auth0, exchange the code, and log the user in."""

    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")
        error = request.GET.get("error")
        frontend_url = settings.FRONTEND_URL

        if error:
            logger.warning("Auth0 returned error: %s – %s", error, request.GET.get("error_description", ""))
            return HttpResponseRedirect(f"{frontend_url}/login?error={error}")

        saved_state = request.COOKIES.get("auth0_state")
        if not state or not saved_state or not secrets.compare_digest(state, saved_state):
            return HttpResponseRedirect(f"{frontend_url}/login?error=invalid_state")

        if not code:
            return HttpResponseRedirect(f"{frontend_url}/login?error=missing_code")

        next_url = request.COOKIES.get("auth0_next", "/")

        try:
            token_data = exchange_code_for_tokens(code)
        except Auth0TokenExchangeError:
            return HttpResponseRedirect(f"{frontend_url}/login?error=token_exchange_failed")

        id_token_raw = token_data.get("id_token")
        if not id_token_raw:
            return HttpResponseRedirect(f"{frontend_url}/login?error=no_id_token")

        try:
            id_claims = verify_id_token(id_token_raw)
        except Auth0IDTokenError:
            return HttpResponseRedirect(f"{frontend_url}/login?error=id_token_invalid")

        email = id_claims.get("email", "")
        if not email:
            return HttpResponseRedirect(f"{frontend_url}/login?error=no_email")

        user = get_or_create_user(
            sub=id_claims.get("sub", ""),
            email=email,
            name=id_claims.get("name", ""),
        )

        if not user.is_active:
            return HttpResponseRedirect(f"{frontend_url}/login?error=account_disabled")

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        redirect_url = frontend_url + next_url if next_url.startswith("/") else frontend_url + "/"
        response = HttpResponseRedirect(redirect_url)
        self.set_refresh_cookie(response, str(refresh))
        response.delete_cookie("auth0_state")
        response.delete_cookie("auth0_next")
        response.data = {"access": access_token}
        return response
