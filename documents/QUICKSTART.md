# QUICKSTART: Começar Desenvolvimento

**Time:** 1-2 devs  
**Prazo:** 4 semanas MVP → Production  
**Budget:** $100/mês infra  

---

## 1. LEIA PRIMEIRO (30 min)

```
PRD.md      ← O QUE fazer (product vision)
SPEC.md     ← COMO fazer (technical blueprint)
Este arquivo ← ONDE começar (next steps)
```

---

## 2. SETUP INICIAL (30 min)

### 2.1 Criar Repos

```bash
# Backend
gh repo create medical-reports-backend --private --template=None
cd medical-reports-backend

# Frontend (dashboard para médicos)
gh repo create medical-reports-dashboard --private
cd medical-reports-dashboard
```

### 2.2 Criar Railway Project

```bash
railway init
# Select: Python
# Name: medical-reports-api

# Add services:
# ├─ PostgreSQL (managed)
# ├─ Redis (managed)
# └─ Python service (your code)

# Get connection strings:
railway variables
# Copy: DATABASE_URL, REDIS_URL, SECRET_KEY
```

### 2.3 Environment Setup

```bash
# Backend/.env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
WHAHA_TOKEN=whh_...
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
GOOGLE_CREDENTIALS_JSON={...}  # Service account JSON
DEBUG=1
LOG_LEVEL=INFO
```

---

## 3. PHASE 1: MVP (Weeks 1-2)

### Week 1: Backend Core

```bash
# 1.1 Project structure
backend/
├─ app/
│  ├─ __init__.py
│  ├─ main.py              # FastAPI app
│  ├─ config.py            # Environment
│  ├─ models.py            # SQLAlchemy schemas
│  ├─ security.py          # Auth, encryption, RBAC
│  ├─ routes/
│  │  ├─ webhook.py        # POST /webhook/whatsapp
│  │  ├─ admin.py          # POST /admin/process
│  │  ├─ specialist.py     # POST /specialist/report
│  │  ├─ audit.py          # GET /audit/logs
│  │  └─ health.py         # GET /health
│  ├─ agents/
│  │  ├─ admin_agent.py    # CrewAI
│  │  └─ specialist_agent.py # LangGraph
│  ├─ utils/
│  │  ├─ encryption.py     # AES-256
│  │  ├─ validators.py
│  │  └─ helpers.py
│  └─ db.py                # SQLAlchemy setup
├─ migrations/             # Alembic
├─ tests/
│  ├─ test_models.py
│  ├─ test_security.py
│  ├─ test_routes.py
│  └─ test_agents.py
├─ requirements.txt
├─ .env.example
└─ railway.toml

# 1.2 Create requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
cryptography==41.0.7
bcrypt==4.1.1
python-jose==3.3.0
pyotp==2.9.0
python-dotenv==1.0.0
celery==5.3.4
redis==5.0.0
crewai==0.15.0
langgraph==0.1.0
langchain==0.2.0
openai==1.6.0
anthropic==0.25.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
sentry-sdk==1.38.0
```

### Week 1 Tasks

- [ ] Setup PostgreSQL (Railway managed)
- [ ] Setup Redis (Railway managed)
- [ ] Create models.py (audit_logs, medical_exams, users, consents)
- [ ] Create security.py (JWT, encryption, RBAC)
- [ ] Create routes/webhook.py (Whaha receiver)
- [ ] Create routes/health.py (monitoring)
- [ ] Unit tests (models, security)
- [ ] Deploy to Railway (test)

### Week 2: Agents

- [ ] Create agents/admin_agent.py (CrewAI - organize docs)
  - [ ] Tool: list_google_docs
  - [ ] Tool: read_google_doc
  - [ ] Tool: convert_to_markdown
  - [ ] Tool: upload_to_s3
  - [ ] Task: organize_documents
  
- [ ] Create agents/specialist_agent.py (LangGraph - generate report)
  - [ ] State: {context_md, analysis, findings, report}
  - [ ] Node: analyze_node()
  - [ ] Node: validate_node()
  - [ ] Node: structure_node()
  - [ ] Graph: connect nodes

- [ ] Create routes/admin.py (POST /admin/process)
- [ ] Create routes/specialist.py (POST /specialist/report)
- [ ] Integration tests (end-to-end)
- [ ] Deploy Phase 1 to Railway

---

## 4. PHASE 2: Compliance (Week 3)

- [ ] Add AES-256 encryption (security.py)
- [ ] Add RBAC middleware (security.py)
- [ ] Add 2FA (TOTP)
- [ ] Create consent forms (DB + digital signature)
- [ ] Audit log enhancements (immutable)
- [ ] LGPD policy + privacy.html
- [ ] Backup automation (pg_dump daily)
- [ ] Sentry integration
- [ ] Legal review (advogado)

---

## 5. PHASE 3: Production (Week 4)

