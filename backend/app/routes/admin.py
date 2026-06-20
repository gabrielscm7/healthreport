import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import MedicalExam, Patient, AsyncTask, AuditLog
from app.schemas import AdminProcessRequest, AdminProcessResponse, ExamResponse
from app.security import get_current_user, require_role
from app.agents.admin_agent import (
    list_google_docs,
    read_google_doc,
    convert_to_markdown,
    upload_to_s3,
)
from app.utils.encryption import encrypt_aes256

router = APIRouter(prefix="/admin", tags=["admin"])


async def _log_audit(
    db: AsyncSession,
    action: str,
    status: str,
    patient_id: str | None = None,
    user_id: str | None = None,
    ip_address: str = "0.0.0.0",
    resource_type: str | None = None,
    error_message: str | None = None,
):
    log = AuditLog(
        user_id=user_id,
        patient_id=patient_id,
        action_type=action,
        resource_type=resource_type,
        status=status,
        ip_address=ip_address,
        error_message=error_message,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)


@router.post("/process", response_model=AdminProcessResponse)
async def process_documents(
    payload: AdminProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "doctor")),
):
    patient_result = await db.execute(
        select(Patient).where(Patient.id == payload.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    user_id = current_user["sub"]

    await _log_audit(
        db,
        "ORGANIZE_START",
        "success",
        patient_id=str(patient.id),
        user_id=user_id,
        resource_type="exam",
    )

    try:
        docs = list_google_docs(query=patient.full_name, limit=20)

        organized: dict[str, int] = {"lab_exams": 0, "imaging": 0, "other": 0}
        markdown_parts: list[str] = [f"# {patient.full_name}\n"]

        for doc in docs:
            content = read_google_doc(doc.get("id", ""))
            if not content:
                continue

            md_content = convert_to_markdown(content)
            doc_type = doc.get("type", "other")

            ciphertext, nonce, tag = encrypt_aes256(md_content)

            exam = MedicalExam(
                id=uuid.uuid4(),
                patient_id=patient.id,
                exam_type=doc.get("exam_type", "document"),
                exam_date=doc.get("date", datetime.now(timezone.utc).date()),
                content_encrypted=ciphertext,
                content_nonce=nonce.hex(),
                content_tag=tag.hex(),
                google_doc_id=doc.get("id"),
                markdown_content_encrypted=ciphertext,
                uploaded_by=uuid.UUID(user_id) if user_id else None,
            )
            db.add(exam)

            markdown_parts.append(f"## {doc.get('title', 'Documento')}\n{md_content}")

            if doc_type in ("lab", "laboratorial"):
                organized["lab_exams"] += 1
            elif doc_type in ("imaging", "imagenologia", "image"):
                organized["imaging"] += 1
            else:
                organized["other"] += 1

        full_md = "\n".join(markdown_parts)
        storage_url = upload_to_s3(f"{patient.id}/exams_organized.md", full_md)

        task = AsyncTask(
            id=uuid.uuid4(),
            task_type="organize_exams",
            patient_id=str(patient.id),
            status="completed",
            input_data={"query": payload.query, "patient_id": str(payload.patient_id)},
            output_data={"documents_found": len(docs), "organized": organized},
            completed_at=datetime.now(timezone.utc),
        )
        db.add(task)

        await _log_audit(
            db,
            "ORGANIZE_SUCCESS",
            "success",
            patient_id=str(patient.id),
            user_id=user_id,
            resource_type="exam",
        )

        await db.commit()

        return AdminProcessResponse(
            status="success",
            documents_found=len(docs),
            documents_organized=organized,
            markdown_reference=f"ref_{str(patient.id)[:8]}",
            storage_url=storage_url,
        )

    except Exception as e:
        await _log_audit(
            db,
            "ORGANIZE_ERROR",
            "error",
            patient_id=str(patient.id),
            user_id=user_id,
            resource_type="exam",
            error_message=str(e),
        )
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/exams/{patient_id}", response_model=list[ExamResponse])
async def list_patient_exams(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(MedicalExam)
        .where(MedicalExam.patient_id == patient_id, MedicalExam.deleted_at.is_(None))
        .order_by(MedicalExam.exam_date.desc())
    )
    return result.scalars().all()
