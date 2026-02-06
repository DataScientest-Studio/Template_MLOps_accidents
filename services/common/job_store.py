"""
Async Job Store for MLOps microservices.

Provides in-memory job tracking for long-running operations like:
- Data preprocessing
- Model training

For production, consider replacing with Redis or a database backend.
"""

import asyncio
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union


class JobStatus(str, Enum):
    """Status of an async job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Types of async jobs."""

    PREPROCESSING = "preprocessing"
    FEATURE_ENGINEERING = "feature_engineering"
    TRAINING = "training"
    FETCH_BEST_MODEL = "fetch_best_model"


@dataclass
class Job:
    """Represents an async job."""

    id: str
    job_type: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_by: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    logs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for API responses."""
        return {
            "job_id": self.id,
            "job_type": self.job_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_by": self.created_by,
            "logs": self.logs,
        }


class JobStore:
    """
    In-memory job store for tracking async operations.

    Thread-safe using asyncio locks. Jobs are stored in an OrderedDict
    to maintain insertion order and enable FIFO eviction when max capacity
    is reached.

    For production deployments, consider replacing with:
    - Redis: Fast, persistent, supports pub/sub for real-time updates
    - PostgreSQL: Full persistence, queryable job history
    - Celery + Redis: Full job queue with retries and scheduling
    """

    def __init__(self, max_jobs: int = 1000):
        """
        Initialize the job store.

        Args:
            max_jobs: Maximum number of jobs to keep in memory.
                      Oldest jobs are evicted when limit is reached.
        """
        self._jobs: OrderedDict[str, Job] = OrderedDict()
        self._max_jobs = max_jobs
        self._lock = asyncio.Lock()

    async def create_job(
        self,
        job_type: str,
        created_by: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Job:
        """
        Create a new job.

        Args:
            job_type: Type of job (e.g., "training", "preprocessing")
            created_by: Username of the user who created the job
            parameters: Optional parameters for the job

        Returns:
            The created Job instance
        """
        async with self._lock:
            # Evict oldest jobs if limit reached
            while len(self._jobs) >= self._max_jobs:
                self._jobs.popitem(last=False)

            job = Job(
                id=str(uuid.uuid4()),
                job_type=job_type,
                created_by=created_by,
                parameters=parameters,
            )
            self._jobs[job.id] = job
            return job

    async def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get a job by ID.

        Args:
            job_id: The job ID to look up

        Returns:
            The Job if found, None otherwise
        """
        return self._jobs.get(job_id)

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
        """
        Update a job's status and/or progress.

        Args:
            job_id: The job ID to update
            status: New status (optional)
            progress: Progress percentage 0-100 (optional)
            message: Status message (optional)
            result: Job result data (optional)
            error: Error message if failed (optional)
            logs: Full list of log lines (optional)

        Returns:
            The updated Job if found, None otherwise
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None

            if status is not None:
                job.status = status
                if status == JobStatus.RUNNING and job.started_at is None:
                    job.started_at = datetime.utcnow()
                elif status in (
                    JobStatus.COMPLETED,
                    JobStatus.FAILED,
                    JobStatus.CANCELLED,
                ):
                    job.completed_at = datetime.utcnow()

            if progress is not None:
                job.progress = min(max(progress, 0.0), 100.0)

            if message is not None:
                job.message = message

            if result is not None:
                job.result = result

            if error is not None:
                job.error = error

            if logs is not None:
                job.logs = logs

            return job

    async def list_jobs(
        self,
        job_type: Optional[Union[str, Sequence[str]]] = None,
        status: Optional[JobStatus] = None,
        created_by: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Job]:
        """
        List jobs with optional filtering, sorted by created_at descending.

        Args:
            job_type: Filter by job type (optional)
            status: Filter by status (optional)
            created_by: Filter by creator (optional)
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip (for pagination)

        Returns:
            List of matching jobs (newest first)
        """
        jobs = list(self._jobs.values())

        # Apply filters
        job_types = None
        if job_type:
            if isinstance(job_type, str):
                job_types = [job_type]
            else:
                job_types = list(job_type)
        if job_types:
            jobs = [j for j in jobs if j.job_type in job_types]
        if status:
            jobs = [j for j in jobs if j.status == status]
        if created_by:
            jobs = [j for j in jobs if j.created_by == created_by]

        # Sort by created_at descending (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[offset : offset + limit]

    async def count_jobs(
        self,
        job_type: Optional[Union[str, Sequence[str]]] = None,
        status: Optional[JobStatus] = None,
        created_by: Optional[str] = None,
    ) -> int:
        """
        Count jobs matching optional filters (for pagination total).

        Args:
            job_type: Filter by job type (optional)
            status: Filter by status (optional)
            created_by: Filter by creator (optional)

        Returns:
            Total number of matching jobs
        """
        jobs = list(self._jobs.values())
        job_types = None
        if job_type:
            if isinstance(job_type, str):
                job_types = [job_type]
            else:
                job_types = list(job_type)
        if job_types:
            jobs = [j for j in jobs if j.job_type in job_types]
        if status:
            jobs = [j for j in jobs if j.status == status]
        if created_by:
            jobs = [j for j in jobs if j.created_by == created_by]
        return len(jobs)

    async def cancel_job(self, job_id: str) -> Optional[Job]:
        """
        Cancel a pending or running job.

        Args:
            job_id: The job ID to cancel

        Returns:
            The cancelled Job if found and cancellable, None otherwise
        """
        job = self._jobs.get(job_id)
        if not job:
            return None

        if job.status in (JobStatus.PENDING, JobStatus.RUNNING):
            return await self.update_job(
                job_id,
                status=JobStatus.CANCELLED,
                message="Job cancelled by user",
            )
        return None

    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from the store.

        Args:
            job_id: The job ID to delete

        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get job store statistics.

        Returns:
            Dictionary with job counts by status
        """
        stats = {
            "total": len(self._jobs),
            "by_status": {},
            "by_type": {},
        }

        for job in self._jobs.values():
            # Count by status
            status_key = job.status.value
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1

            # Count by type
            stats["by_type"][job.job_type] = stats["by_type"].get(job.job_type, 0) + 1

        return stats


# Global job store instance (shared within each service).
# Uses Postgres when DATABASE_URL is postgresql (sync driver); otherwise in-memory.
def _get_job_store() -> JobStore:
    from services.common import database

    if database._is_postgres():
        from services.common.job_store_postgres import PostgresJobStore

        return PostgresJobStore()
    return JobStore()


job_store = _get_job_store()
