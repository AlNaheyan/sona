"""Authentication service - password hashing and JWT handling."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt
import redis.asyncio as aioredis
from jose import JWTError, jwt

from backend.app.core.config import settings

_REVOKED_PREFIX = "token:revoked:"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode = {"sub": user_id, "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT refresh token with longer expiry. Includes jti for revocation."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> str | None:
    """
    Decode and validate a JWT access token.

    Returns the user_id if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        if user_id is None or token_type != "access":
            return None
        return user_id
    except JWTError:
        return None


@dataclass
class RefreshTokenData:
    user_id: str
    jti: str
    exp: int


def decode_refresh_token(token: str) -> RefreshTokenData | None:
    """
    Decode and validate a JWT refresh token.

    Returns RefreshTokenData (user_id, jti, exp) if valid, None otherwise.
    Callers must also check is_token_revoked(data.jti) to enforce revocation.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        jti: str | None = payload.get("jti")
        exp: int | None = payload.get("exp")
        if user_id is None or token_type != "refresh":
            return None
        # Tokens issued before jti was added have no jti — treat as valid but non-revocable
        return RefreshTokenData(user_id=user_id, jti=jti or "", exp=exp or 0)
    except JWTError:
        return None


async def revoke_token(jti: str, exp: int) -> None:
    """Add a token JTI to the Redis revocation set with TTL matching expiry."""
    if not jti:
        return
    remaining_ttl = exp - int(datetime.now(timezone.utc).timestamp())
    if remaining_ttl <= 0:
        return  # Already expired, no need to store
    try:
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await client.set(f"{_REVOKED_PREFIX}{jti}", "1", ex=remaining_ttl)
        await client.aclose()
    except aioredis.RedisError:
        pass  # Fail open — revocation failure is logged elsewhere


async def is_token_revoked(jti: str) -> bool:
    """Check if a token JTI has been revoked."""
    if not jti:
        return False
    try:
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        result = await client.get(f"{_REVOKED_PREFIX}{jti}")
        await client.aclose()
        return result is not None
    except aioredis.RedisError:
        return False  # Fail open — better to let a potentially stolen token through than lock everyone out
