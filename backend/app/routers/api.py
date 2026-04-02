from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.url import URL
from app.schemas.url import ShortenRequest, ShortenResponse, StatsResponse
from app.services.click_buffer import get_buffered_clicks
from app.services.shortener import build_short_url, create_url_mapping

router = APIRouter(prefix="/api", tags=["api"])


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


@router.post("/shorten", response_model=ShortenResponse, status_code=status.HTTP_201_CREATED)
async def shorten_url(payload: ShortenRequest, db: AsyncSession = Depends(get_db)):
    try:
        url_obj = await create_url_mapping(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return ShortenResponse(
        short_url=build_short_url(settings.app_domain, url_obj.short_code),
        short_code=url_obj.short_code,
    )


@router.get("/stats/{short_code}", response_model=StatsResponse)
async def get_stats(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url_obj = result.scalar_one_or_none()
    if not url_obj:
        raise HTTPException(status_code=404, detail="Short code not found")

    if url_obj.expires_at and url_obj.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=410, detail="Short URL has expired")

    buffered = await get_buffered_clicks(redis, short_code)

    return StatsResponse(
        original_url=url_obj.original_url,
        clicks=url_obj.clicks + buffered,
        created_at=url_obj.created_at,
        last_accessed=url_obj.last_accessed,
        expires_at=url_obj.expires_at,
    )
