from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.sentry import init_sentry

from app.routes.health import router as health_router
from app.routes.auth import router as auth_router
from app.routes.twofa import router as twofa_router
from app.routes.patients import router as patients_router
from app.routes.webhook import router as webhook_router
from app.routes.admin import router as admin_router
from app.routes.specialist import router as specialist_router
from app.routes.audit import router as audit_router
from app.routes.consents import router as consents_router
from app.routes.access import router as access_router
from app.routes.lgpd import router as lgpd_router
from app.routes.privacy import router as privacy_router
from app.routes.doctor import router as doctor_router
from app.routes.patient_portal import router as patient_portal_router
from app.routes.comparison import router as comparison_router

settings = get_settings()

init_sentry()

app = FastAPI(title=settings.APP_NAME, docs_url="/docs", redoc_url="/redoc")

app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health
app.include_router(health_router)

# Auth + 2FA
app.include_router(auth_router)
app.include_router(twofa_router)

# Core business
app.include_router(patients_router)
app.include_router(webhook_router)
app.include_router(admin_router)
app.include_router(specialist_router)

# Compliance (Marco 2)
app.include_router(audit_router)
app.include_router(consents_router)
app.include_router(access_router)
app.include_router(lgpd_router)
app.include_router(privacy_router)

# Features (Marco 4)
app.include_router(doctor_router)
app.include_router(patient_portal_router)
app.include_router(comparison_router)

# Serve frontend SPA at /app (or root URL for Railway)
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    print(f"Frontend mounted at /app — {frontend_dir}")
