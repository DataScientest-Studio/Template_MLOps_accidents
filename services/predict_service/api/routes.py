"""
FastAPI routes for the predict service.
"""

import asyncio

from fastapi import APIRouter, Depends, Request

from services.common.dependencies import AuthenticatedUser

from ..core.predictor import make_batch_prediction, make_prediction
from .schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    PredictionRequest,
    PredictionResponse,
)

router = APIRouter(prefix="/api/v1/predict", tags=["predict"])


def get_model_cache(request: Request):
    """Dependency: cached model loaded at startup."""
    return request.app.state.model_cache


@router.post("/", response_model=PredictionResponse)
async def single_prediction(
    request: PredictionRequest,
    current_user: AuthenticatedUser,
    model_cache=Depends(get_model_cache),
):
    """Make a single prediction using the loaded Production model."""
    result = await asyncio.to_thread(
        make_prediction,
        features=request.features,
        model_cache=model_cache,
    )
    return PredictionResponse(
        prediction=result["prediction"],
        probability=result["probability"],
        model_type=result["model_type"],
    )


@router.post("/batch", response_model=BatchPredictionResponse)
async def batch_prediction(
    request: BatchPredictionRequest,
    current_user: AuthenticatedUser,
    model_cache=Depends(get_model_cache),
):
    """Make batch predictions using the loaded Production model."""
    result = await asyncio.to_thread(
        make_batch_prediction,
        features_list=request.features_list,
        model_cache=model_cache,
    )
    return BatchPredictionResponse(
        predictions=result["predictions"],
        probabilities=result["probabilities"],
        count=result["count"],
        model_type=result["model_type"],
    )


@router.get("/models")
async def list_loaded_model(
    current_user: AuthenticatedUser,
    model_cache=Depends(get_model_cache),
):
    """Return the currently loaded Production model (loaded at container start)."""
    return {
        "loaded_model_type": model_cache["model_type"],
        "source": "MLflow Production (best by f1_score)",
    }
