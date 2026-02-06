#!/bin/bash
# Example script to run API endpoint tests

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}MLOps Microservices API Test Suite${NC}"
echo "=================================="
echo ""

# Check if services are running (optional)
# Uncomment to check service health before running tests
# echo "Checking service health..."
# curl -f http://localhost/health || echo "Warning: Services may not be running"

# Set default BASE_URL if not set
if [ -z "$BASE_URL" ]; then
    export BASE_URL="http://localhost"
    echo "Using default BASE_URL: $BASE_URL"
else
    echo "Using BASE_URL: $BASE_URL"
fi

# Set default admin credentials if not set
if [ -z "$ADMIN_USERNAME" ]; then
    export ADMIN_USERNAME="admin"
fi

if [ -z "$ADMIN_PASSWORD" ]; then
    export ADMIN_PASSWORD="Mlops@Admin2024!Secure"
fi

echo ""
echo -e "${GREEN}Running all tests...${NC}"
echo ""

# Run tests with options
pytest tests/ \
    -v \
    --tb=short \
    --strict-markers \
    "$@"

echo ""
echo -e "${GREEN}Tests completed!${NC}"
