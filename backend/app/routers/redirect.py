from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.url import URL
from app.services.cache import get_url_cache, set_url_cache
from app.services.click_buffer import buffer_click

router = APIRouter(tags=["redirect"])


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


@router.get("/{short_code}")
async def redirect_short_url(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    original_url = await get_url_cache(redis, short_code)

    if not original_url:
        result = await db.execute(select(URL).where(URL.short_code == short_code))
        url_obj = result.scalar_one_or_none()

        if not url_obj:
            raise HTTPException(status_code=404, detail="Short code not found")

        if url_obj.expires_at and url_obj.expires_at < datetime.now(UTC):
            raise HTTPException(status_code=410, detail="Short URL has expired")

        await set_url_cache(redis, url_obj)
        original_url = url_obj.original_url

    await buffer_click(redis, short_code)
    return RedirectResponse(url=original_url, status_code=302)
