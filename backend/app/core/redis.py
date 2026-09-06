from typing import Optional
from redis.asyncio import Redis, from_url

from app.core.config import settings

redis_client: Optional[Redis] = None


async def get_redis_pool() -> Redis:
    """Async Redis client connection factory and dependency provider."""
    global redis_client
    if redis_client is None:
        redis_client = from_url(
            str(settings.REDIS_URL),
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_connect_timeout=1.0,
            socket_timeout=1.0,
        )
    return redis_client


async def close_redis_pool() -> None:
    """Close active Redis client connection."""
    global redis_client
    if redis_client is not None:
        if hasattr(redis_client, "aclose"):
            await redis_client.aclose()
        else:
            await redis_client.close()
        redis_client = None
