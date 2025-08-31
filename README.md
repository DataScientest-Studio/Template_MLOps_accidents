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

## Steps to follow

Convention : All python scripts must be run from the root specifying the relative file path.

### 1- Create a virtual environment using Virtualenv.

`python -m venv my_env`  
### Activate it

`./my_env/Scripts/activate`

### 2- Build docker container

`docker build -t accidentpredictionservice:1.0.0 .`

### 3- Create the `.env` file

Create a file named `.env` in the project root (next to `docker-compose.yml`).  
Start from `.env.example`:

#### macOS / Linux
cp .env.example .env
echo "AIRFLOW_UID=$(id -u)" >> .env

#### Windows (PowerShell or cmd)
copy .env.example .env

open .env and ensure AIRFLOW_UID=50000

Do not commit your `.env` (keep `.env` in .gitignore). Commit only `.env.example`.

### 4- Execute docker compose

`docker-compose up -d`

### 5- Run the Docker Container

`docker run --rm -d -p 3000:3000 examen_bentoml:1.0.0`  
BentoML API will be available at http://localhost:3000

### 6- Please use the login-service with this credentials

USERNAME = "admin"  
PASSWORD = "4dm1N"

- **Airflow (Web UI)**  
  URL: `http://localhost:8080`  
  Username: `airflow`  
  Password: `airflow`

- **Grafana**  
  URL: `http://localhost:3001`  
  Username: `admin`  
  Password: `admin`

- **BentoML / API**
  URL: http://localhost:3000
  
- **Prometheus**
  URL: http://localhost:9090

- **Flower (Celery UI)**
  URL: http://localhost:5555






