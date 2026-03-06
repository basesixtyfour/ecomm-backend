from django.conf import settings


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
