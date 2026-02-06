"""
Train service FastAPI application.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.common.config import settings
from services.common.models import HealthResponse

from .api.routes import router as train_router
from .core.config_io import ensure_config_exists

app = FastAPI(title="MLOps Train Service", version="0.1.0")

logging.getLogger().setLevel(logging.INFO)


@app.on_event("startup")
async def startup_ensure_config():
    """Copy default model config on first run if active path does not exist."""
    ensure_config_exists(settings.MODEL_CONFIG_PATH)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    return HealthResponse(service=settings.SERVICE_NAME)


app.include_router(train_router)
