// ============================================================
// ENUMS — mesmos valores do backend (models.py)
// ============================================================

export type UserRole = "admin" | "doctor" | "patient" | "auditor";

export type ConsentType = "ai_analysis" | "data_storage" | "research";

export type ReportFormat = "json" | "pdf" | "markdown";

export type ReportStatus = "generating" | "success" | "error";

export type AccessLevel = "read" | "write" | "full";

export type TaskStatus = "pending" | "processing" | "completed" | "failed";

export type TaskType = "organize_exams" | "generate_report";

export type AuditAction =
  | "VIEW_EXAM"
  | "CREATE_REPORT"
  | "DOWNLOAD"
  | "EXPORT"
  | "DELETE"
  | "LOGIN"
  | "WEBHOOK_RECEIVED"
  | "ORGANIZE_START"
  | "ORGANIZE_SUCCESS"
  | "ORGANIZE_ERROR"
  | "REPORT_REQUEST"
  | "REPORT_SUCCESS"
  | "REPORT_ERROR"
  | "WHATSAPP_SENT";

// ============================================================
// MODELS
// ============================================================

export interface User {
  id: string; // UUID
  email: string;
  password_hash: string;
  role: UserRole;
  full_name?: string;
  crm?: string;
  phone?: string;
  two_fa_enabled: boolean;
  two_fa_secret?: string;
  created_at: string; // ISO 8601
  updated_at: string;
  deleted_at?: string | null;
}

export interface Patient {
  id: string;
  full_name: string;
  cpf_hash?: string;
  date_of_birth?: string; // ISO date
  contact_phone?: string;
  created_at: string;
}

export interface PatientConsent {
  id: string;
  patient_id: string;
  doctor_id: string;
  consent_type: ConsentType;
  consent_text: string;
  signed_at: string;
  expires_at?: string | null;
  ip_address?: string;
  user_agent?: string;
  signature_hash?: string;
  created_at: string;
}

export interface MedicalExam {
  id: string;
  patient_id: string;
  exam_type: string;
  exam_date: string;
  content_encrypted: string; // base64 BYTEA
  content_nonce: string;
  content_tag: string;
  google_doc_id?: string;
  markdown_content_encrypted?: string;
  uploaded_by?: string;
  uploaded_at: string;
  deleted_at?: string | null;
}

export interface MedicalReport {
  id: string;
  patient_id: string;
  requesting_doctor_id: string;
  exams_used: string[]; // UUID[]
  report_content_encrypted: string;
  report_nonce: string;
  report_tag: string;
  report_format: ReportFormat;
  model_version: string;
  model_confidence?: number;
  generated_at: string;
  expires_at?: string | null;
  status: ReportStatus;
  error_message?: string;
}

export interface AuditLog {
  id: number; // BIGSERIAL
  user_id?: string;
  patient_id?: string;
  action_type: string;
  resource_type?: string;
  resource_id?: string;
  status: string;
  error_message?: string;
  ip_address: string;
  user_agent?: string;
  timestamp: string;
  duration_ms?: number;
  request_id?: string;
  created_at: string;
}

export interface AsyncTask {
  id: string;
  task_type: TaskType;
  patient_id?: string;
  status: TaskStatus;
  input_data?: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  error_message?: string;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  retry_count: number;
  max_retries: number;
}

export interface DoctorPatientAccess {
  id: string;
  doctor_id: string;
  patient_id: string;
  access_level: AccessLevel;
  access_granted_at: string;
  access_revoked_at?: string | null;
  granted_by?: string;
}

// ============================================================
// REQUEST / RESPONSE DTOS
// ============================================================

export interface LoginRequest {
  email: string;
  password: string;
  totp_code?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  user: User;
}

export interface WebhookPayload {
  messages: Array<{
    from: string;
    body: string;
    timestamp: number;
    id: string;
    media?: Array<{ url: string; type: string }>;
  }>;
}

export interface WebhookAckResponse {
  status: "queued";
  job_id: string;
  estimated_time: string;
}

export interface ReportContent {
  summary: string;
  findings: Array<{
    finding: string;
    relevance: string;
    confidence: number;
  }>;
  alerts: Array<{
    severity: "low" | "medium" | "high";
    message: string;
  }>;
  recommendations: string[];
  disclaimer: string;
}

export interface AuditLogQuery {
  patient_id?: string;
  user_id?: string;
  action_type?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}

export interface PaginatedResponse<T> {
  total: number;
  items: T[];
}
