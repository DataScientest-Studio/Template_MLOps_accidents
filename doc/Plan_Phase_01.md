# 🚦 MLOps Road Accident Prediction - Technical Execution Plan

This plan outlines a containerized MLOps workflow for a 3-person team. The infrastructure pivots from AWS to **DVC + Dagshub** for data versioning and experiment tracking.

---

## 🏗️ MLOps Architecture: The Containerized Flow

The system is designed to be fully containerized, ensuring environment parity across development and production.



| Component | Technology | Role |
| :--- | :--- | :--- |
| **Data Versioning** | **DVC + Dagshub** | Versioning raw data and artifacts without AWS. |
| **Experiment Tracking** | **MLflow (Dagshub)** | Tracking metrics, parameters, and models. |
| **Pipeline Stages** | **Docker Containers** | Isolated environments for Data, Training, and API. |
| **Model Serving** | **FastAPI** | REST API for real-time accident prediction. |
| **CI/CD** | **GitHub Actions** | Automated testing, linting, and image building. |

---

## 👥 The 3-Person Team Split

To ensure a clear "Separation of Concerns," the work is divided into three distinct workstreams.

### **Engineer A: Data & Pipeline Infra**
* **Focus:** Getting data from raw to "model-ready".
* **Deliverables:** DVC pipelines, data validation (e.g. Pandera or manual), and Dagshub integration.
* **Primary Files:** `src/data/`, `dvc.yaml`, `params.yaml`.

### **Engineer B: ML Modeling & Tracking**
* **Focus:** ML model development and experiment logging.
* **Deliverables:** Training scripts, MLflow tracking, and model registry management.
* **Primary Files:** `src/models/`, `src/config/model_config.yaml`.

### **Engineer C: API, Docker & CI/CD**
* **Focus:** Containerization, API development, and automation.
* **Deliverables:** FastAPI application, Dockerfiles, and GitHub Actions pipelines.
* **Primary Files:** `src/api/`, `Dockerfile`, `.github/workflows/`.

---

## 📅 Phase 1: Foundations (Deadline: Dec 19th)

### 📊 Engineer B (ML Modeling & Tracking) - Current Status Summary

**Overall Progress: 46% Complete (2/5 tickets complete, 2 partially complete, 1 not started)**

| Ticket | Status | Completion | Priority |
|--------|--------|-----------|----------|
| **ML-1** | ✅ Complete | 100% | - |
| **ML-0** | 🚧 Partial | ~70% | High (blocked by ML-2) |
| **ML-2** | ❌ Not Started | 0% | **Critical** (blocks ML-0) |
| **ML-3** | 🚧 Partial | ~60% | Medium |
| **TEST-1** | ❌ Not Started | 0% | Medium |

**Next Steps (Priority Order):**
1. **ML-2**: Implement MLflow integration (unblocks ML-0)
2. **ML-3**: Complete DVC metrics format
3. **TEST-1**: Create unit tests for models

---

### Step 0: Project Foundation
| ID | Ticket Title | Assignee | Status | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **PROJ-1** | **Define Objectives & Metrics** | **All** | ✅ | Document project objectives, success metrics (F1, Precision, Recall), baseline model definition (XGBoost with optimized params), and minimum performance thresholds. |
| **DATA-0** | **Containerize Data Import** | **Eng A** | 🚧 | Wrap existing `import_raw_data.py` in Docker; integrate into DVC pipeline; ensure data collection step is part of reproducible workflow. |

### Step 1: Environment & Remote Sync
| ID | Ticket Title | Assignee | Status | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **INFRA-1** | **Dagshub & DVC Setup** | **Eng A** | 🚧 | DVC initialized; Remote set to Dagshub; `dvc push` works. |
| **INFRA-2** | **Project Dockerization** | **Eng C** | 🚧 | Multi-stage Dockerfile created; `.dockerignore` configured. |
| **ML-1** | **Config-Driven Training** | **Eng B** | ✅ **COMPLETE** | Move hardcoded params from `train_model.py` to `model_config.yaml`; refactor training script to use config. **Done:** Config file created, all parameters moved, training script refactored to use config with CLI overrides. |

### Step 2: The Data & Training Core
| ID | Ticket Title | Assignee | Status | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **DATA-1** | **Validation Pipeline** | **Eng A** | 🚧 | Pandera or manual schema validates raw CSVs; Checks types/ranges; integrates with existing `make_dataset.py` workflow. |
| **ML-0** | **Baseline Model Definition** | **Eng B** | 🚧 **70% COMPLETE** | Train XGBoost baseline model (optimized params) using existing `train_model.py` structure; establish performance benchmark; document metrics in MLflow. **Done:** XGBoost baseline trained, metrics calculated (Accuracy, Precision, Recall, F1), saved to files. **Missing:** Metrics not logged to MLflow (blocked by ML-2). |
| **ML-2** | **MLflow Integration** | **Eng B** | ❌ **NOT STARTED** | Logging metrics/params to Dagshub MLflow remote; track experiments for baseline and future models. **Status:** Config placeholder exists, but no MLflow implementation yet. **Blocking:** ML-0 completion. |
| **API-1** | **FastAPI Skeleton** | **Eng C** | 🚧 | `/predict` and `/health` endpoints active with Pydantic models; integrate with existing `predict_model.py` logic. |

