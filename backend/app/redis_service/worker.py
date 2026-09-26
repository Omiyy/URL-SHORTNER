import asyncio
from datetime import datetime, timedelta, timezone

from redis.asyncio import Redis
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.url import URL
from app.redis_service.clicks import flush_click_buffer
from app.redis_service.deletion import remove_deletion_tombstone


async def purge_deleted_urls(redis: Redis, db: AsyncSession, retention_seconds: int) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=retention_seconds)
    result = await db.execute(
        select(URL.short_code).where(
            URL.deleted_at.is_not(None),
            URL.deleted_at <= cutoff,
        )
    )
    short_codes = list(result.scalars())
    if not short_codes:
        return

    await db.execute(delete(URL).where(URL.short_code.in_(short_codes)))
    await db.commit()
    for short_code in short_codes:
        await remove_deletion_tombstone(redis, short_code)


async def maintenance_loop(redis: Redis, session_factory, interval_seconds: int, retention_seconds: int) -> None:
    while True:
        try:
            async with session_factory() as db:
                await flush_click_buffer(redis, db)
                await purge_deleted_urls(redis, db, retention_seconds)
        except Exception:
            pass
        await asyncio.sleep(interval_seconds)
