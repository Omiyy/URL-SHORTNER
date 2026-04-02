import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

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
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
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
