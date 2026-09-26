import secrets
import string

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.url import URL
from app.schemas.url import CreateUrlRequest

BASE62_ALPHABET = string.ascii_letters + string.digits
MAX_GENERATION_ATTEMPTS = 8


class ShortCodeConflictError(Exception):
    """Raised when a requested custom alias already exists."""


class ShortCodeGenerationError(Exception):
    """Raised when random-code collisions exceed the retry limit."""


def build_short_url(short_code: str) -> str:
    return f"{settings.app_domain.rstrip('/')}/{short_code}"


def generate_short_code(length: int = 7) -> str:
    return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))


async def create_url_mapping(
    db: AsyncSession,
    *,
    user_id,
    payload: CreateUrlRequest,
) -> URL:
    """Persist a unique mapping, retrying only random-code collisions."""
    attempts = 1 if payload.custom_alias else MAX_GENERATION_ATTEMPTS

    for _ in range(attempts):
        short_code = payload.custom_alias or generate_short_code()
        url = URL(
            short_code=short_code,
            user_id=user_id,
            original_url=str(payload.original_url),
        )
        db.add(url)

        try:
            await db.commit()
            await db.refresh(url)
            return url
        except IntegrityError as exc:
            await db.rollback()
            if payload.custom_alias:
                raise ShortCodeConflictError("Custom alias is already in use") from exc

    raise ShortCodeGenerationError("Could not generate a unique short code")
