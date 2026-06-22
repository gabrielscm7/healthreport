"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AuditLog } from "@/lib/types";

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    const data = await api.getAuditLogs(filter ? { action_type: filter } : undefined);
    setLogs(data.logs);
    setTotal(data.total);
    setLoading(false);
  }

  useEffect(() => { load(); }, [filter]);

  return (
    <div className="container">
      <div className="page-header">
        <h2>Auditoria</h2>
        <div className="header-actions">
          <select className="search-input" style={{ maxWidth: 200 }} value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="">Todas ações</option>
            <option value="WEBHOOK_RECEIVED">Webhook</option>
            <option value="ORGANIZE_START">Organização</option>
            <option value="REPORT_REQUEST">Relatório</option>
            <option value="LOGIN">Login</option>
            <option value="CONSENT_CREATED">Consentimento</option>
          </select>
        </div>
      </div>

      {loading ? <div className="spinner" /> : logs.length === 0 ? (
        <div className="empty-state"><p>Nenhum registro de auditoria</p></div>
      ) : (
        <>
          <table>
            <thead><tr><th>Data/Hora</th><th>Ação</th><th>Status</th><th>IP</th></tr></thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id}>
                  <td style={{ whiteSpace: "nowrap" }}>{new Date(l.timestamp).toLocaleString("pt-BR")}</td>
                  <td><code style={{ fontSize: ".75rem" }}>{l.action_type}</code></td>
                  <td><span style={{ color: l.status === "success" ? "var(--success)" : "var(--danger)" }}>{l.status}</span></td>
                  <td>{l.ip_address}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ textAlign: "center", marginTop: 8, fontSize: ".8rem", color: "var(--text-secondary)" }}>{total} registros</p>
        </>
      )}
    </div>
  );
}
