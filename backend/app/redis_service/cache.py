from redis.asyncio import Redis

from app.core.config import settings
from app.redis_service.keys import cache_key


async def get_cached_url(redis: Redis, short_code: str) -> str | None:
    return await redis.get(cache_key(short_code))


async def cache_url(redis: Redis, short_code: str, original_url: str) -> None:
    await redis.setex(cache_key(short_code), settings.redis_cache_ttl_seconds, original_url)


async def remove_cached_url(redis: Redis, short_code: str) -> None:
    await redis.delete(cache_key(short_code))
