import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import DoctorPatientAccess, Patient, User, AuditLog
from app.schemas import UserResponse, PatientResponse
from app.security import get_current_user, require_role

router = APIRouter(prefix="/access", tags=["access"])


@router.post("/grant")
async def grant_access(
    doctor_id: str,
    patient_id: str,
    access_level: str = "read",
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    doctor_result = await db.execute(select(User).where(User.id == doctor_id))
    doctor = doctor_result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    existing = await db.execute(
        select(DoctorPatientAccess).where(
            DoctorPatientAccess.doctor_id == doctor_id,
            DoctorPatientAccess.patient_id == patient_id,
            DoctorPatientAccess.access_revoked_at.is_(None),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Access already granted")

    access = DoctorPatientAccess(
        id=uuid.uuid4(),
        doctor_id=uuid.UUID(doctor_id),
        patient_id=uuid.UUID(patient_id),
        access_level=access_level,
        granted_by=uuid.UUID(current_user["sub"]),
    )
    db.add(access)

    audit = AuditLog(
        user_id=current_user["sub"],
        patient_id=patient_id,
        action_type="ACCESS_GRANTED",
        resource_type="doctor_patient_access",
        status="success",
        ip_address=request.client.host if request and request.client else "0.0.0.0",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit)

    await db.flush()
    return {"status": "granted", "doctor_id": doctor_id, "patient_id": patient_id}


@router.post("/revoke")
async def revoke_access(
    doctor_id: str,
    patient_id: str,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    result = await db.execute(
        select(DoctorPatientAccess).where(
            DoctorPatientAccess.doctor_id == doctor_id,
            DoctorPatientAccess.patient_id == patient_id,
            DoctorPatientAccess.access_revoked_at.is_(None),
        )
    )
    access = result.scalar_one_or_none()
    if not access:
        raise HTTPException(status_code=404, detail="Active access not found")

    access.access_revoked_at = datetime.now(timezone.utc)

    audit = AuditLog(
        user_id=current_user["sub"],
        patient_id=patient_id,
        action_type="ACCESS_REVOKED",
        resource_type="doctor_patient_access",
        status="success",
        ip_address=request.client.host if request and request.client else "0.0.0.0",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit)

    await db.flush()
    return {"status": "revoked", "doctor_id": doctor_id, "patient_id": patient_id}


@router.get("/doctor/{doctor_id}/patients", response_model=list[PatientResponse])
async def list_doctor_patients(
    doctor_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Patient)
        .join(DoctorPatientAccess, DoctorPatientAccess.patient_id == Patient.id)
        .where(
            DoctorPatientAccess.doctor_id == doctor_id,
            DoctorPatientAccess.access_revoked_at.is_(None),
        )
    )
    return result.scalars().all()


@router.get("/patient/{patient_id}/doctors", response_model=list[UserResponse])
async def list_patient_doctors(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(User)
        .join(DoctorPatientAccess, DoctorPatientAccess.doctor_id == User.id)
        .where(
            DoctorPatientAccess.patient_id == patient_id,
            DoctorPatientAccess.access_revoked_at.is_(None),
        )
    )
    return result.scalars().all()
