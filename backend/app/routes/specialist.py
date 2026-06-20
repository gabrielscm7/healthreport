import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import (
    AuditLog,
    AsyncTask,
    MedicalExam,
    MedicalReport,
    Patient,
    PatientConsent,
    DoctorPatientAccess,
)
from app.schemas import (
    SpecialistRequest,
    SpecialistResponse,
    ReportResponse,
    ReportDetailResponse,
    ReportContent,
)
from app.security import get_current_user, require_role
from app.agents.specialist_agent import run_report

router = APIRouter(prefix="/specialist", tags=["specialist"])


async def _check_consent(db: AsyncSession, patient_id: str) -> bool:
    result = await db.execute(
        select(PatientConsent).where(
            PatientConsent.patient_id == patient_id,
            PatientConsent.expires_at > datetime.now(timezone.utc),
        )
    )
    return result.scalar_one_or_none() is not None


async def _check_doctor_access(
    db: AsyncSession, doctor_id: str, patient_id: str
) -> bool:
    result = await db.execute(
        select(DoctorPatientAccess).where(
            DoctorPatientAccess.doctor_id == doctor_id,
            DoctorPatientAccess.patient_id == patient_id,
            DoctorPatientAccess.access_revoked_at.is_(None),
        )
    )
    return result.scalar_one_or_none() is not None


async def _log_audit(
    db: AsyncSession,
    action: str,
    status: str,
    patient_id: str | None = None,
    user_id: str | None = None,
    ip_address: str = "0.0.0.0",
    error_message: str | None = None,
):
    log = AuditLog(
        user_id=user_id,
        patient_id=patient_id,
        action_type=action,
        status=status,
        ip_address=ip_address,
        error_message=error_message,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)


@router.post("/report", response_model=SpecialistResponse)
async def generate_report(
    payload: SpecialistRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "doctor")),
):
    doctor_id = current_user["sub"]
    patient_id = str(payload.patient_id)

    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    has_consent = await _check_consent(db, patient_id)
    has_access = await _check_doctor_access(db, doctor_id, patient_id)

    if current_user["role"] != "admin" and not has_access:
        await _log_audit(
            db,
            "REPORT_REQUEST",
            "denied",
            patient_id=patient_id,
            user_id=doctor_id,
            error_message="No access to patient",
        )
        await db.commit()
        raise HTTPException(
            status_code=403, detail="You do not have access to this patient"
        )

    if not has_consent:
        await _log_audit(
            db,
            "REPORT_REQUEST",
            "denied",
            patient_id=patient_id,
            user_id=doctor_id,
            error_message="Missing patient consent",
        )
        await db.commit()
        raise HTTPException(
            status_code=403, detail="Patient consent is required and missing/expired"
        )

    await _log_audit(
        db,
        "REPORT_REQUEST",
        "success",
        patient_id=patient_id,
        user_id=doctor_id,
    )

    try:
        result = run_report(payload.exams_markdown)

        exams_result = await db.execute(
            select(MedicalExam).where(
                MedicalExam.patient_id == patient_id,
                MedicalExam.deleted_at.is_(None),
            )
        )
        exams = exams_result.scalars().all()

        report = MedicalReport(
            id=uuid.uuid4(),
            patient_id=uuid.UUID(patient_id),
            requesting_doctor_id=uuid.UUID(doctor_id),
            exams_used=[exam.id for exam in exams],
            report_content_encrypted=b"",
            report_nonce="",
            report_tag="",
            report_format="json",
            model_version="claude-opus-4-6",
            model_confidence=0.95,
            status="success",
        )
        db.add(report)

        await _log_audit(
            db,
            "REPORT_SUCCESS",
            "success",
            patient_id=patient_id,
            user_id=doctor_id,
        )

        task = AsyncTask(
            id=uuid.uuid4(),
            task_type="generate_report",
            patient_id=patient_id,
            status="completed",
            input_data={"patient_id": patient_id, "doctor_id": doctor_id},
            output_data=result,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(task)

        await db.commit()

        return SpecialistResponse(
            status="success",
            report_id=report.id,
            estimated_time="completed",
        )

    except Exception as e:
        await _log_audit(
            db,
            "REPORT_ERROR",
            "error",
            patient_id=patient_id,
            user_id=doctor_id,
            error_message=str(e),
        )
        await db.commit()
        raise HTTPException(
            status_code=500, detail=f"Report generation failed: {str(e)}"
        )


@router.get("/reports/{patient_id}", response_model=list[ReportResponse])
async def list_reports(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(MedicalReport)
        .where(MedicalReport.patient_id == patient_id)
        .order_by(MedicalReport.generated_at.desc())
    )
    return result.scalars().all()


@router.get("/report/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(MedicalReport).where(MedicalReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
