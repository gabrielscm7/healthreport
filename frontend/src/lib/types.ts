export type UserRole = "admin" | "doctor" | "patient" | "auditor";

export interface User {
  id: string;
  email: string;
  role: UserRole;
  full_name?: string;
  crm?: string;
  phone?: string;
  two_fa_enabled: boolean;
  created_at: string;
}

export interface Patient {
  id: string;
  full_name: string;
  cpf_hash?: string;
  date_of_birth?: string;
  contact_phone?: string;
  created_at: string;
}

export interface MedicalReport {
  id: string;
  patient_id: string;
  requesting_doctor_id: string;
  exams_used: string[];
  report_format: string;
  model_version: string;
  model_confidence?: number;
  generated_at: string;
  status: string;
  error_message?: string;
  content?: ReportContent;
}

export interface ReportContent {
  summary: string;
  findings: Array<{ finding: string; relevance: string; confidence: number }>;
  alerts: Array<{ severity: string; message: string }>;
  recommendations: string[];
  disclaimer: string;
}

export interface MedicalExam {
  id: string;
  patient_id: string;
  exam_type: string;
  exam_date: string;
  google_doc_id?: string;
  uploaded_at: string;
}

export interface AuditLog {
  id: number;
  user_id?: string;
  patient_id?: string;
  action_type: string;
  status: string;
  ip_address: string;
  timestamp: string;
}

export interface PatientConsent {
  id: string;
  patient_id: string;
  consent_type: string;
  consent_text: string;
  signed_at: string;
  expires_at?: string;
  signature_hash?: string;
}

export interface DashboardData {
  total_patients: number;
  total_reports: number;
  total_exams: number;
  recent_reports: any[];
  patients: Array<{
    patient_id: string;
    patient_name: string;
    reports_count: number;
    exams_count: number;
  }>;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface PaginatedResponse<T> {
  total: number;
  logs: T[];
}
