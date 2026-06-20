from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ============================================================
# USERS
# ============================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = "doctor"
    full_name: Optional[str] = None
    crm: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    role: str
    full_name: Optional[str] = None
    crm: Optional[str] = None
    phone: Optional[str] = None
    two_fa_enabled: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    two_fa_enabled: Optional[bool] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ============================================================
# PATIENTS
# ============================================================

class PatientCreate(BaseModel):
    full_name: str = Field(min_length=1)
    cpf_hash: Optional[str] = None
    date_of_birth: Optional[date] = None
    contact_phone: Optional[str] = None


class PatientResponse(BaseModel):
    id: UUID
    full_name: str
    cpf_hash: Optional[str] = None
    date_of_birth: Optional[date] = None
    contact_phone: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    contact_phone: Optional[str] = None


# ============================================================
# MEDICAL EXAMS
# ============================================================

class ExamCreate(BaseModel):
    patient_id: UUID
    exam_type: str
    exam_date: date
    content_encrypted: bytes
    content_nonce: str
    content_tag: str
    google_doc_id: Optional[str] = None
    markdown_content_encrypted: Optional[bytes] = None


class ExamResponse(BaseModel):
    id: UUID
    patient_id: UUID
    exam_type: str
    exam_date: date
    content_nonce: str
    content_tag: str
    google_doc_id: Optional[str] = None
    uploaded_by: Optional[UUID] = None
    uploaded_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ExamListResponse(BaseModel):
    total: int
    exams: list[ExamResponse]


# ============================================================
# MEDICAL REPORTS
# ============================================================

class FindingItem(BaseModel):
    finding: str
    relevance: str
    confidence: float = Field(ge=0.0, le=1.0)


class AlertItem(BaseModel):
    severity: str  # low, medium, high
    message: str


class ReportContent(BaseModel):
    summary: str
    findings: list[FindingItem]
    alerts: list[AlertItem] = []
    recommendations: list[str] = []
    disclaimer: str


class ReportCreate(BaseModel):
    patient_id: UUID
    exams_markdown: str
    requesting_doctor_id: UUID


class ReportResponse(BaseModel):
    id: UUID
    patient_id: UUID
    requesting_doctor_id: UUID
    exams_used: list[UUID]
    report_format: str
    model_version: str
    model_confidence: Optional[float] = None
    generated_at: datetime
    expires_at: Optional[datetime] = None
    status: str
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class ReportDetailResponse(ReportResponse):
    content: Optional[ReportContent] = None


# ============================================================
# ADMIN PROCESS
# ============================================================

class AdminProcessRequest(BaseModel):
    action: str = "organize_documents"
    query: str
    patient_id: UUID


class AdminProcessResponse(BaseModel):
    status: str
    documents_found: int = 0
    documents_organized: dict = Field(default_factory=dict)
    markdown_reference: Optional[str] = None
    storage_url: Optional[str] = None


# ============================================================
# SPECIALIST REPORT
# ============================================================

class SpecialistRequest(BaseModel):
    patient_id: UUID
    exams_markdown: str
    requesting_doctor_id: UUID


class SpecialistResponse(BaseModel):
    status: str
    report_id: Optional[UUID] = None
    estimated_time: str = "3-5 minutes"


# ============================================================
# AUDIT LOG
# ============================================================

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    action_type: str
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    status: str
    error_message: Optional[str] = None
    ip_address: str
    user_agent: Optional[str] = None
    timestamp: datetime
    duration_ms: Optional[int] = None
    request_id: Optional[str] = None

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    total: int
    logs: list[AuditLogResponse]


# ============================================================
# ASYNC TASKS
# ============================================================

class TaskResponse(BaseModel):
    id: UUID
    task_type: str
    patient_id: Optional[UUID] = None
    status: str
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3

    model_config = {"from_attributes": True}


# ============================================================
# CONSENT
# ============================================================

class ConsentCreate(BaseModel):
    patient_id: UUID
    consent_type: str
    consent_text: str
    signed_at: datetime
    expires_at: Optional[datetime] = None
    signature_hash: Optional[str] = None


class ConsentResponse(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    consent_type: str
    consent_text: str
    signed_at: datetime
    expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    signature_hash: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# WHABA WEBHOOK
# ============================================================

class WhahaMessage(BaseModel):
    from_: str = Field(alias="from")
    body: str
    timestamp: int
    id: str
    media: Optional[list[dict]] = None


class WhahaWebhookPayload(BaseModel):
    messages: list[WhahaMessage]


class WebhookAckResponse(BaseModel):
    status: str = "queued"
    job_id: str
    estimated_time: str = "2-3 minutes"
