"""Unit tests for auth service - password hashing and JWT handling."""

from datetime import timedelta

import pytest

from backend.app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


class TestPasswordHashing:
    """Tests for bcrypt password hashing."""

    def test_hash_password_returns_hash(self):
        """hash_password should return a bcrypt hash."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix
        assert len(hashed) == 60  # bcrypt hash length

    def test_hash_password_different_salts(self):
        """Same password should produce different hashes (different salts)."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """verify_password should return True for correct password."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password should return False for incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword456"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """verify_password should handle empty password."""
        password = ""
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("notempty", hashed) is False


class TestJWTTokens:
    """Tests for JWT token creation and decoding."""

    def test_create_access_token_returns_string(self):
        """create_access_token should return a JWT string."""
        user_id = "test-user-id-123"
        token = create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0
        # JWT has 3 parts separated by dots
        assert token.count(".") == 2

    def test_decode_access_token_valid(self):
        """decode_access_token should return user_id for valid token."""
        user_id = "test-user-id-123"
        token = create_access_token(user_id)

        decoded_id = decode_access_token(token)

        assert decoded_id == user_id

    def test_decode_access_token_invalid_token(self):
        """decode_access_token should return None for invalid token."""
        invalid_token = "invalid.token.here"

        result = decode_access_token(invalid_token)

        assert result is None

    def test_decode_access_token_malformed(self):
        """decode_access_token should return None for malformed token."""
        malformed_token = "not-a-valid-jwt"

        result = decode_access_token(malformed_token)

        assert result is None

    def test_decode_access_token_empty(self):
        """decode_access_token should return None for empty token."""
        result = decode_access_token("")

        assert result is None

    def test_create_access_token_custom_expiry(self):
        """create_access_token should accept custom expiry."""
        user_id = "test-user-id-123"
        custom_expiry = timedelta(hours=24)

        token = create_access_token(user_id, expires_delta=custom_expiry)
        decoded_id = decode_access_token(token)

        assert decoded_id == user_id

    def test_create_access_token_different_users(self):
        """Different users should get different tokens."""
        user1_token = create_access_token("user-1")
        user2_token = create_access_token("user-2")

        assert user1_token != user2_token
        assert decode_access_token(user1_token) == "user-1"
        assert decode_access_token(user2_token) == "user-2"

    def test_decode_access_token_wrong_secret(self):
        """Token signed with different secret should fail to decode."""
        # Create a token with the real secret
        token = create_access_token("test-user")

        # Manually create a token with wrong claims (simulating wrong secret)
        # The decode function uses settings.secret_key, so any tampered token fails
        tampered_token = token[:-5] + "xxxxx"  # Corrupt the signature

        result = decode_access_token(tampered_token)

        assert result is None
