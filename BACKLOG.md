# Backlog Técnico — Sistema Inteligente de Relatórios Médicos

**Base:** PRD.md (visão de produto), SPEC.md (arquitetura técnica), QUICKSTART.md (setup)
**Stack:** FastAPI + PostgreSQL + CrewAI + LangGraph + Railway

---

## MARCO 1 — MVP Core (Semanas 1-2)

### Banco/Tipagem

| # | Tarefa | Descrição |
|---|--------|-----------|
| 1.1 | Criar schema `users` | UUID, email, password_hash (bcrypt), role ENUM, crm, phone, 2FA fields, timestamps + soft delete. Índices em email e crm. |
| 1.2 | Criar schema `patients` | UUID, full_name, cpf_hash (SHA-256+salt), date_of_birth, contact_phone. Índice em cpf_hash. |
| 1.3 | Criar schema `medical_exams` | UUID, patient_id FK, exam_type, exam_date, content_encrypted (BYTEA), content_nonce, content_tag, google_doc_id, markdown_content_encrypted, uploaded_by FK, timestamps + soft delete. Índices em patient_id e exam_date. |
| 1.4 | Criar schema `medical_reports` | UUID, patient_id FK, requesting_doctor_id FK, exams_used (UUID[]), report_content_encrypted, report_nonce, report_tag, report_format ENUM, model_version, model_confidence, generated_at, expires_at, status ENUM, error_message. Índices em patient_id e requesting_doctor_id. |
| 1.5 | Criar schema `audit_logs` | BIGSERIAL, user_id FK, patient_id FK, action_type, resource_type, resource_id, status, error_message, ip_address (INET), user_agent, timestamp, duration_ms, request_id. Policies de imutabilidade (no UPDATE/DELETE). Índices em patient_id, user_id, timestamp, action_type. |
| 1.6 | Criar schema `async_tasks` | UUID, task_type, patient_id FK, status, input_data (JSONB), output_data (JSONB), error_message, timestamps, retry_count, max_retries. Índices em status e patient_id. |
| 1.7 | Criar models Pydantic v2 | Schemas de request/response para todos os modelos: UserCreate, UserResponse, PatientCreate, PatientResponse, ExamCreate, ExamResponse, ReportCreate, ReportResponse, AuditLogResponse, TaskResponse. |
| 1.8 | Configurar Alembic + migration inicial | `alembic init`, gerar migration autogenerate com todos os schemas, testar `alembic upgrade head`. |

### Backend/Lógica

| # | Tarefa | Descrição |
|---|--------|-----------|
| 1.9 | Setup do projeto FastAPI | Criar estrutura `app/` com `main.py`, `config.py` (pydantic-settings), `db.py` (SQLAlchemy async engine + session), CORS middleware, health check `GET /health`. |
| 1.10 | Implementar módulo `security.py` base | Geração e validação de JWT (python-jose), hash de senha (bcrypt), dependência `get_current_user` via Bearer token. |
| 1.11 | Implementar CRUD `users` | Rotas `POST /users` (register), `GET /users/me`, `POST /auth/login`, `POST /auth/refresh`. |
| 1.12 | Implementar webhook Whaha | Rota `POST /webhook/whatsapp` — recebe payload, valida assinatura `X-Whaha-Signature`, extrai mensagem, retorna ACK imediato (status=queued, job_id), enfileira no Redis/Celery. |
| 1.13 | Implementar serviço de processamento assíncrono | Configurar Celery + Redis, criar tasks base: `process_webhook_message` que faz parse de comando natural e roteia para admin_agent ou specialist_agent. |
| 1.14 | CrewAI Admin Agent — Tool `list_google_docs` | Autenticar Google Service Account, buscar documentos no Drive por query de paciente. |
| 1.15 | CrewAI Admin Agent — Tool `read_google_doc` | Ler conteúdo de um Google Doc pelo ID fornecido. |
| 1.16 | CrewAI Admin Agent — Tool `convert_to_markdown` | Converter conteúdo extraído para Markdown estruturado, preservando seções (exames, imagenologia, laboratorial). |
| 1.17 | CrewAI Admin Agent — Tool `upload_to_s3` | Salvar conteúdo Markdown no S3-compatible (Railway Volumes), retornar URL de referência. |
| 1.18 | CrewAI Admin Agent — Crew orquestrador | Definir Agent, Tasks (collect_documents, organize_by_type, convert_and_store) e Crew para orquestrar fluxo completo de organização. |
| 1.19 | Implementar rota `POST /admin/process` | Endpoint com JWT auth, recebe `{action, query, patient_id}`, dispara CrewAI Admin Agent via Celery, retorna status + job_id. |
| 1.20 | LangGraph Specialist Agent — Node `analyze` | Recebe `context_md` do paciente, chama Claude Opus para ler exames e identificar achados relevantes com confiança (%). |
| 1.21 | LangGraph Specialist Agent — Node `validate` | Verifica qualidade da análise: se confiança < threshold, refaz; se dados insuficientes, flag de alerta. |
| 1.22 | LangGraph Specialist Agent — Node `structure` | Formata relatório nas seções: Summary, Findings (com confidence), Alerts, Recommendations, Disclaimer obrigatório. |
| 1.23 | LangGraph Specialist Agent — Graph compiler | Construir StateGraph com nós `analyze → validate → structure → finalize`, compilar e expor função `invoke()`. |
| 1.24 | Implementar rota `POST /specialist/report` | Endpoint com JWT auth, recebe `{patient_id, exams_markdown, requesting_doctor_id}`, dispara LangGraph Specialist via Celery, retorna status + report_id. |
| 1.25 | Implementar envio de resposta via Whaha | Ao concluir tarefa, envia `POST https://api.whaha.com/v1/messages` com resultado (texto + anexo PDF) para o número do WhatsApp de origem. |
| 1.26 | Implementar audit log no fluxo principal | Registrar eventos: WEBHOOK_RECEIVED, ORGANIZE_START, ORGANIZE_SUCCESS/ERROR, REPORT_REQUEST, REPORT_SUCCESS/ERROR, WHATSAPP_SENT em `audit_logs`. |

