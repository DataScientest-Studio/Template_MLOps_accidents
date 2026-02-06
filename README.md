# 🚦 MLOps Road Accident Prediction

[![CI Pipeline](https://github.com/DataScientest-Studio/Template_MLOps_accidents/actions/workflows/ci.yaml/badge.svg)](https://github.com/DataScientest-Studio/Template_MLOps_accidents/actions/workflows/ci.yaml)
[![codecov](https://codecov.io/github/DataScientest-Studio/Template_MLOps_accidents/branch/master/graph/badge.svg)](https://codecov.io/github/DataScientest-Studio/Template_MLOps_accidents)

A **containerized** MLOps project for predicting road accidents using machine learning. This project implements a complete MLOps workflow from data ingestion to model serving, with a focus on **reproducibility, versioning, and containerization**.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [🐳 Docker & Containerization](#-docker--containerization) ⭐ **Start Here**
- [Pipeline Overview](#pipeline-overview)
- [Current State](#current-state)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Workflow](#workflow)
- [MLflow Model Registry](#-mlflow-model-registry)
- [Multi-Model Training Framework](#-multi-model-training-framework)
- [Team Structure](#-team-structure)
- [Roadmap](#-roadmap)
- [GO-LIVE Checklist](#-go-live-checklist)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Project Overview

This project is an MLOps implementation for road accident prediction, designed as a learning and production-ready template. The system processes road accident data from multiple sources, trains machine learning models to predict accident severity, and serves predictions through a REST API.

### Core Principles

- **🔒 Containerization First**: All workflows run in Docker containers for environment parity
- **📊 Reproducibility**: Ensure all experiments and workflows can be reproduced across different environments
- **📦 Versioning**: Track data, models, and experiments using DVC and MLflow
- **🤖 Automation**: Implement CI/CD pipelines for testing, linting, and deployment
- **📈 Monitoring**: Track model performance and detect data drift in production

### Success Metrics

- **Model Performance**: F1 Score, Precision, and Recall for accident severity classification
- **Baseline Model**: XGBoost with optimized parameters as initial benchmark
- **Minimum Performance Threshold**: To be defined based on baseline results

## 🐳 Docker & Containerization

> **⭐ This project is designed to run in Docker containers. Docker ensures environment parity across development, training, and production.**

The project uses a **multi-stage Dockerfile** with three stages:
- **`dev`**: Development environment with all tools and dependencies
- **`train`**: Training pipeline container for model training
- **`prod`**: Production container for inference (commented out, ready for FastAPI)

### Quick Start with Docker

**Option 1: Docker Compose (Recommended)**

```bash
# Build all services
docker compose build

# Start development shell
docker compose up dev

# Run training pipeline
docker compose up train

# Pull data/models via DVC (if configured)
docker compose --profile dvc up dvc-pull
# Or using Makefile:
make docker-dvc-pull
```

**Option 2: Makefile Commands**

```bash
# Build images
make docker-build-dev      # Development image
make docker-build-train     # Training image

# Run containers
make docker-run-dev                    # Interactive dev shell
make docker-run-train                  # Run training pipeline
make docker-run-dev-exec CMD="..."    # Run one-off command
make docker-dvc-pull                   # Pull data/models from DVC remote
```

**Option 3: Direct Docker Commands**

```bash
# Development shell
docker run -it --rm -v $(PWD):/app mlops-accidents:dev

# Training pipeline
docker run --rm -v $(PWD):/app mlops-accidents:train
```

### Docker Compose Services

The `docker-compose.yml` defines several services:

| Service | Purpose | Usage |
|---------|---------|-------|
| **`nginx`** | Reverse proxy / API Gateway | Routes requests to microservices (port 80) |
| **`auth`** | Authentication service | User management and JWT authentication (port 8004) |
| **`data`** | Data preprocessing service | Data preprocessing and feature engineering (port 8001) |
| **`train`** | Model training service | Model training and MLflow integration (port 8002) |
| **`predict`** | Prediction service | Model inference API (port 8003) |
| **`test`** | API endpoint test service | Runs comprehensive API tests (profile: test) |
| **`dev`** | Development environment | Interactive shell for development and testing |
| **`dvc-pull`** | Data sync | Pulls data from DVC remote (optional profile) |

### Running the Pipeline in Docker

```bash
# Pull latest data/models from DVC (if configured)
make docker-dvc-pull
# Or: docker compose --profile dvc up dvc-pull

# Complete workflow in Docker
docker compose up train

# Or step-by-step in dev container
docker compose up dev
# Inside container:
make run-import      # Step 1: Download data
make run-preprocess  # Step 2: Clean & merge
make run-features    # Step 3: Feature engineering
make run-train       # Step 4: Train models
make run-predict     # Step 5: Make predictions
```

### Volume Mounts

- **`.:/app`**: Project code mounted for dev/train (read-write)
- **`./models:/app/models`**: Model artifacts (read-write for train, read-only for prod)
- **`./data:/app/data`**: Data directory (read-write for train, read-only for prod)
- **`~/.dvc:/home/mlops/.dvc`**: DVC configuration (read-only for dev/train)

### Production Deployment (Template)

The production stage is commented out in the Dockerfile. To enable:

1. **Uncomment prod stage** in `Dockerfile`
2. **Uncomment prod service** in `docker-compose.yml` (if using compose)
3. **Build and run**:
   ```bash
   make docker-build-prod
   docker run --rm -v $(PWD)/models:/app/models:ro -v $(PWD)/data:/app/data:ro mlops-accidents:prod
   ```

> **Note**: The prod stage will be updated to run FastAPI when the API is implemented (Phase 1).

## 🔄 Pipeline Overview

The ML pipeline follows a simple 5-step workflow from raw data to predictions:

```
┌─────────────────┐
│  1. Data Import │  Downloads 4 CSV files from AWS S3
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Preprocessing│  Cleans & merges data → interim dataset
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Feature Eng. │  Creates ML-ready features (temporal, cyclic, interactions)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. Training    │  Trains multiple models (XGBoost, RF, LR, LightGBM) with SMOTE
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  5. Prediction  │  Makes predictions on new data
└─────────────────┘
```

### Key Files & Their Roles

| Step | File | What It Does | Output |
|------|------|--------------|--------|
| **1. Import** | `src/data/import_raw_data.py` | Downloads raw CSV files from S3 | `data/raw/*.csv` |
| **2. Preprocess** | `src/data/make_dataset.py` | Merges 4 datasets, cleans data, creates target variable | `data/preprocessed/interim_dataset.csv` |
| **3. Features** | `src/features/build_features.py` | Feature engineering: temporal, cyclic encoding, interactions | `data/preprocessed/features.csv` + `models/label_encoders.joblib` |
| **4. Train** | `src/models/train_multi_model.py` | Trains multiple models, compares performance, saves models + metadata | `models/{model_type}_model.joblib` + `data/metrics/model_comparison.csv` |
| **5. Predict** | `src/models/predict_model.py` | Loads model, preprocesses input, makes predictions | Prediction results |

### Supporting Utilities

- **`src/features/preprocess.py`**: Reusable preprocessing functions for inference (ensures training/inference consistency)

### Quick Command Reference

```bash
# Run complete pipeline
make workflow-all

# Or run steps individually
make run-import      # Step 1: Download data
make run-preprocess  # Step 2: Clean & merge
make run-features    # Step 3: Feature engineering
make run-train       # Step 4: Train model
make run-predict     # Step 5: Make predictions
```

## 📊 Current State

**Phase**: Phase 1 - Foundations (Deadline: December 19th, 2024)

### ✅ Completed

**Project Foundation:**
- ✅ Project structure based on cookiecutter-data-science template
- ✅ Reproducible Python environment setup with `pyproject.toml` and UV
- ✅ Development automation with Makefile
- ✅ Python version management (`.python-version`, `.tool-versions`)
- ✅ Initial data exploration notebook

**Containerization (Engineer C):**
- ✅ **Multi-stage Dockerfile**: Dev, train, and prod stages implemented
- ✅ **Docker Compose**: Services for dev, train, and dvc-pull configured
- ✅ **Volume mounts**: Proper data and model persistence
- 🚧 **Production stage**: Template ready, awaiting FastAPI implementation

**ML Modeling & Tracking (Engineer B):**
- ✅ **Feature Engineering Pipeline**: Complete feature engineering module (`build_features.py`) with temporal features, cyclic encoding, categorical transformations, and interactions
- ✅ **Preprocessing Utilities**: Reusable preprocessing functions (`preprocess.py`) ensuring training/inference consistency
- ✅ **Model Training**: Multi-model training framework (`train_multi_model.py`) with XGBoost, Random Forest, Logistic Regression, LightGBM + SMOTE
- ✅ **Model Prediction**: Inference script (`predict_model.py`) with feature preprocessing and model artifact loading
- ✅ **Model Artifacts**: Model and metadata saving (per-model files: `{model_type}_model.joblib`, `label_encoders.joblib`, `{model_type}_model_metadata.joblib`)
- ✅ **Metrics Saving**: Evaluation metrics saved to files (accuracy, precision, recall, F1-score)
- ✅ **ML-0**: Baseline Model Definition (XGBoost baseline implemented)
- ✅ **ML-1**: Config-Driven Training (`model_config.yaml` created, all parameters moved from hardcoded values)
- ✅ **ML-2**: MLflow Integration (experiment tracking and model registry with versioning and staging implemented)

### 🚧 In Progress

**ML Modeling & Tracking (Engineer B):**
- 🚧 **ML-3**: Model Evaluation (metrics saved to files, but not to DVC metrics format; confusion matrix pending)
- 🚧 **TEST-1**: Unit Test Implementation (test suite for models not yet created)

**Data & Pipeline Infrastructure (Engineer A):**
- 🚧 **DVC + Dagshub integration**: Data versioning setup in progress
- 🚧 **Data validation**: Pandera or manual schema validation pending

**API & CI/CD (Engineer C):**
- ✅ **Microservices Architecture**: Auth, Data, Train, Predict services implemented
- ✅ **API Endpoint Test Suite**: Comprehensive test suite for all microservices
- ✅ **Test Service Docker Container**: Dockerized test service for CI/CD integration
- 🚧 **CI/CD pipeline**: GitHub Actions workflows pending

### 📝 Planned

See [Roadmap](#-roadmap) section for detailed phase breakdown.

## 🚀 Getting Started

### Prerequisites

- **Docker & Docker Compose** - **Required** for containerized workflow
- **Python 3.8+** (3.11 recommended) - For local development (optional)
- **UV** - Fast Python package installer ([Install](https://github.com/astral-sh/uv): `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **DVC** - Installed automatically with dependencies
- **Git** & **Make** - Usually pre-installed
- **Dagshub account** - [Sign up](https://dagshub.com) for data versioning (optional)

> **⚠️ Windows Users**: This project uses Makefiles and shell scripts that require a Unix-like environment. On Windows, please use one of the following:
> - **Git Bash** (recommended) - Comes with Git for Windows
> - **WSL (Windows Subsystem for Linux)** - Full Linux environment
> - **MSYS2/MinGW** - Unix-like environment for Windows
>
> The Makefile and shell commands will not work in native Windows PowerShell or CMD.

### Quick Start (Docker - Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/chrmei/MLOps_accidents.git
   cd MLOps_accidents
   ```

2. **Build Docker images**
   ```bash
   docker compose build
   # Or using Makefile:
   make docker-build-dev
   make docker-build-train
   ```

3. **Run the complete pipeline**
   ```bash
   # Option 1: Using Docker Compose
   docker compose up train
   
   # Option 2: Using Makefile
   make docker-run-train
   ```

4. **Start development shell**
   ```bash
   docker compose up dev
   # Or: make docker-run-dev
   ```

### Local Development Setup (Optional)

If you prefer to run locally without Docker:

1. **Clone and setup Python**
   ```bash
   git clone https://github.com/chrmei/MLOps_accidents.git
   cd MLOps_accidents
   # Using pyenv: pyenv install 3.11.0 && pyenv local 3.11.0
   # Using asdf: asdf install python 3.11.0 && asdf reshim python
   ```

2. **Install dependencies**
   ```bash
   make install-dev  # Installs project + dev dependencies (pytest, black, isort, mypy, etc.)
   # Alternative: uv pip install -e ".[dev]"
   ```

3. **Verify installation**
   ```bash
   python --version && make help
   ```

4. **Set up DVC and Dagshub (Optional but recommended)**
   
   DVC is used for data versioning. To set it up:
   
   ```bash
   # Step 1: Create .env file from template (if .env.example exists)
   cp .env.example .env
   
   # Step 2: MANUALLY EDIT .env file with your Dagshub credentials:
   #   - DAGSHUB_USERNAME: Your Dagshub username
   #   - DAGSHUB_TOKEN: Get from https://dagshub.com/user/settings/tokens
   #   - DAGSHUB_REPO: Your repository (e.g., chrmei/MLOps_accidents)
   # 
   # IMPORTANT: You must manually edit .env before running the next commands!
   
   # Step 3: Initialize DVC and configure remote using Makefile
   make dvc-init
   make dvc-setup-remote
   ```
   
   **Important Notes**:
   - The `.env` file must be **manually edited** with your credentials before running `make dvc-setup-remote`
   - The `.env` file is gitignored and will never be committed
   - Each team member should create their own `.env` file with their personal Dagshub credentials

### Run the Pipeline

**In Docker (Recommended):**
```bash
# Complete workflow
docker compose up train

# Or step-by-step in dev container
docker compose up dev
# Inside container:
make workflow-all
```

**Locally:**
```bash
# 1. Import raw data (downloads 4 CSV files from AWS S3)
make run-import

# 2. Preprocess data (creates train/test splits in data/preprocessed/)
make run-preprocess

# 3. Train models (saves to models/{model_type}_model.joblib)
make run-train

# 4. Make predictions
make run-predict                    # Interactive mode
make run-predict-file FILE=path     # From JSON file
```

## 📁 Project Structure

```
MLOps_accidents/
├── .github/workflows/         # CI/CD pipelines (to be implemented)
│   ├── lint.yaml
│   └── test.yaml
├── data/                      # Data directory (created at runtime)
│   ├── external/              # Data from third party sources
│   ├── interim/               # Intermediate data that has been transformed
│   ├── processed/             # The final, canonical data sets for modeling
│   └── raw/                   # The original, immutable data dump
├── doc/                       # Project documentation
│   ├── README_INITIAL.md      # Initial project documentation
│   ├── Plan_Phase_01.md       # Detailed Phase 1 execution plan
│   └── Roadmap.md             # Project roadmap and milestones
├── logs/                      # Logs from training and predicting
├── models/                    # Trained and serialized models
├── notebooks/                 # Jupyter notebooks
│   └── 1.0-ldj-initial-data-exploration.ipynb
├── references/                # Data dictionaries, manuals, and explanatory materials
├── reports/                   # Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures/               # Generated graphics and figures
├── src/                       # Source code for use in this project
│   ├── __init__.py
│   ├── config/                # Configuration files (YAML configs)
│   │   └── model_config.yaml
│   ├── data/                  # Scripts to download or generate data
│   │   ├── __init__.py
│   │   ├── check_structure.py
│   │   ├── import_raw_data.py # Downloads data from S3
│   │   └── make_dataset.py    # Preprocesses raw data
│   ├── features/              # Scripts to turn raw data into features
│   │   ├── __init__.py
│   │   ├── build_features.py
│   │   └── preprocess.py      # Reusable preprocessing for inference
│   ├── models/                # Scripts to train models and make predictions
│   │   ├── __init__.py
│   │   ├── predict_model.py   # Model inference script
│   │   ├── train_multi_model.py # Multi-model training framework
│   │   └── test_features.json # Example features for testing
│   └── visualization/         # Scripts to create visualizations
│       ├── __init__.py
│       └── visualize.py
├── scripts/                   # Utility scripts
│   ├── manage_model_registry.py # MLflow model registry management
│   └── setup_dvc_remote.sh
├── tests/                     # Pytest suite for API endpoint testing
│   ├── __init__.py
│   ├── conftest.py           # Shared fixtures and configuration
│   ├── test_auth_service.py  # Auth service endpoint tests
│   ├── test_data_service.py  # Data service endpoint tests
│   ├── test_train_service.py # Train service endpoint tests
│   ├── test_predict_service.py # Predict service endpoint tests
│   ├── README.md             # Test suite documentation
│   ├── TEST_SERVICE.md        # Docker test service usage guide
│   └── run_tests.sh          # Convenience script for running tests
├── Dockerfile                 # Multi-stage Dockerfile
├── docker-compose.yml         # Docker Compose configuration
├── dvc.yaml                   # DVC pipeline definition
├── LICENSE                    # MIT License
├── Makefile                   # Development commands and automation
├── pyproject.toml             # Python project configuration and dependencies
├── requirements.txt           # Python dependencies (legacy, use pyproject.toml)
├── setup.py                   # Package setup configuration (legacy)
└── README.md                  # This file
```

## 🛠️ Technology Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Containerization** | **Docker** | Multi-stage containers for dev, train, and prod |
| **Data Versioning** | **DVC + Dagshub** | Versioning raw data and artifacts without AWS |
| **Experiment Tracking** | **MLflow (Dagshub)** | Tracking metrics, parameters, and models |
| **Model Serving** | **FastAPI** | REST API for real-time accident prediction (planned) |
| **CI/CD** | **GitHub Actions** | Automated testing, linting, and image building (planned) |
| **Machine Learning** | **scikit-learn, XGBoost, LightGBM** | Model training and evaluation |
| **Data Processing** | **pandas, numpy** | Data manipulation and preprocessing |
| **Testing** | **pytest** | Unit and integration testing |
| **Code Quality** | **black, flake8, isort** | Code formatting and linting |
| **Dependency Management** | **UV** | Fast Python package installer and resolver |
| **Build System** | **setuptools** | Package building and distribution |

## 🧪 API Endpoint Testing

The project includes a comprehensive test suite for all microservices API endpoints. Tests cover successful requests, error handling, authentication, and authorization.

### Quick Start

**Run all tests in Docker (recommended):**
```bash
# Start services and run all API tests
make docker-test

# Or using Docker Compose directly
docker compose --profile test run --rm test
```

**Run tests locally (requires services running):**
```bash
# Set BASE_URL if services are not on localhost
export BASE_URL=http://localhost

# Run all API tests
make test-api

# Run with coverage
make test-api-cov

# Run tests for specific service
make test-api-auth      # Auth service only
make test-api-data      # Data service only
make test-api-train     # Train service only
make test-api-predict   # Predict service only
```

### Docker Compose Usage

The test service runs as a Docker container that can execute tests against all microservices:

```bash
# Run all tests
docker compose --profile test run --rm test

# Run specific test file
docker compose --profile test run --rm test pytest tests/test_auth_service.py -v

# Run tests with coverage
docker compose --profile test run --rm test pytest tests/ -v --cov=services --cov-report=html

# Run with custom BASE_URL
docker compose --profile test run --rm -e BASE_URL=http://192.168.1.100 test

# Interactive shell in test container
docker compose --profile test run --rm test bash
```

### Test Coverage

The test suite covers:
- ✅ **Auth Service**: Login, token refresh, user management, authorization
- ✅ **Data Service**: Preprocessing jobs, feature engineering, job status, listing
- ✅ **Train Service**: Training jobs, job status, metrics retrieval
- ✅ **Predict Service**: Single/batch predictions, model listing

### Configuration

Tests can be configured via environment variables:

```bash
export BASE_URL=http://localhost          # Base URL for API endpoints
export ADMIN_USERNAME=admin              # Admin username
export ADMIN_PASSWORD=your_password      # Admin password
export TEST_USER_USERNAME=testuser       # Test user username
export TEST_USER_PASSWORD=TestUser@123   # Test user password
```

For detailed documentation, see:
- [Test Suite README](tests/README.md) - Complete test documentation
- [Test Service Guide](tests/TEST_SERVICE.md) - Docker test service usage

## 🛠️ Development Commands

Run `make help` to see all commands. Key commands:

**Setup & Dependencies**
- `make install-dev` - Install with dev dependencies
- `make setup-venv` - Create venv and install dependencies
- `make clean` - Remove build artifacts

**Code Quality**
- `make format` - Format with black & isort
- `make lint` - Lint with flake8
- `make type-check` - Type checking with mypy

**Testing**
- `make test` - Run pytest
- `make test-cov` - Run with coverage report
- `make test-api` - Run API endpoint tests (requires services running)
- `make test-api-cov` - Run API tests with coverage
- `make test-api-auth` - Run auth service tests only
- `make test-api-data` - Run data service tests only
- `make test-api-train` - Run train service tests only
- `make test-api-predict` - Run predict service tests only
- `make docker-test` - Run all API tests in Docker (auto-starts services)
- `make docker-test-build` - Build test service Docker image
- `make docker-test-run CMD="..."` - Run custom test command in Docker
- `make docker-test-cov` - Run API tests with coverage in Docker
- `make docker-test-service SERVICE=auth` - Run tests for specific service

**Data Pipeline**
- `make run-import` - Import raw data
- `make run-preprocess` - Preprocess data
- `make run-features` - Build features
- `make run-train` - Train models
- `make run-predict` - Interactive predictions
- `make run-predict-file FILE=path` - Predictions from JSON

**Docker**
- `make docker-build-dev` - Build development image
- `make docker-build-train` - Build training image
- `make docker-build-services` - Build all microservice images
- `make docker-up` - Start all microservices
- `make docker-down` - Stop all microservices
- `make docker-health` - Check health of all services
- `make docker-run-dev` - Run dev container (interactive)
- `make docker-run-train` - Run training pipeline
- `make docker-run-dev-exec CMD="..."` - Run one-off command
- `make docker-dvc-pull` - Pull data/models from DVC remote via Docker Compose

**DVC (Data Version Control)**
- `make dvc-init` - Initialize DVC
- `make dvc-setup-remote` - Configure Dagshub remote (**requires manually edited .env**)
- `make dvc-status` / `dvc-push` / `dvc-pull` / `dvc-repro`

> **Important**: For `make dvc-setup-remote`, you must first manually edit `.env` with your Dagshub credentials (copy from `.env.example`).

## 🔄 Workflow

### Detailed Pipeline Steps

#### Step 1: Data Import (`src/data/import_raw_data.py`)
- **Purpose**: Download raw data from AWS S3
- **Input**: None (downloads from S3)
- **Output**: 4 CSV files in `data/raw/`
  - `caracteristiques-2021.csv` (accident characteristics)
  - `lieux-2021.csv` (location data)
  - `usagers-2021.csv` (victim/user data)
  - `vehicules-2021.csv` (vehicle data)

#### Step 2: Data Preprocessing (`src/data/make_dataset.py`)
- **Purpose**: Clean and merge raw data into a single dataset
- **Input**: 4 raw CSV files
- **Process**:
  - Merges all datasets on accident ID (`Num_Acc`)
  - Cleans data (handles missing values, converts types)
  - Creates aggregations (`nb_victim`, `nb_vehicules`)
  - Transforms target variable to binary classification
- **Output**: `data/preprocessed/interim_dataset.csv`

#### Step 3: Feature Engineering (`src/features/build_features.py`)
- **Purpose**: Transform interim data into ML-ready features
- **Input**: `interim_dataset.csv`
- **Process**:
  - **Temporal features**: Creates datetime, extracts hour/month/day, cyclic encoding
  - **Age features**: Calculates victim age, creates age bins
  - **Categorical transformations**: Groups vehicle types, atmospheric conditions
  - **Interactions**: Creates feature interactions (e.g., `victims_per_vehicle`)
  - **Encoding**: Label encodes categorical features
- **Output**: 
  - `data/preprocessed/features.csv` (feature-engineered dataset)
  - `models/label_encoders.joblib` (saved encoders for inference)

#### Step 4: Model Training (`src/models/train_multi_model.py`)
- **Purpose**: Train multiple models (XGBoost, Random Forest, Logistic Regression, LightGBM) with SMOTE for imbalanced data
- **Input**: `features.csv`
- **Process**:
  - Splits data into train/test sets (same split for all models for fair comparison)
  - Applies SMOTE (oversampling) to handle class imbalance
  - Trains multiple model types (with or without grid search)
  - Evaluates each model's performance
  - Generates model comparison report
- **Output**:
  - `models/{model_type}_model.joblib` (trained model pipelines, e.g., `xgboost_model.joblib`)
  - `models/{model_type}_model_metadata.joblib` (feature names, config per model)
  - `data/metrics/{model_type}_metrics.json` (evaluation metrics per model)
  - `data/metrics/model_comparison.csv` (comparison report ranking models by F1 score)

#### Step 5: Prediction (`src/models/predict_model.py`)
- **Purpose**: Make predictions on new data
- **Input**: JSON file with input features
- **Process**:
  - Loads trained model and artifacts (encoders, metadata)
  - Preprocesses input using same pipeline as training (`src/features/preprocess.py`)
  - Aligns features with model expectations
  - Makes prediction
- **Output**: Prediction result (0 = Non-Priority, 1 = Priority)

### Complete Workflow Command

```bash
# Run entire pipeline in one command
make workflow-all

# Or run steps individually for more control
make run-import      # Step 1: Download raw data
make run-preprocess  # Step 2: Create interim dataset
make run-features    # Step 3: Build features
make run-train       # Step 4: Train model
make run-predict     # Step 5: Make predictions
```

### Reproducing the Workflow using DVC

Run `make dvc-repro` to reproduce the workflow using default configurations. This will:

1. Pull the latest version of raw data from the remote storage using `dvc pull`

2. Complete the workflow from [Step 2](#step-2-data-preprocessing-srcdatamake_datasetpy) on

Note that DVC needs to be set up first using `make dvc-setup-remote`.
 
The default configurations are defined [here](src/config/model_config.yaml) and the prediction step is done on test features defined [here](src/models/test_features.json), which finally should output

```
Prediction: 1
Interpretation: Priority
```

**Target (Post Phase 1)**: DVC Pipeline → MLflow Tracking → FastAPI Serving → CI/CD

## 📦 MLflow Model Registry

The project uses MLflow Model Registry for model versioning and staging. Models are automatically registered during training, and you can manage their lifecycle through staging transitions.

### Configuration

Model registry settings are configured in `src/config/model_config.yaml`:

```yaml
mlflow:
  enabled: true
  tracking_uri: ""  # Set via MLFLOW_TRACKING_URI or DAGSHUB_REPO env vars
  experiment_name: "accident_prediction"
  log_model: true
  log_artifacts: true
  model_registry:
    registered_model_name: "Accident_Prediction"  # Base name - model type will be appended automatically
    default_stage: "None"  # Options: None, Staging, Production, Archived
    auto_transition_to_staging: false  # Auto-promote to Staging after registration
    production_stage: "Production"
```

### Quick Start: Model Staging Workflow

Follow these steps to train, stage, and deploy models using the MLflow Model Registry:

#### Step 1: Set Up Environment

Configure your MLflow tracking URI (choose one method):

```bash
# Option 1: Set environment variable directly
export MLFLOW_TRACKING_URI="https://dagshub.com/yourusername/yourrepo.mlflow"

# Option 2: Use DAGSHUB_REPO (auto-constructs URI)
export DAGSHUB_REPO="yourusername/yourrepo"
```

Or add to your `.env` file for persistence.

#### Step 2: Train and Register Models

Train models - they will be automatically registered:

```bash
# Train multiple models (default - creates versions for each model type)
make run-train

# Or with grid search for hyperparameter tuning
make run-train-grid

# Or train specific models only
python src/models/train_multi_model.py --models xgboost random_forest
```

**What happens:**
- Multiple models are trained (XGBoost, Random Forest, Logistic Regression, LightGBM by default)
- Each model is saved locally to `models/{model_type}_model.joblib`
- Each model is automatically registered to MLflow Model Registry with name `Accident_Prediction_{ModelType}`
- New versions are created for each model (starts in "None" stage)
- Metrics, parameters, and artifacts are logged to MLflow for each model
- Model comparison report is generated at `data/metrics/model_comparison.csv`

#### Step 3: Check Registered Models

View what's in your registry:

```bash
# See all registered models
python scripts/manage_model_registry.py list-models

# See all versions of your specific model
python scripts/manage_model_registry.py list-versions \
  --model-name Accident_Prediction_XGBoost
```

#### Step 4: Move Model to Staging

After validating the model locally, promote it to Staging for testing:

```bash
# Move version 1 to Staging
python scripts/manage_model_registry.py transition \
  --model-name Accident_Prediction_XGBoost \
  --version 1 \
  --stage Staging
```

#### Step 5: Test Model from Staging

Test the Staging model to ensure it works correctly:

```bash
# Make predictions using Staging model
python src/models/predict_model.py src/models/test_features.json \
  --model-name Accident_Prediction_XGBoost \
  --stage Staging
```

#### Step 6: Promote to Production

Once testing passes, promote to Production:

```bash
# Option A: Promote latest version (recommended)
python scripts/manage_model_registry.py promote \
  --model-name Accident_Prediction_XGBoost \
  --stage Production

# Option B: Promote specific version
python scripts/manage_model_registry.py transition \
  --model-name Accident_Prediction_XGBoost \
  --version 1 \
  --stage Production
```

#### Step 7: Use Production Model

In production environments, always load from the Production stage:

```bash
# Load from Production stage (recommended)
python src/models/predict_model.py src/models/test_features.json \
  --model-name Accident_Prediction_XGBoost \
  --stage Production
```

#### Step 8: Archive Old Models

When a model is deprecated, archive it (don't delete - maintains history):

```bash
# Archive old version
python scripts/manage_model_registry.py archive \
  --model-name Accident_Prediction_XGBoost \
  --version 1
```

### Complete Example Workflow

Here's a complete example from training to production:

```bash
# 1. Set up environment
export DAGSHUB_REPO="yourusername/yourrepo"

# 2. Train a new model
make run-train
# Output: Model registered as 'Accident_Prediction_XGBoost' version 1

# 3. Check what was registered
python scripts/manage_model_registry.py list-versions \
  --model-name Accident_Prediction_XGBoost
# You'll see version 1 in "None" stage

# 4. Move to Staging for testing
python scripts/manage_model_registry.py transition \
  --model-name Accident_Prediction_XGBoost \
  --version 1 \
  --stage Staging

# 5. Test the Staging model
python src/models/predict_model.py src/models/test_features.json \
  --model-name Accident_Prediction_XGBoost \
  --stage Staging

# 6. If tests pass, promote to Production
python scripts/manage_model_registry.py transition \
  --model-name Accident_Prediction_XGBoost \
  --version 1 \
  --stage Production

# 7. Use Production model
python src/models/predict_model.py src/models/test_features.json \
  --model-name Accident_Prediction_XGBoost \
  --stage Production

# 8. Later, train a better model (creates version 2)
make run-train

# 9. After validating version 2, promote it
python scripts/manage_model_registry.py promote \
  --model-name Accident_Prediction_XGBoost \
  --stage Production
# This moves version 2 to Production

# 10. Archive old version 1
python scripts/manage_model_registry.py archive \
  --model-name Accident_Prediction_XGBoost \
  --version 1
```

### Model Staging Lifecycle

Models progress through the following stages:

1. **None** (default) - Newly registered models start here
2. **Staging** - Models under evaluation/testing
3. **Production** - Models deployed and serving predictions
4. **Archived** - Deprecated models

### Managing Models

Use the `scripts/manage_model_registry.py` script to manage models:

#### List Registered Models

```bash
# List all registered models
python scripts/manage_model_registry.py list-models

# List all versions of a specific model
python scripts/manage_model_registry.py list-versions --model-name Accident_Prediction_XGBoost
```

#### Transition Models Between Stages

```bash
# Transition a specific version to Production
python scripts/manage_model_registry.py transition \
  --model-name Accident_Prediction_XGBoost \
  --version 1 \
  --stage Production

# Promote latest version to Production
python scripts/manage_model_registry.py promote \
  --model-name Accident_Prediction_XGBoost \
  --stage Production

# Archive an old version
python scripts/manage_model_registry.py archive \
  --model-name Accident_Prediction_XGBoost \
  --version 1
```

#### Get Model Information

```bash
# Get model info by stage
python scripts/manage_model_registry.py get-model \
  --model-name Accident_Prediction_XGBoost \
  --stage Production
```

### Loading Models from Registry

The prediction script (`src/models/predict_model.py`) supports loading models from the MLflow registry:

**Best Practice: Use MLflow Model Registry for Production Inference**

```bash
# Automatically use best Production model across all model types (recommended)
python src/models/predict_model.py src/models/test_features.json \
  --use-best-model

# Or load from Production stage for specific model type
python src/models/predict_model.py src/models/test_features.json \
  --use-mlflow-production

# Or explicitly specify model name and stage
python src/models/predict_model.py src/models/test_features.json \
  --model-name Accident_Prediction_XGBoost \
  --stage Production

# Load specific version
python src/models/predict_model.py src/models/test_features.json \
  --model-name Accident_Prediction_XGBoost \
  --version 6

# Load from local filesystem (for development/testing only)
python src/models/predict_model.py src/models/test_features.json \
  --model-path models/xgboost_model.joblib

# Use environment variables
export USE_BEST_MODEL=true  # Auto-select best model
# or
export USE_MLFLOW_PRODUCTION=true  # Use default model type (XGBoost)
python src/models/predict_model.py src/models/test_features.json
```

**Architecture:**
- **MLflow Model Registry**: Used for production model serving (default with `--use-mlflow-production`)
- **Local filesystem (DVC)**: Used for development/testing and pipeline reproducibility
- Models are tracked in DVC for reproducible training pipelines, but production inference loads from MLflow

### Automatic Staging Transitions

You can enable automatic transition to Staging after model registration by setting `auto_transition_to_staging: true` in the config. This is useful for automated workflows where new models should be immediately available for testing.

### Model Storage Architecture (Best Practices)

**MLflow Model Registry** (for models):
- ✅ Production model serving and deployment
- ✅ Model versioning and lifecycle management (Staging → Production → Archived)
- ✅ Model metadata, metrics, and parameters tracking
- ✅ Experiment tracking and model comparison

**DVC** (for data):
- ✅ Data pipeline reproducibility (raw → preprocessed → features)
- ✅ Data versioning and tracking
- ✅ Label encoders and preprocessing artifacts
- ✅ Metrics files for pipeline tracking
- ⚠️ Model files tracked only for pipeline reproducibility (not for production use)

**Key Points:**
- Production inference should load from MLflow Model Registry (Production stage)
- **Multi-model setup**: Use `--use-best-model` to automatically select the best performing Production model across all model types (XGBoost, RandomForest, etc.)
- Each model type is registered separately: `Accident_Prediction_XGBoost`, `Accident_Prediction_Random_Forest`, etc.
- Local model files in DVC are for development/testing and pipeline reproducibility only
- Use `--use-mlflow-production` flag or `USE_MLFLOW_PRODUCTION=true` for production inference (defaults to XGBoost)
- Use `--use-best-model` flag or `USE_BEST_MODEL=true` to auto-select best model
- `make dvc-pull` pulls data and training artifacts for local development, not production models

### Best Practices

1. **Version Control**: Each training run creates a new model version automatically
2. **Staging Workflow**: 
   - New models → None stage
   - After validation → Staging stage
   - After approval → Production stage
3. **Production Models**: Always load from Production stage in production environments
4. **Archiving**: Archive old models instead of deleting them to maintain history

### Environment Setup

Set up MLflow tracking URI via environment variables:

```bash
# Option 1: Direct MLflow URI
export MLFLOW_TRACKING_URI="https://dagshub.com/username/repo.mlflow"

# Option 2: Use DAGSHUB_REPO (auto-constructs URI)
export DAGSHUB_REPO="username/repo"
```

The tracking URI can also be set in `model_config.yaml`, but environment variables take precedence.

## 🔄 Multi-Model Training Framework

**The multi-model training framework is now the default training method.** The project includes a standardized framework for training and comparing multiple ML models. This framework enables easy experimentation with different algorithms (XGBoost, Random Forest, Logistic Regression, LightGBM) and automatic comparison of their performance.

### Features

- **Standardized Training**: All models use the same train/test split for fair comparison
- **MLflow Integration**: Models are automatically logged with type-specific tags for easy filtering
- **Model Registry**: Each model type gets its own registered model name (format: `Accident_Prediction_{ModelType}`)
- **Automatic Comparison**: Generates comparison reports ranking models by performance metrics
- **Extensible**: Easy to add new model types by creating a trainer class
- **Default Training**: Used by default in `make run-train` and DVC pipeline

### Quick Start

```bash
# Train all enabled models (default)
make run-train

# Train with grid search for hyperparameter tuning
make run-train-grid

# Train specific models only
python src/models/train_multi_model.py --models xgboost random_forest

# Train single model (legacy mode)
make run-train-single
```

### Output Files

After training, you'll find:
- **Models**: `models/{model_type}_model.joblib` (e.g., `models/xgboost_model.joblib`)
- **Metadata**: `models/{model_type}_model_metadata.joblib`
- **Metrics**: `data/metrics/{model_type}_metrics.json`
- **Comparison**: `data/metrics/model_comparison.csv` (ranks models by F1 score)

### Model Names in Registry

Models are registered with the format `Accident_Prediction_{ModelType}`:
- `Accident_Prediction_XGBoost`
- `Accident_Prediction_Random_Forest`
- `Accident_Prediction_Logistic_Regression`
- `Accident_Prediction_Lightgbm`

This naming convention groups all models under the project prefix for easy identification in MLflow.

For detailed documentation on the multi-model training framework, including how to add new models, see the [Multi-Model Training README](src/models/README_MULTI_MODEL.md).

### Quick Reference: Common Commands

```bash
# LIST MODELS
python scripts/manage_model_registry.py list-models
python scripts/manage_model_registry.py list-versions --model-name Accident_Prediction_XGBoost

# TRANSITION STAGES
python scripts/manage_model_registry.py transition --model-name Accident_Prediction_XGBoost --version 1 --stage Staging
python scripts/manage_model_registry.py transition --model-name Accident_Prediction_XGBoost --version 1 --stage Production

# PROMOTE LATEST VERSION
python scripts/manage_model_registry.py promote --model-name Accident_Prediction_XGBoost --stage Production

# ARCHIVE OLD MODEL
python scripts/manage_model_registry.py archive --model-name Accident_Prediction_XGBoost --version 1

# GET MODEL INFO
python scripts/manage_model_registry.py get-model --model-name Accident_Prediction_XGBoost --stage Production

# USE IN PREDICTIONS
python src/models/predict_model.py file.json --model-name Accident_Prediction_XGBoost --stage Production
python src/models/predict_model.py file.json --model-name Accident_Prediction_XGBoost --version 1
python src/models/predict_model.py file.json --model-path models/trained_model.joblib  # Local filesystem
```

## 👥 Team Structure

The project is designed for a 3-person team with clear separation of concerns:

### **Engineer A: Data & Pipeline Infrastructure**
- **Focus**: Getting data from raw to "model-ready"
- **Deliverables**: DVC pipelines, data validation (Pandera or manual), Dagshub integration
- **Primary Files**: `src/data/`, `dvc.yaml`, `params.yaml`
- **Status**: 
  - 🚧 DVC + Dagshub integration in progress
  - 🚧 Data validation pending

### **Engineer B: ML Modeling & Tracking**
- **Focus**: ML model development and experiment logging
- **Deliverables**: Training scripts, MLflow tracking, model registry management
- **Primary Files**: `src/models/`, `src/features/`, `src/config/model_config.yaml`
- **Status**: 
  - ✅ Feature engineering pipeline complete
  - ✅ Model training and prediction scripts functional
  - ✅ Config-driven training (ML-1) - Complete
  - ✅ MLflow integration (ML-2) - Model registry with versioning and staging implemented
  - 🚧 DVC metrics format (ML-3) - Partial (metrics saved, DVC format pending)
  - 🚧 Unit tests (TEST-1) - Pending

### **Engineer C: API, Docker & CI/CD**
- **Focus**: Containerization, API development, and automation
- **Deliverables**: FastAPI application, Dockerfiles, GitHub Actions pipelines
- **Primary Files**: `src/api/`, `Dockerfile`, `.github/workflows/`
- **Status**:
  - ✅ Multi-stage Dockerfile implemented (dev, train, prod template)
  - ✅ Docker Compose configuration complete
  - 🚧 FastAPI service pending
  - 🚧 CI/CD pipeline pending

## 🗺️ Roadmap

### Phase 1: Foundations (Deadline: December 19th, 2024)

**Containerization (Engineer C) Progress:**
- ✅ Multi-stage Dockerfile (dev, train, prod template)
- ✅ Docker Compose services configured
- ✅ Volume mounts and environment setup
- 🚧 Production stage ready for FastAPI integration

**ML Modeling & Tracking (Engineer B) Progress:**
- ✅ Feature engineering pipeline (`build_features.py`, `preprocess.py`)
- ✅ Multi-model training framework (`train_multi_model.py`) with XGBoost, Random Forest, Logistic Regression, LightGBM + SMOTE
- ✅ Model prediction script (`predict_model.py`) with preprocessing
- ✅ Model artifacts and metadata saving (per-model files)
- ✅ **ML-0**: XGBoost baseline model implemented
- ✅ **ML-1**: Config-driven training (`model_config.yaml` created, all parameters moved)
- ✅ **ML-2**: MLflow integration for experiment tracking and model registry
- ✅ **Multi-Model Framework**: Standardized framework for training and comparing multiple models
- 🚧 **ML-3**: DVC metrics format and confusion matrix (partial - metrics saved, DVC format pending)
- 🚧 **TEST-1**: Unit tests for model training and prediction

**Overall Phase 1 Status:**
- ✅ Define project objectives and key metrics
- ✅ Set up reproducible development environment (containerization, Docker) - **Docker implemented**
- ✅ Collect and preprocess data (ML Pipeline) - **Data pipeline functional**
- 🚧 Build and evaluate baseline ML model, implement unit tests - **Model training functional, baseline complete, tests pending**
- 🚧 Implement basic inference API - **Pending**

### Phase 2: Microservices, Tracking & Versioning (Deadline: January 16th, 2026)
- ✅ Set up experiment tracking with MLflow
- 🚧 Implement data & model versioning (MLflow, DVC)
- Decompose application into microservices and design orchestration

### Phase 3: Orchestration & Deployment (Deadline: January 29th, 2026)
- Finalize end-to-end orchestration
- Create CI Pipeline (GitHub Actions: linter and others)
- Optimize and secure the API
- Implement scalability with Docker/Kubernetes

### Phase 4: Monitoring & Maintenance (Deadline: February 6th, 2026)
- Set up performance monitoring using Prometheus/Grafana
- Implement drift detection with Evidently
- Develop automated model and component updates
- Finalize technical documentation

**Final Presentation (Defence)**: February 9th, 2026

For detailed execution plans, see:
- [Phase 1 Plan](doc/Plan_Phase_01.md)
- [Roadmap](doc/Roadmap.md)

## 📝 Development Guidelines

**Code**: Run scripts from project root, use conventional commits (`feat:`, `fix:`), follow PEP 8, add type hints  
**Branches**: `feature/<ticket-id>-description`, PRs require approval + passing CI  
**Testing**: >70% coverage for `src/data/`, `src/models/`, `src/api/`; run `make test` before PRs  
**Dependencies**: Managed in `pyproject.toml` via UV (`make install-dev`); Python version in `.python-version`  
**Containerization**: All workflows should run in Docker containers for reproducibility

## ✅ GO-LIVE Checklist

Before production deployment, complete these items:

**Secrets and config**
- [ ] Set strong `JWT_SECRET_KEY` (never use default `CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET_KEY`)
- [ ] Change default admin password (`ADMIN_PASSWORD`); do not use default in production

**Security**
- [ ] Set `CORS_ORIGINS` to actual front-end origins (no wildcards in production)
- [ ] Review rate limits and lockout settings (per-username limits, lockout duration in `config.py`)

**Infrastructure**
- [ ] Enable HTTPS when implemented
- [ ] Replace in-memory user store with persistent database for production
- [ ] For multi-instance: replace in-memory rate/lockout/blocklist with a shared store (e.g. Redis)

**Application**
- [ ] Token revocation: in-memory blocklist is single-instance only; for multi-instance use a shared store (e.g. Redis)
- [ ] Ensure auth events (failed login, lockout) are logged for audit (logging is configured in auth routes)

## 🤝 Contributing

1. Setup: `make install-dev` (or use Docker: `docker compose up dev`)
2. Branch: `git checkout -b feature/your-feature-name`
3. Develop: Make changes following guidelines
4. Quality: `make format && make lint && make type-check`
5. Test: `make test` (coverage: `make test-cov`)
6. PR: Ensure all checks pass, submit with clear description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Project based on the [cookiecutter data science project template](https://drivendata.github.io/cookiecutter-data-science/)
- Data sourced from French road accident databases

## 📚 Additional Documentation

- [Initial README](doc/README_INITIAL.md) - Original project documentation
- [Phase 1 Plan](doc/Plan_Phase_01.md) - Detailed Phase 1 execution plan
- [Roadmap](doc/Roadmap.md) - Project roadmap and milestones

---

**Note**: This project is in active development. The structure and workflows are being refined as we progress through Phase 1. For the most up-to-date information, refer to the documentation in the `doc/` directory.
