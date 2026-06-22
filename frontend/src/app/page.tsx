"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totp, setTotp] = useState("");
  const [showTotp, setShowTotp] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api.login(email, password, totp || undefined);
      localStorage.setItem("token", data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      if (err.message.includes("2FA code required")) {
        setShowTotp(true);
        setError("Código 2FA obrigatório");
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", background: "linear-gradient(135deg, #eff6ff 0%, #f5f7fa 100%)", padding: 24 }}>
      <div className="card" style={{ padding: 40, width: "100%", maxWidth: 420 }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ fontSize: "2.5rem", marginBottom: 8 }}>📋</div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700 }}>Medical Reports</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: ".875rem", marginTop: 4 }}>Sistema de Apoio à Decisão Clínica</p>
        </div>
        <form onSubmit={handleLogin}>
          <div className="field">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="medico@clinic.com" required />
          </div>
          <div className="field">
            <label>Senha</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required />
          </div>
          {showTotp && (
            <div className="field">
              <label>Código 2FA</label>
              <input type="text" value={totp} onChange={(e) => setTotp(e.target.value)} placeholder="000000" maxLength={6} />
            </div>
          )}
          {error && <div className="msg-error">{error}</div>}
          <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: "100%", marginTop: 8 }}>
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  );
}
