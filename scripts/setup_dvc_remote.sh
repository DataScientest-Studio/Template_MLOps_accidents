#!/bin/bash
# Setup DVC remote with Dagshub credentials from .env file

set -e

if [ ! -f .env ]; then
    echo "Error: .env file not found. Please copy .env.example to .env and fill in your credentials."
    echo "  cp .env.example .env"
    echo "  # Then edit .env with your Dagshub username and token"
    exit 1
fi

# Load environment variables from .env file
export $(grep -v '^#' .env | grep -v '^$' | xargs)

if [ -z "$DAGSHUB_USERNAME" ] || [ -z "$DAGSHUB_TOKEN" ] || [ -z "$DAGSHUB_REPO" ]; then
    echo "Error: DAGSHUB_USERNAME, DAGSHUB_TOKEN, and DAGSHUB_REPO must be set in .env file"
    exit 1
fi

# Detect DVC executable
DVC=$(if [ -f .venv/bin/dvc ]; then echo .venv/bin/dvc; else echo dvc; fi)

echo "Setting up DVC remote with Dagshub..."

# Add or modify remote
$DVC remote add origin s3://dvc 2>/dev/null || $DVC remote modify origin url s3://dvc

# Configure remote settings
$DVC remote modify origin endpointurl https://dagshub.com/${DAGSHUB_REPO}.s3
# For Dagshub S3, use access_key_id and secret_access_key (both set to the token)
$DVC remote modify origin --local access_key_id ${DAGSHUB_TOKEN}
$DVC remote modify origin --local secret_access_key ${DAGSHUB_TOKEN}

echo "DVC remote configured successfully!"
echo "Repository: ${DAGSHUB_REPO}"
echo "Endpoint: https://dagshub.com/${DAGSHUB_REPO}.s3"

