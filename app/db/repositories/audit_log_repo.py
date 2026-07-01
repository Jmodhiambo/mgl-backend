#!/usr/bin/env python3
"""Repository layer for AuditLog.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select

from app.db.models.audit_log import AuditLog
from app.db.session import get_async_session
from app.schemas.audit_log import AuditLogCreate, AuditLogOut


# ─── Write ────────────────────────────────────────────────────────────────────

async def create_audit_log_repo(data: AuditLogCreate) -> AuditLogOut:
    """Append one audit-log entry.

    FIX: Pass the dict directly to the JSON column — SQLAlchemy + PostgreSQL
    handle serialisation internally.  The old code called json.dumps() first,
    which produced a TEXT string that PostgreSQL's JSON column rejected (422).
    """
    async with get_async_session() as session:
        row = AuditLog(
            admin_id=data.admin_id,
            admin_name=data.admin_name,
            action=data.action,
            target_type=data.target_type,
            target_id=data.target_id,
            details=data.details or {},   # ← dict, NOT json.dumps(...)
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return AuditLogOut.model_validate(row)


# ─── Read ─────────────────────────────────────────────────────────────────────

async def get_audit_log_by_id_repo(log_id: int) -> Optional[AuditLogOut]:
    """Fetch a single audit-log entry by primary key."""
    async with get_async_session() as session:
        result = await session.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        row = result.scalar_one_or_none()
        return AuditLogOut.model_validate(row) if row else None


async def list_audit_logs_repo(
    admin_id: Optional[int] = None,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    limit: int = 200,
    offset: int = 0,
) -> list[AuditLogOut]:
    """Filtered, paginated list — every param is optional."""
    async with get_async_session() as session:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc())

        if admin_id is not None:
            stmt = stmt.where(AuditLog.admin_id == admin_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if target_type:
            stmt = stmt.where(AuditLog.target_type == target_type)
        if from_dt:
            stmt = stmt.where(AuditLog.created_at >= from_dt)
        if to_dt:
            stmt = stmt.where(AuditLog.created_at <= to_dt)

        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [AuditLogOut.model_validate(r) for r in rows]


async def count_audit_logs_repo(
    admin_id: Optional[int] = None,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> int:
    """Count matching rows — used to build the total field in paginated responses."""
    async with get_async_session() as session:
        stmt = select(func.count()).select_from(AuditLog)

        if admin_id is not None:
            stmt = stmt.where(AuditLog.admin_id == admin_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if target_type:
            stmt = stmt.where(AuditLog.target_type == target_type)
        if from_dt:
            stmt = stmt.where(AuditLog.created_at >= from_dt)
        if to_dt:
            stmt = stmt.where(AuditLog.created_at <= to_dt)

        result = await session.execute(stmt)
        return result.scalar_one()


async def list_audit_logs_for_admin_repo(admin_id: int, limit: int = 15) -> list[AuditLogOut]:
    """Most recent entries for one admin, newest-first — used by the profile
    'My Activity' tab."""
    return await list_audit_logs_repo(admin_id=admin_id, limit=limit)