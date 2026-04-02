import json
from datetime import UTC, datetime

from redis.asyncio import Redis

from app.core.config import settings
from app.models.url import URL


def cache_key(short_code: str) -> str:
    return f"url:{short_code}"


def _serialize_mapping(url_obj: URL) -> str:
    payload = {
        "original_url": url_obj.original_url,
        "expires_at": url_obj.expires_at.isoformat() if url_obj.expires_at else None,
    }
    return json.dumps(payload)


async def set_url_cache(redis: Redis, url_obj: URL) -> None:
    await redis.setex(cache_key(url_obj.short_code), settings.redis_cache_ttl_seconds, _serialize_mapping(url_obj))


async def get_url_cache(redis: Redis, short_code: str) -> str | None:
    raw = await redis.get(cache_key(short_code))
    if not raw:
        return None

    payload = json.loads(raw)
    expires_at = payload.get("expires_at")
    if expires_at:
        expires_dt = datetime.fromisoformat(expires_at)
        if expires_dt < datetime.now(UTC):
            return None

    return payload["original_url"]
