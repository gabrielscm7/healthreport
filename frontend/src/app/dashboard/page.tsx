"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Patient, DashboardData } from "@/lib/types";

export default function DashboardPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    Promise.all([
      api.listPatients(),
      api.doctorDashboard().catch(() => null),
    ]).then(([p, d]) => {
      setPatients(p);
      setDashboard(d);
      setLoading(false);
    });
  }, []);

  async function handleSearch(val: string) {
    setSearch(val);
    const p = await api.listPatients(val || undefined);
    setPatients(p);
  }

  if (loading) return <div className="container"><div className="spinner" /></div>;

  return (
    <div className="container">
      <div className="page-header">
        <h2>Pacientes</h2>
        <div className="header-actions">
          <input className="search-input" placeholder="Buscar paciente..." value={search} onChange={(e) => handleSearch(e.target.value)} />
        </div>
      </div>

      {dashboard && (
        <div className="stats-row">
          <div className="stat-card"><div className="stat-value">{dashboard.total_patients}</div><div className="stat-label">Pacientes</div></div>
          <div className="stat-card"><div className="stat-value">{dashboard.total_exams}</div><div className="stat-label">Exames</div></div>
          <div className="stat-card"><div className="stat-value">{dashboard.total_reports}</div><div className="stat-label">Relatórios</div></div>
        </div>
      )}

      <div className="card-list">
        {patients.length === 0 ? (
          <div className="empty-state"><div className="empty-icon">👤</div><p>Nenhum paciente encontrado</p></div>
        ) : patients.map((p) => (
          <div key={p.id} className="card-item" onClick={() => router.push(`/patient/${p.id}`)}>
            <div>
              <div className="card-name">{p.full_name}</div>
              <div className="card-meta">{p.contact_phone || "Sem telefone"}</div>
            </div>
            <span className="card-badge">ver detalhes</span>
          </div>
        ))}
      </div>
    </div>
  );
}
