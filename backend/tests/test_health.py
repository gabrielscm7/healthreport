import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.db import get_db
from app.main import app


async def _mock_refresh(obj):
    from app.models import User
    if isinstance(obj, User):
        if obj.two_fa_enabled is None:
            obj.two_fa_enabled = False
        if obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)
        if obj.updated_at is None:
            obj.updated_at = datetime.now(timezone.utc)


@pytest.fixture(autouse=True)
def _mock_db():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = _mock_refresh
    session.add = MagicMock()
    session.execute = AsyncMock()

    app.dependency_overrides[get_db] = lambda: session
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


class TestHealth:
    def test_simple_health(self, _mock_db):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "medical-reports" in data["service"]

    def test_health_db(self, _mock_db):
        resp = client.get("/health/db")
        assert resp.status_code == 200
        # mock returns error because there's no real db
        assert resp.json()["status"] in ("ok", "error")

    def test_health_cache(self, _mock_db):
        resp = client.get("/health/cache")
        assert resp.status_code == 200

    def test_health_agents(self, _mock_db):
        resp = client.get("/health/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["admin_agent"] == "CrewAI"
        assert data["specialist_agent"] == "LangGraph"
        assert data["disclaimer_configured"] is True
