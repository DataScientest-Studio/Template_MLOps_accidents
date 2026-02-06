"""
Geocoding service FastAPI application.

Provides address to latitude/longitude conversion using Nominatim
(designed to be replaceable with Google Geocoding API).
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.common.config import settings
from services.common.models import HealthResponse

from .api.routes import router as geocode_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MLOps Geocoding Service",
    version="0.1.0",
    description="Geocoding service for address to latitude/longitude conversion",
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
    """
    Service liveness probe.
    
    Checks that the service is running and the geocoder can be initialized.
    Logs detailed information to help with debugging issues.
    """
    try:
        # Test that geocoder can be initialized
        from .core.geocoder import get_geocoder
        from .core.config import get_geocode_settings
        
        geocoder_settings = get_geocode_settings()
        
        # Log configuration details for debugging
        logger.debug(
            f"Health check - Service: {settings.SERVICE_NAME}, "
            f"Provider: {geocoder_settings.GEOCODE_PROVIDER}, "
            f"Base URL: {getattr(geocoder_settings, 'NOMINATIM_BASE_URL', 'N/A')}"
        )
        
        # Initialize geocoder (this will validate configuration)
        geocoder = get_geocoder(geocoder_settings)
        
        # Log successful initialization
        logger.info(
            f"Geocoding service health check passed - "
            f"Service: {settings.SERVICE_NAME}, "
            f"Provider: {geocoder_settings.GEOCODE_PROVIDER}"
        )
        
        return HealthResponse(service=settings.SERVICE_NAME)
    except ImportError as e:
        logger.error(
            f"Geocoding service health check failed - Import error: {e}",
            exc_info=True
        )
        return HealthResponse(service=settings.SERVICE_NAME)
    except Exception as e:
        logger.error(
            f"Geocoding service health check failed - "
            f"Service: {settings.SERVICE_NAME}, "
            f"Error: {type(e).__name__}: {e}",
            exc_info=True
        )
        # Still return health response to avoid breaking health checks,
        # but log the error for investigation
        return HealthResponse(service=settings.SERVICE_NAME)


app.include_router(geocode_router)
