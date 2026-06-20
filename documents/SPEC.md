# SPEC: Arquitetura Técnica e Implementação

**Versão:** 1.0  
**Referência PRD:** PRD.md  
**Stack:** FastAPI + PostgreSQL + CrewAI + LangGraph + Railway  

---

## 1. ARQUITETURA GERAL

```
┌─────────────────────────────────────────────────┐
│         RAILWAY (Single Provider)               │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ FastAPI Service (3 replicas auto-scale)   │ │
│  │ ├─ POST /webhook/whatsapp (Whaha)        │ │
│  │ ├─ POST /admin/process (CrewAI)          │ │
│  │ ├─ POST /specialist/report (LangGraph)   │ │
│  │ ├─ GET /audit/logs (compliance)          │ │
│  │ └─ Health checks (Railway monitoring)    │ │
│  └───────────────────────────────────────────┘ │
│                 │                               │
│  ┌──────────────┼──────────────┐               │
│  │              │              │               │
│  ▼              ▼              ▼               │
│ PostgreSQL   Redis Queue   S3-Compatible      │
│ (Database +  (Celery)      (Exams + MD)       │
│  Audit Log)  (Async Job)    (Volumes)         │
│              (Cache)                          │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 2. STACK TÉCNICO

### Backend
```yaml
Language: Python 3.11
Framework: FastAPI 0.104+
Async: AsyncIO + Uvicorn
Validation: Pydantic v2
Database: SQLAlchemy 2.0 + Alembic
Queue: Celery + Redis
AI/Agents: 
  - CrewAI 0.15+ (Admin)
  - LangGraph 0.1+ (Specialist)
  - LangChain 0.2+
  - OpenAI SDK (Claude via Anthropic)
Auth: PyJWT + python-jose
Encryption: cryptography + bcrypt
Security: python-dotenv + secrets
Testing: pytest + pytest-asyncio
```

### Infrastructure
```yaml
Compute: Railway.app (Python service)
Database: Railway PostgreSQL 15
Cache: Railway Redis 7
Storage: Railway Volumes (S3-compat)
Monitoring: Railway built-in + Sentry
Backup: Railway managed + pg_dump daily
CI/CD: GitHub auto-deploy
Domain: Railway SSL (ou custom)
```

### External Services
```yaml
WhatsApp: Whaha API (webhook)
AI Models: Anthropic API (Claude)
Storage: Google Drive/Docs API
Compliance: Sentry (error tracking)
```

---

## 3. BANCO DE DADOS

### Schema (PostgreSQL)

```sql
-- Users (Médicos, Admins)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt
    role ENUM('admin', 'doctor', 'patient', 'auditor') NOT NULL,
    full_name VARCHAR(255),
    crm VARCHAR(20),  -- CFM registration
    phone VARCHAR(20),
    two_fa_enabled BOOLEAN DEFAULT FALSE,
    two_fa_secret VARCHAR(255),  -- TOTP secret (encrypted)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL  -- Soft delete
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_crm ON users(crm);

-- Patients
CREATE TABLE patients (
    id UUID PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,  -- Hashed for privacy
    cpf_hash VARCHAR(255) UNIQUE,  -- SHA-256 + salt
    date_of_birth DATE,
    contact_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    -- Never store PII in logs
    CONSTRAINT no_plain_text CHECK (full_name != '')
);
CREATE INDEX idx_patients_cpf_hash ON patients(cpf_hash);

-- Patient Consent (LGPD Art. 8)
CREATE TABLE patient_consents (
    id UUID PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES patients(id),
    doctor_id UUID NOT NULL REFERENCES users(id),
    consent_type ENUM('ai_analysis', 'data_storage', 'research') NOT NULL,
    consent_text TEXT NOT NULL,  -- Versioned legal text
    signed_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    signature_hash VARCHAR(255),  -- Digital signature
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT consent_must_be_explicit CHECK (signed_at IS NOT NULL)
);
CREATE INDEX idx_consents_patient ON patient_consents(patient_id);
CREATE INDEX idx_consents_expiry ON patient_consents(expires_at);

