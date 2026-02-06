"""
Docs aggregator FastAPI application.
Fetches OpenAPI specs from auth, data, train, predict on startup and serves
a merged spec at /openapi.json and Swagger UI at /docs.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI

from services.common.models import HealthResponse

from .aggregator import fetch_and_merge

logger = logging.getLogger(__name__)

# Server URL for "Try it out" in Swagger UI (gateway root)
DOCS_SERVER_URL = "/"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Fetch and merge OpenAPI specs from all backend services at startup."""
    logger.info("Fetching OpenAPI specs from backend services...")
    try:
        merged = await fetch_and_merge(server_url=DOCS_SERVER_URL)
        app.state.merged_openapi = merged
        logger.info(
            "Merged OpenAPI spec ready (%s paths)", len(merged.get("paths", {}))
        )
    except Exception as e:
        logger.exception("Failed to build merged OpenAPI spec")
        raise RuntimeError("Docs service could not fetch backend specs") from e
    yield
    app.state.merged_openapi = None


app = FastAPI(
    title="MLOps API (Unified)",
    version="0.1.0",
    description="Unified API documentation for MLOps microservices (auth, data, train, predict).",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


def custom_openapi() -> Dict[str, Any]:
    """Return the merged OpenAPI spec (built at startup)."""
    if not hasattr(app.state, "merged_openapi") or app.state.merged_openapi is None:
        raise RuntimeError("Merged OpenAPI spec not available")
    return app.state.merged_openapi


app.openapi = custom_openapi  # type: ignore[assignment]


@app.get("/health", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    """Service liveness probe."""
    return HealthResponse(service="docs-service")
