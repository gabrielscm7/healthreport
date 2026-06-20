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

__all__ = [
    "health_router",
    "auth_router",
    "twofa_router",
    "patients_router",
    "webhook_router",
    "admin_router",
    "specialist_router",
    "audit_router",
    "consents_router",
    "access_router",
    "lgpd_router",
    "privacy_router",
    "doctor_router",
    "patient_portal_router",
    "comparison_router",
]
