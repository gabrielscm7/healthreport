"use client";

import { useEffect, useState } from "react";
import {
  MedicalReport,
  MedicalExam,
  Patient,
  AuditLog,
  PatientConsent,
  DoctorPatientAccess,
  LoginResponse,
  ReportContent,
  PaginatedResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// ============================================================
// AUTH
// ============================================================

export async function login(
  email: string,
  password: string,
  totpCode?: string
): Promise<LoginResponse> {
  const data = await request<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password, totp_code: totpCode }),
  });
  if (typeof window !== "undefined") {
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
  }
  return data;
}

export async function register(
  email: string,
  password: string,
  role: string,
  fullName?: string,
  crm?: string
): Promise<Patient> {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, role, full_name: fullName, crm }),
  });
}

export async function getMe(): Promise<Patient> {
  return request("/auth/me");
}

// ============================================================
// 2FA
// ============================================================

export async function setup2FA(): Promise<{ secret: string; qr_code_uri: string }> {
  return request("/auth/2fa/setup", { method: "POST" });
}

export async function verify2FA(code: string): Promise<{ status: string }> {
  return request(`/auth/2fa/verify?code=${code}`, { method: "POST" });
}

export async function disable2FA(code: string): Promise<{ status: string }> {
  return request(`/auth/2fa/disable?code=${code}`, { method: "POST" });
}

export async function get2FAStatus(): Promise<{ two_fa_enabled: boolean }> {
  return request("/auth/2fa/status");
}

// ============================================================
// PATIENTS
// ============================================================

export async function listPatients(search?: string): Promise<Patient[]> {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return request(`/patients${query}`);
}

export async function getPatient(id: string): Promise<Patient> {
  return request(`/patients/${id}`);
}

export async function createPatient(data: {
  full_name: string;
  cpf_hash?: string;
  date_of_birth?: string;
  contact_phone?: string;
}): Promise<Patient> {
  return request("/patients", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ============================================================
// EXAMINATIONS & REPORTS
// ============================================================

export async function listPatientExams(patientId: string): Promise<MedicalExam[]> {
  return request(`/patient/${patientId}/exams`);
}

export async function listPatientReports(patientId: string): Promise<MedicalReport[]> {
  return request(`/patient/${patientId}/reports`);
}

export async function getReport(reportId: string): Promise<MedicalReport> {
  return request(`/specialist/report/${reportId}`);
}

export async function listReports(patientId: string): Promise<MedicalReport[]> {
  return request(`/specialist/reports/${patientId}`);
}

// ============================================================
// AUDIT
// ============================================================

export async function getAuditLogs(
  params: {
    patient_id?: string;
    user_id?: string;
    action_type?: string;
    limit?: number;
    offset?: number;
  } = {}
): Promise<PaginatedResponse<AuditLog>> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined) query.set(k, String(v));
  });
  return request(`/audit/logs?${query.toString()}`);
}

// ============================================================
// CONSENTS
// ============================================================

export async function createConsent(data: {
  patient_id: string;
  consent_type: string;
  consent_text: string;
  signed_at: string;
  expires_at?: string;
  signature_hash?: string;
}): Promise<PatientConsent> {
  return request("/consents", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listConsents(patientId: string): Promise<PatientConsent[]> {
  return request(`/consents/${patientId}`);
}

export async function listActiveConsents(patientId: string): Promise<PatientConsent[]> {
  return request(`/consents/${patientId}/active`);
}

export async function revokeConsent(consentId: string): Promise<void> {
  await request(`/consents/${consentId}`, { method: "DELETE" });
}

// ============================================================
// ACCESS (RBAC)
// ============================================================

export async function grantAccess(
  doctorId: string,
  patientId: string,
  accessLevel: string = "read"
): Promise<{ status: string }> {
  return request(
    `/access/grant?doctor_id=${doctorId}&patient_id=${patientId}&access_level=${accessLevel}`,
    { method: "POST" }
  );
}

export async function revokeAccess(
  doctorId: string,
  patientId: string
): Promise<{ status: string }> {
  return request(
    `/access/revoke?doctor_id=${doctorId}&patient_id=${patientId}`,
    { method: "POST" }
  );
}

// ============================================================
// DOCTOR DASHBOARD
// ============================================================

export async function getDoctorDashboard(): Promise<{
  total_patients: number;
  total_reports: number;
  total_exams: number;
  recent_reports: any[];
  patients: any[];
}> {
  return request("/doctor/dashboard");
}

// ============================================================
// COMPARISON
// ============================================================

export async function compareExams(
  patientId: string,
  examBeforeId: string,
  examAfterId: string
): Promise<{ comparison_id: string; differences: any }> {
  return request(
    `/comparison/create?patient_id=${patientId}&exam_before_id=${examBeforeId}&exam_after_id=${examAfterId}`,
    { method: "POST" }
  );
}

export async function listComparisons(patientId: string): Promise<any[]> {
  return request(`/comparison/${patientId}`);
}

// ============================================================
// WEBHOOK (admin)
// ============================================================

export async function organizeExams(
  query: string,
  patientId: string
): Promise<{ status: string }> {
  return request("/admin/process", {
    method: "POST",
    body: JSON.stringify({ action: "organize_documents", query, patient_id: patientId }),
  });
}

export async function generateReport(
  patientId: string,
  examsMarkdown: string,
  doctorId: string
): Promise<{ status: string; report_id?: string }> {
  return request("/specialist/report", {
    method: "POST",
    body: JSON.stringify({
      patient_id: patientId,
      exams_markdown: examsMarkdown,
      requesting_doctor_id: doctorId,
    }),
  });
}

// ============================================================
// LGPD
// ============================================================

export async function exportMyData(): Promise<any> {
  return request("/lgpd/my-data");
}

export async function requestCorrection(
  patientId: string,
  field: string,
  newValue: string,
  reason: string
): Promise<{ status: string }> {
  return request(
    `/lgpd/correction?patient_id=${patientId}&field=${field}&new_value=${encodeURIComponent(newValue)}&reason=${encodeURIComponent(reason)}`,
    { method: "POST" }
  );
}

export async function requestDeletion(
  patientId: string
): Promise<{ status: string }> {
  return request(`/lgpd/my-data?patient_id=${patientId}`, { method: "DELETE" });
}
