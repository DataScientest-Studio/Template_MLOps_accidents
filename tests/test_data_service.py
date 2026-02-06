"""
Test suite for Data Service API endpoints.

Tests cover:
- Health checks
- Preprocessing job creation and status
- Feature engineering job creation and status
- Job listing and filtering
- Authorization checks (admin-only endpoints)
"""

import pytest
from httpx import AsyncClient


@pytest.mark.data
class TestDataService:
    """Test suite for Data Service endpoints."""

    # =========================================================================
    # Health Check Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_health_check(self, http_client: AsyncClient, data_health_url: str):
        """Test health check endpoint."""
        response = await http_client.get(data_health_url)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    # =========================================================================
    # Preprocessing Job Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_start_preprocess_success(
        self,
        http_client: AsyncClient,
        data_base_url: str,
        admin_headers: dict,
    ):
        """Test starting preprocessing job with valid request."""
        request_data = {}
        response = await http_client.post(
            f"{data_base_url}/preprocess",
            json=request_data,
            headers=admin_headers,
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["job_type"] == "preprocessing"

    @pytest.mark.asyncio
    async def test_start_preprocess_with_custom_paths(
        self,
        http_client: AsyncClient,
        data_base_url: str,
        admin_headers: dict,
        ensure_test_raw_data_session,
    ):
        """Test starting preprocessing job with custom paths (writable test dir in container)."""
        request_data = {
            "raw_dir": "/app/data/test/raw",
            "preprocessed_dir": "/app/data/test/preprocessed",
        }
        response = await http_client.post(
            f"{data_base_url}/preprocess",
            json=request_data,
            headers=admin_headers,
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data

    @pytest.mark.asyncio
    async def test_start_preprocess_unauthorized(
        self,
        http_client: AsyncClient,
        data_base_url: str,
        user_headers: dict,
    ):
        """Test starting preprocessing job as regular user (should fail)."""
        response = await http_client.post(
            f"{data_base_url}/preprocess",
            json={},
            headers=user_headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_start_preprocess_no_auth(
        self, http_client: AsyncClient, data_base_url: str
    ):
        """Test starting preprocessing job without authentication."""
        response = await http_client.post(
            f"{data_base_url}/preprocess",
            json={},
        )
        assert response.status_code == 401

    # =========================================================================
    # Feature Engineering Job Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_start_build_features_success(
        self,
        http_client: AsyncClient,
        data_base_url: str,
        admin_headers: dict,
    ):
        """Test starting feature engineering job with valid request."""
        request_data = {}
        response = await http_client.post(
            f"{data_base_url}/build-features",
            json=request_data,
            headers=admin_headers,
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["job_type"] == "feature_engineering"

    @pytest.mark.asyncio
    async def test_start_build_features_with_options(
        self,
        http_client: AsyncClient,
        data_base_url: str,
        admin_headers: dict,
    ):
        """Test starting feature engineering job with custom options."""
        request_data = {
            "cyclic_encoding": False,
            "interactions": False,
        }
        response = await http_client.post(
            f"{data_base_url}/build-features",
            json=request_data,
            headers=admin_headers,
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data

    @pytest.mark.asyncio
    async def test_start_build_features_unauthorized(
        self,
        http_client: AsyncClient,
        data_base_url: str,
        user_headers: dict,
    ):
        """Test starting feature engineering job as regular user."""
        response = await http_client.post(
            f"{data_base_url}/build-features",
            json={},
            headers=user_headers,
        )
        assert response.status_code == 403

    # =========================================================================
    # Job Status Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_job_status_success(
        self,
        http_client: AsyncClient,
        data_base_url: str,
        admin_headers: dict,
    ):
        """Test getting job status for existing job."""
        # First create a job
        create_response = await http_client.post(
            f"{data_base_url}/preprocess",
            json={},
            headers=admin_headers,
        )
        assert create_response.status_code == 202
        job_id = create_response.json()["job_id"]

        # Get job status
        response = await http_client.get(
            f"{data_base_url}/status/{job_id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "job_type" in data

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(
        self,
        http_client: AsyncClient,
        data_base_url: str,
        admin_headers: dict,
    ):
        """Test getting status for non-existent job."""
        response = await http_client.get(
            f"{data_base_url}/status/nonexistent-job-id",
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_job_status_unauthorized(
        self,
        http_client: AsyncClient,
        data_base_url: str,
        user_headers: dict,
    ):
        """Test getting job status as regular user."""
        response = await http_client.get(
            f"{data_base_url}/status/some-job-id",
            headers=user_headers,
        )
        assert response.status_code == 403

    # =========================================================================
    # Job Listing Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_list_jobs_success(
        self,
        http_client: AsyncClient,
        data_base_url: str,
        admin_headers: dict,
    ):
        """Test listing all jobs (paginated response)."""
        response = await http_client.get(
            f"{data_base_url}/jobs",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "items" in data and "total" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_jobs_with_filters(
        self,
        http_client: AsyncClient,
        data_base_url: str,
        admin_headers: dict,
    ):
        """Test listing jobs with filters."""
        # Filter by job type
        response = await http_client.get(
            f"{data_base_url}/jobs?job_type=preprocessing",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "items" in data and "total" in data
        items = data["items"]
        # All returned jobs should be preprocessing jobs
        for job in items:
            assert job["job_type"] == "preprocessing"

        # Filter by status
        response = await http_client.get(
            f"{data_base_url}/jobs?status=pending",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "items" in data and "total" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_jobs_unauthorized(
        self,
        http_client: AsyncClient,
        data_base_url: str,
        user_headers: dict,
    ):
        """Test listing jobs as regular user."""
        response = await http_client.get(
            f"{data_base_url}/jobs",
            headers=user_headers,
        )
        assert response.status_code == 403
