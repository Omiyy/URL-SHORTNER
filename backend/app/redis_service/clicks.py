import asyncio
from collections.abc import Mapping
from uuid import uuid4

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.redis_service.keys import CLICK_BUFFER_KEY, INFLIGHT_CLICK_PREFIX


async def buffer_click(redis: Redis, short_code: str) -> None:
    await redis.hincrby(CLICK_BUFFER_KEY, short_code, 1)


async def get_buffered_clicks(redis: Redis, short_code: str) -> int:
    total = int(await redis.hget(CLICK_BUFFER_KEY, short_code) or 0)
    async for key in redis.scan_iter(match=f"{INFLIGHT_CLICK_PREFIX}:*"):
        total += int(await redis.hget(key, short_code) or 0)
    return total


async def _scan_inflight_keys(redis: Redis) -> list[str]:
    keys: list[str] = []
    async for key in redis.scan_iter(match=f"{INFLIGHT_CLICK_PREFIX}:*"):
        keys.append(key)
    return keys


async def _move_pending_to_inflight(redis: Redis) -> str | None:
    if not await redis.exists(CLICK_BUFFER_KEY):
        return None

    inflight_key = f"{INFLIGHT_CLICK_PREFIX}:{uuid4().hex}"
    if not await redis.renamenx(CLICK_BUFFER_KEY, inflight_key):
        return None
    return inflight_key


async def _apply_click_batch(db: AsyncSession, redis_key: str, counts: Mapping[str, str]) -> None:
    batch_id = redis_key.rsplit(":", maxsplit=1)[-1]
    async with db.begin():
        inserted = await db.execute(
            text(
                """
                INSERT INTO click_flush_batches (batch_id)
                VALUES (:batch_id)
                ON CONFLICT (batch_id) DO NOTHING
                RETURNING batch_id
                """
            ),
            {"batch_id": batch_id},
        )
        if inserted.scalar_one_or_none() is None:
            return

        for short_code, raw_count in counts.items():
            count = int(raw_count)
            if count <= 0:
                continue
            await db.execute(
                text(
                    """
                    UPDATE urls
                    SET no_of_clicks = no_of_clicks + :count
                    WHERE short_code = :short_code AND deleted_at IS NULL
                    """
                ),
                {"short_code": short_code, "count": count},
            )


async def flush_click_buffer(redis: Redis, db: AsyncSession) -> None:
    moved_key = await _move_pending_to_inflight(redis)
    inflight_keys = await _scan_inflight_keys(redis)
    if moved_key and moved_key not in inflight_keys:
        inflight_keys.append(moved_key)

    for inflight_key in inflight_keys:
        counts = await redis.hgetall(inflight_key)
        if not counts:
            await redis.delete(inflight_key)
            continue
        await _apply_click_batch(db, inflight_key, counts)
        await redis.delete(inflight_key)


async def click_flush_loop(redis: Redis, session_factory, interval_seconds: int) -> None:
    while True:
        try:
            async with session_factory() as db:
                await flush_click_buffer(redis, db)
        except Exception:
            pass
        await asyncio.sleep(interval_seconds)
