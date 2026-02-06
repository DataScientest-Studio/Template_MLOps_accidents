"""
Geocoding providers - abstract base and implementations.

Nominatim Usage Policy Compliance:
- Rate limiting: Maximum 1 request per second (enforced)
- User-Agent: Custom User-Agent required (set)
- Attribution: Must display "© OpenStreetMap contributors" to end users
- ODbL License: Data provided under ODbL license
- NO Auto-complete: Nominatim Usage Policy prohibits autocomplete search
- Caching: Results are cached to reduce API calls
"""
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict

import requests

from .config import GeocodeSettings, get_geocode_settings

logger = logging.getLogger(__name__)


@dataclass
class GeocodeResult:
    """Result from geocoding operation."""

    latitude: float
    longitude: float
    display_name: str
    address: dict
    raw_data: dict


class GeocoderBase(ABC):
    """Abstract base class for geocoding providers."""

    @abstractmethod
    def geocode(self, address: str) -> Optional[GeocodeResult]:
        """
        Geocode a single address.

        Args:
            address: Address string to geocode

        Returns:
            GeocodeResult if found, None otherwise
        """
        pass

    @abstractmethod
    def suggest(self, query: str, limit: int = 5) -> List[GeocodeResult]:
        """
        Get address suggestions for autocomplete.

        Args:
            query: Partial address query
            limit: Maximum number of suggestions

        Returns:
            List of GeocodeResult suggestions
        """
        pass


class NominatimGeocoder(GeocoderBase):
    """
    Nominatim geocoding provider.
    
    Complies with Nominatim Usage Policy:
    - Rate limiting: 1 request/second
    - User-Agent: Custom User-Agent set
    - Caching: Results cached to reduce API calls
    - NO Autocomplete: suggest() returns empty list per policy
    """

    def __init__(self, settings: Optional[GeocodeSettings] = None):
        """
        Initialize Nominatim geocoder.

        Args:
            settings: Geocoding settings (uses defaults if not provided)
        """
        self.settings = settings or get_geocode_settings()
        self.base_url = self.settings.NOMINATIM_BASE_URL.rstrip("/")
        self.user_agent = self.settings.NOMINATIM_USER_AGENT
        self.rate_limit = self.settings.GEOCODE_RATE_LIMIT_PER_SECOND
        self.last_request_time = 0.0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        # Cache for geocoding results (per-instance, cleared on restart)
        self._geocode_cache: Dict[str, Optional[GeocodeResult]] = {}

    def _rate_limit_wait(self):
        """Wait if necessary to respect rate limit."""
        now = time.time()
        time_since_last = now - self.last_request_time
        min_interval = 1.0 / self.rate_limit

        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            time.sleep(wait_time)

        self.last_request_time = time.time()

    def geocode(self, address: str) -> Optional[GeocodeResult]:
        """
        Geocode a single address using Nominatim.
        
        Results are cached to reduce API calls per Nominatim Usage Policy.

        Args:
            address: Address string to geocode

        Returns:
            GeocodeResult if found, None otherwise
        """
        if not address or not address.strip():
            return None

        # Check cache first (per Nominatim policy: cache results)
        address_key = address.strip().lower()
        if address_key in self._geocode_cache:
            logger.debug(f"Returning cached result for: {address}")
            cached_result = self._geocode_cache[address_key]
            # Return a copy to avoid modifying cached data
            if cached_result is None:
                return None
            return GeocodeResult(
                latitude=cached_result.latitude,
                longitude=cached_result.longitude,
                display_name=cached_result.display_name,
                address=cached_result.address.copy(),
                raw_data=cached_result.raw_data.copy(),
            )

        self._rate_limit_wait()

        try:
            url = f"{self.base_url}/search"
            params = {
                "q": address.strip(),
                "format": "json",
                "limit": 1,
                "addressdetails": 1,
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if not data or len(data) == 0:
                logger.info(f"No results found for address: {address}")
                self._geocode_cache[address_key] = None
                return None

            result = data[0]
            geocode_result = GeocodeResult(
                latitude=float(result["lat"]),
                longitude=float(result["lon"]),
                display_name=result.get("display_name", address),
                address=result.get("address", {}),
                raw_data=result,
            )

            # Cache the result (per Nominatim policy)
            self._geocode_cache[address_key] = geocode_result
            return geocode_result

        except requests.exceptions.RequestException as e:
            logger.error(f"Geocoding request failed for '{address}': {e}")
            return None
        except (KeyError, ValueError, IndexError) as e:
            logger.error(f"Invalid response format for '{address}': {e}")
            return None

    def suggest(self, query: str, limit: int = 5) -> List[GeocodeResult]:
        """
        Get address suggestions for autocomplete.
        
        WARNING: Nominatim Usage Policy prohibits autocomplete search!
        This method returns an empty list to comply with the policy.
        Use Google Geocoding API provider for autocomplete functionality.

        Args:
            query: Partial address query
            limit: Maximum number of suggestions (ignored for Nominatim)

        Returns:
            Empty list (autocomplete not supported by Nominatim per usage policy)
        """
        logger.warning(
            "Autocomplete/suggestions are prohibited by Nominatim Usage Policy. "
            "This method returns empty results. Switch to Google Geocoding API provider "
            "for autocomplete functionality."
        )
        return []


class GoogleGeocoder(GeocoderBase):
    """Google Geocoding API provider (placeholder for future implementation)."""

    def __init__(self, settings: Optional[GeocodeSettings] = None):
        """
        Initialize Google geocoder.

        Args:
            settings: Geocoding settings (uses defaults if not provided)
        """
        self.settings = settings or get_geocode_settings()
        self.api_key = self.settings.GOOGLE_GEOCODING_API_KEY

        if not self.api_key:
            logger.warning(
                "Google Geocoding API key not configured. "
                "Google geocoder will not work."
            )

    def geocode(self, address: str) -> Optional[GeocodeResult]:
        """
        Geocode a single address using Google Geocoding API.

        Args:
            address: Address string to geocode

        Returns:
            GeocodeResult if found, None otherwise

        Note:
            This is a placeholder implementation. To be implemented when
            Google Geocoding API integration is needed.
        """
        logger.warning("Google Geocoding API not yet implemented")
        return None

    def suggest(self, query: str, limit: int = 5) -> List[GeocodeResult]:
        """
        Get address suggestions using Google Places API.

        Args:
            query: Partial address query
            limit: Maximum number of suggestions

        Returns:
            List of GeocodeResult suggestions

        Note:
            This is a placeholder implementation. To be implemented when
            Google Places API integration is needed.
        """
        logger.warning("Google Places API suggestions not yet implemented")
        return []


def get_geocoder(settings: Optional[GeocodeSettings] = None) -> GeocoderBase:
    """
    Factory function to get the configured geocoder instance.

    Args:
        settings: Geocoding settings (uses defaults if not provided)

    Returns:
        GeocoderBase instance based on GEOCODE_PROVIDER setting
    """
    if settings is None:
        settings = get_geocode_settings()

    provider = settings.GEOCODE_PROVIDER.lower()

    if provider == "nominatim":
        return NominatimGeocoder(settings)
    elif provider == "google":
        return GoogleGeocoder(settings)
    else:
        logger.warning(
            f"Unknown geocoding provider '{provider}', defaulting to Nominatim"
        )
        return NominatimGeocoder(settings)
