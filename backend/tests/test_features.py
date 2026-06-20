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


class TestDoctorDashboard:
    def test_dashboard_without_token(self, _mock_db):
        response = client.get("/doctor/dashboard")
        assert response.status_code == 401


class TestPatientPortal:
    def test_patient_exams_without_token(self, _mock_db):
        response = client.get("/patient/pid123/exams")
        assert response.status_code == 401

    def test_patient_reports_without_token(self, _mock_db):
        response = client.get("/patient/pid123/reports")
        assert response.status_code == 401


class TestComparison:
    def test_list_comparisons_without_token(self, _mock_db):
        response = client.get("/comparison/pid123")
        assert response.status_code == 401

    def test_create_comparison_without_token(self, _mock_db):
        response = client.post("/comparison/create?patient_id=a&exam_before_id=b&exam_after_id=c")
        assert response.status_code == 401


class TestEHR:
    def test_ehr_export_to_fhir(self):
        from app.utils.ehr import export_report_to_fhir
        bundle = export_report_to_fhir(
            report_id="rep-1",
            patient_name="João Silva",
            doctor_name="Dr. Silva",
            summary="Paciente com exames normais",
            findings=[{"finding": "Hemoglobina normal", "relevance": "Dentro do esperado", "confidence": 0.95}],
            generated_at="2026-06-19T10:00:00Z",
        )
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "document"
        assert len(bundle["entry"]) == 2  # report + 1 finding

    def test_ehr_client_stub(self):
        from app.utils.ehr import EHRClient
        client = EHRClient(base_url="https://ehr.test.com/fhir")
        result = client.send_report({"entry": [{"resource": {"id": "1"}}]})
        assert result["status"] == "simulated"
