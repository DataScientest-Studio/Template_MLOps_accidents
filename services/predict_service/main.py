"""
Predict service FastAPI application.

The best Production model from MLflow is loaded once at container startup
and reused for all prediction requests. The train service operates
independently and registers models to MLflow; this service only reads from it.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.common.config import settings
from services.common.models import HealthResponse

from .api.routes import router as predict_router

logger = logging.getLogger(__name__)

# Config path relative to project root (WORKDIR /app in container)
MODEL_CONFIG_PATH = "src/config/model_config.yaml"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the best Production model from MLflow once at startup."""
    from src.models.predict_model import load_best_production_model

    try:
        model, label_encoders, metadata, model_type = load_best_production_model(
            config_path=MODEL_CONFIG_PATH,
        )
    except Exception as e:
        logger.exception("Failed to load best Production model from MLflow at startup")
        raise RuntimeError(
            "Predict service requires a Production model in MLflow. "
            "Ensure MLFLOW_TRACKING_URI is set and at least one model is in Production."
        ) from e

    app.state.model_cache = {
        "model": model,
        "label_encoders": label_encoders,
        "metadata": metadata,
        "model_type": model_type,
    }
    logger.info("Loaded best Production model from MLflow (model_type=%s)", model_type)
    yield
    # Shutdown: nothing to release


app = FastAPI(
    title="MLOps Predict Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    """Service liveness probe."""
    return HealthResponse(service=settings.SERVICE_NAME)


app.include_router(predict_router)
