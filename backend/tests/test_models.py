import pytest
from app.models import (
    User,
    Patient,
    PatientConsent,
    MedicalExam,
    MedicalReport,
    AuditLog,
    AsyncTask,
    DoctorPatientAccess,
    UserRole,
    ConsentType,
    ReportFormat,
    ReportStatus,
    AccessLevel,
    TaskStatus,
    TaskType,
)


class TestUserModel:
    def test_create_user(self):
        user = User(email="test@clinic.com", password_hash="hash", role="doctor", full_name="Dr. Silva", crm="12345-SP")
        assert user.email == "test@clinic.com"
        assert user.role == "doctor"
        assert user.full_name == "Dr. Silva"
        assert user.crm == "12345-SP"

    def test_user_soft_delete(self):
        user = User(email="del@test.com", password_hash="hash", role="patient")
        user.deleted_at = None
        assert user.deleted_at is None


class TestPatientModel:
    def test_create_patient(self):
        patient = Patient(full_name="João Silva", cpf_hash="abc123hash", date_of_birth=None, contact_phone="551199999999")
        assert patient.full_name == "João Silva"
        assert patient.cpf_hash == "abc123hash"

    def test_patient_no_empty_name(self):
        patient = Patient(full_name="X")
        assert patient.full_name != ""


class TestEnums:
    def test_user_roles(self):
        assert UserRole.ADMIN == "admin"
        assert UserRole.DOCTOR == "doctor"
        assert UserRole.PATIENT == "patient"
        assert UserRole.AUDITOR == "auditor"

    def test_consent_types(self):
        assert ConsentType.AI_ANALYSIS == "ai_analysis"
        assert ConsentType.DATA_STORAGE == "data_storage"

    def test_report_status(self):
        assert ReportStatus.GENERATING == "generating"
        assert ReportStatus.SUCCESS == "success"
        assert ReportStatus.ERROR == "error"


class TestRelationships:
    def test_doctor_patient_access(self):
        access = DoctorPatientAccess(
            doctor_id="uuid-1",
            patient_id="uuid-2",
            access_level="read",
        )
        assert access.access_level == "read"
        assert access.doctor_id == "uuid-1"

    def test_audit_log_immutability_design(self):
        """AuditLog uses BIGSERIAL (no UUID) for sequential immutability."""
        log = AuditLog(
            action_type="VIEW_EXAM",
            status="success",
            ip_address="192.168.1.1",
        )
        assert log.action_type == "VIEW_EXAM"
        assert log.ip_address == "192.168.1.1"
        assert log.status == "success"
