Project Name
==============================

This project is a starting Pack for MLOps projects based on the subject "road accident". It's not perfect so feel free to make some modifications on it.

Project Organization
------------
    ├── devcontainer          <- Contains the Dockerfile and devcontainer.json for VS Code remote development.
    │   ├── devcontainer.json
    ├── .dvc                <- DVC configuration files for data versioning.
    │   ├── cache
    │   ├── tmp
    │   ├── config
    │   ├── config.local
    │   ├── gitignore
    ├── github/workflows <- GitHub Actions workflows for CI/CD.
    │   ├── python-app.yml 
    ├── LICENSE
    ├── dvcignore          <- DVC ignore file, similar to .gitignore.
    ├── .gitignore         <- A default gitignore file for Python projects
    ├── Dockerfile          <- Dockerfile for containerizing the application.
    ├── dvc.yaml 
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    ├── mlruns
    │   ├── .trash
    │   ├── 0                <- Directory for the first experiment run
    │   ├── 128208172982319055                <- Directory for the second experiment run
    │   ├── models          <- Directory for storing model artifacts

    ├── logs               <- Logs from training and predicting
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │   ├── check_structure.py    
    │   │   ├── import_raw_data.py 
    │   │   └── make_dataset.py
    │   │
    │   ├── features       <- Scripts to turn raw data into features for modeling
    │   │   └── build_features.py
    │   │
    │   ├── models         <- Scripts to train models and then use trained models to make
    │   │   │                 predictions
    │   │   ├── predict_model.py
    │   │   └── train_model.py
    │   │
    │   ├── visualization  <- Scripts to create exploratory and results oriented visualizations
    │   │   └── visualize.py
    │   └── config         <- Describe the parameters used in train_model.py and predict_model.py

---------

## Prerequisites
- Docker and Docker Compose installed
- Run commands from the repository root

## Steps to follow

### 1 Prepare environment (.env)
#### On macOS / Linux:
cp .env.example .env
echo AIRFLOW_UID=$(id -u) >> .env

#### On Windows (PowerShell):
copy .env.example .env
rem open .env and set AIRFLOW_UID=50000 if needed

### 2 (Optional) Build local prediction image
docker build -t accidentpredictionservice:1.0.0 .

### 3 Start the stack
docker compose -f docker-compose.yaml up -d

### 4 Confirm services are running
docker compose -f docker-compose.yaml ps

### 5 Confirm Grafana provisioning files are mounted in the container
docker compose -f docker-compose.yaml exec -T grafana sh -c "ls -la /etc/grafana/provisioning/dashboards /etc/grafana/provisioning/datasources /var/lib/grafana/dashboards || true"

### 6 Use Grafana API to list dashboards
curl -sS -u admin:admin "http://localhost:3001/api/search?query="

### 7 Check that grafana-dashboard is provisioned from file
curl -sS -u admin:admin "http://localhost:3001/api/dashboards/uid/grafana-dashboard" | python -c "import sys,json; j=json.load(sys.stdin); m=j.get('meta',{}); print('provisioned:', m.get('provisioned')); print('provisionedExternalId:', m.get('provisionedExternalId'))"

### 8 Check that bentoml-dashboard is present
curl -sS -u admin:admin "http://localhost:3001/api/dashboards/uid/bentoml-dashboard" | python -c "import sys,json; j=json.load(sys.stdin); print(j.get('dashboard', {}).get('uid'))"

### 9 Credentials
http://localhost:3001/d/grafana-dashboard/grafana-dashboard

http://localhost:3001/d/bentoml-dashboard/bentoml-admission-prediction-api-dashboard

Grafana credentials
Username: admin
Password: admin

BentoML / API 
http://localhost:3000

Prometheus UI
http://localhost:9090

Flower (Celery UI) 
http://localhost:5555

Airflow UI
http://localhost:8080
Username: airflow
Password: airflow

### 10 Prediction server
docker compose -f docker-compose.yaml ps prediction-server
If the image does not serve automatically, run:
docker run --rm -d -p 3000:3000 accidentpredictionservice:1.0.0

### 11 Stop the stack
docker compose -f docker-compose.yaml down










