"""
Authentication service FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from services.common.config import settings
from services.common.models import HealthResponse

from .api.routes import router as auth_router

# Auth service body size limit (64KB) so even without Nginx we reject huge bodies
AUTH_MAX_BODY_BYTES = 64 * 1024


class LimitBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject requests with body larger than max_bytes (Content-Length check)."""

    def __init__(self, app, max_bytes: int = AUTH_MAX_BODY_BYTES):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": "Request body too large",
                            "max_bytes": self.max_bytes,
                        },
                    )
            except ValueError:
                pass
        return await call_next(request)


app = FastAPI(title="MLOps Auth Service", version="0.1.0")

app.add_middleware(LimitBodySizeMiddleware, max_bytes=AUTH_MAX_BODY_BYTES)
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


app.include_router(auth_router)