-- Medical Exams (Criptografados)
CREATE TABLE medical_exams (
    id UUID PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES patients(id),
    exam_type VARCHAR(100) NOT NULL,  -- Lab, Imaging, ECG, etc
    exam_date DATE NOT NULL,
    content_encrypted BYTEA NOT NULL,  -- AES-256-GCM
    content_nonce VARCHAR(255) NOT NULL,  -- IV/Nonce
    content_tag VARCHAR(255) NOT NULL,  -- Auth tag
    google_doc_id VARCHAR(255),  -- Reference original
    markdown_content_encrypted BYTEA,  -- Converted version
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL  -- Soft delete (never hard delete)
);
CREATE INDEX idx_exams_patient ON medical_exams(patient_id);
CREATE INDEX idx_exams_date ON medical_exams(exam_date);

-- Generated Reports
CREATE TABLE medical_reports (
    id UUID PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES patients(id),
    requesting_doctor_id UUID NOT NULL REFERENCES users(id),
    exams_used UUID[] NOT NULL,  -- Array of exam IDs used
    report_content_encrypted BYTEA NOT NULL,  -- AES-256-GCM
    report_nonce VARCHAR(255) NOT NULL,
    report_tag VARCHAR(255) NOT NULL,
    report_format ENUM('json', 'pdf', 'markdown') DEFAULT 'json',
    model_version VARCHAR(50) NOT NULL,  -- "claude-opus-4-6"
    model_confidence FLOAT,  -- 0.0-1.0
    generated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,  -- Auto-delete old reports
    status ENUM('generating', 'success', 'error') DEFAULT 'generating',
    error_message TEXT
);
CREATE INDEX idx_reports_patient ON medical_reports(patient_id);
CREATE INDEX idx_reports_doctor ON medical_reports(requesting_doctor_id);

