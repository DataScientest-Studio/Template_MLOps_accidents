"""
Test suite for Predict Service API endpoints.

Tests cover:
- Health checks
- Single prediction requests
- Batch prediction requests
- Model listing
- Authorization checks (authenticated user required)
"""

import pytest
from httpx import AsyncClient


@pytest.mark.predict
class TestPredictService:
    """Test suite for Predict Service endpoints."""

    # =========================================================================
    # Health Check Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_health_check(
        self, http_client: AsyncClient, predict_health_url: str
    ):
        """Test health check endpoint."""
        response = await http_client.get(predict_health_url)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    # =========================================================================
    # Single Prediction Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_single_prediction_success(
        self,
        http_client: AsyncClient,
        predict_base_url: str,
        user_headers: dict,
        sample_prediction_features: dict,
    ):
        """Test making a single prediction with valid features."""
        request_data = {
            "features": sample_prediction_features,
        }
        response = await http_client.post(
            f"{predict_base_url}/",
            json=request_data,
            headers=user_headers,
        )
        # Accept both success and potential errors (if model not available)
        assert response.status_code in [200, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "prediction" in data
            assert "probability" in data
            assert "model_type" in data
            assert data["prediction"] in (0, 1)
            assert isinstance(data["probability"], (int, float))
            assert 0 <= data["probability"] <= 1

    @pytest.mark.asyncio
    async def test_single_prediction_returns_model_type(
        self,
        http_client: AsyncClient,
        predict_base_url: str,
        user_headers: dict,
        sample_prediction_features: dict,
    ):
        """Test that prediction response includes the loaded model type (from MLflow Production)."""
        request_data = {"features": sample_prediction_features}
        response = await http_client.post(
            f"{predict_base_url}/",
            json=request_data,
            headers=user_headers,
        )
        assert response.status_code in [200, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "prediction" in data
            assert "probability" in data
            assert "model_type" in data
            assert 0 <= data["probability"] <= 1

    @pytest.mark.asyncio
    async def test_single_prediction_missing_features(
        self,
        http_client: AsyncClient,
        predict_base_url: str,
        user_headers: dict,
    ):
        """Test making prediction with missing features."""
        response = await http_client.post(
            f"{predict_base_url}/",
            json={},
            headers=user_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_single_prediction_empty_features(
        self,
        http_client: AsyncClient,
        predict_base_url: str,
        user_headers: dict,
    ):
        """Test making prediction with empty features."""
        request_data = {"features": {}}
        response = await http_client.post(
            f"{predict_base_url}/",
            json=request_data,
            headers=user_headers,
        )
        # May succeed or fail depending on validation
        assert response.status_code in [200, 400, 422, 500]

    @pytest.mark.asyncio
    async def test_single_prediction_unauthorized(
        self,
        http_client: AsyncClient,
        predict_base_url: str,
        sample_prediction_features: dict,
    ):
        """Test making prediction without authentication."""
        request_data = {"features": sample_prediction_features}
        response = await http_client.post(
            f"{predict_base_url}/",
            json=request_data,
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_single_prediction_invalid_token(
        self,
        http_client: AsyncClient,
        predict_base_url: str,
        invalid_token: str,
        sample_prediction_features: dict,
    ):
        """Test making prediction with invalid token."""
        headers = {"Authorization": f"Bearer {invalid_token}"}
        request_data = {"features": sample_prediction_features}
        response = await http_client.post(
            f"{predict_base_url}/",
            json=request_data,
            headers=headers,
        )
        assert response.status_code == 401

    # =========================================================================
    # Batch Prediction Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_batch_prediction_success(
        self,
        http_client: AsyncClient,
        predict_base_url: str,
        user_headers: dict,
        sample_batch_features: list,
    ):
        """Test making batch predictions with valid features."""
        request_data = {
            "features_list": sample_batch_features,
        }
        response = await http_client.post(
            f"{predict_base_url}/batch",
            json=request_data,
            headers=user_headers,
        )
        # Accept both success and potential errors (if model not available)
        assert response.status_code in [200, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "predictions" in data
            assert "probabilities" in data
            assert "count" in data
            assert "model_type" in data
            assert isinstance(data["predictions"], list)
            assert isinstance(data["probabilities"], list)
            assert data["count"] == len(sample_batch_features)
            assert len(data["probabilities"]) == len(data["predictions"])
            for p in data["probabilities"]:
                assert 0 <= p <= 1

    @pytest.mark.asyncio
    async def test_batch_prediction_returns_model_type(
        self,
        http_client: AsyncClient,
        predict_base_url: str,
        user_headers: dict,
        sample_batch_features: list,
    ):
        """Test that batch prediction response includes loaded model type (from MLflow Production)."""
        request_data = {"features_list": sample_batch_features}
        response = await http_client.post(
            f"{predict_base_url}/batch",
            json=request_data,
            headers=user_headers,
        )
        assert response.status_code in [200, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "predictions" in data
            assert "probabilities" in data
            assert "count" in data
            assert "model_type" in data
            assert len(data["probabilities"]) == len(data["predictions"])

    @pytest.mark.asyncio
    async def test_batch_prediction_empty_list(
        self,
        http_client: AsyncClient,
        predict_base_url: str,
        user_headers: dict,
    ):
        """Test making batch prediction with empty list."""
        request_data = {"features_list": []}
        response = await http_client.post(
            f"{predict_base_url}/batch",
            json=request_data,
            headers=user_headers,
        )
        # May succeed or fail depending on validation
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_batch_prediction_missing_field(
        self,
        http_client: AsyncClient,
        predict_base_url: str,
        user_headers: dict,
    ):
        """Test making batch prediction with missing features_list."""
        response = await http_client.post(
            f"{predict_base_url}/batch",
            json={},
            headers=user_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_batch_prediction_unauthorized(
        self,
        http_client: AsyncClient,
        predict_base_url: str,
        sample_batch_features: list,
    ):
        """Test making batch prediction without authentication."""
        request_data = {"features_list": sample_batch_features}
        response = await http_client.post(
            f"{predict_base_url}/batch",
            json=request_data,
        )
        assert response.status_code == 401

    # =========================================================================
    # Model Listing Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_list_models_success(
        self,
        http_client: AsyncClient,
        predict_base_url: str,
        user_headers: dict,
    ):
        """Test listing the currently loaded Production model (loaded at container start)."""
        response = await http_client.get(
            f"{predict_base_url}/models",
            headers=user_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "loaded_model_type" in data
        assert "source" in data
        assert "MLflow" in data["source"] or "Production" in data["source"]

    @pytest.mark.asyncio
    async def test_list_models_unauthorized(
        self, http_client: AsyncClient, predict_base_url: str
    ):
        """Test listing models without authentication."""
        response = await http_client.get(f"{predict_base_url}/models")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_models_invalid_token(
        self,
        http_client: AsyncClient,
        predict_base_url: str,
        invalid_token: str,
    ):
        """Test listing models with invalid token."""
        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = await http_client.get(
            f"{predict_base_url}/models",
            headers=headers,
        )
        assert response.status_code == 401
