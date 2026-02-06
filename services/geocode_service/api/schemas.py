"""
Pydantic schemas for geocoding service API.
"""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class GeocodeRequest(BaseModel):
    """Request payload for geocoding a single address."""

    address: str = Field(..., description="Address string to geocode", min_length=1)


class GeocodeResponse(BaseModel):
    """Response payload for geocoding result."""

    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    display_name: str = Field(..., description="Formatted display name of the location")
    address: Dict = Field(default_factory=dict, description="Structured address components")


class GeocodeSuggestRequest(BaseModel):
    """Request payload for address suggestions."""

    query: str = Field(..., description="Partial address query for autocomplete", min_length=1)
    limit: int = Field(default=5, ge=1, le=10, description="Maximum number of suggestions")


class AddressSuggestion(BaseModel):
    """Single address suggestion."""

    address: str = Field(..., description="Formatted address string")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    display_name: str = Field(..., description="Display name")


class GeocodeSuggestResponse(BaseModel):
    """Response payload for address suggestions."""

    suggestions: List[AddressSuggestion] = Field(
        default_factory=list, description="List of address suggestions"
    )


class ErrorResponse(BaseModel):
    """Error response payload."""

    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error detail message")
