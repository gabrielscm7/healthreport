import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import PatientConsent, Patient, User, AuditLog
from app.schemas import ConsentCreate, ConsentResponse
from app.security import get_current_user, require_role

router = APIRouter(prefix="/consents", tags=["consents"])


@router.post("", response_model=ConsentResponse, status_code=201)
async def create_consent(
    payload: ConsentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "doctor")),
):
    patient_result = await db.execute(
        select(Patient).where(Patient.id == payload.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    doctor_id = current_user["sub"]

    consent = PatientConsent(
        id=uuid.uuid4(),
        patient_id=uuid.UUID(payload.patient_id),
        doctor_id=uuid.UUID(doctor_id),
        consent_type=payload.consent_type,
        consent_text=payload.consent_text,
        signed_at=payload.signed_at,
        expires_at=payload.expires_at,
        ip_address=request.client.host if request.client else "0.0.0.0",
        user_agent=request.headers.get("user-agent", ""),
        signature_hash=payload.signature_hash,
    )
    db.add(consent)

    audit = AuditLog(
        user_id=doctor_id,
        patient_id=str(payload.patient_id),
        action_type="CONSENT_CREATED",
        resource_type="consent",
        status="success",
        ip_address=request.client.host if request.client else "0.0.0.0",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit)

    await db.flush()
    await db.refresh(consent)
    return consent


@router.get("/{patient_id}", response_model=list[ConsentResponse])
async def list_consents(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(PatientConsent)
        .where(PatientConsent.patient_id == patient_id)
        .order_by(PatientConsent.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{patient_id}/active", response_model=list[ConsentResponse])
async def list_active_consents(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(PatientConsent)
        .where(
            PatientConsent.patient_id == patient_id,
            PatientConsent.expires_at > now,
        )
        .order_by(PatientConsent.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{consent_id}", status_code=204)
async def revoke_consent(
    consent_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "doctor")),
):
    result = await db.execute(
        select(PatientConsent).where(PatientConsent.id == consent_id)
    )
    consent = result.scalar_one_or_none()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")

    consent.expires_at = datetime.now(timezone.utc)

    audit = AuditLog(
        user_id=current_user["sub"],
        patient_id=str(consent.patient_id),
        action_type="CONSENT_REVOKED",
        resource_type="consent",
        resource_id=uuid.UUID(consent_id),
        status="success",
        ip_address=request.client.host if request.client else "0.0.0.0",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit)

    await db.flush()
