"""
OpenAPI aggregator: fetch specs from backend services and merge into one document.
"""

import logging
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

# Service base URLs (Docker service names; override via env if needed)
OPENAPI_SOURCES = [
    ("auth", "http://auth:8004/openapi.json"),
    ("data", "http://data:8001/openapi.json"),
    ("train", "http://train:8002/openapi.json"),
    ("predict", "http://predict:8003/openapi.json"),
]

# Retries for fetching each spec at startup
FETCH_RETRIES = 10
FETCH_RETRY_DELAY_S = 2


def _deep_merge_components(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """Merge source components into target; first occurrence wins for schemas."""
    if not source:
        return
    for key, value in source.items():
        if key not in target:
            target[key] = value
            continue
        if (
            key == "schemas"
            and isinstance(value, dict)
            and isinstance(target[key], dict)
        ):
            for schema_name, schema_def in value.items():
                if schema_name not in target[key]:
                    target[key][schema_name] = schema_def
        elif isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge_components(target[key], value)
        # else: keep target (first wins)


def _merge_tags(
    existing: List[Dict[str, Any]], new_tags: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Merge tag lists; deduplicate by name, keep first."""
    seen: set[str] = {t.get("name") for t in existing if t.get("name")}
    for t in new_tags or []:
        name = t.get("name")
        if name and name not in seen:
            seen.add(name)
            existing.append(t)
    return existing


async def fetch_spec(
    client: httpx.AsyncClient, name: str, url: str
) -> Dict[str, Any] | None:
    """Fetch OpenAPI spec from a single service."""
    try:
        r = await client.get(url, timeout=10.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Failed to fetch OpenAPI from %s (%s): %s", name, url, e)
        return None


def merge_openapi_specs(
    specs: List[Dict[str, Any]], server_url: str = "/"
) -> Dict[str, Any]:
    """
    Merge multiple OpenAPI 3.x specs into one.
    - Paths: combined (no path overlap across services).
    - Tags: merged and deduplicated by name.
    - Components (schemas, etc.): merged; first occurrence wins on name clash.
    - info/servers: set to a single gateway-oriented value.
    """
    merged: Dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": "MLOps API",
            "version": "0.1.0",
            "description": "Unified API for MLOps microservices (auth, data, train, predict).",
        },
        "servers": [{"url": server_url}],
        "paths": {},
        "tags": [],
        "components": {"schemas": {}},
    }

    for spec in specs:
        if not spec or not isinstance(spec, dict):
            continue
        paths = spec.get("paths") or {}
        for path, path_item in paths.items():
            if path not in merged["paths"]:
                merged["paths"][path] = dict(path_item) if path_item else {}
            else:
                merged["paths"][path].update(path_item or {})
        _merge_tags(merged["tags"], spec.get("tags"))
        comp = spec.get("components") or {}
        _deep_merge_components(merged["components"], comp)

    return merged


async def fetch_and_merge(
    sources: List[tuple[str, str]] | None = None,
    server_url: str = "/",
    retries: int = FETCH_RETRIES,
    retry_delay_s: float = FETCH_RETRY_DELAY_S,
) -> Dict[str, Any]:
    """
    Fetch OpenAPI from each source (with retries) and return merged spec.
    Raises RuntimeError if any source fails after all retries.
    """
    import asyncio

    sources = sources or OPENAPI_SOURCES
    specs: List[Dict[str, Any]] = []
    async with httpx.AsyncClient() as client:
        for name, url in sources:
            for attempt in range(1, retries + 1):
                spec = await fetch_spec(client, name, url)
                if spec is not None:
                    specs.append(spec)
                    logger.info("Fetched OpenAPI from %s", name)
                    break
                if attempt < retries:
                    logger.info(
                        "Retry %s/%s for %s in %ss",
                        attempt,
                        retries,
                        name,
                        retry_delay_s,
                    )
                    await asyncio.sleep(retry_delay_s)
            else:
                raise RuntimeError(
                    f"Docs aggregator: failed to fetch OpenAPI from {name} ({url}) after {retries} attempts"
                )
    return merge_openapi_specs(specs, server_url=server_url)