- [ ] Load testing (pytest-locust)
- [ ] Penetration testing
- [ ] Doctor training (1h video)
- [ ] Go-live checklist
- [ ] Monitor 24/7 (Sentry + Railway)
- [ ] Incident response plan
- [ ] **LAUNCH**

---

## 6. CRITICAL DECISIONS

### Model Choice

**Admin Agent:** Claude Haiku 4.5
```bash
# Cost: $0.80 per 1M tokens input
# Speed: <2 min
# Quality: Sufficient for document organization

# In requirements.txt:
# anthropic>=0.25.0
# crewai>=0.15.0
```

**Specialist Agent:** Claude Opus 4.6
```bash
# Cost: $0.04 per 1K tokens input
# Speed: <3 min
# Quality: Best reasoning for medical content
```

### Deployment

**Only Railway** (no n8n, no complex orchestration)
```bash
# Deploy via GitHub:
railway up

# Monitor:
railway logs -s fastapi
railway variables

# Scale:
# Automatic (Railway auto-scales based on CPU/memory)
```

### Database

**PostgreSQL only** (no MongoDB, no NoSQL)
```bash
# Audit trail requirement
# Transactions requirement
# Compliance requirement
```

---

## 7. FOLDER STRUCTURE TO CREATE

```bash
mkdir -p backend/{app/{routes,agents,utils},migrations,tests}
mkdir -p frontend/src/{components,pages,utils}

# Backend files
touch backend/app/__init__.py
touch backend/app/main.py
touch backend/app/config.py
touch backend/app/models.py
touch backend/app/security.py
touch backend/app/db.py
touch backend/app/routes/{__init__.py,webhook.py,health.py,admin.py,specialist.py,audit.py}
touch backend/app/agents/{__init__.py,admin_agent.py,specialist_agent.py}
touch backend/app/utils/{__init__.py,encryption.py,validators.py,helpers.py}
touch backend/tests/{__init__.py,test_models.py,test_security.py,test_routes.py}
touch backend/{requirements.txt,.env.example,railway.toml,pytest.ini,alembic.ini}
```

---

## 8. FIRST COMMAND (1 min)

```bash
# Start FastAPI locally
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v  # Should pass (0 tests initially)
uvicorn app.main:app --reload

# Open http://localhost:8000/docs (FastAPI Swagger)
```

---

## 9. DEPLOY FIRST VERSION (10 min)

```bash
cd backend

# Initialize Railway
railway init

# Deploy
railway up

# Check logs
railway logs -s fastapi

# Test health
curl https://{railway-domain}.railway.app/health
```

---

## 10. BRANCHING STRATEGY

```
main
├─ feature/db-schema
├─ feature/webhook-receiver
├─ feature/admin-agent
├─ feature/specialist-agent
└─ feature/audit-log

# PR → GitHub Actions → Tests → Deploy (if pass)
```

---

## 11. KEY COMMITS (in order)

```
1. "init: project structure + requirements"
2. "feat: database schema + models"
3. "feat: encryption + security utils"
4. "feat: RBAC + JWT authentication"
5. "feat: Whaha webhook receiver"
6. "feat: CrewAI admin agent"
7. "feat: LangGraph specialist agent"
8. "feat: audit log + compliance"
9. "test: integration tests"
10. "chore: deploy to production"
```

---

## 12. MONITORING CHECKLIST

```
✓ Railway CPU/Memory/Network
✓ Sentry error tracking
✓ PostgreSQL slow queries
✓ Redis connection pool
✓ API latency (p50, p99)
✓ Webhook processing time
✓ Database backup logs
```

---

## 13. COMMUNICATION

### Team Sync
- Daily standup (15 min): What done? What blocked?
- Weekly review (30 min): PRs + progress

### Doctor/Client
- Phase 1 demo (Week 2): "Here's the system"
- Phase 2 review (Week 3): "Compliance is done"
- Phase 3 launch (Week 4): "Go live"

---

## 14. SHORTCUTS (Save Time)

```
❌ Don't:
├─ Spend time on UI initially (focus backend)
├─ Over-engineer architecture (YAGNI)
├─ Create 100% test coverage day 1 (cover main paths)
├─ Optimize prematurely (Railway auto-scales)
└─ Add features not in PRD (scope creep)

✅ Do:
├─ Get working MVP by end of Week 2
├─ Test with real Whaha webhook (not mock)
├─ Deploy every day (small increments)
├─ Ask for legal review early (don't wait)
└─ Involve doctor in Phase 2 (feedback loop)
```

---

**Ready to code?** Start with `app/main.py` →

```python
from fastapi import FastAPI

app = FastAPI(title="Medical Reports API")

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Save as `backend/app/main.py` → `uvicorn app.main:app --reload`

---

**Questions?** Refer to SPEC.md section-by-section as you build.
