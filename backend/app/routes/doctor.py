from datetime import datetime, timezone, date
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Patient, MedicalExam, MedicalReport, DoctorPatientAccess
from app.security import get_current_user

router = APIRouter(prefix="/doctor", tags=["doctor"])


@router.get("/dashboard")
async def doctor_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    doctor_id = current_user["sub"]

    patients_result = await db.execute(
        select(Patient)
        .join(DoctorPatientAccess, DoctorPatientAccess.patient_id == Patient.id)
        .where(
            DoctorPatientAccess.doctor_id == doctor_id,
            DoctorPatientAccess.access_revoked_at.is_(None),
        )
    )
    patients = patients_result.scalars().all()
    patient_count = len(patients)

    patient_ids = [str(p.id) for p in patients]

    reports_count = 0
    recent_reports = []
    if patient_ids:
        reports_result = await db.execute(
            select(MedicalReport)
            .where(MedicalReport.patient_id.in_(patient_ids))
            .order_by(MedicalReport.generated_at.desc())
            .limit(10)
        )
        reports_data = reports_result.scalars().all()
        reports_count = len(reports_data)
        recent_reports = [
            {
                "report_id": str(r.id),
                "patient_id": str(r.patient_id),
                "status": r.status,
                "generated_at": r.generated_at.isoformat(),
                "model_version": r.model_version,
            }
            for r in reports_data
        ]

    exams_count = 0
    if patient_ids:
        exams_result = await db.execute(
            select(func.count(MedicalExam.id)).where(
                MedicalExam.patient_id.in_(patient_ids),
                MedicalExam.deleted_at.is_(None),
            )
        )
        exams_count = exams_result.scalar() or 0

    results = []
    for p in patients:
        p_reports = await db.execute(
            select(func.count(MedicalReport.id)).where(MedicalReport.patient_id == str(p.id))
        )
        p_exams = await db.execute(
            select(func.count(MedicalExam.id)).where(
                MedicalExam.patient_id == str(p.id),
                MedicalExam.deleted_at.is_(None),
            )
        )
        results.append({
            "patient_id": str(p.id),
            "patient_name": p.full_name,
            "reports_count": p_reports.scalar() or 0,
            "exams_count": p_exams.scalar() or 0,
        })

    return {
        "doctor_id": doctor_id,
        "total_patients": patient_count,
        "total_reports": reports_count,
        "total_exams": exams_count,
        "recent_reports": recent_reports[:5],
        "patients": results,
    }
