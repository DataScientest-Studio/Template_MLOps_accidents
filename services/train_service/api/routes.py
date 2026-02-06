"""
FastAPI routes for the train service.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

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

from ..core.config_io import ensure_config_exists, load_config, save_config
from ..core.trainer import run_training
from .schemas import TrainRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/train", tags=["train"])


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _job_to_response(job) -> JobResponse:
    result = job.result
    if result is not None:
        result = _make_result_serializable(result)
    return JobResponse(
        job_id=job.id,
        status=ApiJobStatus(job.status.value),
        job_type=job.job_type,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        result=result,
        error=job.error,
        progress=job.progress,
        message=job.message or None,
        logs=job.logs if job.logs else None,
    )


_TRAIN_LOG_PREFIXES = ("src.", "services.train_service.")


def _make_result_serializable(obj: Any) -> Any:
    """Return a JSON-serializable copy of obj; replace non-serializable values with a placeholder."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _make_result_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_result_serializable(v) for v in obj]
    return f"<{type(obj).__name__}>"


async def _run_training_job(job_id: str, request: TrainRequest, settings: Settings):
    await job_store.update_job(
        job_id,
        status=StoreJobStatus.RUNNING,
        progress=5.0,
        message="Training started",
    )

    config_path = request.config_path or settings.MODEL_CONFIG_PATH
    result, exc = await run_sync_with_streaming_logs(
        job_id,
        run_training,
        request.models,
        request.grid_search,
        request.compare,
        config_path,
        request.config,
        log_prefixes=_TRAIN_LOG_PREFIXES,
        update_interval_seconds=2.0,
    )
    if exc is not None:
        logger.exception("Training job failed")
        await job_store.update_job(
            job_id,
            status=StoreJobStatus.FAILED,
            progress=100.0,
            message="Training failed",
            error=str(exc),
        )
    else:
        await job_store.update_job(
            job_id,
            status=StoreJobStatus.COMPLETED,
            progress=100.0,
            message="Training completed",
            result=_make_result_serializable(result),
        )


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


@router.post("/", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_training(
    request: TrainRequest,
    current_user: AdminUser,
    settings: SettingsDep,
):
    """Trigger model training (admin-only)."""
    job = await job_store.create_job(
        job_type=JobType.TRAINING.value,
        created_by=current_user.username,
        parameters=request.model_dump(),
    )

    asyncio.create_task(_run_training_job(job.id, request, settings))
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
        job_types = [JobType.TRAINING.value]

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


@router.get("/metrics/{model_type}")
async def get_model_metrics(
    model_type: str, current_user: AdminUser, settings: SettingsDep
):
    """Return saved metrics for a given model type."""
    metrics_dir = os.path.join(settings.DATA_DIR, "metrics")
    metrics_path = os.path.join(metrics_dir, f"{model_type}_metrics.json")

    if not os.path.exists(metrics_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metrics not found for model type '{model_type}'",
        )

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    return {"model_type": model_type, "metrics": metrics}


# -----------------------------------------------------------------------------
# Config API (structure matches src/config/model_config.yaml; Option A: dict)
# -----------------------------------------------------------------------------


@router.get("/config", response_model=Dict[str, Any])
async def get_config(
    current_user: AdminUser,
    settings: SettingsDep,
    path: Optional[str] = Query(
        None, description="Override config file path (default: MODEL_CONFIG_PATH)"
    ),
):
    """Return current training config as JSON (admin-only)."""
    if path is None:
        ensure_config_exists(settings.MODEL_CONFIG_PATH)
        config_path = settings.MODEL_CONFIG_PATH
    else:
        config_path = path
    if not Path(config_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Config file not found: {config_path}",
        )
    try:
        return load_config(config_path)
    except (OSError, ValueError) as e:
        logger.exception("Failed to load config from %s", config_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load config: {e}",
        ) from e


@router.put("/config", response_model=Dict[str, Any])
async def put_config(
    body: Dict[str, Any],
    current_user: AdminUser,
    settings: SettingsDep,
):
    """Update training config from JSON body; persists to MODEL_CONFIG_PATH (admin-only)."""
    config_path = settings.MODEL_CONFIG_PATH
    try:
        save_config(config_path, body)
        return load_config(config_path)
    except OSError as e:
        logger.exception("Failed to write config to %s", config_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write config: {e}",
        ) from e