-- AUDIT LOG (IMUTÁVEL - Nunca delete/update)
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,  -- Sequential, no UUID (better for immutability)
    user_id UUID REFERENCES users(id),
    patient_id UUID REFERENCES patients(id),
    action_type VARCHAR(50) NOT NULL,
      -- ENUM: VIEW_EXAM, CREATE_REPORT, DOWNLOAD, EXPORT, DELETE, LOGIN, etc
    resource_type VARCHAR(50),  -- exam, report, patient, consent
    resource_id UUID,
    status VARCHAR(20) NOT NULL,  -- success, error, denied
    error_message TEXT,
    ip_address INET NOT NULL,
    user_agent TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    duration_ms INTEGER,
    request_id VARCHAR(255),  -- Trace ID
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- CONSTRAINTS para imutabilidade
    CONSTRAINT audit_immutable AS (
        -- Prevent future updates
    )
);
-- Índices para compliance
CREATE INDEX idx_audit_patient ON audit_logs(patient_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_action ON audit_logs(action_type);
-- POLICY: No update/delete allowed
CREATE POLICY audit_no_update ON audit_logs FOR UPDATE USING (FALSE);
CREATE POLICY audit_no_delete ON audit_logs FOR DELETE USING (FALSE);

-- Task Queue (Celery + Async jobs)
CREATE TABLE async_tasks (
    id UUID PRIMARY KEY,
    task_type VARCHAR(100) NOT NULL,  -- organize_exams, generate_report
    patient_id UUID REFERENCES patients(id),
    status VARCHAR(20),  -- pending, processing, completed, failed
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);
CREATE INDEX idx_tasks_status ON async_tasks(status);
CREATE INDEX idx_tasks_patient ON async_tasks(patient_id);

-- Doctor-Patient Relationship (RBAC)
CREATE TABLE doctor_patient_access (
    id UUID PRIMARY KEY,
    doctor_id UUID NOT NULL REFERENCES users(id),
    patient_id UUID NOT NULL REFERENCES patients(id),
    access_level VARCHAR(50) NOT NULL,  -- read, write, full
    access_granted_at TIMESTAMP DEFAULT NOW(),
    access_revoked_at TIMESTAMP NULL,
    granted_by UUID REFERENCES users(id),  -- Admin who granted
    UNIQUE(doctor_id, patient_id)
);
CREATE INDEX idx_access_doctor ON doctor_patient_access(doctor_id);
CREATE INDEX idx_access_patient ON doctor_patient_access(patient_id);
```

### Encryption Strategy
```
Data at Rest (AES-256-GCM):
├─ medical_exams.content_encrypted
├─ medical_reports.report_content_encrypted
├─ users.two_fa_secret
└─ Key Management: Railway env vars + future HashiCorp Vault

Data in Transit:
├─ TLS 1.3 (Railway enforced)
├─ Certificate pinning (mobile apps)
└─ API authentication via JWT + Bearer token

Key Rotation:
├─ Master key: monthly rotation
├─ Encrypted with new key, keep old for decryption
└─ Audit trail: log de rotação de chaves
```

---

## 4. API ENDPOINTS

### 4.1 Webhook (Whaha → FastAPI)

```http
POST /webhook/whatsapp
Content-Type: application/json
X-Whaha-Signature: {webhook_secret_signature}

Request:
{
  "messages": [{
    "from": "5599999999",
    "body": "Organize exames de João Silva",
    "timestamp": 1718000000,
    "id": "msg_abc123",
    "media": [{"url": "s3://...", "type": "image"}]  // Optional
  }]
}

Response (immediate):
{
  "status": "queued",
  "job_id": "job_xyz789",
  "estimated_time": "2-3 minutes"
}

-- Webhook sends job result later via Whaha
```

### 4.2 Admin Agent Processing

```http
POST /admin/process
Authorization: Bearer {jwt_token}
Content-Type: application/json

Request:
{
  "action": "organize_documents",
  "query": "João Silva",
  "patient_id": "uuid_123"
}

Response:
{
  "status": "success",
  "documents_found": 12,
  "documents_organized": {
    "lab_exams": 5,
    "imaging": 4,
    "other": 3
  },
  "markdown_reference": "ref_abc123",
  "storage_url": "s3://clinic/patients/uuid_123/exams_organized.md"
}
```

### 4.3 Specialist Report Generation

```http
POST /specialist/report
Authorization: Bearer {jwt_token}
Content-Type: application/json

Request:
{
  "patient_id": "uuid_123",
  "exams_markdown": "# João Silva\n## Exames\n...",
  "requesting_doctor_id": "uuid_doctor"
}

Response:
{
  "status": "generating",
  "report_id": "report_abc123",
  "estimated_time": "3-5 minutes"
}

-- Later via callback:
{
  "report_id": "report_abc123",
  "status": "completed",
  "content": {
    "summary": "Análise de 12 exames...",
    "findings": [
      {
        "finding": "Hemoglobina 12.5 g/dL",
        "relevance": "Possível anemia",
        "confidence": 0.95
      }
    ],
    "alerts": [
      {
        "severity": "medium",
        "message": "Resultado acima do esperado"
      }
    ],
    "recommendations": [
      "Investigação adicional de anemia"
    ],
    "disclaimer": "Este relatório é ferramenta de apoio..."
  },
  "model_used": "claude-opus-4-6",
  "generated_at": "2024-06-17T10:30:00Z"
}
```

### 4.4 Audit Log Query

```http
GET /audit/logs?patient_id={uuid}&limit=100&offset=0
Authorization: Bearer {jwt_token}
Role: admin or auditor

Response:
{
  "total": 245,
  "logs": [
    {
      "id": 12345,
      "action": "VIEW_EXAM",
      "user": "Dr. Silva",
      "patient": "João",
      "timestamp": "2024-06-17T10:15:00Z",
      "ip_address": "192.168.1.1",
      "status": "success"
    }
  ]
}
```

---

## 5. FLOW: Detalhado Passo-a-Passo

### Fluxo 1: Organizar Exames

```
1. Usuário envia WhatsApp:
   "Organize exames de João Silva"

2. Whaha envia webhook para FastAPI:
   POST /webhook/whatsapp
   {from: "5599999999", body: "..."}

3. FastAPI responde imediatamente:
   {status: "queued", job_id: "job_xyz"}
   [Cria async task em DB + Redis]

4. Celery worker inicia tarefa:
   - Log: audit_logs INSERT (ORGANIZE_START)

5. CrewAI Admin Agent executa:
   Tool 1: list_google_docs(query="João Silva")
   Tool 2: read_google_doc(doc_id) [para cada doc]
   Tool 3: convert_to_markdown(content)
   Tool 4: upload_to_s3(markdown_content)
   
6. Salva resultado:
   - medical_exams INSERT (1 record por exame)
   - async_tasks UPDATE (status='completed')
   - audit_logs INSERT (ORGANIZE_SUCCESS)

7. Envia resposta via Whaha:
   POST https://api.whaha.com/v1/messages
   {
     to: "5599999999",
     body: "✅ 12 exames organizados! Ref: #XYZ789"
   }

Tempo: <5 minutos
Audit Trail: 15+ eventos registrados
```

### Fluxo 2: Gerar Relatório

```
1. Médico envia WhatsApp:
   "Gere relatório para João Silva, ref #XYZ789"

2. FastAPI recebe via Whaha webhook:
   - Valida consentimento do paciente
   - Verifica permissão médico->paciente
   - Log: audit_logs INSERT (REPORT_REQUEST)

3. Se error (sem consentimento):
   - Responde: "❌ Sem consentimento. Solicitar ao paciente."
   - Log: audit_logs INSERT (status='denied')
   - STOP

4. Se autorizado, cria tarefa:
   - async_tasks INSERT (type='generate_report')
   - Celery worker inicia

5. LangGraph Specialist Agent:
   Input:
   {
     context_md: "# João Silva\n## Lab\n...",
     patient_context: {age: 45, gender: M},
     requesting_doctor: "Dr. Silva"
   }
   
   Node 1 (Analyze):
   - Claude Opus lê exames
   - Identifica achados relevantes
   - Calcula confiança (%)
   
   Node 2 (Validate):
   - Verifica se análise tem qualidade
   - Se ruim, refaz
   
   Node 3 (Structure):
   - Formata relatório:
     * Summary
     * Findings (com confidence)
     * Alerts
     * Recommendations
     * Disclaimer obrigatório
   
   Output:
   {
     summary: "...",
     findings: [...],
     alerts: [...],
     recommendations: [...]
   }

6. Salva resultado:
   - medical_reports INSERT (content encrypted AES-256)
   - async_tasks UPDATE (status='completed')
   - audit_logs INSERT (REPORT_SUCCESS)

7. Envia resposta:
   WhatsApp: "✅ Relatório gerado! PDF anexo."
   + PDF attachado via Whaha

Tempo: <5 minutos
Audit Trail: 20+ eventos registrados
Encryption: AES-256-GCM + auth tag
```

---

## 6. COMPONENTES DE IA

### 6.1 CrewAI Admin Agent

```python
# Structure
agents/admin_agent.py
├─ Admin Agent (role, goal, backstory)
├─ Tools:
│  ├─ list_google_docs(query, limit)
│  ├─ read_google_doc(doc_id)
│  ├─ convert_to_markdown(content)
│  └─ upload_to_s3(filename, content)
├─ Tasks:
│  ├─ collect_documents(patient_name)
│  ├─ organize_by_type()
│  └─ convert_and_store()
└─ Crew (orchestrator)

Model: Claude Haiku 4.5
├─ Cost: ~$0.80 per 1M tokens input
├─ Speed: <2 min para organizar 12 docs
└─ Why: Simples, rápido, confiável

Fallback:
├─ DeepSeek (custo menor, menos confiável)
├─ Llama 3.1 (open-source, local - future)
```

### 6.2 LangGraph Specialist Agent

```python
# Structure
agents/specialist_agent.py
├─ State:
│  ├─ context_md: str
│  ├─ analysis: str
│  ├─ findings: list
│  └─ report: str
├─ Nodes:
│  ├─ analyze_node()
│  ├─ validate_node()
│  ├─ structure_node()
│  └─ finalize_node()
├─ Graph (directed state graph)
└─ Compiler + invoker

Model: Claude Opus 4.6
├─ Cost: ~$0.04 per 1K tokens input
├─ Quality: Melhor reasoning, análise complexa
├─ Speed: <3 min para análise
└─ Why: Dados médicos exigem máxima confiabilidade

Edge Cases:
├─ Exame incompleto: alert médico
├─ Resultado fora da curva: flag + confidence baixa
├─ Modelo não confidente: ask for human review
```

---

## 7. SEGURANÇA E COMPLIANCE

### 7.1 LGPD (Lei Geral de Proteção de Dados)

```
Art. 1-8: Escopo
├─ ✅ Dados médicos = sensíveis
├─ ✅ Consentimento explícito
└─ ✅ Finalidade determinada

Art. 13: Informações ao Titular
├─ ✅ Política de privacidade (disponível)
├─ ✅ Dados coletados (exames, consentimento)
├─ ✅ Finalidade (relatório + apoio cirúrgico)
└─ ✅ Direito a acessar/corrigir

Art. 18-21: Direitos do Titular
├─ ✅ Acesso aos dados (endpoint GET /my-data)
├─ ✅ Correção (request form)
├─ ✅ Exclusão (soft delete + criptografia)
├─ ✅ Portabilidade (export JSON)
└─ ✅ Revogação de consentimento (imediata)

Art. 43-49: Responsabilidade
├─ ✅ Incident response (72h notification)
├─ ✅ Processamento seguro (encryption)
├─ ✅ Backup + recovery (diário)
└─ ✅ DPA (Data Processing Agreement) com clínica

Implementation:
├─ Consent table (patient_consents)
├─ Audit log (imutável)
├─ Encryption (AES-256)
├─ Backup (diário, tested)
└─ Privacy policy + LGPD disclosure
```

### 7.2 CFM (Conselho Federal de Medicina)

```
Res. 2299/2021: IA em Medicina
├─ IA é ferramenta, não profissional
├─ Médico sempre responsável
├─ Transparência sobre uso de IA
├─ Rastreabilidade + auditoria
└─ Consentimento do paciente

Parecer 32/2021: Diagnóstico + IA
├─ IA NÃO faz diagnóstico independente
├─ IA NÃO substitui médico
├─ IA PODE ser segundo parecer
├─ Disclaimer obrigatório (Resolução 2299)
└─ Médico sempre decide

Implementation:
├─ Relatório com disclaimer:
│  "Este relatório é ferramenta de apoio..."
│  "Decisão clínica é responsabilidade do médico..."
├─ Audit trail (quem, quando, resultado)
├─ Rastreabilidade de modelo (versão Claude usado)
├─ Consentimento informado (assinar antes)
└─ Prontuário com trail (audit log)
```

### 7.3 Encryption & Data Protection

```
AES-256-GCM Implementation:
├─ Library: cryptography (Hazmat)
├─ Mode: Galois/Counter (autenticação)
├─ Key: 32 bytes (256 bits)
├─ IV/Nonce: 12 bytes (96 bits) - random per message
├─ Auth Tag: 16 bytes (128 bits)
└─ Format: IV + ciphertext + tag (binary)

Key Storage:
├─ Master Key: Railway env var (secret)
├─ Rotation: monthly (encrypt com new key, keep old)
└─ Audit log: log de rotação (imutável)

TLS/Transport:
├─ TLS 1.3 (Railway enforced)
├─ Certificate: Railway SSL (auto-renewed)
├─ HSTS: enabled (strict-transport-security)
└─ Certificate pinning: mobile (future)

API Security:
├─ JWT + Bearer token (FastAPI dependency)
├─ 2FA (TOTP) para médicos
├─ IP whitelist (optional, per clinic)
├─ Rate limiting (100 req/min per IP)
└─ CORS: only clinic domain
```

---

## 8. DEPLOYMENT & OPS

### 8.1 Railway Configuration

```yaml
# railway.toml
[build]
builder = "dockerfile"

[variables]
PYTHON_VERSION = "3.11"
PYTHONUNBUFFERED = "1"

[services]
fastapi:
  nixpacks = ["python"]
  startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
  healthUrl = "http://localhost/health"
  replicas = 3  # Auto-scale

postgres:
  image = "postgres:15-alpine"
  version = "15.0"
  
redis:
  image = "redis:7-alpine"
  version = "7.0"

[volumes]
exams_storage = "/data/exams"
backups = "/data/backups"
```

### 8.2 GitHub Actions (CI/CD)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/ -v

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### 8.3 Monitoring & Alerts

```
Railway Dashboard:
├─ CPU usage (alert if >80%)
├─ Memory usage (alert if >85%)
├─ Network I/O
├─ Request latency
└─ Error rate (alert if >5%)

Sentry Integration:
├─ Error tracking (real-time)
├─ Release tracking
├─ Performance monitoring
└─ Notification: Slack + email

Health Checks:
├─ GET /health → {status: "ok"}
├─ GET /health/db → {status: "ok"}
├─ GET /health/cache → {status: "ok"}
└─ Every 30s (Railway + Sentry)

Logging:
├─ Structured logs (JSON + timestamp)
├─ Level: DEBUG (dev) / INFO (prod)
├─ Never log PII
├─ Rotate daily (keep 30 days)
```

---

## 9. TESTES

### 9.1 Test Strategy

```
Unit Tests (pytest):
├─ Encryption/decryption
├─ JWT validation
├─ RBAC authorization
├─ Pydantic models
└─ Database queries

Integration Tests:
├─ Whaha webhook → FastAPI → CrewAI
├─ CrewAI → Google Drive API
├─ LangGraph → Claude API
└─ PostgreSQL transactions

E2E Tests:
├─ Full flow: WhatsApp → Relatório
├─ Audit trail: log completo
├─ Encryption: data encrypted/decrypted
└─ RBAC: médico não vê dados alheios

Performance Tests:
├─ 100 req/min (webhook load)
├─ <500ms webhook ACK
├─ <3min relatório generation
└─ <100ms query audit log
```

### 9.2 Coverage

```
Target: >85% code coverage
├─ models.py: 100%
├─ security.py: 100%
├─ routes/: 95%
├─ agents/: 80% (IA unpredictable)
└─ utils/: 90%

Excluded:
├─ main.py (entry point)
├─ config.py (env vars)
└─ migrations/ (alembic)
```

---

## 10. ROADMAP TÉCNICO

### Phase 1: MVP (Weeks 1-2)
```
┌─ FastAPI scaffold
├─ PostgreSQL schema + migrations
├─ Whaha webhook receiver
├─ CrewAI admin agent (basic)
├─ LangGraph specialist (basic)
├─ Basic audit log
└─ Deployment to Railway
```

### Phase 2: Compliance (Week 3)
```
┌─ AES-256 encryption
├─ RBAC + 2FA
├─ Consent forms (digital + PDF)
├─ Audit log enhancement (immutable)
├─ LGPD policy + legal review
├─ Backup automation
└─ Sentry monitoring
```

### Phase 3: Production (Week 4)
```
┌─ Load testing (100 req/min)
├─ Penetration testing
├─ Doctor training materials
├─ Go-live checklist
├─ 24/7 monitoring setup
└─ Incident response plan
```

### Phase 4+: Features
```
┌─ Doctor dashboard (histórico)
├─ Patient portal (view próprio dados)
├─ Report comparison (before/after)
├─ EHR integration
├─ Multi-language support
└─ Mobile app (native iOS/Android)
```

---

## 11. INSTRUÇÕES DE DESENVOLVIMENTO

### Quick Start

```bash
# 1. Clone + setup
git clone repo
cd repo
python -m venv venv
source venv/bin/activate  # ou `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# 2. Environment
cp .env.example .env
# Edit .env: OPENAI_API_KEY, DATABASE_URL, WHAHA_TOKEN, GOOGLE_CREDENTIALS_JSON

# 3. Database
alembic upgrade head  # Run migrations

# 4. Run locally
python -m pytest tests/  # Run tests first
uvicorn app.main:app --reload

# 5. Deploy
railway up  # Requires Railway CLI + RAILWAY_TOKEN
```

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/organize-exams

# Make changes, test locally
pytest tests/ -v --cov

# Commit + push
git add .
git commit -m "feat: add organize exams tool"
git push origin feature/organize-exams

# GitHub Actions runs tests + deploys to Railway (if all pass)
```

### Database Migrations

```bash
# Generate migration (after model changes)
alembic revision --autogenerate -m "add exam_type to medical_exams"

# Review generated migration file
vim alembic/versions/xxx_add_exam_type.py

# Apply locally
alembic upgrade head

# Deploy to Railway (automatic with CD)
```

### Debugging

```
Environment Variables:
├─ DEBUG=1 (uvicorn logs + traceback)
├─ LOG_LEVEL=DEBUG (verbose logs)
└─ SENTRY_DSN (error tracking)

Remote Debugging:
├─ Railway logs: railway logs -s fastapi
├─ Database: psql $DATABASE_URL
├─ Redis: redis-cli -u $REDIS_URL
├─ Sentry: sentry.io dashboard
```

---

## 12. TECH DEBT & FUTURE

```
Known Limitations:
├─ [ ] No local model fallback (DeepSeek) yet
├─ [ ] No multi-clinic support (planned Phase 5)
├─ [ ] No offline mode (future)
├─ [ ] No SMS fallback (if Whaha down)
└─ [ ] No integration with EHR systems yet

Tech Debt:
├─ [ ] Refactor agents/ (too monolithic)
├─ [ ] Add type hints (100% coverage)
├─ [ ] Improve error messages (UX)
├─ [ ] Add request tracing (OpenTelemetry)
└─ [ ] Cache optimization (Redis strategy)
```

---

## 13. REFERÊNCIAS

| Documento | Link |
|-----------|------|
| PRD | PRD.md |
| LGPD | https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd |
| CFM Res. 2299 | https://www.in.gov.br/en/web/dou |
| FastAPI Docs | https://fastapi.tiangolo.com |
| CrewAI Docs | https://docs.crewai.com |
| LangGraph Docs | https://langchain-ai.github.io/langgraph |
| Railway Docs | https://docs.railway.app |

---

**Pronto para Development.** Próximo: Criar repos e iniciar Phase 1.
