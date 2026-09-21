"""Unit tests for password hashing and JWT token issuing/validation."""
import pytest

from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("Str0ngPass!")
    assert hashed != "Str0ngPass!"
    assert verify_password("Str0ngPass!", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_roundtrip():
    token = create_access_token("user-123", "candidate")
    payload = decode_token(token)
    assert payload.sub == "user-123"
    assert payload.role == "candidate"
    assert payload.token_type == "access"


def test_refresh_token_roundtrip():
    token = create_refresh_token("user-123")
    payload = decode_token(token)
    assert payload.token_type == "refresh"


def test_decode_invalid_token_raises():
    with pytest.raises(ValueError):
        decode_token("not-a-valid-token")
