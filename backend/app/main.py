import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import text

from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import ClickFlushBatch, RefreshSession, URL, User  # noqa: F401
from app.redis_service.clicks import flush_click_buffer
from app.redis_service.worker import maintenance_loop
from app.routers.auth import router as auth_router
from app.routers.redirect import router as redirect_router
from app.routers.urls import router as urls_router

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Imports above ensure SQLAlchemy knows both models.
    async with engine.begin() as connection:
        logger.info("Starting DB initialization...")
        print("DB initialization")
        await connection.run_sync(Base.metadata.create_all)
        

    redis = None
    maintenance_task = None

    try:
        redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=settings.redis_max_connections,
            socket_connect_timeout=settings.redis_socket_timeout_seconds,
            socket_timeout=settings.redis_socket_timeout_seconds,
        )
        await redis.ping()
        logger.info("Redis connected successfully")
        maintenance_task = asyncio.create_task(
            maintenance_loop(
                redis,
                SessionLocal,
                settings.click_flush_interval_seconds,
                settings.deleted_url_retention_seconds,
            )
        )
    except (RedisConnectionError, OSError, Exception) as exc:
        logger.warning("Redis unavailable, running without cache: %s", exc)
        if redis is not None:
            try:
                await redis.aclose()
            except Exception:
                pass
        redis = None

    app.state.redis = redis

    yield

    if maintenance_task is not None:
        maintenance_task.cancel()
        try:
            await maintenance_task
        except asyncio.CancelledError:
            pass

    if redis is not None:
        try:
            async with SessionLocal() as db:
                await flush_click_buffer(redis, db)
        except Exception as exc:
            logger.warning("Failed to flush click buffer on shutdown: %s", exc)
        await redis.aclose()

    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in settings.frontend_origin.split(",")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(urls_router)


@app.get("/health")
async def health_check():
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    return {"status": "ok"}


# Keep this last: its root-level path would otherwise match /health and future routes.
app.include_router(redirect_router)
