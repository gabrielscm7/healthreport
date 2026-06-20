import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import MedicalExam, ExamComparison, AuditLog
from app.schemas import FindingItem, AlertItem, ReportContent
from app.security import get_current_user, require_role

router = APIRouter(prefix="/comparison", tags=["comparison"])


@router.post("/create")
async def compare_exams(
    patient_id: str,
    exam_before_id: str,
    exam_after_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "doctor")),
):
    before = await db.execute(
        select(MedicalExam).where(
            MedicalExam.id == exam_before_id,
            MedicalExam.patient_id == patient_id,
            MedicalExam.deleted_at.is_(None),
        )
    )
    exam_before = before.scalar_one_or_none()
    if not exam_before:
        raise HTTPException(status_code=404, detail="Before exam not found")

    after = await db.execute(
        select(MedicalExam).where(
            MedicalExam.id == exam_after_id,
            MedicalExam.patient_id == patient_id,
            MedicalExam.deleted_at.is_(None),
        )
    )
    exam_after = after.scalar_one_or_none()
    if not exam_after:
        raise HTTPException(status_code=404, detail="After exam not found")

    differences = {
        "exam_type": exam_after.exam_type,
        "date_before": str(exam_before.exam_date),
        "date_after": str(exam_after.exam_date),
        "same_type": exam_before.exam_type == exam_after.exam_type,
        "days_between": (exam_after.exam_date - exam_before.exam_date).days,
    }

    comparison = ExamComparison(
        id=uuid.uuid4(),
        patient_id=uuid.UUID(patient_id),
        exam_before_id=uuid.UUID(exam_before_id),
        exam_after_id=uuid.UUID(exam_after_id),
        differences=differences,
        generated_by=uuid.UUID(current_user["sub"]),
    )
    db.add(comparison)

    audit = AuditLog(
        user_id=current_user["sub"],
        patient_id=patient_id,
        action_type="COMPARISON_CREATED",
        resource_type="comparison",
        status="success",
        ip_address="0.0.0.0",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit)

    await db.flush()
    await db.refresh(comparison)

    return {
        "comparison_id": str(comparison.id),
        "differences": differences,
    }


@router.get("/{patient_id}")
async def list_comparisons(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(ExamComparison)
        .where(ExamComparison.patient_id == patient_id)
        .order_by(ExamComparison.created_at.desc())
    )
    comparisons = result.scalars().all()

    return [
        {
            "comparison_id": str(c.id),
            "exam_before_id": str(c.exam_before_id),
            "exam_after_id": str(c.exam_after_id),
            "differences": c.differences,
            "created_at": c.created_at.isoformat(),
        }
        for c in comparisons
    ]
