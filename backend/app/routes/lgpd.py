from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Patient, MedicalExam, MedicalReport, PatientConsent, AuditLog
from app.security import get_current_user, require_role

router = APIRouter(prefix="/lgpd", tags=["lgpd"])


@router.get("/my-data")
async def export_my_data(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """LGPD Art. 18 - Direito de acesso aos dados pessoais"""
    user_id = current_user["sub"]

    exams_result = await db.execute(
        select(MedicalExam).where(
            MedicalExam.uploaded_by == user_id,
            MedicalExam.deleted_at.is_(None),
        )
    )
    exams = exams_result.scalars().all()

    reports_result = await db.execute(
        select(MedicalReport).where(
            MedicalReport.requesting_doctor_id == user_id,
        )
    )
    reports = reports_result.scalars().all()

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exams_count": len(exams),
        "reports_count": len(reports),
        "exams": [
            {
                "id": str(e.id),
                "exam_type": e.exam_type,
                "exam_date": str(e.exam_date),
                "uploaded_at": str(e.uploaded_at),
            }
            for e in exams
        ],
        "reports": [
            {
                "id": str(r.id),
                "model_version": r.model_version,
                "generated_at": str(r.generated_at),
                "status": r.status,
            }
            for r in reports
        ],
    }


@router.post("/correction")
async def request_correction(
    patient_id: str,
    field: str,
    new_value: str,
    reason: str,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "doctor")),
):
    """LGPD Art. 18 - Direito de correção de dados incompletos/inexatos"""
    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    allowed_fields = {"full_name", "date_of_birth", "contact_phone"}
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"Field '{field}' cannot be corrected. Allowed: {allowed_fields}")

    if field == "full_name":
        patient.full_name = new_value
    elif field == "date_of_birth":
        from datetime import date
        patient.date_of_birth = date.fromisoformat(new_value)
    elif field == "contact_phone":
        patient.contact_phone = new_value

    audit = AuditLog(
        user_id=current_user["sub"],
        patient_id=patient_id,
        action_type="DATA_CORRECTION",
        resource_type="patient",
        resource_id=patient.id,
        status="success",
        ip_address=request.client.host if request and request.client else "0.0.0.0",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit)

    await db.flush()
    await db.refresh(patient)

    return {
        "status": "corrected",
        "field": field,
        "reason": reason,
    }


@router.delete("/my-data")
async def request_deletion(
    patient_id: str,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """LGPD Art. 18 - Direito de exclusão (soft delete + revogação consentimentos)"""
    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    now = datetime.now(timezone.utc)

    # Soft delete exams
    exams_result = await db.execute(
        select(MedicalExam).where(
            MedicalExam.patient_id == patient_id,
            MedicalExam.deleted_at.is_(None),
        )
    )
    for exam in exams_result.scalars().all():
        exam.deleted_at = now

    # Revoke all consents
    consents_result = await db.execute(
        select(PatientConsent).where(
            PatientConsent.patient_id == patient_id,
            PatientConsent.expires_at > now,
        )
    )
    for consent in consents_result.scalars().all():
        consent.expires_at = now

    audit = AuditLog(
        user_id=current_user["sub"],
        patient_id=patient_id,
        action_type="DATA_DELETION",
        resource_type="patient",
        status="success",
        ip_address=request.client.host if request and request.client else "0.0.0.0",
        timestamp=now,
    )
    db.add(audit)

    await db.flush()

    return {"status": "deleted", "patient_id": patient_id, "deleted_at": now.isoformat()}
