import redis
from django.conf import settings

_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            getattr(settings, "REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
        )
    return _redis_client


def blacklist_token(jti: str, ttl_seconds: int = 86400):
    get_redis().setex(f"bl:{jti}", ttl_seconds, "1")


def is_token_blacklisted(jti: str) -> bool:
    return get_redis().exists(f"bl:{jti}") == 1
