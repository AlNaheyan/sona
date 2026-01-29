"""Pydantic schemas for authentication."""

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """User registration request."""

    email: EmailStr = Field(..., description="Valid email address (must be unique)")
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Username (3-50 chars, alphanumeric and underscores only)",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (minimum 8 characters)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "username": "music_lover",
                    "password": "securepassword123",
                }
            ]
        }
    }


class UserLogin(BaseModel):
    """User login request."""

    email: EmailStr = Field(..., description="Your registered email address")
    password: str = Field(..., description="Your password")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "securepassword123",
                }
            ]
        }
    }


class Token(BaseModel):
    """JWT token response with access and refresh tokens."""

    access_token: str = Field(..., description="Short-lived JWT for API access (30 min)")
    refresh_token: str = Field(..., description="Long-lived JWT for token refresh (7 days)")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                }
            ]
        }
    }


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str = Field(..., description="Valid refresh token from login")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                }
            ]
        }
    }


class TokenPayload(BaseModel):
    """JWT token payload (internal use)."""

    sub: str = Field(..., description="User ID")
    exp: int = Field(..., description="Expiration timestamp (Unix epoch)")
    type: str = Field(default="access", description="Token type: 'access' or 'refresh'")


class UserOut(BaseModel):
    """User response (public info)."""

    id: str = Field(..., description="Unique user identifier (UUID)")
    email: str = Field(..., description="User's email address")
    username: str = Field(..., description="User's display name")
    is_active: bool = Field(..., description="Whether the account is active")
    created_at: str = Field(..., description="Account creation timestamp (ISO 8601)")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "user@example.com",
                    "username": "music_lover",
                    "is_active": True,
                    "created_at": "2024-01-15T10:30:00Z",
                }
            ]
        },
    }
