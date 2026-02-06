"""
FastAPI routes for geocoding service.
"""
import logging

from fastapi import APIRouter, HTTPException, status

from services.common.dependencies import AuthenticatedUser

from ..core.geocoder import get_geocoder
from .schemas import (
    GeocodeRequest,
    GeocodeResponse,
    GeocodeSuggestRequest,
    GeocodeSuggestResponse,
    AddressSuggestion,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/geocode", tags=["geocode"])


@router.post("/", response_model=GeocodeResponse)
async def geocode_address(
    request: GeocodeRequest,
    current_user: AuthenticatedUser,
):
    """
    Geocode a single address to latitude/longitude.

    When using Nominatim provider:
    - Data is provided under ODbL license
    - Attribution must be displayed: "© OpenStreetMap contributors"
    - Results are cached to reduce API calls
    - Rate limited to 1 request/second

    Args:
        request: GeocodeRequest with address string
        current_user: Authenticated user (required for access)

    Returns:
        GeocodeResponse with coordinates and address details

    Raises:
        HTTPException: If geocoding fails or address not found
    """
    geocoder = get_geocoder()

    try:
        result = geocoder.geocode(request.address)

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Address not found: {request.address}",
            )

        return GeocodeResponse(
            latitude=result.latitude,
            longitude=result.longitude,
            display_name=result.display_name,
            address=result.address,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Geocoding error for '{request.address}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Geocoding service error: {str(e)}",
        )


@router.post("/suggest", response_model=GeocodeSuggestResponse)
async def suggest_addresses(
    request: GeocodeSuggestRequest,
    current_user: AuthenticatedUser,
):
    """
    Get address suggestions for autocomplete.

    NOTE: Nominatim Usage Policy prohibits autocomplete search.
    This endpoint returns empty results when using Nominatim provider.
    Switch to Google Geocoding API provider for autocomplete functionality.

    Args:
        request: GeocodeSuggestRequest with query string and limit
        current_user: Authenticated user (required for access)

    Returns:
        GeocodeSuggestResponse with list of address suggestions (empty for Nominatim)
    """
    from ..core.config import get_geocode_settings

    settings = get_geocode_settings()
    
    # Nominatim does not support autocomplete per their usage policy
    if settings.GEOCODE_PROVIDER.lower() == "nominatim":
        logger.info(
            "Autocomplete not available with Nominatim provider (policy violation). "
            "Use Google Geocoding API provider for autocomplete."
        )
        return GeocodeSuggestResponse(suggestions=[])

    geocoder = get_geocoder()

    try:
        results = geocoder.suggest(request.query, limit=request.limit)

        suggestions = [
            AddressSuggestion(
                address=result.display_name,
                latitude=result.latitude,
                longitude=result.longitude,
                display_name=result.display_name,
            )
            for result in results
        ]

        return GeocodeSuggestResponse(suggestions=suggestions)

    except Exception as e:
        logger.error(f"Address suggestion error for '{request.query}': {e}", exc_info=True)
        # Return empty suggestions rather than error for better UX
        return GeocodeSuggestResponse(suggestions=[])
