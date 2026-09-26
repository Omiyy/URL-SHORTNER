from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.url import URL
from app.models.user import User
from app.redis_service.cache import cache_url
from app.redis_service.clicks import get_buffered_clicks
from app.redis_service.client import get_redis
from app.redis_service.deletion import mark_url_deleted
from app.schemas.url import CreateUrlRequest, UrlResponse, UrlStatsResponse
from app.services.shortener import (
    ShortCodeConflictError,
    ShortCodeGenerationError,
    build_short_url,
    create_url_mapping,
)

router = APIRouter(prefix="/api/urls", tags=["urls"])

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def serialize_url(url: URL) -> UrlResponse:
    return UrlResponse(
        short_code=url.short_code,
        short_url=build_short_url(url.short_code),
        original_url=url.original_url,
        no_of_clicks=url.no_of_clicks,
        created_at=url.created_at,
    )


@router.post("", response_model=UrlResponse, status_code=status.HTTP_201_CREATED)
async def create_url(
    payload: CreateUrlRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
    redis: Annotated[Optional[Redis], Depends(get_redis)],
) -> UrlResponse:
    try:
        url = await create_url_mapping(
            db,
            user_id=current_user.user_id,
            payload=payload,
        )
    except ShortCodeConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ShortCodeGenerationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if redis is not None:
        try:
            await cache_url(redis, url.short_code, url.original_url)
        except RedisError:
            pass
    return serialize_url(url)


@router.get("", response_model=list[UrlResponse])
async def list_urls(current_user: CurrentUser, db: DatabaseSession) -> list[UrlResponse]:
    result = await db.execute(
        select(URL)
        .where(URL.user_id == current_user.user_id, URL.deleted_at.is_(None))
        .order_by(URL.created_at.desc())
    )
    return [serialize_url(url) for url in result.scalars().all()]


@router.get("/{short_code}/stats", response_model=UrlStatsResponse)
async def get_url_stats(
    short_code: str,
    current_user: CurrentUser,
    db: DatabaseSession,
    redis: Annotated[Optional[Redis], Depends(get_redis)],
) -> UrlStatsResponse:
    result = await db.execute(
        select(URL).where(
            URL.short_code == short_code,
            URL.user_id == current_user.user_id,
            URL.deleted_at.is_(None),
        )
    )
    url = result.scalar_one_or_none()
    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")

    buffered_clicks = 0
    if redis is not None:
        try:
            buffered_clicks = await get_buffered_clicks(redis, short_code)
        except RedisError:
            buffered_clicks = 0
    return UrlStatsResponse(
        short_code=url.short_code,
        original_url=url.original_url,
        no_of_clicks=url.no_of_clicks + buffered_clicks,
        created_at=url.created_at,
    )


@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(
    short_code: str,
    current_user: CurrentUser,
    db: DatabaseSession,
    redis: Annotated[Optional[Redis], Depends(get_redis)],
) -> None:
    result = await db.execute(
        update(URL)
        .where(
            URL.short_code == short_code,
            URL.user_id == current_user.user_id,
            URL.deleted_at.is_(None),
        )
        .values(deleted_at=datetime.now(timezone.utc))
        .returning(URL.short_code)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Short URL not found")

    await db.commit()
    if redis is not None:
        try:
            await mark_url_deleted(redis, short_code)
        except RedisError:
            # PostgreSQL remains authoritative if Redis is temporarily unavailable.
            pass
