from __future__ import annotations

import redis

from app.core.config import get_settings


def get_redis_client() -> redis.Redis:
    settings = get_settings()
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)
