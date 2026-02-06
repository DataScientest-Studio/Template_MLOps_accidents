.PHONY: help install install-dev sync lock update clean lint format type-check test test-cov test-api test-api-cov test-api-service test-api-service-cov test-api-auth test-api-data test-api-train test-api-predict run-import run-preprocess run-features run-train run-train-grid run-predict run-predict-file workflow-all workflow-data workflow-ml dvc-init dvc-setup-remote dvc-status dvc-push dvc-pull dvc-repro docker-up docker-down docker-build-services docker-logs docker-status docker-health docker-restart docker-dev docker-build docker-build-dev docker-build-train docker-dvc-pull docker-clean docker-test docker-test-build docker-test-run docker-test-cov docker-test-service

# Load .env file if it exists (cross-platform with GNU Make)
# Note: On Windows, use Git Bash, WSL, or another Unix-like environment
ifneq (,$(wildcard .env))
    include .env
    export
endif

# Default Python version (can be overridden)
PYTHON_VERSION ?= 3.11

# UV executable (use uv if available, otherwise suggest installation)
UV := $(shell command -v uv 2> /dev/null)

# Detect virtual environment and use its Python if available
# Check if .venv/bin/python exists, otherwise fall back to system python
PYTHON := $(shell if [ -f .venv/bin/python ]; then echo .venv/bin/python; else echo python; fi)

# Detect virtual environment tools (flake8, black, isort, mypy, pytest, dvc)
# Use venv versions if available, otherwise use system versions
FLAKE8 := $(shell if [ -f .venv/bin/flake8 ]; then echo .venv/bin/flake8; else echo flake8; fi)
BLACK := $(shell if [ -f .venv/bin/black ]; then echo .venv/bin/black; else echo black; fi)
ISORT := $(shell if [ -f .venv/bin/isort ]; then echo .venv/bin/isort; else echo isort; fi)
MYPY := $(shell if [ -f .venv/bin/mypy ]; then echo .venv/bin/mypy; else echo mypy; fi)
PYTEST := $(shell if [ -f .venv/bin/pytest ]; then echo .venv/bin/pytest; else echo pytest; fi)
DVC := $(shell if [ -f .venv/bin/dvc ]; then echo .venv/bin/dvc; else echo dvc; fi)

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

check-uv:
	@if [ -z "$(UV)" ]; then \
		echo "Error: uv is not installed. Please install it first:"; \
		echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		echo "  or visit: https://github.com/astral-sh/uv"; \
		exit 1; \
	fi

install: check-uv ## Install project dependencies using UV
	@echo "Installing dependencies with UV..."
	uv pip install -e .

install-dev: check-uv ## Install project with development dependencies
	@echo "Installing dependencies with UV (including dev dependencies)..."
	uv pip install -e ".[dev]"

sync: check-uv ## Sync dependencies from pyproject.toml (UV equivalent of pip-sync)
	@echo "Syncing dependencies with UV..."
	uv pip install -e ".[dev]"

lock: check-uv ## Generate lock file (if using UV's lock feature)
	@echo "Note: UV manages dependencies directly from pyproject.toml"
	@echo "No separate lock file needed with UV pip install"

update: check-uv ## Update all dependencies to latest versions
	@echo "Updating dependencies with UV..."
	uv pip install --upgrade -e ".[dev]"

clean: ## Remove build artifacts and cache files
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -r {} + 2>/dev/null || true

lint: ## Run linting with flake8
	@echo "Running flake8..."
	$(FLAKE8) src/ --max-line-length=88 --extend-ignore=E203,W503

format: ## Format code with black and isort
	@echo "Formatting code with black..."
	@if [ -d tests ]; then \
		$(BLACK) src/ tests/; \
	else \
		$(BLACK) src/; \
	fi
	@echo "Sorting imports with isort..."
	@if [ -d tests ]; then \
		$(ISORT) src/ tests/; \
	else \
		$(ISORT) src/; \
	fi

type-check: ## Run type checking with mypy
	@echo "Running mypy..."
	$(MYPY) src/

test: ## Run tests with pytest
	@echo "Running tests..."
	$(PYTEST)

test-cov: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	$(PYTEST) --cov=src --cov-report=term-missing --cov-report=html

# =============================================================================
# API Endpoint Tests
# =============================================================================

test-api: ## Run API endpoint tests (requires services to be running)
	@echo "Running API endpoint tests..."
	@if [ -z "$(BASE_URL)" ]; then \
		echo "Using default BASE_URL: http://localhost"; \
		BASE_URL=http://localhost $(PYTEST) tests/ -v --tb=short; \
	else \
		echo "Using BASE_URL: $(BASE_URL)"; \
		BASE_URL=$(BASE_URL) $(PYTEST) tests/ -v --tb=short; \
	fi

