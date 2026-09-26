from redis.asyncio import Redis

from app.redis_service.keys import cache_key, deleted_key


async def is_url_deleted(redis: Redis, short_code: str) -> bool:
    return bool(await redis.exists(deleted_key(short_code)))


async def mark_url_deleted(redis: Redis, short_code: str) -> None:
    """Atomically invalidate cache and add a non-TTL deletion tombstone."""
    async with redis.pipeline(transaction=True) as pipeline:
        pipeline.delete(cache_key(short_code))
        pipeline.set(deleted_key(short_code), "1")
        await pipeline.execute()


async def remove_deletion_tombstone(redis: Redis, short_code: str) -> None:
    await redis.delete(deleted_key(short_code), cache_key(short_code))