### Step 3: Integration & Testing
| ID | Ticket Title | Assignee | Status | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **DATA-2** | **DVC Pipeline (dvc.yaml)**| **Eng A** | 🚧 | `dvc repro` runs ingestion -> validation -> preprocessing; integrates existing `import_raw_data.py` and `make_dataset.py`. |
| **ML-3** | **Model Evaluation** | **Eng B** | 🚧 **60% COMPLETE** | Precision/Recall/F1 and Confusion Matrix saved as DVC metrics; baseline model performance documented. **Done:** All metrics calculated, confusion matrix supported (when enabled in config), saved to JSON/text files. **Missing:** Metrics not in DVC format (`metrics.json`), confusion matrix not saved as separate file/image. **Subtasks:** 1) Refactor `training_metrics.json` to DVC-compliant format (remove non-numeric fields like `timestamp`, `used_grid_search`; flatten or separate complex nested structures like `classification_report` and `confusion_matrix`); ensure numeric metrics are at top level or simple hierarchy (e.g., `test_metrics.accuracy`). |
| **TEST-1** | **Unit Test Implementation** | **Eng B/C** | ❌ **NOT STARTED** | Unit tests for data validation, model training, and API endpoints; >70% code coverage for core modules (`src/data/`, `src/models/`, `src/api/`). **Status:** No test files created yet. |
| **CI-1** | **GitHub Actions CI** | **Eng C** | 🚧 | Automated `pytest` and `black/flake8` on every PR; test coverage reporting. |

---

## 🚀 Execution Strategy

### 1. The "Clean Slate" Start
Engineers must ensure their local environment matches the container environment.

#### Setting up Dagshub Credentials

1. **Create your `.env` file** (credentials are stored locally and gitignored):
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`** with your Dagshub credentials:
   - Get your Dagshub token from: https://dagshub.com/user/settings/tokens
   - Update `DAGSHUB_USERNAME`, `DAGSHUB_TOKEN`, and `DAGSHUB_REPO` in `.env`

3. **Initialize DVC and configure remote** (Engineer A):
   ```bash
   # Option 1: Using Makefile (recommended)
   make dvc-init
   make dvc-setup-remote
   
   # Option 2: Manual setup
   dvc init
   # Load environment variables and configure remote
   export $(grep -v '^#' .env | xargs)
   dvc remote add origin s3://dvc
   dvc remote modify origin endpointurl https://dagshub.com/${DAGSHUB_REPO}.s3
   # For Dagshub S3, use access_key_id and secret_access_key (both set to the token)
   dvc remote modify origin --local access_key_id ${DAGSHUB_TOKEN}
   dvc remote modify origin --local secret_access_key ${DAGSHUB_TOKEN}
   ```

**Note**: The `.env` file is gitignored and will never be committed. Each team member should create their own `.env` file with their personal Dagshub credentials.

### 2. Containerized Development

Use Docker Compose to manage services locally.

```yaml
# docker-compose.yaml example
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./src:/app/src
      - ./data:/app/data
      - ./models:/app/models
    environment:
      - MLFLOW_TRACKING_URI=https://dagshub.com/repo/mlflow
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
# Build and run the API service
docker-compose up --build
```


### 3. Version Control Strategy

- Branching: Use feature/<ticket-id>-description.

- PRs: Require at least 1 approval and passing CI checks.

- Commits: Use conventional commits (e.g., feat:, fix:).

---

## ✅ Definition of Done (Phase 1)

Phase 1 is considered complete when:

1. **Data Pipeline**: Raw data can be imported, validated, and preprocessed via `dvc repro` in a containerized environment.
2. **Baseline Model**: An XGBoost baseline model is trained, evaluated, and logged to MLflow with documented metrics (F1, Precision, Recall).
3. **API**: FastAPI service runs in Docker, accepts prediction requests, and returns results.
4. **Testing**: Unit tests cover core functionality with >70% coverage; CI pipeline runs tests on every PR.
5. **Documentation**: All tickets have acceptance criteria met; code is config-driven and follows project structure.
6. **Reproducibility**: Entire workflow (data → model → API) can be reproduced using Docker and DVC.


## Project Structure (Phase 1 Target)

```
MLOps_accidents/
├── .github/workflows/         # CI/CD (Eng C)
│   ├── lint.yaml
│   └── test.yaml
├── data/
│   ├── raw/                   # .dvc files (Eng A)
│   └── processed/
├── src/
│   ├── api/                   # FastAPI logic (Eng C)
│   │   └── main.py
│   ├── data/                  # Validation & Prep (Eng A)
│   │   ├── import_raw_data.py # Existing - to be containerized
│   │   ├── make_dataset.py    # Existing - to be integrated
│   │   └── validation.py      # New - data validation
│   ├── models/                # Training & Eval (Eng B)
│   │   ├── train_model.py     # Existing - to be refactored
│   │   └── predict_model.py  # Existing - to be integrated
│   └── config/                # YAML configs (Eng B)
│       └── model_config.yaml
├── tests/                     # Pytest suite (Eng B/C)
│   ├── test_data.py
│   ├── test_models.py
│   └── test_api.py
├── Dockerfile                 # Multi-stage build (Eng C)
├── docker-compose.yaml        # Local orchestration (Eng C)
└── dvc.yaml                   # Pipeline definition (Eng A)
```

**Note**: This structure builds upon existing codebase (`import_raw_data.py`, `make_dataset.py`, `train_model.py`, `predict_model.py`) while adding containerization, validation, and testing layers.