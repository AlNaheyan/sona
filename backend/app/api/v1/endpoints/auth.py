"""Authentication endpoints - register, login, me."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.core.rate_limit import limiter, RateLimits
from backend.app.models.user import User
from backend.app.schemas.auth import Token, UserLogin, UserOut, UserRegister
from backend.app.services.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(RateLimits.REGISTER)
async def register(
    request: Request,
    user_in: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """
    Register a new user.

    - **email**: Valid email address (must be unique)
    - **username**: 3-50 characters, alphanumeric and underscores only (must be unique)
    - **password**: Minimum 8 characters
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


@router.post("/login", response_model=Token)
@limiter.limit(RateLimits.LOGIN)
async def login(
    request: Request,
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Login and get an access token.

    - **email**: Your registered email
    - **password**: Your password
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

    # Create access token
    access_token = create_access_token(user.id)

    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    """
    Get current user profile.

    Requires authentication.
    """
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )
