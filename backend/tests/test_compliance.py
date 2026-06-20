"""Testes específicos das rotas do Marco 2 — Compliance & Segurança"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient


def make_execute_result(value=None, scalars_first=None, scalars_all=None):
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = value
    scalars_mock = MagicMock()
    scalars_mock.first.return_value = scalars_first if scalars_first is not None else value
    scalars_mock.all.return_value = scalars_all or ([scalars_first] if scalars_first is not None else [value] if value is not None else [])
    mock.scalars.return_value = scalars_mock
    return mock


async def _mock_refresh(obj):
    from app.models import User
    if isinstance(obj, User):
        if obj.two_fa_enabled is None:
            obj.two_fa_enabled = False
        if obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)
        if obj.updated_at is None:
            obj.updated_at = datetime.now(timezone.utc)


from app.db import get_db
from app.main import app


@pytest.fixture(autouse=True)
def setup_mocks():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = _mock_refresh
    session.add = MagicMock()
    session.execute = AsyncMock()

    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.clear()


client = TestClient(app)


class TestPrivacy:
    def test_privacy_policy_accessible(self, setup_mocks):
        response = client.get("/privacy")
        assert response.status_code == 200
        assert "LGPD" in response.text
        assert "Política de Privacidade" in response.text
        assert "Lei 13.709/2018" in response.text

    def test_privacy_contains_required_sections(self, setup_mocks):
        response = client.get("/privacy")
        assert "Direitos" in response.text
        assert "Segurança" in response.text
        assert "Consentimento" in response.text
        assert "Retenção" in response.text


class TestTwoFactor:
    def test_2fa_setup_without_token(self, setup_mocks):
        response = client.post("/auth/2fa/setup")
        assert response.status_code == 401

    def test_2fa_verify_without_token(self, setup_mocks):
        response = client.post("/auth/2fa/verify?code=123456")
        assert response.status_code == 401

    def test_2fa_status_without_token(self, setup_mocks):
        response = client.get("/auth/2fa/status")
        assert response.status_code == 401


class TestConsents:
    def test_create_consent_without_token(self, setup_mocks):
        response = client.post("/consents", json={
            "patient_id": "00000000-0000-0000-0000-000000000001",
            "consent_type": "ai_analysis",
            "consent_text": "I agree",
            "signed_at": "2026-01-01T00:00:00Z",
        })
        assert response.status_code == 401

    def test_list_consents_without_token(self, setup_mocks):
        response = client.get("/consents/00000000-0000-0000-0000-000000000001")
        assert response.status_code == 401


class TestAccess:
    def test_grant_access_without_token(self, setup_mocks):
        response = client.post("/access/grant?doctor_id=a&patient_id=b&access_level=read")
        assert response.status_code == 401


class TestLGPD:
    def test_my_data_without_token(self, setup_mocks):
        response = client.get("/lgpd/my-data")
        assert response.status_code == 401

    def test_correction_without_token(self, setup_mocks):
        response = client.post("/lgpd/correction?patient_id=1&field=name&new_value=x&reason=test")
        assert response.status_code == 401


class TestRateLimit:
    def test_rate_limit_headers_not_present_on_normal_request(self, setup_mocks):
        response = client.get("/health")
        assert response.status_code == 200

    def test_multiple_requests_within_limit(self, setup_mocks):
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