test-api-cov: ## Run API endpoint tests with coverage
	@echo "Running API endpoint tests with coverage..."
	@if [ -z "$(BASE_URL)" ]; then \
		echo "Using default BASE_URL: http://localhost"; \
		BASE_URL=http://localhost $(PYTEST) tests/ -v --tb=short --cov=services --cov-report=term-missing --cov-report=html; \
	else \
		echo "Using BASE_URL: $(BASE_URL)"; \
		BASE_URL=$(BASE_URL) $(PYTEST) tests/ -v --tb=short --cov=services --cov-report=term-missing --cov-report=html; \
	fi

test-api-auth: ## Run auth service API tests only
	@echo "Running auth service API tests..."
	@if [ -z "$(BASE_URL)" ]; then \
		BASE_URL=http://localhost $(PYTEST) tests/test_auth_service.py -v --tb=short; \
	else \
		BASE_URL=$(BASE_URL) $(PYTEST) tests/test_auth_service.py -v --tb=short; \
	fi

test-api-data: ## Run data service API tests only
	@echo "Running data service API tests..."
	@if [ -z "$(BASE_URL)" ]; then \
		BASE_URL=http://localhost $(PYTEST) tests/test_data_service.py -v --tb=short; \
	else \
		BASE_URL=$(BASE_URL) $(PYTEST) tests/test_data_service.py -v --tb=short; \
	fi

test-api-train: ## Run train service API tests only
	@echo "Running train service API tests..."
	@if [ -z "$(BASE_URL)" ]; then \
		BASE_URL=http://localhost $(PYTEST) tests/test_train_service.py -v --tb=short; \
	else \
		BASE_URL=$(BASE_URL) $(PYTEST) tests/test_train_service.py -v --tb=short; \
	fi

test-api-predict: ## Run predict service API tests only
	@echo "Running predict service API tests..."
	@if [ -z "$(BASE_URL)" ]; then \
		BASE_URL=http://localhost $(PYTEST) tests/test_predict_service.py -v --tb=short; \
	else \
		BASE_URL=$(BASE_URL) $(PYTEST) tests/test_predict_service.py -v --tb=short; \
	fi

test-api-service: ## Run API tests in Docker container (requires docker-compose)
	@echo "Running API tests in Docker container..."
	@echo "Note: This will start services if not already running..."
	docker compose --profile test run --rm test

test-api-service-cov: ## Run API tests in Docker container with coverage
	@echo "Running API tests in Docker container with coverage..."
	docker compose --profile test run --rm test pytest tests/ -v --tb=short --cov=services --cov-report=term-missing --cov-report=html

# Data pipeline commands
run-import: ## Import raw data from S3
	@echo "Importing raw data..."
	$(PYTHON) src/data/import_raw_data.py

run-preprocess: ## Create interim dataset from raw data
	@echo "Preprocessing data (creating interim dataset)..."
	NOCONFIRM=$(NOCONFIRM) $(PYTHON) src/data/make_dataset.py

run-features: ## Build features from interim dataset (XGBoost-optimized)
	@echo "Building features from interim dataset..."
	NOCONFIRM=$(NOCONFIRM) $(PYTHON) src/features/build_features.py

run-train: ## Train multiple models with default parameters (fast, no grid search)
	@echo "Training multiple models with default parameters..."
	$(PYTHON) src/models/train_multi_model.py

run-train-grid: ## Train multiple models with grid search for hyperparameter tuning (slow)
	@echo "Training multiple models with grid search (this may take a while)..."
	$(PYTHON) src/models/train_multi_model.py --grid-search

run-predict: ## Make predictions using default JSON file (src/models/test_features.json) - uses local model (development mode)
	@echo "Making predictions from default JSON file (local model)..."
	$(PYTHON) src/models/predict_model.py

run-predict-mlflow: ## Make predictions using MLflow Production model (best practice for production)
	@echo "Making predictions using MLflow Production model..."
	$(PYTHON) src/models/predict_model.py --use-mlflow-production

run-predict-best: ## Make predictions using best Production model across all model types (automatically selects best)
	@echo "Making predictions using best Production model (auto-selected)..."
	$(PYTHON) src/models/predict_model.py --use-best-model

run-predict-file: ## Make predictions from JSON file (usage: make run-predict-file FILE=src/models/test_features.json)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE variable is required. Usage: make run-predict-file FILE=path/to/file.json"; \
		exit 1; \
	fi
	@echo "Making predictions from $(FILE) (local model)..."
	$(PYTHON) src/models/predict_model.py $(FILE)

