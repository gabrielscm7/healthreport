import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Integer, Float,
    Text, ForeignKey, UniqueConstraint, Index, CheckConstraint,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB, ARRAY, BYTEA, BIGINT
from sqlalchemy.orm import relationship

from app.db import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# ENUMS
# ---------------------------------------------------------------------------

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"
    AUDITOR = "auditor"


class ConsentType(str, enum.Enum):
    AI_ANALYSIS = "ai_analysis"
    DATA_STORAGE = "data_storage"
    RESEARCH = "research"


class ReportFormat(str, enum.Enum):
    JSON = "json"
    PDF = "pdf"
    MARKDOWN = "markdown"


class ReportStatus(str, enum.Enum):
    GENERATING = "generating"
    SUCCESS = "success"
    ERROR = "error"


class AccessLevel(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    FULL = "full"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(str, enum.Enum):
    ORGANIZE_EXAMS = "organize_exams"
    GENERATE_REPORT = "generate_report"


# ---------------------------------------------------------------------------
# MODELS
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False)
    full_name = Column(String(255))
    crm = Column(String(20))
    phone = Column(String(20))
    two_fa_enabled = Column(Boolean, default=False)
    two_fa_secret = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_crm", "crm"),
    )


class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    cpf_hash = Column(String(255), unique=True)
    date_of_birth = Column(Date)
    contact_phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_patients_cpf_hash", "cpf_hash"),
        CheckConstraint("full_name != ''", name="no_plain_text"),
    )


class PatientConsent(Base):
    __tablename__ = "patient_consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    consent_type = Column(SAEnum(ConsentType), nullable=False)
    consent_text = Column(Text, nullable=False)
    signed_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime)
    ip_address = Column(INET)
    user_agent = Column(Text)
    signature_hash = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_consents_patient", "patient_id"),
        Index("idx_consents_expiry", "expires_at"),
        CheckConstraint("signed_at IS NOT NULL", name="consent_must_be_explicit"),
    )


class MedicalExam(Base):
    __tablename__ = "medical_exams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    exam_type = Column(String(100), nullable=False)
    exam_date = Column(Date, nullable=False)
    content_encrypted = Column(BYTEA, nullable=False)
    content_nonce = Column(String(255), nullable=False)
    content_tag = Column(String(255), nullable=False)
    google_doc_id = Column(String(255))
    markdown_content_encrypted = Column(BYTEA)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_exams_patient", "patient_id"),
        Index("idx_exams_date", "exam_date"),
    )


class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    requesting_doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exams_used = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    report_content_encrypted = Column(BYTEA, nullable=False)
    report_nonce = Column(String(255), nullable=False)
    report_tag = Column(String(255), nullable=False)
    report_format = Column(SAEnum(ReportFormat), default=ReportFormat.JSON)
    model_version = Column(String(50), nullable=False)
    model_confidence = Column(Float)
    generated_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    status = Column(SAEnum(ReportStatus), default=ReportStatus.GENERATING)
    error_message = Column(Text)

    __table_args__ = (
        Index("idx_reports_patient", "patient_id"),
        Index("idx_reports_doctor", "requesting_doctor_id"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    action_type = Column(String(50), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(UUID(as_uuid=True))
    status = Column(String(20), nullable=False)
    error_message = Column(Text)
    ip_address = Column(INET, nullable=False)
    user_agent = Column(Text)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    duration_ms = Column(Integer)
    request_id = Column(String(255))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_audit_patient", "patient_id"),
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_action", "action_type"),
    )


class AsyncTask(Base):
    __tablename__ = "async_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_type = Column(String(100), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    status = Column(String(20), default="pending")
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    __table_args__ = (
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_patient", "patient_id"),
    )


class ExamComparison(Base):
    __tablename__ = "exam_comparisons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    exam_before_id = Column(UUID(as_uuid=True), ForeignKey("medical_exams.id"), nullable=False)
    exam_after_id = Column(UUID(as_uuid=True), ForeignKey("medical_exams.id"), nullable=False)
    comparison_result_encrypted = Column(BYTEA)
    comparison_nonce = Column(String(255))
    comparison_tag = Column(String(255))
    differences = Column(JSONB)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_comparisons_patient", "patient_id"),
    )


class DoctorPatientAccess(Base):
    __tablename__ = "doctor_patient_access"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    access_level = Column(String(50), nullable=False)
    access_granted_at = Column(DateTime, default=datetime.utcnow)
    access_revoked_at = Column(DateTime, nullable=True)
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    __table_args__ = (
        UniqueConstraint("doctor_id", "patient_id"),
        Index("idx_access_doctor", "doctor_id"),
        Index("idx_access_patient", "patient_id"),
    )
