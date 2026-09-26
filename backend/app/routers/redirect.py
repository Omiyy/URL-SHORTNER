from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.url import URL
from app.redis_service.cache import cache_url, get_cached_url
from app.redis_service.clicks import buffer_click
from app.redis_service.client import get_redis
from app.redis_service.deletion import is_url_deleted

router = APIRouter(tags=["redirect"])


@router.get("/{short_code}", include_in_schema=False)
async def redirect_short_url(
    short_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Optional[Redis], Depends(get_redis)],
) -> RedirectResponse:
    original_url = None

    if redis is not None:
        try:
            if await is_url_deleted(redis, short_code):
                raise HTTPException(status_code=404, detail="Short URL not found")
            original_url = await get_cached_url(redis, short_code)
        except RedisError:
            original_url = None

    if original_url is None:
        result = await db.execute(
            select(URL.original_url).where(
                URL.short_code == short_code,
                URL.deleted_at.is_(None),
            )
        )
        original_url = result.scalar_one_or_none()

    if original_url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")

    if redis is not None:
        try:
            await cache_url(redis, short_code, original_url)
            await buffer_click(redis, short_code)
        except RedisError:
            # Redis memory pressure/outage must not lose clicks.
            await db.execute(
                update(URL)
                .where(URL.short_code == short_code, URL.deleted_at.is_(None))
                .values(no_of_clicks=URL.no_of_clicks + 1)
            )
            await db.commit()
    else:
        # No Redis available — record click directly in DB.
        await db.execute(
            update(URL)
            .where(URL.short_code == short_code, URL.deleted_at.is_(None))
            .values(no_of_clicks=URL.no_of_clicks + 1)
        )
        await db.commit()

    return RedirectResponse(url=original_url, status_code=302)

