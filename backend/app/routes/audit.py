from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import AuditLog
from app.schemas import AuditLogResponse, AuditLogListResponse
from app.security import require_role

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    patient_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    action_type: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "auditor")),
):
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    if patient_id:
        query = query.where(AuditLog.patient_id == patient_id)
        count_query = count_query.where(AuditLog.patient_id == patient_id)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)
    if action_type:
        query = query.where(AuditLog.action_type == action_type)
        count_query = count_query.where(AuditLog.action_type == action_type)
    if date_from:
        query = query.where(AuditLog.timestamp >= date_from)
        count_query = count_query.where(AuditLog.timestamp >= date_from)
    if date_to:
        query = query.where(AuditLog.timestamp <= date_to)
        count_query = count_query.where(AuditLog.timestamp <= date_to)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return AuditLogListResponse(
        total=total,
        logs=[AuditLogResponse.model_validate(log) for log in logs],
    )


@router.get("/logs/export")
async def export_audit_logs(
    patient_id: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "auditor")),
):
    query = select(AuditLog)

    if patient_id:
        query = query.where(AuditLog.patient_id == patient_id)
    if date_from:
        query = query.where(AuditLog.timestamp >= date_from)
    if date_to:
        query = query.where(AuditLog.timestamp <= date_to)

    query = query.order_by(AuditLog.timestamp.desc()).limit(10000)
    result = await db.execute(query)
    logs = result.scalars().all()

    header = "id,user_id,patient_id,action_type,resource_type,status,ip_address,timestamp\n"
    rows = [
        f"{log.id},{log.user_id},{log.patient_id},{log.action_type},{log.resource_type},{log.status},{log.ip_address},{log.timestamp.isoformat()}"
        for log in logs
    ]
    return {"content": header + "\n".join(rows), "format": "csv", "total": len(logs)}