run-predict-file-mlflow: ## Make predictions from JSON file using MLflow Production (usage: make run-predict-file-mlflow FILE=src/models/test_features.json)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE variable is required. Usage: make run-predict-file-mlflow FILE=path/to/file.json"; \
		exit 1; \
	fi
	@echo "Making predictions from $(FILE) using MLflow Production model..."
	$(PYTHON) src/models/predict_model.py $(FILE) --use-mlflow-production

# Complete workflow commands
workflow-all: $(if $(NOCONFIRM),,run-import) run-preprocess run-features $(if $(filter 1,$(GRID_SEARCH)),run-train-grid,run-train) run-predict ## Run complete pipeline (use GRID_SEARCH=1 for grid search, NOCONFIRM=1 to skip raw data import and auto-confirm overwrites): import → preprocess → features → train → predict
	@echo "Complete workflow finished!"

workflow-data: run-import run-preprocess ## Run data pipeline: import → preprocess
	@echo "Data pipeline finished!"

workflow-ml: run-features run-train ## Run ML pipeline: features → train
	@echo "ML pipeline finished!"

# Setup commands
setup: check-uv ## Initial project setup (install dependencies)
	@echo "Setting up project..."
	@echo "Python version: $(PYTHON_VERSION)"
	@echo "Installing dependencies..."
	uv pip install -e ".[dev]"
	@echo "Setup complete!"

setup-venv: check-uv ## Create virtual environment and install dependencies
	@echo "Creating virtual environment with Python $(PYTHON_VERSION)..."
	python$(PYTHON_VERSION) -m venv .venv
	@echo "Activating virtual environment and installing dependencies..."
	.venv/bin/pip install --upgrade pip
	uv pip install -e ".[dev]"
	@echo "Virtual environment created! Activate it with: source .venv/bin/activate"

# DVC commands
dvc-init: ## Initialize DVC repository
	@echo "Initializing DVC..."
	$(DVC) init
	@echo "DVC initialized! Run 'make dvc-setup-remote' to configure Dagshub remote."

dvc-setup-remote: ## Configure DVC remote with Dagshub (requires .env file)
	@if [ -z "$(DAGSHUB_USERNAME)" ] || [ -z "$(DAGSHUB_TOKEN)" ] || [ -z "$(DAGSHUB_REPO)" ]; then \
		echo "Error: DAGSHUB_USERNAME, DAGSHUB_TOKEN, and DAGSHUB_REPO must be set in .env file"; \
		echo "Please ensure .env file exists and contains these variables."; \
		exit 1; \
	fi
	@echo "Setting up DVC remote with Dagshub..."
	@$(DVC) remote add origin s3://dvc 2>/dev/null || $(DVC) remote modify origin url s3://dvc
	@$(DVC) remote modify origin endpointurl https://dagshub.com/$(DAGSHUB_REPO).s3
	@$(DVC) remote modify origin --local access_key_id $(DAGSHUB_TOKEN)
	@$(DVC) remote modify origin --local secret_access_key $(DAGSHUB_TOKEN)
	@echo "DVC remote configured successfully!"
	@echo "Repository: $(DAGSHUB_REPO)"
	@echo "Endpoint: https://dagshub.com/$(DAGSHUB_REPO).s3"

dvc-status: ## Check DVC status
	@echo "Checking DVC status..."
	$(DVC) status

dvc-push: ## Push data to DVC remote
	@echo "Pushing data to DVC remote..."
	$(DVC) push

dvc-pull: ## Pull data from DVC remote
	@echo "Pulling data from DVC remote..."
	$(DVC) pull

dvc-repro: ## Reproduce DVC pipeline
	@echo "Pulling data from DVC remote (if available)..."
	@$(DVC) pull || echo "Warning: Some files not found in remote, will regenerate..."
	@echo "Reproducing DVC pipeline..."
	@$(DVC) repro

# =============================================================================
# Microservices Docker commands
# =============================================================================

docker-up: ## Start all microservices (nginx, auth, data, train, predict)
	@echo "Starting microservices..."
	docker compose up -d nginx auth data train predict
	@echo "Services started! API available at http://localhost"

docker-up-all: ## Start all microservices including test service
	@echo "Starting all microservices including test..."
	docker compose up -d
	@echo "All services started!"

docker-down: ## Stop all microservices
	@echo "Stopping microservices..."
	docker compose down
	@echo "Services stopped."

docker-build-services: ## Build all microservice images
	@echo "Building microservice images..."
	docker compose build nginx auth data train predict
	@echo "All microservice images built!"

docker-build-test: ## Build test service image
	@echo "Building test service image..."
	docker compose build test
	@echo "Test service image built!"

