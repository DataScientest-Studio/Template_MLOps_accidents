# Airflow Dags

## DAGs
in the Folder `/airflow/dags` we collect all our dags. 

* **1_training_pipeline_dag.py** -> A training and evaluation pipeline to update models after new data were ingested
* **ingest_road_accident_csv_to_db.py** -> A data ingestion pipeline for absorbing new data.
* **read_variable_dag.py** -> Reading Variables 
* **set_variable_dag.py** -> Setting Variables
 
The other files in this folder are collatals for the DAGs.

## Files
Files loaded and saved are stored in several Folders in `/Volumes`
* MAY24_BMLOPS_ACCIDENTS -> In here run the docker compose. Script inside. Start with `./startup_compose.sh`
* **Volumes/airflow** has no purpose 
* **Volumes/data** stores in subfolders many of the data generated in the training and evaluation process
  * Volumes/data/metrics
  * Volumes/data/mlflow -> in here run the mlflow server. Script inside. Start with `./run_mlfow_server.sh`. In this folder the evaluation artefacts are collected
  * Volumes/data/predictions -> archived predictions per training
  * Volumes/data/preprocessed -> output of preprocessing phase. 
  * Volumes/data/raw -> obsolete
  * Volumes/data/raw # Raw Road Accidents CSV files upload path in Docker
  * Volumes/data/raw_db
* **Volumes/db**
* **Volumes/db_admin**
* **Volumes/mlflow** -> obolsete
* **Volumes/models** -> contains the current model, archive models and the new model before Evaluation

## Model Training and Evaluation 

One the 