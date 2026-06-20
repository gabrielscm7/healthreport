# Go-Live Checklist — Medical Reports API

**Data:** _______  
**Responsável:** _______  
**Aprovado por:** _______

---

## 1. Infraestrutura

- [ ] **Railway services rodando**
  - [ ] FastAPI (3 réplicas)
  - [ ] PostgreSQL 15 (managed)
  - [ ] Redis 7 (managed)
  - [ ] Volumes (exams_storage + backups)
- [ ] **Domínio configurado**
  - [ ] api.medicalreports.app → Railway
  - [ ] SSL válido (Railway auto)
  - [ ] HSTS habilitado
- [ ] **Variáveis de ambiente**
  - [ ] `SECRET_KEY` gerada (`python -c 'import secrets; print(secrets.token_urlsafe(32))'`)
  - [ ] `DATABASE_URL` apontando para produção
  - [ ] `REDIS_URL` apontando para produção
  - [ ] `WHAHA_TOKEN` e `WHAHA_WEBHOOK_SECRET` configurados
  - [ ] `ANTHROPIC_API_KEY` configurada
  - [ ] `ENCRYPTION_KEY` gerada (32 bytes)
  - [ ] `SENTRY_DSN` configurado
  - [ ] `GOOGLE_CREDENTIALS_JSON` configurado (service account)
  - [ ] `DEBUG=0` e `LOG_LEVEL=INFO`
- [ ] **IP whitelist** configurada (opcional, por clínica)

---

## 2. Banco de Dados

- [ ] Migration aplicada: `alembic upgrade head`
- [ ] Índices criados (16 índices do schema)
- [ ] RLS policies habilitadas no `audit_logs`
- [ ] Backup automático configurado e testado
- [ ] Conexão SSL/TLS forçada no PostgreSQL
- [ ] Conexões pool configurado (pool_size=10, max_overflow=20)

---

## 3. Segurança

- [ ] **Criptografia AES-256-GCM** ativa
- [ ] **JWT** com expiração configurada (60 min access, 7 dias refresh)
- [ ] **RBAC** testado (admin, doctor, patient, auditor)
- [ ] **2FA (TOTP)** funcional para médicos
- [ ] **Rate limiting** ativo (100 req/min)
- [ ] **Audit log imutável** — policies testadas
- [ ] **Consentimento** validado em cada requisição
- [ ] **CORS** restrito a domínios da clínica
- [ ] **Input sanitization** ativo

---

## 4. Dependências Externas

- [ ] **Whaha API**
  - [ ] Webhook configurado: `POST https://api.medicalreports.app/webhook/whatsapp`
  - [ ] Secret HMAC compartilhado
  - [ ] Teste de envio/recebimento OK
- [ ] **Anthropic Claude API**
  - [ ] Chave ativa e com crédito
  - [ ] Modelos disponíveis: Haiku 4.5 + Opus 4.6
  - [ ] Rate limits compatíveis com throughput esperado
- [ ] **Google Workspace**
  - [ ] Service account criada
  - [ ] Escopos concedidos (Drive, Docs)
  - [ ] Teste de busca e leitura OK

---

## 5. Compliance

- [ ] **Política de privacidade** publicada em `GET /privacy`
- [ ] **Termo de consentimento** versionado e assinado
- [ ] **LGPD disclosure** enviado aos pacientes
- [ ] **DPO** contato disponível: dpo@medicalreports.app
- [ ] **Período de retenção** configurado (7 anos)
- [ ] **Incident Response Plan** documentado

---

## 6. Monitoramento

- [ ] **Sentry**
  - [ ] DSN configurado
  - [ ] Alertas para erro rate > 5%
  - [ ] Release tracking ativo
- [ ] **Railway Dashboard**
  - [ ] CPU alert > 80%
  - [ ] Memória alert > 85%
  - [ ] Latência p99 > 500ms alert
  - [ ] Erro rate > 5% alert
- [ ] **Health checks** configurados
  - [ ] `GET /health` (a cada 30s)
  - [ ] `GET /health/db`
  - [ ] `GET /health/cache`
  - [ ] `GET /health/agents`

---

## 7. Testes

- [ ] **Unit tests**: `pytest tests/ -v` (46 testes)
- [ ] **Teste de carga**: `locust -f tests/load/locustfile.py`
  - [ ] 100 req/min sustentados
  - [ ] Webhook ACK < 500ms p99
  - [ ] Relatório < 3 min
- [ ] **Penetration test** (OWASP Top 10)
  - [ ] SQL injection
  - [ ] XSS
  - [ ] JWT tampering
  - [ ] Broken access control
- [ ] **Teste de rollback** verificado

---

## 8. Go-Live

- [ ] **Horário agendado** (recomendado: domingo 02:00 UTC)
- [ ] **Médicos treinados** (1h de treinamento)
- [ ] **Material de suporte** enviado
- [ ] **Canal de suporte** ativo
- [ ] **Rollback testado** (reverse migration + dump restore)
- [ ] **Todos presentes** no call de go-live

---

## 9. Pós-Go-Live (24h)

- [ ] Monitorar logs de erro (Sentry)
- [ ] Verificar latência (Railway dashboard)
- [ ] Confirmar backups automáticos rodando
- [ ] Validar primeiro relatório gerado
- [ ] Coletar feedback do médico piloto
- [ ] Revisar métricas de sucesso

---

## 10. Assinaturas

| Papel | Nome | Data | Assinatura |
|-------|------|------|------------|
| Tech Lead | | | |
| Product Manager | Gabriel Menezes | | |
| Legal (LGPD) | | | |
| Médico Responsável | | | |
