"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Patient, MedicalExam, MedicalReport, PatientConsent } from "@/lib/types";

type Tab = "exams" | "reports" | "consents";

export default function PatientPage() {
  const params = useParams()!;
  const id = params.id as string;
  const router = useRouter();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [tab, setTab] = useState<Tab>("exams");
  const [exams, setExams] = useState<MedicalExam[]>([]);
  const [reports, setReports] = useState<MedicalReport[]>([]);
  const [consents, setConsents] = useState<PatientConsent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getPatient(id).then(setPatient);
    Promise.all([
      api.patientExams(id).then(setExams),
      api.patientReports(id).then(setReports),
      api.listConsents(id).then(setConsents),
    ]).finally(() => setLoading(false));
  }, [id]);

  if (loading && !patient) return <div className="container"><div className="spinner" /></div>;
  if (!patient) return <div className="container"><div className="empty-state"><p>Paciente não encontrado</p></div></div>;

  return (
    <div className="container">
      <button className="btn btn-ghost" onClick={() => router.push("/dashboard")}>← Voltar</button>
      <h2 style={{ margin: "4px 0" }}>{patient.full_name}</h2>
      <p style={{ color: "var(--text-secondary)", fontSize: ".875rem", marginBottom: 24 }}>{patient.contact_phone || ""}</p>

      <div className="tabs">
        {(["exams", "reports", "consents"] as Tab[]).map((t) => (
          <button key={t} className={`tab ${tab === t ? "active" : ""}`} onClick={() => setTab(t)}>
            {t === "exams" ? "Exames" : t === "reports" ? "Relatórios" : "Consentimentos"}
          </button>
        ))}
      </div>

      {tab === "exams" && (
        <div className="card-list">
          {exams.length === 0 ? <div className="empty-state"><p>Nenhum exame cadastrado</p></div>
          : exams.map((e) => (
            <div key={e.id} className="card-item">
              <div><div className="card-name">{e.exam_type}</div><div className="card-meta">{e.exam_date}</div></div>
              <span className="card-badge">Upload realizado</span>
            </div>
          ))}
        </div>
      )}

      {tab === "reports" && (
        <div className="card-list">
          {reports.length === 0 ? <div className="empty-state"><p>Nenhum relatório gerado</p></div>
          : reports.map((r) => (
            <div key={r.id} className="card-item" onClick={() => router.push(`/report/${r.id}`)}>
              <div>
                <div className="card-name">Relatório · {r.model_version}</div>
                <div className="card-meta">{new Date(r.generated_at).toLocaleString("pt-BR")} · {r.status}</div>
              </div>
              <span className="card-badge">{r.status}</span>
            </div>
          ))}
        </div>
      )}

      {tab === "consents" && (
        <div className="card-list">
          {consents.length === 0 ? <div className="empty-state"><p>Nenhum consentimento registrado</p></div>
          : consents.map((c) => (
            <div key={c.id} className="card-item">
              <div>
                <div className="card-name">{c.consent_type.replace(/_/g, " ")}</div>
                <div className="card-meta">Assinado {new Date(c.signed_at).toLocaleString("pt-BR")}</div>
              </div>
              <span className="card-badge">Ativo</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
