import type { LoginResponse, Patient, MedicalExam, MedicalReport, AuditLog, PatientConsent, DashboardData, User } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (res.status === 204) return null as T;
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

export const api = {
  login: (email: string, password: string, totpCode?: string) =>
    request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password, totp_code: totpCode }),
    }),

  register: (email: string, password: string, role: string, full_name?: string, crm?: string) =>
    request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, role, full_name, crm }),
    }),

  me: () => request<User>("/auth/me"),

  setup2FA: () => request<{ secret: string; qr_code_uri: string }>("/auth/2fa/setup", { method: "POST" }),
  verify2FA: (code: string) => request<{ status: string }>(`/auth/2fa/verify?code=${code}`, { method: "POST" }),
  status2FA: () => request<{ two_fa_enabled: boolean }>("/auth/2fa/status"),

  listPatients: (search?: string) =>
    request<Patient[]>(`/patients${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  getPatient: (id: string) => request<Patient>(`/patients/${id}`),
  createPatient: (data: { full_name: string; contact_phone?: string }) =>
    request<Patient>("/patients", { method: "POST", body: JSON.stringify(data) }),

  patientExams: (pid: string) => request<MedicalExam[]>(`/patient/${pid}/exams`),
  patientReports: (pid: string) => request<MedicalReport[]>(`/patient/${pid}/reports`),
  getReport: (rid: string) => request<MedicalReport>(`/specialist/report/${rid}`),

  getAuditLogs: (params?: Record<string, string>) => {
    const q = new URLSearchParams(params || {});
    return request<{ logs: AuditLog[]; total: number }>(`/audit/logs?${q.toString()}&limit=50`);
  },

  listConsents: (pid: string) => request<PatientConsent[]>(`/consents/${pid}`),
  createConsent: (data: { patient_id: string; consent_type: string; consent_text: string; signed_at: string }) =>
    request<PatientConsent>("/consents", { method: "POST", body: JSON.stringify(data) }),

  doctorDashboard: () => request<DashboardData>("/doctor/dashboard"),
};
