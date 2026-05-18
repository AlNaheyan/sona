"""Authentication endpoints - register, login, me."""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.rate_limit import limiter, RateLimits
from backend.app.models.user import User
from backend.app.schemas.auth import Token, RefreshTokenRequest, UserLogin, UserOut, UserRegister
from backend.app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE = "refresh_token"
_REFRESH_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 86400,
        path=_REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=_REFRESH_COOKIE,
        path=_REFRESH_COOKIE_PATH,
    )


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "description": "Validation error or duplicate email/username",
            "content": {
                "application/json": {
                    "examples": {
                        "email_taken": {"value": {"detail": "Email already registered"}},
                        "username_taken": {"value": {"detail": "Username already taken"}},
                    }
                }
            },
        },
        422: {"description": "Invalid input (validation failed)"},
        429: {"description": "Rate limit exceeded (3/minute)"},
    },
)
@limiter.limit(RateLimits.REGISTER)
async def register(
    request: Request,
    user_in: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """
    Register a new user account.

    Creates a new user with the provided credentials. After registration,
    use `/auth/login` to obtain access tokens.

    **Rate limit**: 3 requests per minute
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create user
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return UserOut(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
    )


@router.post(
    "/login",
    response_model=Token,
    responses={
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {"detail": "Incorrect email or password"}
                }
            },
        },
        403: {
            "description": "Account disabled",
            "content": {
                "application/json": {
                    "example": {"detail": "User account is disabled"}
                }
            },
        },
        429: {"description": "Rate limit exceeded (5/minute)"},
    },
)
@limiter.limit(RateLimits.LOGIN)
async def login(
    request: Request,
    response: Response,
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Authenticate and receive JWT tokens.

    Returns both access and refresh tokens:
    - **access_token**: Use for API requests (expires in 30 minutes)
    - **refresh_token**: Use to get new tokens (expires in 7 days)

    Include the access token in the `Authorization` header:
    ```
    Authorization: Bearer <access_token>
    ```

    **Rate limit**: 5 requests per minute
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Create access and refresh tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Set refresh_token as HttpOnly cookie so JS cannot read it
    _set_refresh_cookie(response, refresh_token)

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.get(
    "/me",
    response_model=UserOut,
    responses={
        401: {
            "description": "Not authenticated or invalid token",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            },
        },
    },
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    """
    Get the current authenticated user's profile.

    Requires a valid access token in the Authorization header.
    """
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )


@router.post(
    "/refresh",
    response_model=Token,
    responses={
        401: {
            "description": "Invalid or expired refresh token",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {"value": {"detail": "Invalid or expired refresh token"}},
                        "user_not_found": {"value": {"detail": "User not found"}},
                    }
                }
            },
        },
        403: {
            "description": "Account disabled",
            "content": {
                "application/json": {
                    "example": {"detail": "User account is disabled"}
                }
            },
        },
        429: {"description": "Rate limit exceeded (5/minute)"},
    },
)
@limiter.limit(RateLimits.LOGIN)
async def refresh_tokens(
    request: Request,
    response: Response,
    token_request: RefreshTokenRequest | None = None,
    refresh_token_cookie: str | None = Cookie(None, alias=_REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Exchange a refresh token for new access and refresh tokens.

    Reads the refresh token from the HttpOnly cookie set at login.
    API clients may also pass it in the request body as a fallback.

    **Rate limit**: 5 requests per minute
    """
    raw_token = refresh_token_cookie or (token_request.refresh_token if token_request else None)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode and validate refresh token
    user_id = decode_refresh_token(raw_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Create new access and refresh tokens (token rotation)
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    _set_refresh_cookie(response, refresh_token)

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    """Clear the HttpOnly refresh token cookie to complete logout."""
    _clear_refresh_cookie(response)
