# API Endpoint Test Suite

Comprehensive test suite for all microservices API endpoints in the MLOps Accidents project.

## Overview

This test suite provides:
- ✅ Tests for all API endpoints across all microservices
- ✅ Successful request scenarios
- ✅ Unsuccessful request scenarios (authentication, authorization, validation errors)
- ✅ Configurable target IP/base URL
- ✅ Best practices: fixtures, parametrization, clear test organization

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_auth_service.py     # Auth service endpoint tests
├── test_data_service.py     # Data service endpoint tests
├── test_train_service.py    # Train service endpoint tests
├── test_predict_service.py  # Predict service endpoint tests
└── README.md               # This file
```

## Prerequisites

Install test dependencies:

```bash
pip install -r requirements.txt
```

Or install only test dependencies:

```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

## Configuration

### Target IP/Base URL Configuration

The test suite supports multiple ways to configure the target IP/base URL:

#### Option 1: Environment Variables (Recommended)

**For Nginx/Reverse Proxy (default):**
```bash
export BASE_URL=http://localhost
# or
export TARGET_IP=localhost
```

**For Direct Service Access:**
```bash
export AUTH_SERVICE_URL=http://localhost:8004/api/v1/auth
export DATA_SERVICE_URL=http://localhost:8001/api/v1/data
export TRAIN_SERVICE_URL=http://localhost:8002/api/v1/train
export PREDICT_SERVICE_URL=http://localhost:8003/api/v1/predict
```

**For Remote Testing:**
```bash
export BASE_URL=http://192.168.1.100
# or
export BASE_URL=https://api.example.com
```

#### Option 2: Default Behavior

If no environment variables are set, tests default to:
- `http://localhost` for nginx/reverse proxy
- `http://localhost:{port}/api/v1/{service}` for direct service access

### Authentication Credentials

Configure admin credentials via environment variables:

```bash
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=your_admin_password
```

Default values (if not set):
- `ADMIN_USERNAME`: `admin`
- `ADMIN_PASSWORD`: `Mlops@Admin2024!Secure`

For regular user testing:
```bash
export TEST_USER_USERNAME=testuser
export TEST_USER_PASSWORD=TestUser@123
```

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Tests for Specific Service

```bash
# Auth service only
pytest tests/test_auth_service.py

# Data service only
pytest tests/test_data_service.py

# Train service only
pytest tests/test_train_service.py

# Predict service only
pytest tests/test_predict_service.py
```

### Run Tests by Marker

```bash
# All auth-related tests
pytest -m auth

# All data-related tests
pytest -m data

# Integration tests
pytest -m integration
```

### Run Specific Test

```bash
pytest tests/test_auth_service.py::TestAuthService::test_login_success
```

### Run with Coverage

```bash
pytest tests/ --cov=services --cov-report=html --cov-report=term
```

### Verbose Output

```bash
pytest tests/ -v
```

### Stop on First Failure

```bash
pytest tests/ -x
```

## Test Coverage

### Auth Service (`/api/v1/auth/`)
- ✅ `POST /login` - Successful login, invalid credentials, missing fields
- ✅ `POST /refresh` - Token refresh, invalid token
- ✅ `GET /me` - Get current user, unauthorized access
- ✅ `GET /users` - List users (admin), unauthorized access
- ✅ `POST /users` - Create user (admin), duplicate user, invalid data, unauthorized
- ✅ `GET /health` - Health check

### Data Service (`/api/v1/data/`)
- ✅ `POST /preprocess` - Start preprocessing job, unauthorized access
- ✅ `POST /build-features` - Start feature engineering job, unauthorized access
- ✅ `GET /status/{job_id}` - Get job status, not found, unauthorized
- ✅ `GET /jobs` - List jobs, filtering, unauthorized access
- ✅ `GET /health` - Health check

### Train Service (`/api/v1/train/`)
- ✅ `POST /` - Start training job, with options, unauthorized access
- ✅ `GET /status/{job_id}` - Get job status, not found, unauthorized
- ✅ `GET /jobs` - List jobs, filtering, unauthorized access
- ✅ `GET /metrics/{model_type}` - Get model metrics, not found, unauthorized
- ✅ `GET /health` - Health check

### Predict Service (`/api/v1/predict/`)
- ✅ `POST /` - Single prediction, missing features, unauthorized access
- ✅ `POST /batch` - Batch predictions, empty list, unauthorized access
- ✅ `GET /models` - List available models, unauthorized access
- ✅ `GET /health` - Health check

## Test Best Practices Applied

1. **Fixtures**: Shared fixtures in `conftest.py` for:
   - HTTP clients
   - Authentication tokens (admin and user)
   - Base URLs
   - Test data

2. **Organization**: Tests organized by service with clear class structure

3. **Naming**: Descriptive test names following `test_<scenario>_<expected_result>` pattern

4. **Markers**: Tests marked with service-specific markers (`@pytest.mark.auth`, etc.)

5. **Async Support**: Proper async/await usage for FastAPI endpoints

6. **Error Handling**: Tests verify both success and failure scenarios

7. **Isolation**: Each test is independent and can run in any order

8. **Configuration**: Flexible configuration via environment variables

## Example Test Run

```bash
# Set target IP
export BASE_URL=http://localhost

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=services --cov-report=term-missing

# Run specific service tests
pytest tests/test_auth_service.py -v
```

## Troubleshooting

### Connection Errors

If you see connection errors:
1. Ensure services are running: `docker-compose up`
2. Check BASE_URL/TARGET_IP environment variable
3. Verify network connectivity to target host

### Authentication Failures

If authentication tests fail:
1. Verify `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables
2. Check that admin user exists in the auth service
3. Ensure JWT_SECRET_KEY matches between test environment and services

### Timeout Errors

If tests timeout:
1. Increase timeout in `conftest.py` (default: 30 seconds)
2. Check service health endpoints
3. Verify services are not overloaded

## Continuous Integration

These tests are designed to run in CI/CD pipelines. Example GitHub Actions:

```yaml
- name: Run API Tests
  env:
    BASE_URL: http://localhost
    ADMIN_USERNAME: admin
    ADMIN_PASSWORD: ${{ secrets.ADMIN_PASSWORD }}
  run: |
    pytest tests/ --cov=services --cov-report=xml
```

## Contributing

When adding new endpoints:
1. Add tests to the appropriate service test file
2. Follow existing test patterns
3. Include both success and failure scenarios
4. Update this README if adding new test categories
