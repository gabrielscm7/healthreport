from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import MedicalExam, MedicalReport, Patient
from app.schemas import ExamResponse, ReportResponse
from app.security import get_current_user

router = APIRouter(prefix="/patient", tags=["patient"])


@router.get("/{patient_id}/exams", response_model=list[ExamResponse])
async def list_patient_exams(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    if not patient_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Patient not found")

    result = await db.execute(
        select(MedicalExam)
        .where(MedicalExam.patient_id == patient_id, MedicalExam.deleted_at.is_(None))
        .order_by(MedicalExam.exam_date.desc())
    )
    return result.scalars().all()


@router.get("/{patient_id}/reports", response_model=list[ReportResponse])
async def list_patient_reports(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    if not patient_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Patient not found")

    result = await db.execute(
        select(MedicalReport)
        .where(MedicalReport.patient_id == patient_id)
        .order_by(MedicalReport.generated_at.desc())
    )
    return result.scalars().all()
