"""JWT-aware HTTP client for backend API."""

from __future__ import annotations

import logging
import streamlit as st
import httpx
import streamlit as st

from ..auth import TOKEN_KEY, get_api_base

logger = logging.getLogger(__name__)


def get_client() -> httpx.Client | None:
    """
    Return an httpx client with Bearer token from session.
    Returns None if not authenticated. Caller should use for a single request and not hold.
    """
    token = st.session_state.get(TOKEN_KEY)
    if not token:
        return None
    return httpx.Client(
        base_url=get_api_base(),
        timeout=30.0,
        headers={"Authorization": f"Bearer {token}"},
    )


def post(path: str, **kwargs) -> httpx.Response | None:
    """POST to API. Returns response or None if not authenticated."""
    client = get_client()
    if client is None:
        return None
    with client:
        return client.post(path, **kwargs)


def get(path: str, **kwargs) -> httpx.Response | None:
    """GET from API. Returns response or None if not authenticated."""
    client = get_client()
    if client is None:
        return None
    with client:
        return client.get(path, **kwargs)


def put(path: str, **kwargs) -> httpx.Response | None:
    """PUT to API. Returns response or None if not authenticated."""
    client = get_client()
    if client is None:
        return None
    with client:
        return client.put(path, **kwargs)


def delete(path: str, **kwargs) -> httpx.Response | None:
    """DELETE to API. Returns response or None if not authenticated."""
    client = get_client()
    if client is None:
        return None
    with client:
        return client.delete(path, **kwargs)


def geocode_address(address: str) -> dict | None:
    """
    Geocode an address to latitude/longitude.

    Args:
        address: Address string to geocode

    Returns:
        Dict with latitude, longitude, display_name, address or None if failed
    """
    resp = post("/api/v1/geocode/", json={"address": address})
    if resp is None:
        return None
    if resp.status_code == 200:
        return resp.json()
    return None


def suggest_addresses(query: str, limit: int = 5) -> list[dict]:
    """
    Get address suggestions for autocomplete.

    Args:
        query: Partial address query
        limit: Maximum number of suggestions (default: 5)

    Returns:
        List of suggestion dicts with address, latitude, longitude, display_name
    """
    resp = post("/api/v1/geocode/suggest", json={"query": query, "limit": limit})
    if resp is None:
        return []
    if resp.status_code == 200:
        data = resp.json()
        return data.get("suggestions", [])
    return []


def check_geocode_health() -> bool:
    """
    Check if geocoding service is available.

    Returns:
        True if service is healthy, False otherwise
    """
    try:
        resp = get("/api/v1/geocode/health")
        if resp is None:
            logger.warning(
                "Geocoding service health check failed: No response (likely not authenticated)"
            )
            return False
        
        if resp.status_code == 200:
            logger.debug("Geocoding service health check passed")
            return True
        else:
            # Log detailed error information
            error_detail = "Unknown error"
            try:
                error_data = resp.json()
                error_detail = error_data.get("detail", str(resp.text))
            except Exception:
                error_detail = f"HTTP {resp.status_code}: {resp.text[:200]}"
            
            logger.warning(
                f"Geocoding service health check failed: HTTP {resp.status_code} - {error_detail}"
            )
            return False
    except httpx.RequestError as e:
        logger.error(
            f"Geocoding service health check failed: Request error - {type(e).__name__}: {e}",
            exc_info=True
        )
        return False
    except Exception as e:
        logger.error(
            f"Geocoding service health check failed: Unexpected error - {type(e).__name__}: {e}",
            exc_info=True
        )
        return False
