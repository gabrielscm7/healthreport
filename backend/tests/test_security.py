import pytest
from app.security import hash_password, verify_password, create_access_token, decode_access_token


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("mysecret")
        assert verify_password("mysecret", hashed)
        assert not verify_password("wrong", hashed)

    def test_hash_is_unique(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


class TestJWT:
    def test_roundtrip(self):
        token = create_access_token({"sub": "user-id", "role": "doctor"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user-id"
        assert payload["role"] == "doctor"

    def test_invalid_token(self):
        assert decode_access_token("invalid.token.here") is None

    def test_expiration_in_token(self):
        token = create_access_token({"sub": "user-id"})
        payload = decode_access_token(token)
        assert payload is not None
        assert "exp" in payload
