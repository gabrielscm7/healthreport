import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient


def make_execute_result(value=None, scalars_first=None, scalars_all=None):
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = value

    scalars_mock = MagicMock()
    scalars_mock.first.return_value = (
        scalars_first if scalars_first is not None else value
    )
    scalars_mock.all.return_value = scalars_all or (
        [scalars_first]
        if scalars_first is not None
        else [value]
        if value is not None
        else []
    )
    mock.scalars.return_value = scalars_mock
    return mock


async def _mock_refresh(obj):
    """Simula db.refresh populando campos que o banco preencheria."""
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


class TestHealth:
    def test_health_check(self, setup_mocks):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestAuth:
    def test_login_invalid_credentials(self, setup_mocks):
        setup_mocks.execute.return_value = make_execute_result(None)

        response = client.post(
            "/auth/login", json={"email": "x@x.com", "password": "wrong"}
        )
        assert response.status_code == 401

    def test_register_missing_fields(self, setup_mocks):
        response = client.post("/auth/register", json={"email": "x@x.com"})
        assert response.status_code == 422

    def test_register_valid(self, setup_mocks):
        setup_mocks.execute.return_value = make_execute_result(None)

        response = client.post(
            "/auth/register",
            json={
                "email": "doctor@clinic.com",
                "password": "securepass123",
                "role": "doctor",
                "full_name": "Dr. Test",
                "crm": "99999-SP",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "doctor@clinic.com"
        assert data["role"] == "doctor"

    def test_get_me_without_token(self, setup_mocks):
        response = client.get("/auth/me")
        assert response.status_code == 401


class TestPatients:
    def test_list_patients_without_token(self, setup_mocks):
        response = client.get("/patients")
        assert response.status_code == 401

    def test_get_patient_not_found(self, setup_mocks):
        response = client.get("/patients/nonexistent-id")
        assert response.status_code == 401


class TestWebhook:
    def test_webhook_no_signature(self, setup_mocks):
        setup_mocks.execute.return_value = make_execute_result(None)

        response = client.post(
            "/webhook/whatsapp",
            json={
                "messages": [
                    {
                        "from": "551199999999",
                        "body": "hello",
                        "timestamp": 123,
                        "id": "m1",
                    }
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "job_id" in data

    def test_webhook_empty_messages(self, setup_mocks):
        response = client.post("/webhook/whatsapp", json={"messages": []})
        assert response.status_code == 200
        assert response.json()["job_id"] == "empty"

    def test_webhook_organize_command(self, setup_mocks):
        setup_mocks.execute.return_value = make_execute_result(None)

        response = client.post(
            "/webhook/whatsapp",
            json={
                "messages": [
                    {
                        "from": "551199999999",
                        "body": "Organize exames de João Silva",
                        "timestamp": 123,
                        "id": "m2",
                    }
                ]
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "queued"


class TestAudit:
    def test_audit_logs_without_token(self, setup_mocks):
        response = client.get("/audit/logs")
        assert response.status_code == 401


class TestAdmin:
    def test_admin_process_without_token(self, setup_mocks):
        response = client.post(
            "/admin/process",
            json={
                "action": "organize_documents",
                "query": "João",
                "patient_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        assert response.status_code == 401


class TestSpecialist:
    def test_specialist_report_without_token(self, setup_mocks):
        response = client.post(
            "/specialist/report",
            json={
                "patient_id": "00000000-0000-0000-0000-000000000001",
                "exams_markdown": "# Test",
                "requesting_doctor_id": "00000000-0000-0000-0000-000000000002",
            },
        )
        assert response.status_code == 401
