# =========================
# Base image
# =========================
ARG BASE_IMAGE=python:3.11-slim
FROM $BASE_IMAGE AS base

# =========================
# System dependencies
# =========================
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# =========================
# Environment variables
# =========================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_SYSTEM_PYTHON=1 \
    PYTHONPATH=/app

# =========================
# Set workdir
# =========================
ARG WORKSPACE=/app
WORKDIR $WORKSPACE

# =========================
# Install UV
# =========================
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.local/bin/uv /usr/local/bin/uv && \
    /root/.local/bin/uv --version

ENV PATH="/root/.local/bin:${PATH}"

# =========================
# Copy dependency files(cache-friendly)
# =========================
COPY pyproject.toml uv.lock ./

# =========================
# Development stage
# Install dev dependencies
# Copy full source code
# =========================
FROM base AS dev
COPY . .
RUN uv pip install --system -e ".[dev]"
CMD ["bash"]

# =========================
# Training stage
# For running training pipeline
# =========================
FROM dev AS train
ENTRYPOINT ["make"]
CMD ["workflow-ml"]

# =========================
# Production stage
# Install only runtime dependencies (no dev tools)
# =========================
# FROM base AS prod
# COPY . .
# RUN uv pip install --system .
# EXPOSE 8000
# CMD ["python", "src/models/predict_model.py"]