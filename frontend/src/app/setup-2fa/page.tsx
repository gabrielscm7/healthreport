"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function Setup2FAPage() {
  const [enabled, setEnabled] = useState(false);
  const [qrUri, setQrUri] = useState("");
  const [secret, setSecret] = useState("");
  const [code, setCode] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.status2FA().then((s) => {
      setEnabled(s.two_fa_enabled);
      setLoading(false);
    });
  }, []);

  async function handleSetup() {
    const data = await api.setup2FA();
    setSecret(data.secret);
    setQrUri(data.qr_code_uri);
  }

  async function handleVerify() {
    try {
      await api.verify2FA(code);
      setMsg("✅ 2FA ativado com sucesso!");
      setEnabled(true);
    } catch (err: any) {
      setMsg(`❌ ${err.message}`);
    }
  }

  if (loading) return <div className="container"><div className="spinner" /></div>;

  return (
    <div className="container" style={{ maxWidth: 600, margin: "0 auto" }}>
      <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: 24 }}>Autenticação em duas etapas</h2>
      <div className="card" style={{ padding: 32 }}>
        {enabled ? (
          <>
            <p style={{ color: "var(--success)", fontWeight: 600, marginBottom: 16 }}>✅ 2FA está ativo</p>
            <p>Para desativar, contate o administrador.</p>
          </>
        ) : (
          <>
            <p style={{ marginBottom: 16 }}>❌ 2FA não está configurado.</p>
            {!qrUri ? (
              <button className="btn btn-primary" onClick={handleSetup}>Configurar 2FA</button>
            ) : (
              <>
                <div style={{ textAlign: "center", marginBottom: 16 }}>
                  <p style={{ fontSize: ".8rem", color: "var(--text-secondary)", marginBottom: 8 }}>Escaneie com Google Authenticator / Authy:</p>
                  <img src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(qrUri)}`} alt="QR Code" style={{ borderRadius: 8 }} />
                </div>
                <p style={{ fontFamily: "monospace", fontSize: ".8rem", textAlign: "center", color: "var(--text-secondary)", wordBreak: "break-all", marginBottom: 16 }}>Secret: {secret}</p>
                <div className="field">
                  <label>Código do autenticador</label>
                  <input type="text" value={code} onChange={(e) => setCode(e.target.value)} placeholder="000000" maxLength={6} />
                </div>
                <button className="btn btn-primary" onClick={handleVerify}>Verificar e ativar</button>
              </>
            )}
            {msg && <p className="msg-success" style={{ marginTop: 12 }}>{msg}</p>}
          </>
        )}
      </div>
    </div>
  );
}
