import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.models import AuditLog, AsyncTask, Patient, User
from app.schemas import WhahaWebhookPayload, WebhookAckResponse

router = APIRouter(prefix="/webhook", tags=["webhook"])

settings = get_settings()


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    if not settings.WHAHA_WEBHOOK_SECRET:
        return True
    expected = hmac.new(
        settings.WHAHA_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def _log_audit(
    db: AsyncSession,
    action: str,
    status: str,
    patient_id: str | None = None,
    user_id: str | None = None,
    ip_address: str = "0.0.0.0",
    request_id: str = "",
    error_message: str | None = None,
):
    log = AuditLog(
        user_id=user_id,
        patient_id=patient_id,
        action_type=action,
        status=status,
        ip_address=ip_address,
        request_id=request_id,
        error_message=error_message,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)


async def _resolve_user_by_phone(db: AsyncSession, phone: str) -> User | None:
    clean = phone.replace("+", "").strip()
    result = await db.execute(select(User).where(User.phone == clean))
    return result.scalar_one_or_none()


async def _find_patient_by_name(db: AsyncSession, name: str) -> Patient | None:
    result = await db.execute(
        select(Patient).where(Patient.full_name.ilike(f"%{name}%"))
    )
    return result.scalars().first()


@router.post("/whatsapp", response_model=WebhookAckResponse)
async def whatsapp_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    signature = request.headers.get("X-Whaha-Signature", "")

    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        data = json.loads(body)
        payload = WhahaWebhookPayload(**data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")

    if not payload.messages:
        return WebhookAckResponse(job_id="empty", estimated_time="0 minutes")

    msg = payload.messages[0]
    job_id = str(uuid.uuid4())
    request_id = msg.id
    phone = msg.from_
    command = msg.body.strip()

    user = await _resolve_user_by_phone(db, phone)

    await _log_audit(
        db,
        action="WEBHOOK_RECEIVED",
        status="success",
        user_id=str(user.id) if user else None,
        ip_address=request.client.host if request.client else "0.0.0.0",
        request_id=request_id,
    )

    task_type, patient_name = _parse_command(command)

    if not task_type:
        await _log_audit(
            db,
            action="WEBHOOK_RECEIVED",
            status="error",
            user_id=str(user.id) if user else None,
            ip_address=request.client.host if request.client else "0.0.0.0",
            request_id=request_id,
            error_message=f"Unrecognized command: {command}",
        )
        await db.commit()
        return WebhookAckResponse(job_id=job_id, estimated_time="N/A - unknown command")

    patient = await _find_patient_by_name(db, patient_name) if patient_name else None

    task = AsyncTask(
        id=uuid.uuid4(),
        task_type=task_type,
        patient_id=str(patient.id) if patient else None,
        status="pending",
        input_data={
            "phone": phone,
            "command": command,
            "patient_name": patient_name,
            "user_id": str(user.id) if user else None,
        },
    )
    db.add(task)

    await _log_audit(
        db,
        action=f"{'ORGANIZE_START' if task_type == 'organize_exams' else 'REPORT_REQUEST'}",
        status="success",
        patient_id=str(patient.id) if patient else None,
        user_id=str(user.id) if user else None,
        ip_address=request.client.host if request.client else "0.0.0.0",
        request_id=request_id,
    )

    await db.commit()

    return WebhookAckResponse(job_id=job_id, estimated_time="2-3 minutes")


def _parse_command(command: str) -> tuple[str | None, str | None]:
    """Parse natural language command from WhatsApp message."""
    cmd_lower = command.lower()

    organize_patterns = ["organize exames", "organizar exames", "organize documents"]
    report_patterns = ["gere relatório", "gerar relatório", "generate report"]
    history_patterns = ["histórico", "historico", "history"]
    audit_patterns = ["audit log", "auditoria"]

    for pattern in organize_patterns:
        if pattern in cmd_lower:
            name = (
                command.lower().split(pattern)[-1].strip().lstrip("de do da ").strip()
            )
            return ("organize_exams", name if name else None)

    for pattern in report_patterns:
        if pattern in cmd_lower:
            name = command.lower().split(pattern)[-1].strip()
            name = name.split("ref")[0].strip().lstrip("de do da para ").strip()
            return ("generate_report", name if name else None)

    for pattern in history_patterns:
        if pattern in cmd_lower:
            name = (
                command.lower().split(pattern)[-1].strip().lstrip("de do da ").strip()
            )
            return ("view_history", name if name else None)

    for pattern in audit_patterns:
        if pattern in cmd_lower:
            return ("audit_query", None)

    return (None, None)
