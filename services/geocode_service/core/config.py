"""
Configuration for geocoding service.
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class GeocodeSettings(BaseSettings):
    """Geocoding service settings."""

    # Provider selection
    GEOCODE_PROVIDER: Literal["nominatim", "google"] = "nominatim"

    # Nominatim configuration
    NOMINATIM_BASE_URL: str = "https://nominatim.openstreetmap.org"
    NOMINATIM_USER_AGENT: str = "MLOps-Accidents-Geocoding/1.0"
    GEOCODE_RATE_LIMIT_PER_SECOND: float = 1.0

    # Google Geocoding API configuration (for future use)
    GOOGLE_GEOCODING_API_KEY: str = ""

    class Config:
        """Pydantic settings configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_geocode_settings() -> GeocodeSettings:
    """Get cached geocoding settings."""
    return GeocodeSettings()
