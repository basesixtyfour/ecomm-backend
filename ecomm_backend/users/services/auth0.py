import hashlib
import logging
import secrets

import httpx
import jwt
from jwt import PyJWKClient

from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class Auth0TokenExchangeError(Exception):
    pass


class Auth0IDTokenError(Exception):
    pass


def exchange_code_for_tokens(code: str) -> dict:
    """Exchange an Auth0 authorisation code for token data."""
    domain = settings.AUTH0_DOMAIN
    token_url = f"https://{domain}/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.AUTH0_CLIENT_ID,
        "client_secret": settings.AUTH0_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.AUTH0_CALLBACK_URL,
    }

    try:
        resp = httpx.post(token_url, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        logger.error("Auth0 token exchange failed: %s", exc)
        raise Auth0TokenExchangeError(str(exc)) from exc


def verify_id_token(id_token_raw: str) -> dict:
    """Verify an Auth0 id_token via JWKS and return its claims."""
    domain = settings.AUTH0_DOMAIN
    client_id = settings.AUTH0_CLIENT_ID

    try:
        jwks_client = PyJWKClient(f"https://{domain}/.well-known/jwks.json")
        signing_key = jwks_client.get_signing_key_from_jwt(id_token_raw)
        return jwt.decode(
            id_token_raw,
            signing_key.key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=f"https://{domain}/",
        )
    except jwt.PyJWTError as exc:
        logger.error("Auth0 id_token verification failed: %s", exc)
        raise Auth0IDTokenError(str(exc)) from exc


def get_or_create_user(sub: str, email: str, name: str = "") -> User:
    """Find an existing user by Auth0 sub or email, or create a new one."""
    user = User.objects.filter(auth0_sub=sub).first()
    if user:
        return user

    user = User.objects.filter(email=email).first()
    if user:
        user.auth0_sub = sub
        user.save(update_fields=["auth0_sub"])
        return user

    username = email.split("@")[0]
    base = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1

    user = User.objects.create_user(
        username=username,
        email=email,
        password=hashlib.sha256(secrets.token_bytes(32)).hexdigest(),
        auth0_sub=sub,
    )
    if name:
        parts = name.split(" ", 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ""
        user.save(update_fields=["first_name", "last_name"])

    return user
