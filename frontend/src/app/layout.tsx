"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      if (pathname !== "/") router.push("/");
      setLoading(false);
      return;
    }
    api.me()
      .then((u) => { setUser(u); setLoading(false); })
      .catch(() => { localStorage.removeItem("token"); router.push("/"); setLoading(false); });
  }, [pathname]);

  if (loading) return <html><body style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}><div className="spinner" /></body></html>;

  return (
    <html lang="pt-BR">
      <head><meta name="viewport" content="width=device-width, initial-scale=1" /><title>Medical Reports</title></head>
      <body>
        {user && (
          <header style={{ background: "var(--surface)", borderBottom: "1px solid var(--border)", position: "sticky", top: 0, zIndex: 100 }}>
            <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px", height: 56, display: "flex", alignItems: "center", gap: 24 }}>
              <span style={{ fontWeight: 600, color: "var(--primary)" }}>📋 Medical Reports</span>
              <nav style={{ display: "flex", gap: 8, flex: 1 }}>
                <a href="/dashboard" className="btn-ghost">Pacientes</a>
                <a href="/audit" className="btn-ghost">Auditoria</a>
                <a href="/setup-2fa" className="btn-ghost">2FA</a>
              </nav>
              <span style={{ fontSize: ".875rem", color: "var(--text-secondary)", background: "var(--bg)", padding: "4px 12px", borderRadius: 8 }}>{user.full_name || user.email}</span>
              <button className="btn-ghost" onClick={() => { localStorage.removeItem("token"); router.push("/"); }}>Sair</button>
            </div>
          </header>
        )}
        <main style={{ padding: "32px 0" }}>{children}</main>
      </body>
    </html>
  );
}
