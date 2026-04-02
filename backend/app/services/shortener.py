import re
import secrets
import string
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.url import URL
from app.schemas.url import ShortenRequest

BASE62_ALPHABET = string.ascii_letters + string.digits
ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,20}$")
RESERVED_CODES = {"api", "stats", "health", "docs", "redoc", "openapi.json"}


def build_short_url(domain: str, short_code: str) -> str:
    return f"{domain.rstrip('/')}/{short_code}"


def generate_base62_code(length: int = 6) -> str:
    return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))


async def _code_exists(db: AsyncSession, short_code: str) -> bool:
    result = await db.execute(select(URL.id).where(URL.short_code == short_code))
    return result.scalar_one_or_none() is not None


async def create_short_code(db: AsyncSession, payload: ShortenRequest) -> str:
    if payload.custom_alias:
        alias = payload.custom_alias.strip()
        if alias.lower() in RESERVED_CODES or not ALIAS_PATTERN.match(alias):
            raise ValueError("Invalid or reserved custom alias")
        if await _code_exists(db, alias):
            raise ValueError("Custom alias already in use")
        return alias

    for _ in range(8):
        candidate = generate_base62_code()
        if candidate.lower() not in RESERVED_CODES and not await _code_exists(db, candidate):
            return candidate

    raise RuntimeError("Could not generate a unique short code after retries")


async def create_url_mapping(db: AsyncSession, payload: ShortenRequest) -> URL:
    short_code = await create_short_code(db, payload)

    expires_at = None
    if payload.expires_in_days:
        expires_at = datetime.now(UTC) + timedelta(days=payload.expires_in_days)

    url_obj = URL(
        short_code=short_code,
        original_url=str(payload.url),
        expires_at=expires_at,
    )
    db.add(url_obj)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise RuntimeError("Collision detected while creating short URL")

    await db.refresh(url_obj)
    return url_obj
