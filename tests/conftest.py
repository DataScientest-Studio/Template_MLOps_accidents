"""
Pytest configuration and shared fixtures for API endpoint testing.

This module provides:
- Configurable base URLs for all services
- Authentication fixtures (admin and regular user tokens)
- HTTP client fixtures
- Test data fixtures
"""

import os
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient

# =============================================================================
# Configuration
# =============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "auth: marks tests related to authentication")
    config.addinivalue_line("markers", "data: marks tests related to data service")
    config.addinivalue_line("markers", "train: marks tests related to train service")
    config.addinivalue_line(
        "markers", "predict: marks tests related to predict service"
    )
    config.addinivalue_line("markers", "integration: marks integration tests")


# =============================================================================
# Base URL Configuration
# =============================================================================


def get_base_url(service: str = None) -> str:
    """
    Get base URL for a service.

    Supports configuration via:
    1. Environment variable (e.g., BASE_URL, AUTH_SERVICE_URL)
    2. Default to localhost with standard ports

    Args:
        service: Service name ('auth', 'data', 'train', 'predict', or None for nginx)

    Returns:
        Base URL string
    """
    # Check for service-specific environment variable
    if service:
        env_var = f"{service.upper()}_SERVICE_URL"
        url = os.getenv(env_var)
        if url:
            return url.rstrip("/")

    # Check for general base URL (for nginx/reverse proxy)
    base_url = os.getenv("BASE_URL") or os.getenv("TARGET_IP", "http://localhost")
    base_url = base_url.rstrip("/")

    # If BASE_URL is set, use it with service-specific paths
    if service and base_url != "http://localhost":
        # Assume BASE_URL points to nginx, use API paths
        service_paths = {
            "auth": "/api/v1/auth",
            "data": "/api/v1/data",
            "train": "/api/v1/train",
            "predict": "/api/v1/predict",
        }
        return f"{base_url}{service_paths.get(service, '')}"

    # Default ports for direct service access
    default_ports = {
        "auth": 8004,
        "data": 8001,
        "train": 8002,
        "predict": 8003,
    }

    if service and service in default_ports:
        port = default_ports[service]
        # Extract host from BASE_URL if it's a full URL, otherwise use localhost
        if base_url.startswith("http"):
            # Extract hostname from URL
            from urllib.parse import urlparse

            parsed = urlparse(base_url)
            host = parsed.hostname or "localhost"
            return f"http://{host}:{port}/api/v1/{service}"
        return f"http://localhost:{port}/api/v1/{service}"

    # For nginx/reverse proxy (no service specified)
    if not base_url.startswith("http"):
        base_url = f"http://{base_url}"
    return base_url


# =============================================================================
# HTTP Client Fixtures
# =============================================================================


@pytest.fixture
def auth_base_url() -> str:
    """Base URL for auth service."""
    return get_base_url("auth")


@pytest.fixture
def data_base_url() -> str:
    """Base URL for data service."""
    return get_base_url("data")


@pytest.fixture
def train_base_url() -> str:
    """Base URL for train service."""
    return get_base_url("train")


@pytest.fixture
def predict_base_url() -> str:
    """Base URL for predict service."""
    return get_base_url("predict")


@pytest.fixture
def nginx_base_url() -> str:
    """Base URL for nginx reverse proxy."""
    return get_base_url()


@pytest.fixture
def auth_health_url() -> str:
    """Health check URL for auth service."""
    return get_health_url("auth")


@pytest.fixture
def data_health_url() -> str:
    """Health check URL for data service."""
    return get_health_url("data")


@pytest.fixture
def train_health_url() -> str:
    """Health check URL for train service."""
    return get_health_url("train")


@pytest.fixture
def predict_health_url() -> str:
    """Health check URL for predict service."""
    return get_health_url("predict")


