"""
Postgres-backed job store for persisting job logs and metadata between runs.

Uses the same async interface as JobStore; sync DB calls run in a thread pool.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Union

from services.common.database import JobModel, create_tables_if_postgres, get_session
from services.common.job_store import Job, JobStatus, JobStore


def _row_to_job(row: JobModel) -> Job:
    """Convert DB row to Job dataclass."""
    return Job(
        id=row.id,
        job_type=row.job_type,
        status=JobStatus(row.status),
        created_at=row.created_at or datetime.utcnow(),
        started_at=row.started_at,
        completed_at=row.completed_at,
        progress=row.progress or 0.0,
        message=row.message or "",
        result=row.result,
        error=row.error,
        created_by=row.created_by,
        parameters=row.parameters,
        logs=(row.logs or []) if isinstance(row.logs, list) else [],
    )


def _job_to_row(job: Job) -> dict:
    """Convert Job to dict for upsert."""
    return {
        "id": job.id,
        "job_type": job.job_type,
        "status": job.status.value,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "progress": job.progress,
        "message": job.message,
        "result": job.result,
        "error": job.error,
        "created_by": job.created_by,
        "parameters": job.parameters,
        "logs": job.logs,
    }


def _sync_create_job(
    job_type: str,
    created_by: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
) -> Job:
    with get_session() as session:
        job = Job(
            id=str(uuid.uuid4()),
            job_type=job_type,
            created_by=created_by,
            parameters=parameters,
        )
        row = JobModel(**_job_to_row(job))
        session.add(row)
        session.flush()
        return _row_to_job(row)


def _sync_get_job(job_id: str) -> Optional[Job]:
    with get_session() as session:
        row = session.get(JobModel, job_id)
        return _row_to_job(row) if row else None


def _sync_update_job(
    job_id: str,
    status: Optional[JobStatus] = None,
    progress: Optional[float] = None,
    message: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    logs: Optional[List[str]] = None,
) -> Optional[Job]:
    with get_session() as session:
        row = session.get(JobModel, job_id)
        if not row:
            return None
        if status is not None:
            row.status = status.value
            if status == JobStatus.RUNNING and row.started_at is None:
                row.started_at = datetime.utcnow()
            elif status in (
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
            ):
                row.completed_at = datetime.utcnow()
        if progress is not None:
            row.progress = min(max(progress, 0.0), 100.0)
        if message is not None:
            row.message = message
        if result is not None:
            row.result = result
        if error is not None:
            row.error = error
        if logs is not None:
            row.logs = logs
        session.flush()
        return _row_to_job(row)


def _sync_list_jobs(
    job_type: Optional[Union[str, Sequence[str]]] = None,
    status: Optional[JobStatus] = None,
    created_by: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Job]:
    from sqlalchemy import desc, select

    with get_session() as session:
        q = select(JobModel).order_by(desc(JobModel.created_at))
        if job_type:
            if isinstance(job_type, str):
                q = q.where(JobModel.job_type == job_type)
            else:
                types_list = list(job_type)
                if types_list:
                    q = q.where(JobModel.job_type.in_(types_list))
        if status:
            q = q.where(JobModel.status == status.value)
        if created_by:
            q = q.where(JobModel.created_by == created_by)
        q = q.offset(offset).limit(limit)
        result = session.execute(q)
        rows = result.scalars().all()
        return [_row_to_job(r) for r in rows]


def _sync_count_jobs(
    job_type: Optional[Union[str, Sequence[str]]] = None,
    status: Optional[JobStatus] = None,
    created_by: Optional[str] = None,
) -> int:
    from sqlalchemy import func, select

    with get_session() as session:
        q = select(func.count()).select_from(JobModel)
        if job_type:
            if isinstance(job_type, str):
                q = q.where(JobModel.job_type == job_type)
            else:
                types_list = list(job_type)
                if types_list:
                    q = q.where(JobModel.job_type.in_(types_list))
        if status:
            q = q.where(JobModel.status == status.value)
        if created_by:
            q = q.where(JobModel.created_by == created_by)
        return session.execute(q).scalar() or 0


def _sync_cancel_job(job_id: str) -> Optional[Job]:
    job = _sync_get_job(job_id)
    if not job or job.status not in (JobStatus.PENDING, JobStatus.RUNNING):
        return None
    return _sync_update_job(
        job_id,
        status=JobStatus.CANCELLED,
        message="Job cancelled by user",
    )


def _sync_delete_job(job_id: str) -> bool:
    with get_session() as session:
        row = session.get(JobModel, job_id)
        if not row:
            return False
        session.delete(row)
        session.flush()
        return True


def _sync_get_stats() -> Dict[str, Any]:
    from sqlalchemy import func, select

    with get_session() as session:
        total_q = select(func.count()).select_from(JobModel)
        total = session.execute(total_q).scalar() or 0
        by_status_q = select(JobModel.status, func.count()).group_by(JobModel.status)
        by_status = {row[0]: row[1] for row in session.execute(by_status_q)}
        by_type_q = select(JobModel.job_type, func.count()).group_by(JobModel.job_type)
        by_type = {row[0]: row[1] for row in session.execute(by_type_q)}
    return {"total": total, "by_status": by_status, "by_type": by_type}


class PostgresJobStore(JobStore):
    """
    Postgres-backed job store. Same async API as JobStore; DB work runs in thread pool.
    """

    def __init__(self):
        create_tables_if_postgres()

    async def create_job(
        self,
        job_type: str,
        created_by: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Job:
        return await asyncio.to_thread(
            _sync_create_job, job_type, created_by, parameters
        )

    async def get_job(self, job_id: str) -> Optional[Job]:
        return await asyncio.to_thread(_sync_get_job, job_id)

    async def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        logs: Optional[List[str]] = None,
    ) -> Optional[Job]:
        return await asyncio.to_thread(
            _sync_update_job,
            job_id,
            status=status,
            progress=progress,
            message=message,
            result=result,
            error=error,
            logs=logs,
        )

    async def list_jobs(
        self,
        job_type: Optional[Union[str, Sequence[str]]] = None,
        status: Optional[JobStatus] = None,
        created_by: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Job]:
        return await asyncio.to_thread(
            _sync_list_jobs,
            job_type=job_type,
            status=status,
            created_by=created_by,
            limit=limit,
            offset=offset,
        )

    async def count_jobs(
        self,
        job_type: Optional[Union[str, Sequence[str]]] = None,
        status: Optional[JobStatus] = None,
        created_by: Optional[str] = None,
    ) -> int:
        return await asyncio.to_thread(
            _sync_count_jobs,
            job_type=job_type,
            status=status,
            created_by=created_by,
        )

    async def cancel_job(self, job_id: str) -> Optional[Job]:
        return await asyncio.to_thread(_sync_cancel_job, job_id)

    async def delete_job(self, job_id: str) -> bool:
        return await asyncio.to_thread(_sync_delete_job, job_id)

    async def get_stats(self) -> Dict[str, Any]:
        return await asyncio.to_thread(_sync_get_stats)
