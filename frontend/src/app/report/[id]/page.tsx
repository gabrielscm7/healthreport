"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { MedicalReport } from "@/lib/types";

export default function ReportPage() {
  const params = useParams()!;
  const id = params.id as string;
  const router = useRouter();
  const [report, setReport] = useState<MedicalReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getReport(id).then((r) => { setReport(r); setLoading(false); }).catch(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="container"><div className="spinner" /></div>;
  if (!report) return <div className="container"><div className="empty-state"><p>Relatório não encontrado</p></div></div>;

  const c = report.content || { summary: "", findings: [], alerts: [], recommendations: [], disclaimer: "" };

  return (
    <div className="container" style={{ maxWidth: 800, margin: "0 auto" }}>
      <button className="btn btn-ghost" onClick={() => router.back()}>← Voltar</button>
      <div className="card" style={{ padding: 32, marginTop: 8 }}>
        <h1 style={{ fontSize: "1.25rem", marginBottom: 4 }}>Relatório de Apoio à Decisão Clínica</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: ".8rem", marginBottom: 24 }}>
          Gerado {new Date(report.generated_at).toLocaleString("pt-BR")} · {report.model_version} · Confiança {Math.round((report.model_confidence || 0) * 100)}%
        </p>

        <div style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: ".9rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".5px", marginBottom: 8 }}>Resumo</h3>
          <p>{c.summary || "Nenhum resumo disponível."}</p>
        </div>

        {c.findings.length > 0 && (
          <div style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: ".9rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".5px", marginBottom: 8 }}>Achados Relevantes</h3>
            {c.findings.map((f, i) => (
              <div key={i} className="finding-item">
                <strong>{f.finding}</strong><span className="confidence">{Math.round(f.confidence * 100)}% confiança</span>
                <p style={{ marginTop: 4, fontSize: ".875rem", color: "var(--text-secondary)" }}>{f.relevance}</p>
              </div>
            ))}
          </div>
        )}

        {c.alerts.length > 0 && (
          <div style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: ".9rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".5px", marginBottom: 8 }}>Alertas</h3>
            {c.alerts.map((a, i) => (
              <div key={i} className={`alert-item severity-${a.severity}`}><strong>{a.severity.toUpperCase()}:</strong> {a.message}</div>
            ))}
          </div>
        )}

        {c.recommendations.length > 0 && (
          <div style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: ".9rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: ".5px", marginBottom: 8 }}>Investigações Sugeridas</h3>
            <ul style={{ paddingLeft: 20 }}>{c.recommendations.map((r, i) => <li key={i} style={{ marginBottom: 4 }}>{r}</li>)}</ul>
          </div>
        )}

        <div className="report-disclaimer">
          <strong>⚠️ {c.disclaimer || "Ferramenta de apoio. Decisão médica é responsabilidade do médico."}</strong>
        </div>
      </div>
    </div>
  );
}
