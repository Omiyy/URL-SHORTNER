from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(tags=["health"])


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    await db.execute(text("SELECT 1"))
    await redis.ping()
    return {"status": "ok"}