def get_health_url(service: str) -> str:
    """
    Get health check URL for a service.

    When using nginx (BASE_URL is set), health endpoints are at /api/v1/{service}/health.
    When accessing services directly, health endpoints are at the root /health.

    Args:
        service: Service name ('auth', 'data', 'train', 'predict')

    Returns:
        Health check URL string
    """
    # Check if we're using nginx (BASE_URL is set to something other than localhost)
    base_url_env = os.getenv("BASE_URL") or os.getenv("TARGET_IP", "")

    if base_url_env and "localhost" not in base_url_env:
        # Using nginx - health endpoints are proxied at /api/v1/{service}/health
        base = base_url_env.rstrip("/")
        if not base.startswith("http"):
            base = f"http://{base}"
        return f"{base}/api/v1/{service}/health"

    # Direct service access - health endpoint is at root /health
    base_url = get_base_url(service)
    if f"/api/v1/{service}" in base_url:
        # Extract service root URL (e.g., http://localhost:8004)
        service_root = base_url.replace(f"/api/v1/{service}", "")
        return f"{service_root}/health"
    return f"{base_url}/health"


@pytest.fixture
async def http_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client fixture.

    Yields:
        httpx.AsyncClient instance
    """
    # 60s so predict (first-request model load) and other services are not starved under load
    async with AsyncClient(timeout=60.0, follow_redirects=True) as client:
        yield client


# =============================================================================
# Authentication Fixtures
# =============================================================================


@pytest.fixture
def admin_credentials() -> dict:
    """Admin credentials for testing (from env: ADMIN_USERNAME, ADMIN_PASSWORD)."""
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin")
    if len(username) < 3:
        username = "admin"
    if len(password) < 8:
        password = "admin"
    return {
        "username": username,
        "password": password,
    }


@pytest.fixture
def regular_user_credentials() -> dict:
    """Regular user credentials for testing (from env: TEST_USER_USERNAME, TEST_USER_PASSWORD).
    Password must be at least 8 characters per auth API; short env values are replaced with default.
    """
    username = os.getenv("TEST_USER_USERNAME", "testuser")
    password = os.getenv("TEST_USER_PASSWORD", "TestUser@123")
    if len(password) < 8:
        password = "TestUser@123"
    return {"username": username, "password": password}


@pytest.fixture
async def admin_token(
    http_client: AsyncClient, auth_base_url: str, admin_credentials: dict
) -> str:
    """
    Get admin access token.

    Args:
        http_client: HTTP client fixture
        auth_base_url: Auth service base URL
        admin_credentials: Admin credentials fixture

    Returns:
        JWT access token string

    Raises:
        AssertionError: If login fails
    """
    import asyncio

    # Retry logic for service startup
    max_retries = 5
    retry_delay = 2.0
    last_response = None

    for attempt in range(max_retries):
        response = await http_client.post(
            f"{auth_base_url}/login",
            json=admin_credentials,
        )
        last_response = response

        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            return data["access_token"]

        # If 503, 502 (service unavailable) or 429 (rate limit), wait and retry
        if response.status_code in (502, 503, 429) and attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
            continue

        # For other errors (401, etc.), fail immediately
        if response.status_code != 200:
            break

    # If we get here, login failed
    assert last_response is not None, "No response received"
    assert (
        last_response.status_code == 200
    ), f"Login failed after {max_retries} attempts: {last_response.status_code} - {last_response.text}"


@pytest.fixture
async def user_token(
    http_client: AsyncClient,
    auth_base_url: str,
    admin_token: str,
    regular_user_credentials: dict,
) -> str:
    """
    Get regular user access token.

    Creates a test user if it doesn't exist, then logs in.

    Args:
        http_client: HTTP client fixture
        auth_base_url: Auth service base URL
        admin_token: Admin token for user creation
        regular_user_credentials: Regular user credentials

    Returns:
        JWT access token string

    Raises:
        AssertionError: If user creation or login fails
    """
    import asyncio

    # Try to create user (may fail if user exists, which is OK)
    headers = {"Authorization": f"Bearer {admin_token}"}
    user_data = {
        **regular_user_credentials,
        "email": "testuser@example.com",
        "full_name": "Test User",
        "role": "user",
    }

    # Retry user creation in case of transient errors
    user_created = False
    created_user_id = None
    for attempt in range(3):
        create_response = await http_client.post(
            f"{auth_base_url}/users",
            json=user_data,
            headers=headers,
        )
        # Success (200/201) or user already exists (400) are both OK
        if create_response.status_code in (200, 201, 400):
            user_created = True
            if create_response.status_code in (200, 201):
                created_user_id = create_response.json().get("id")
            break
        # If we get 401/403, admin token might be invalid - fail fast
        if create_response.status_code in (401, 403):
            raise AssertionError(
                f"User creation failed with {create_response.status_code}: {create_response.text}. "
                f"Admin token may be invalid."
            )
        # Retry on 5xx errors
        if create_response.status_code >= 500 and attempt < 2:
            await asyncio.sleep(1.0)
            continue

    if not user_created:
        raise AssertionError(
            f"Failed to create user after 3 attempts. Last response: {create_response.status_code} - {create_response.text}"
        )

    # Login as regular user with retry logic
    max_retries = 5
    retry_delay = 2.0
    last_response = None

    for attempt in range(max_retries):
        response = await http_client.post(
            f"{auth_base_url}/login",
            json=regular_user_credentials,
        )
        last_response = response

        if response.status_code == 200:
            data = response.json()
            assert (
                "access_token" in data
            ), f"Login response missing access_token: {data}"
            token = data["access_token"]
            # Verify token is not empty
            assert token, "Access token is empty"
            try:
                yield token
            finally:
                # Teardown: remove the test user we created (only if we created it this run)
                if created_user_id is not None:
                    await http_client.delete(
                        f"{auth_base_url}/users/{created_user_id}",
                        headers=headers,
                    )
            return

        # If 401, user might not exist yet - wait and retry (user creation might be async)
        if response.status_code == 401 and attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
            continue

        # If 502/503 (service unavailable), wait and retry
        if response.status_code in (502, 503) and attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
            continue

        # For other errors (400, 422, etc.), fail immediately
        if response.status_code != 200:
            break

    # If we get here, login failed
    assert last_response is not None, "No response received"
    error_msg = (
        f"User login failed after {max_retries} attempts.\n"
        f"Status: {last_response.status_code}\n"
        f"Response: {last_response.text}\n"
        f"User credentials: username={regular_user_credentials.get('username')}"
    )
    assert last_response.status_code == 200, error_msg


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """Headers with admin authorization."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_headers(user_token: str) -> dict:
    """Headers with regular user authorization."""
    return {"Authorization": f"Bearer {user_token}"}


