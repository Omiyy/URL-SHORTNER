import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from redis.exceptions import TimeoutError as RedisTimeoutError
from sqlalchemy.exc import DBAPIError

from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.flush_batch import ClickFlushBatch  # noqa: F401
from app.models.url import URL  # noqa: F401
from app.routers.api import router as api_router
from app.routers.health import router as health_router
from app.routers.redirect import router as redirect_router
from app.services.click_buffer import flush_click_buffer, flush_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = Redis.from_url(
        settings.redis_url, 
        decode_responses=True,
        max_connections=settings.redis_max_connections,
        socket_timeout=settings.api_timeout_seconds
    )
    app.state.redis = redis

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    flush_task = asyncio.create_task(flush_loop(redis, SessionLocal))
    app.state.flush_task = flush_task

    yield

    flush_task.cancel()
    try:
        await flush_task
    except asyncio.CancelledError:
        pass

    async with SessionLocal() as db:
        await flush_click_buffer(redis, db)

    await redis.close()
    await engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

@app.exception_handler(RedisTimeoutError)
async def redis_timeout_handler(request: Request, exc: RedisTimeoutError):
    return JSONResponse(status_code=503, content={"detail": "Service Unavailable - Cache Timeout"})

@app.exception_handler(DBAPIError)
async def dbapi_error_handler(request: Request, exc: DBAPIError):
    return JSONResponse(status_code=503, content={"detail": "Service Unavailable - Database Timeout"})

@app.exception_handler(asyncio.exceptions.TimeoutError)
async def asyncio_timeout_handler(request: Request, exc: asyncio.exceptions.TimeoutError):
    return JSONResponse(status_code=503, content={"detail": "Service Unavailable - Request Timeout"})

frontend_origin = settings.frontend_origin.rstrip("/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(api_router)
app.include_router(redirect_router)