### Frontend

| # | Tarefa | Descrição |
|---|--------|-----------|
| 1.27 | Criar estrutura base do dashboard | Inicializar projeto frontend (Next.js/React), configurar roteamento, tema base (Tailwind/shadcn). |
| 1.28 | Tela de login | Formulário com email + senha, chamada `POST /auth/login`, armazenamento de JWT, redirecionamento pós-login. |
| 1.29 | Página inicial do médico | Listar pacientes vinculados, exibir status de cada um (exames organizados? relatório pendente?), busca por nome. |
| 1.30 | Tela de visualização de relatório | Buscar relatório por ID, renderizar seções (Summary, Findings, Alerts, Recommendations, Disclaimer), botão de download PDF. |

---

## MARCO 2 — Compliance & Segurança (Semana 3)

### Banco/Tipagem

| # | Tarefa | Descrição |
|---|--------|-----------|
| 2.1 | Criar schema `patient_consents` | UUID, patient_id FK, doctor_id FK, consent_type ENUM, consent_text, signed_at, expires_at, ip_address, user_agent, signature_hash. Índices em patient_id e expires_at. Constraint: signed_at NOT NULL. |
| 2.2 | Criar schema `doctor_patient_access` | UUID, doctor_id FK, patient_id FK, access_level ENUM, access_granted_at, access_revoked_at, granted_by FK. Unique (doctor_id, patient_id). Índices em doctor_id e patient_id. |

### Backend/Lógica

| # | Tarefa | Descrição |
|---|--------|-----------|
| 2.3 | Implementar módulo `encryption.py` | Funções `encrypt_aes256(data, key) -> (ciphertext, nonce, tag)` e `decrypt_aes256(...)`. Modo GCM, IV random 12 bytes, auth tag 16 bytes. |
| 2.4 | Aplicar criptografia nos modelos sensíveis | Criptografar medical_exams.content_encrypted, markdown_content_encrypted, medical_reports.report_content_encrypted, users.two_fa_secret (AES-256-GCM no save/load). |
| 2.5 | Implementar RBAC middleware | Dependência `require_role(*roles)` que verifica role no JWT, retorna 403 se não autorizado. Aplicar nas rotas admin, specialist, audit. |
| 2.6 | Implementar relacionamento médico-paciente | CRUD `doctor_patient_access`: admin concede/revoga acesso. Middleware que verifica vínculo antes de qualquer operação. |
| 2.7 | Implementar 2FA (TOTP) | Gerar secret TOTP (pyotp), endpoint `POST /auth/2fa/setup` (QR code URI), `POST /auth/2fa/verify` (valida código). Exigir 2FA no login de médicos. |
| 2.8 | Implementar consentimento digital | Endpoints `POST /consents`, `GET /consents/{patient_id}`, `DELETE /consents/{id}`. Bloquear acesso se consentimento expirado/revogado. |
| 2.9 | Implementar rota `GET /audit/logs` | Query params: patient_id, user_id, action_type, date_from, date_to, limit, offset. Apenas admin/auditor. Paginado. |
| 2.10 | Implementar export CSV de audit log | `GET /audit/logs/export?format=csv` com mesmos filtros, gera CSV com id, user, patient, action, timestamp, ip, status. |
| 2.11 | Implementar backup automatizado | `pg_dump` diário via Railway Cron, armazenar em `/data/backups`, criptografar dump, log de backup em audit_logs. |
| 2.12 | Integrar Sentry | Configurar `sentry-sdk` no startup do FastAPI, capturar exceções, alertas para erro rate > 5%. |
| 2.13 | Implementar rate limiting | Middleware com Redis para 100 req/min por IP, retornar 429 com `Retry-After`. |
| 2.14 | Implementar política de privacidade | Rota estática `GET /privacy` servindo HTML com política LGPD: dados coletados, finalidade, direitos do titular, contato do DPO. |
| 2.15 | Implementar direitos do titular (LGPD) | `GET /my-data` (exportar dados), `POST /my-data/correction` (solicitar correção), `DELETE /my-data` (soft delete + revogação). |

