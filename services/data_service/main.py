"""
Data service FastAPI application.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.common.config import settings
from services.common.models import HealthResponse

from .api.routes import router as data_router

app = FastAPI(title="MLOps Data Service", version="0.1.0")

logging.getLogger().setLevel(logging.INFO)

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


app.include_router(data_router)
