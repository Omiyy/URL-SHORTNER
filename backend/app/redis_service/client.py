from typing import Optional

from fastapi import Request
from redis.asyncio import Redis


def get_redis(request: Request) -> Optional[Redis]:
    return getattr(request.app.state, "redis", None)
