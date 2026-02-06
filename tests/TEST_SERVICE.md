# Test Service - Docker Container Usage

The test service is now available as a Docker container that can run API endpoint tests against all microservices.

## Quick Start

### Run All Tests in Docker

```bash
# Start services and run all tests
make docker-test

# Or manually:
docker compose --profile test run --rm test
```

### Build Test Service Image

```bash
make docker-test-build
# or
docker compose build test
```

## Makefile Commands

### Local Testing (requires services running)

```bash
# Run all API tests locally
make test-api

# Run with coverage
make test-api-cov

# Run specific service tests
make test-api-auth      # Auth service only
make test-api-data      # Data service only
make test-api-train     # Train service only
make test-api-predict   # Predict service only
```

### Docker Testing

```bash
# Run all tests in Docker (auto-starts services)
make docker-test

# Build test service image
make docker-test-build

# Run tests with custom command
make docker-test-run CMD="pytest tests/test_auth_service.py -v"

# Run tests with coverage
make docker-test-cov

# Run tests for specific service
make docker-test-service SERVICE=auth
```

## Docker Compose Usage

### Run All Tests

```bash
docker compose --profile test run --rm test
```

### Run Specific Test File

```bash
docker compose --profile test run --rm test pytest tests/test_auth_service.py -v
```

### Run Tests with Coverage

```bash
docker compose --profile test run --rm test pytest tests/ -v --cov=services --cov-report=html
```

### Run Tests with Custom BASE_URL

```bash
docker compose --profile test run --rm -e BASE_URL=http://192.168.1.100 test
```

### Interactive Shell in Test Container

```bash
docker compose --profile test run --rm test bash
```

## Environment Variables

The test service supports the following environment variables:

- `BASE_URL`: Base URL for API endpoints (default: `http://nginx:80` in Docker, `http://localhost` locally)
- `ADMIN_USERNAME`: Admin username for authentication (default: `admin`)
- `ADMIN_PASSWORD`: Admin password (default: `CHANGE_ME_ADMIN_PASSWORD`)
- `TEST_USER_USERNAME`: Test user username (default: `testuser`)
- `TEST_USER_PASSWORD`: Test user password (default: `TestUser@123`)

## Service Dependencies

The test service depends on all other microservices being healthy:
- `auth` service
- `data` service
- `train` service
- `predict` service
- `nginx` (reverse proxy)

The test service will wait for all dependencies to be healthy before running tests.

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start services
        run: |
          docker compose up -d
          sleep 10  # Wait for services to be healthy
      
      - name: Run API tests
        run: |
          docker compose --profile test run --rm test
      
      - name: Upload coverage
        if: always()
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

## Troubleshooting

### Services Not Ready

If tests fail because services aren't ready:

```bash
# Check service health
make docker-health

# Wait for services to be healthy
docker compose up -d
sleep 15
make docker-test
```

### Connection Errors

If you see connection errors, verify:
1. Services are running: `docker compose ps`
2. Network connectivity: `docker compose --profile test run --rm test curl http://nginx:80/health`
3. BASE_URL is correct (use `http://nginx:80` inside Docker network)

### Authentication Failures

Ensure environment variables are set correctly:
```bash
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=your_password
docker compose --profile test run --rm test
```
