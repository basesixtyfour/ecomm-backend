import os

import jwt

DJANGO_SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-#&4@-74b2@c7)ql^%i^(gjq0@7e^hj4ue@0spc-gg-k*l6itkz",
)
JWT_ALGORITHM = "HS256"


def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, DJANGO_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            return None
        return {
            "user_id": str(user_id).replace("-", ""),
            "is_staff": payload.get("is_staff", False),
        }
    except jwt.InvalidTokenError:
        return None
