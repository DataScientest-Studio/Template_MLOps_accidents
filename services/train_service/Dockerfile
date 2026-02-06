# =============================================================================
# Train Service Dockerfile
# =============================================================================
# Handles model training and MLflow integration
# =============================================================================

FROM python:3.11-slim AS base

LABEL maintainer="MLOps Team"
LABEL description="Model training and registry service"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash mlops
WORKDIR /app

# Install Python dependencies
# Copy files needed for package installation first
COPY requirements.txt pyproject.toml setup.py README.md ./
COPY src /app/src
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy common module
COPY services/common /app/services/common

# Copy service code
COPY services/train_service /app/services/train_service

# Change ownership to non-root user
RUN chown -R mlops:mlops /app
USER mlops

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the service
CMD ["uvicorn", "services.train_service.main:app", "--host", "0.0.0.0", "--port", "8002"]

