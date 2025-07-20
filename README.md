# MLOps_accidents — Technical Documentation

This repository is a production-grade MLOps project designed around road accident data. It follows a modular structure enabling reproducibility, scalability, monitoring, and CI/CD deployment using modern MLOps best practices.

---

## Project Structure

```
├── .dvc/                         # DVC metadata for versioning
├── .github/workflows/           # GitHub Actions CI/CD pipeline
│   └── python-app.yml           # Main CI workflow definition
├── Grafana/                     # Dashboard JSONs for monitoring
├── config/
│   └── airflow.cfg              # Airflow configuration
├── dags/                        # Airflow DAGs for orchestration
│   ├── example_teardown.py      
│   └── our_first_dag.py
├── data/
│   ├── .gitignore
│   ├── preprocessed.dvc         # Preprocessed dataset
│   └── raw.dvc                  # Raw input dataset
├── mlruns/                      # MLflow experiment logs and metadata
│   └── <run_id>/                # MLflow experiment subfolders
├── models/                      # Trained and serialized models
├── notebooks/
│   └── 1.0-ldj-initial-data-exploration.ipynb
├── references/                  # Data dictionaries & documentation
├── reports/                     # Generated plots, HTML reports, etc.
│   └── figures/
├── src/
│   ├── api/                     # Inference API logic (FastAPI)
│   ├── data/                    # Scripts for loading and preprocessing
│   ├── features/                # Feature engineering scripts
│   ├── models/                  # Model training & evaluation
│   ├── orchestration/          # Microservices and workflow composition
│   ├── pipeline/               # Training/inference DAG pipelines
│   ├── tests/                  # Unit and integration tests
│   └── visualization/          # EDA, plotting, and monitoring visuals
├── Dockerfile
├── docker-compose.yml
├── dvc.yaml                    # Pipeline specification for DVC
├── requirements.txt
├── bentofile.yaml             # Model serving definition for BentoML
├── setup.py
├── LICENSE
└── README.md
```

---

## Objectives

This project is focused on implementing the full MLOps lifecycle for a road accident prediction model. It ensures:

- Reproducible research & production setup  
- Modular microservices for training, inference & monitoring  
- GitHub-integrated CI/CD  
- MLflow tracking & DVC versioning  
- Orchestration using Airflow  
- Containerized deployment via Docker  

---

## Roadmap & Milestones

### Phase 1: Foundations & Containerization

- [x] Define project objectives and KPIs  
- [x] Set up Dockerized Python environment  
- [x] Load & preprocess raw data using `data/` and DVC  
- [x] Establish baseline models via `src/models/` & notebook  
- [x] Unit tests in `src/tests/`  
- [x] Create minimal inference API in `src/api/`  

### Phase 2: Microservices, Tracking & Versioning

- [x] Track experiments using MLflow (`mlruns/`)  
- [x] Version datasets and models via DVC  
- [x] Implement DAGs in `dags/` with Airflow  
- [x] Orchestrate model training & evaluation  

### Phase 3: Orchestration & Deployment

- [x] CI pipeline with GitHub Actions (`.github/workflows/python-app.yml`)  
- [x] Secure, optimized FastAPI-based inference API  
- [x] Containerized deployment with Docker & Compose  
- [ ] Kubernetes scalability layer (WIP)  

### Phase 4: Monitoring & Maintenance

- [x] Monitor metrics using Prometheus & Grafana  
- [ ] Drift detection using Evidently  
- [ ] Automated model updates & retraining triggers  
- [ ] Complete & publish technical documentation  

---

## CI/CD Pipeline

- Trigger: Pull requests on `dev` and `main`  
- Validation: Unit tests, flake8, Black formatting  
- Build: Docker image builds on push  
- Deploy: Model artifacts versioned & deployed via MLflow/BentoML (WIP)  

Workflow file: `.github/workflows/python-app.yml`

---

## Versioning & Reproducibility

- Data: Managed via DVC (`data/raw.dvc`, `data/preprocessed.dvc`)  
- Models: Stored in `models/`, versioned and logged via MLflow  
- Code: All components tracked with Git, commits tied to artifacts  
- Parameters: Stored in `params.yaml` and tracked per experiment run  

---

## Notebooks

Exploratory and modeling notebooks are tracked in:

```
notebooks/
└── 1.0-ldj-initial-data-exploration.ipynb
```

Each notebook is named using the convention:  
`[PHASE].[INITIALS]-[short-description].ipynb`

---

## Monitoring Stack

- Prometheus: Collects inference latency and resource usage  
- Grafana: Preconfigured dashboards in `Grafana/dashboard.json`
