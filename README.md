🚦 Green Lights Services
==============================
# About

This project is a starting Pack for MLOps projects based on the subject "road accident". It's not perfect so feel free to make some modifications on it.

> TODO add project description

# 👨🏼‍💻👩‍💻👨🏻‍💻 Development Team

Green Lights Services has been developed by:
- Josef Hartmann
- Paula Robina Beck
- Evan Blablapoulos

Green Lights Services represents our final project for the DataScientest MLOps Program.

# 🏗️ Architecture

> TODO add figures and description


# 📂 Project Organization
The repository is structured as follows:

------------
    ├── .github/
    │    │
    │    └── workflows/                     <- GitHub workflow files.
    │
    ├── README.md          <- The top-level README for developers using this project.
    │
    ├── Airflow                <- Airflow related files.
    │   │
    │   ├── dags           <- Airflow DAGs used in this project.
    │   │   ├── ingest_road_accident_csv_to_db.py    <- Airflow DAG that reads road accidents CSV files and adds then to the RoadAccidents database.
    │   │   └── 1_training_pipeline_dag.py <-
    │   │
    ├── Volumes     <- Shared directories between the host and the docker-compose application.
    │   │
    │   ├──         <- Data from third party sources.
    │   ├──          <- Intermediate data that has been transformed.
    │   ├──        <- The final, canonical data sets for modeling.
    │   └──              <- The original, immutable data dump.
    │
    ├── notebooks               <- Logs from training and predicting
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── python-packages                <- Source code for use in this project.
    │   │
    │   ├── green_light_ui    
    │   ├── model_api 
    │   └── road_accidents_database_ingestion
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── Volumes                <- Source code for use in this project.
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
    │
    ├── .env         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── docker-compose.yml         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── LICENSE
    │
    ├── LICENSE

---------

# 👩‍💻 Development

# 👟 Running the App

# 📝 TODO List / Remaining Items



------------------------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
