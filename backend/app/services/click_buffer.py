import asyncio
from collections.abc import Mapping
from uuid import uuid4

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

PENDING_BUFFER_KEY = "click_buffer"
INFLIGHT_PREFIX = "click_buffer_inflight"


async def buffer_click(redis: Redis, short_code: str) -> None:
    await redis.hincrby(PENDING_BUFFER_KEY, short_code, 1)


async def _scan_inflight_keys(redis: Redis) -> list[str]:
    keys: list[str] = []
    async for key in redis.scan_iter(match=f"{INFLIGHT_PREFIX}:*"):
        keys.append(key)
    return keys


async def _move_pending_to_inflight(redis: Redis) -> str | None:
    if not await redis.exists(PENDING_BUFFER_KEY):
        return None

    inflight_key = f"{INFLIGHT_PREFIX}:{uuid4().hex}"
    moved = await redis.renamenx(PENDING_BUFFER_KEY, inflight_key)
    if not moved:
        return None
    return inflight_key


async def _apply_inflight_counts(db: AsyncSession, redis_key: str, counts: Mapping[str, str]) -> None:
    batch_id = redis_key.split(":")[-1]

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
                    SET clicks = clicks + :count,
                        last_accessed = NOW()
                    WHERE short_code = :short_code
                    """
                ),
                {"count": count, "short_code": short_code},
            )


async def flush_click_buffer(redis: Redis, db: AsyncSession) -> None:
    inflight_candidate = await _move_pending_to_inflight(redis)
    inflight_keys = await _scan_inflight_keys(redis)
    if inflight_candidate and inflight_candidate not in inflight_keys:
        inflight_keys.append(inflight_candidate)

    for inflight_key in inflight_keys:
        counts = await redis.hgetall(inflight_key)
        if not counts:
            await redis.delete(inflight_key)
            continue

        await _apply_inflight_counts(db, inflight_key, counts)
        await redis.delete(inflight_key)


async def get_buffered_clicks(redis: Redis, short_code: str) -> int:
    pending = await redis.hget(PENDING_BUFFER_KEY, short_code)
    buffered_total = int(pending or 0)

    for inflight_key in await _scan_inflight_keys(redis):
        value = await redis.hget(inflight_key, short_code)
        buffered_total += int(value or 0)

    return buffered_total


async def flush_loop(redis: Redis, session_factory) -> None:
    while True:
        try:
            async with session_factory() as db:
                await flush_click_buffer(redis, db)
        except Exception:
            # Keep loop alive and retry on next interval.
            pass

        await asyncio.sleep(settings.click_flush_interval_seconds)