### Frontend

| # | Tarefa | Descrição |
|---|--------|-----------|
| 2.16 | Tela de configuração 2FA | Exibir QR code, campo de verificação TOTP, feedback de sucesso/erro. |
| 2.17 | Tela de consentimentos | Listar consentimentos ativos, botão "Revogar", formulário de novo consentimento com texto legal. |
| 2.18 | Tela de auditoria (admin) | Filtros por paciente, usuário, ação, data. Tabela paginada. Botão "Exportar CSV". |
| 2.19 | Tela de política de privacidade | Renderizar `GET /privacy` em página dedicada, acessível publicamente. |

---

## MARCO 3 — Production Readiness (Semana 4)

### Backend/Lógica

| # | Tarefa | Descrição |
|---|--------|-----------|
| 3.1 | Testes de carga — webhook | Locust/k6 simulando 100 req/min, validar latência <500ms p99. |
| 3.2 | Testes de carga — agentes | 10 relatórios simultâneos, validar <5 min cada, sem degradação do webhook ACK. |
| 3.3 | Testes de penetração | OWASP Top 10: SQL injection, XSS, CSRF, JWT tampering, broken access control. |
| 3.4 | Health checks avançados | `GET /health/db` (SELECT 1), `GET /health/cache` (Redis PING), `GET /health/agents` (CrewAI/LangGraph ping). |
| 3.5 | Configurar monitoramento 24/7 | Railway alerts: CPU > 80%, mem > 85%, erro > 5%. Sentry alerts no Slack/email. |
| 3.6 | Plano de incident response | Documentar runbook: rollback, restore backup, comunicação com clínica, notificação LGPD (72h). |
| 3.7 | Configurar CI/CD final | GitHub Actions: testes, linter, type check no PR; deploy automático no merge para main. |
| 3.8 | Go-live checklist | Env vars de produção, secrets rotacionados, backup agendado, Sentry ativo, SSL, domínio configurado. |
| 3.9 | Otimização de cold start | `--preload` no uvicorn, health check para warm, timeout configurado. |

### Frontend

| # | Tarefa | Descrição |
|---|--------|-----------|
| 3.10 | Testes E2E no dashboard | Playwright/Cypress: login → listar pacientes → gerar relatório → visualizar → logout. |
| 3.11 | Modo offline / loading states | Skeletons, spinners, tratamento de erros de rede, retry automático com feedback visual. |
| 3.12 | Responsividade mobile | Adaptar para tablet (médicos em trânsito), menu colapsável, tabelas com scroll horizontal. |

---

## MARCO 4 — Features Pós-Lançamento (Opcional)

### Banco/Tipagem

| # | Tarefa | Descrição |
|---|--------|-----------|
| 4.1 | Criar schema `exam_comparisons` | Tabela para pares de exames comparados (antes/depois), com diff analysis results. |

### Backend/Lógica

| # | Tarefa | Descrição |
|---|--------|-----------|
| 4.2 | Dashboard de histórico do médico | `GET /doctor/dashboard`: total pacientes, relatórios/mês, pendências, tempo médio de processamento. |
| 4.3 | Portal do paciente | `GET /patient/exams`, `GET /patient/reports` com autenticação própria (não WhatsApp). |
| 4.4 | Comparação de exames (antes/depois) | Agente que recebe 2 conjuntos de exames e gera análise comparativa (evolução de indicadores). |
| 4.5 | Integração com Prontuário Eletrônico (EHR) | Conector HL7/FHIR, exportação de relatório para prontuário. |

### Frontend

| # | Tarefa | Descrição |
|---|--------|-----------|
| 4.6 | Dashboard do médico avançado | Gráficos: relatórios/mês, tempo médio, taxa de sucesso. Cards com métricas em tempo real. |
| 4.7 | Portal do paciente | Página pública com login, listagem de exames, visualização de relatório simplificado. |
| 4.8 | Tela de comparação de exames | Selecionar 2 datas, exibir diff lado a lado com highlights de alterações significativas. |

---

## Dependências entre Marcos

```
Marco 1 (MVP) ──────► Marco 2 (Compliance) ──────► Marco 3 (Production)
                                                          │
                                                          ▼
                                                   Marco 4 (Features)
```

- Nenhuma tarefa dentro de um marco depende de tarefas de marcos posteriores.
- Dentro de cada marco: **Banco/Tipagem** → **Backend/Lógica** → **Frontend** (onde há dependência).
- Tarefas independentes dentro da mesma categoria podem ser paralelizadas.