docker-logs: ## Show logs from all services (follow mode)
	docker compose logs -f

docker-logs-nginx: ## Show nginx logs
	docker compose logs -f nginx

docker-logs-data: ## Show data service logs
	docker compose logs -f data

docker-logs-train: ## Show train service logs
	docker compose logs -f train

docker-logs-predict: ## Show predict service logs
	docker compose logs -f predict

docker-status: ## Show status of all services
	docker compose ps

docker-health: ## Check health of all services via API
	@echo "Checking service health..."
	@echo "--- Nginx Gateway ---"
	@curl -sf http://localhost/health 2>/dev/null && echo "" || echo "  Not responding"
	@echo "--- Auth Service ---"
	@curl -sf http://localhost/api/v1/auth/health 2>/dev/null && echo "" || echo "  Not responding"
	@echo "--- Data Service ---"
	@curl -sf http://localhost/api/v1/data/health 2>/dev/null && echo "" || echo "  Not responding"
	@echo "--- Train Service ---"
	@curl -sf http://localhost/api/v1/train/health 2>/dev/null && echo "" || echo "  Not responding"
	@echo "--- Predict Service ---"
	@curl -sf http://localhost/api/v1/predict/health 2>/dev/null && echo "" || echo "  Not responding"

docker-restart: ## Restart all microservices
	@echo "Restarting microservices..."
	docker compose restart nginx auth data train predict

# Compose files: base + test overrides (relaxed auth rate limits and nginx for tests)
COMPOSE_TEST := -f docker-compose.yml -f docker-compose.test.yml

docker-test: ## Run API tests in Docker (starts services if needed, runs tests, stops test container)
	@echo "Running API tests in Docker..."
	@echo "Building and starting services if not running..."
	@docker compose $(COMPOSE_TEST) build nginx auth data train predict
	@docker compose $(COMPOSE_TEST) up -d nginx auth data train predict || true
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@echo "Running tests..."
	docker compose $(COMPOSE_TEST) --profile test run --rm test
	@echo "Tests completed!"

docker-test-build: ## Build test service Docker image
	@echo "Building test service..."
	docker compose $(COMPOSE_TEST) build test

docker-test-run: ## Run API tests in Docker with custom command (usage: make docker-test-run CMD="pytest tests/test_auth_service.py -v")
	@if [ -z "$(CMD)" ]; then \
		echo "Running all API tests..."; \
		docker compose $(COMPOSE_TEST) --profile test run --rm test; \
	else \
		echo "Running custom test command: $(CMD)"; \
		docker compose $(COMPOSE_TEST) --profile test run --rm test $(CMD); \
	fi

docker-test-cov: ## Run API tests in Docker with coverage report
	@echo "Running API tests with coverage..."
	docker compose $(COMPOSE_TEST) --profile test run --rm test pytest tests/ -v --tb=short --cov=services --cov-report=term-missing --cov-report=html

docker-test-service: ## Run tests for specific service (usage: make docker-test-service SERVICE=auth)
	@if [ -z "$(SERVICE)" ]; then \
		echo "Error: SERVICE variable required. Usage: make docker-test-service SERVICE=auth"; \
		echo "Available services: auth, data, train, predict"; \
		exit 1; \
	fi
	@echo "Running tests for $(SERVICE) service..."
	docker compose $(COMPOSE_TEST) --profile test run --rm test pytest tests/test_$(SERVICE)_service.py -v --tb=short

docker-dev: ## Start development shell container (interactive)
	@echo "Starting development container..."
	docker compose --profile dev run --rm dev

# =============================================================================
# Legacy Docker commands (standalone containers)
# =============================================================================

docker-build: ## Build legacy Docker images (dev, train)
	@echo "Building legacy Docker images..."
	docker build -t mlops-accidents:dev --target dev .
	docker build -t mlops-accidents:train --target train .
	@echo "Legacy Docker images built!"

docker-build-dev: ## Build development Docker image (standalone)
	@echo "Building development Docker image..."
	docker build -t mlops-accidents:dev --target dev .

docker-build-train: ## Build training Docker image (standalone)
	@echo "Building training Docker image..."
	docker build -t mlops-accidents:train --target train .

docker-dvc-pull: ## Pull data/models from DVC remote using Docker Compose
	@echo "Pulling data/models from DVC remote via Docker..."
	docker compose --profile dvc run --rm dvc-pull

docker-clean: ## Remove all Docker containers, images, and volumes
	@echo "Stopping and removing containers..."
	docker compose down --rmi local --volumes 2>/dev/null || true
	@echo "Removing legacy images..."
	docker rmi mlops-accidents:dev mlops-accidents:train 2>/dev/null || true
	@echo "Cleanup complete!"
