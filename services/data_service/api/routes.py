"""
FastAPI routes for the data service.
"""

import asyncio
import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from services.common.config import Settings
from services.common.dependencies import AdminUser, SettingsDep
from services.common.job_runner import run_sync_with_streaming_logs
from services.common.job_store import JobStatus as StoreJobStatus
from services.common.job_store import JobType, job_store
from services.common.models import (
    JobResponse,
    JobsListResponse,
)
from services.common.models import JobStatus as ApiJobStatus

from ..core.features import build_feature_dataset
from ..core.preprocessing import preprocess_data
from .schemas import BuildFeaturesRequest, PreprocessRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/data", tags=["data"])


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _job_to_response(job) -> JobResponse:
    return JobResponse(
        job_id=job.id,
        status=ApiJobStatus(job.status.value),
        job_type=job.job_type,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        result=job.result,
        error=job.error,
        progress=job.progress,
        message=job.message or None,
        logs=job.logs if job.logs else None,
    )


_DATA_LOG_PREFIXES = ("src.", "services.data_service.")


async def _run_preprocess_job(
    job_id: str, request: PreprocessRequest, settings: Settings
):
    raw_dir = request.raw_dir or settings.RAW_DATA_DIR
    preprocessed_dir = request.preprocessed_dir or settings.PREPROCESSED_DATA_DIR

    await job_store.update_job(
        job_id,
        status=StoreJobStatus.RUNNING,
        progress=5.0,
        message="Preprocessing started",
    )

    result, exc = await run_sync_with_streaming_logs(
        job_id,
        preprocess_data,
        raw_dir,
        preprocessed_dir,
        log_prefixes=_DATA_LOG_PREFIXES,
        update_interval_seconds=2.0,
    )
    if exc is not None:
        logger.exception("Preprocessing job failed")
        await job_store.update_job(
            job_id,
            status=StoreJobStatus.FAILED,
            progress=100.0,
            message="Preprocessing failed",
            error=str(exc),
        )
    else:
        await job_store.update_job(
            job_id,
            status=StoreJobStatus.COMPLETED,
            progress=100.0,
            message="Preprocessing completed",
            result=result,
        )


async def _run_feature_job(
    job_id: str, request: BuildFeaturesRequest, settings: Settings
):
    preprocessed_dir = request.preprocessed_dir or settings.PREPROCESSED_DATA_DIR
    interim_path = request.interim_path or os.path.join(
        preprocessed_dir, "interim_dataset.csv"
    )
    models_dir = request.models_dir or settings.MODELS_DIR

    await job_store.update_job(
        job_id,
        status=StoreJobStatus.RUNNING,
        progress=5.0,
        message="Feature engineering started",
    )

    result, exc = await run_sync_with_streaming_logs(
        job_id,
        build_feature_dataset,
        interim_path,
        preprocessed_dir,
        models_dir,
        request.cyclic_encoding,
        request.interactions,
        log_prefixes=_DATA_LOG_PREFIXES,
        update_interval_seconds=2.0,
    )
    if exc is not None:
        logger.exception("Feature job failed")
        await job_store.update_job(
            job_id,
            status=StoreJobStatus.FAILED,
            progress=100.0,
            message="Feature engineering failed",
            error=str(exc),
        )
    else:
        await job_store.update_job(
            job_id,
            status=StoreJobStatus.COMPLETED,
            progress=100.0,
            message="Feature engineering completed",
            result=result,
        )


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


@router.post(
    "/preprocess", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED
)
async def start_preprocess(
    request: PreprocessRequest,
    current_user: AdminUser,
    settings: SettingsDep,
):
    """Trigger preprocessing job (admin-only)."""
    job = await job_store.create_job(
        job_type=JobType.PREPROCESSING.value,
        created_by=current_user.username,
        parameters=request.model_dump(),
    )

    asyncio.create_task(_run_preprocess_job(job.id, request, settings))
    return _job_to_response(job)


@router.post(
    "/build-features", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED
)
async def start_feature_engineering(
    request: BuildFeaturesRequest,
    current_user: AdminUser,
    settings: SettingsDep,
):
    """Trigger feature engineering job (admin-only)."""
    job = await job_store.create_job(
        job_type=JobType.FEATURE_ENGINEERING.value,
        created_by=current_user.username,
        parameters=request.model_dump(),
    )

    asyncio.create_task(_run_feature_job(job.id, request, settings))
    return _job_to_response(job)


@router.get("/status/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, current_user: AdminUser):
    job = await job_store.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return _job_to_response(job)


_JOB_PAGE_SIZES = (10, 20, 50, 100)


@router.get("/jobs", response_model=JobsListResponse)
async def list_jobs(
    current_user: AdminUser,
    job_type: Optional[str] = Query(
        None, description="Filter by job type (comma-separated for multiple)"
    ),
    status_filter: Optional[ApiJobStatus] = Query(
        None, alias="status", description="Filter by job status"
    ),
    limit: int = Query(10, ge=1, le=100, description="Page size (10, 20, 50, or 100)"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
):
    if limit not in _JOB_PAGE_SIZES:
        limit = 10
    status_value = None
    if status_filter:
        status_value = StoreJobStatus(status_filter.value)

    job_types = None
    if job_type:
        job_types = [j.strip() for j in job_type.split(",") if j.strip()]
    else:
        job_types = [JobType.PREPROCESSING.value, JobType.FEATURE_ENGINEERING.value]

    jobs = await job_store.list_jobs(
        job_type=job_types,
        status=status_value,
        created_by=current_user.username,
        limit=limit,
        offset=offset,
    )
    total = await job_store.count_jobs(
        job_type=job_types,
        status=status_value,
        created_by=current_user.username,
    )
    return JobsListResponse(
        items=[_job_to_response(job) for job in jobs],
        total=total,
    )
