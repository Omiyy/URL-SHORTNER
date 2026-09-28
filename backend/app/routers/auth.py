from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.refresh_session import RefreshSession
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["authentication"])

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


def refresh_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path="/api/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path="/api/auth",
    )


async def revoke_family(db: AsyncSession, family_id, revoked_at: datetime) -> None:
    await db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.family_id == family_id,
            RefreshSession.revoked_at.is_(None),
        )
        .values(revoked_at=revoked_at)
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: DatabaseSession) -> User:
    existing = await db.execute(select(User.user_id).where(User.user_name == payload.user_name))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Username is already registered")
    
    user = User(
        user_name=payload.user_name,
        password_hash=await run_in_threadpool(hash_password, payload.password),
    )
    db.add(user)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Username is already registered") from exc

    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, response: Response, db: DatabaseSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.user_name == payload.user_name))
    user = result.scalar_one_or_none()

    password_is_valid = user is not None and await run_in_threadpool(
        verify_password, payload.password, user.password_hash
    )
    if not password_is_valid:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    refresh_token = generate_refresh_token()
    db.add(
        RefreshSession(
            user_id=user.user_id,
            family_id=uuid4(),
            token_hash=hash_refresh_token(refresh_token),
            expires_at=refresh_expiry(),
        )
    )
    await db.commit()

    set_refresh_cookie(response, refresh_token)
    return TokenResponse(
        access_token=create_access_token(user.user_id),
        user=user
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: Request, response: Response, db: DatabaseSession
) -> TokenResponse:
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token is required")

    result = await db.execute(
        select(RefreshSession)
        .where(RefreshSession.token_hash == hash_refresh_token(refresh_token))
        .with_for_update()
    )
    session = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if session is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if session.revoked_at is not None:
        await revoke_family(db, session.family_id, now)
        await db.commit()
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    if session.expires_at <= now:
        session.revoked_at = now
        await db.commit()
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Refresh token has expired")

    session.revoked_at = now
    session.last_used_at = now
    new_refresh_token = generate_refresh_token()
    db.add(
        RefreshSession(
            user_id=session.user_id,
            family_id=session.family_id,
            token_hash=hash_refresh_token(new_refresh_token),
            expires_at=refresh_expiry(),
        )
    )
    await db.commit()

    set_refresh_cookie(response, new_refresh_token)
    
    user_result = await db.execute(select(User).where(User.user_id == session.user_id))
    user = user_result.scalar_one()
    
    return TokenResponse(
        access_token=create_access_token(session.user_id),
        user=user
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, db: DatabaseSession) -> Response:
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if refresh_token:
        result = await db.execute(
            select(RefreshSession).where(
                RefreshSession.token_hash == hash_refresh_token(refresh_token)
            )
        )
        session = result.scalar_one_or_none()
        if session is not None and session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            await db.commit()

    clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