# =============================================================================
# Test Raw Data (for data service preprocessing tests)
# =============================================================================


def get_test_raw_dir() -> str:
    """Directory for test raw data (used by data service preprocessing tests)."""
    from pathlib import Path

    return os.getenv("TEST_RAW_DIR") or str(
        Path(__file__).resolve().parent.parent / "data" / "test" / "raw"
    )


def ensure_test_raw_data() -> None:
    """
    Ensure test raw directory contains the four required CSVs.
    Downloads from S3 if any are missing; skips download if all are present.
    """
    raw_dir = get_test_raw_dir()
    try:
        from src.data.make_dataset import discover_raw_file_paths

        discover_raw_file_paths(raw_dir)
        return  # all four files already present
    except FileNotFoundError:
        pass  # at least one file missing, run import
    from src.data.import_raw_data import import_raw_data

    import_raw_data(
        raw_data_relative_path=raw_dir,
        filenames=[
            "caracteristiques-2021.csv",
            "lieux-2021.csv",
            "usagers-2021.csv",
            "vehicules-2021.csv",
        ],
        bucket_folder_url="https://mlops-project-db.s3.eu-west-1.amazonaws.com/accidents/",
    )


@pytest.fixture(scope="session")
def ensure_test_raw_data_session():
    """
    Session-scoped fixture: ensure test raw data directory is populated
    before any data service preprocessing tests run.
    """
    ensure_test_raw_data()


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def sample_prediction_features() -> dict:
    """Sample features for prediction testing."""
    return {
        "age": 35,
        "sex": "M",
        "vehicle_type": "car",
        "weather": "clear",
        "road_type": "highway",
        "time_of_day": "morning",
    }


@pytest.fixture
def sample_batch_features() -> list:
    """Sample batch features for prediction testing."""
    return [
        {"age": 25, "sex": "F", "vehicle_type": "motorcycle", "weather": "rain"},
        {"age": 45, "sex": "M", "vehicle_type": "truck", "weather": "clear"},
        {"age": 30, "sex": "M", "vehicle_type": "car", "weather": "snow"},
    ]


@pytest.fixture
def invalid_token() -> str:
    """Invalid JWT token for testing."""
    return "invalid.token.here"


@pytest.fixture
def expired_token() -> str:
    """Expired JWT token for testing (if needed)."""
    # This is a placeholder - in real tests you'd generate an expired token
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxNjAwMDAwMDAwfQ.invalid"
