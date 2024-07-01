# Description: Script that defines the training Pipeline.
# ========================================================

import os
from datetime import timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
from airflow.utils.timezone import datetime

import sys

# the path to our source code directories
sys.path.append(
    "/Users/drjosefhartmann/Development/Accidents/may24_bmlops_accidents/src/data"
)
sys.path.append(
    "/Users/drjosefhartmann/Development/Accidents/may24_bmlops_accidents/src/models"
)

cwd = os.getcwd()
print(cwd)
sys_path = sys.path
print(sys_path)

from train_model import Train_Model

from make_dataset_from_db import process_data

from model_api.evaluate import evaluate

# from cd4ml.data_processing import ingest_data
# from cd4ml.data_processing import split_train_test
# from cd4ml.data_processing import validate_data
# from cd4ml.data_processing import transform_data

# from cd4ml.model_validation import validate_model
# from cd4ml.model_validation import push_model
# from cd4ml.data_processing.track_data import track_data

### SET A UNIQUE MODEL NAME (e.g. "model_<YOUR NAME>"):
_model_name = "accidents_model"

### SET A UNIQUE EXPERIMENT NAME (e.g. "experiment_<YOUR NAME>"):
_mlflow_experiment_name = "accidents_experiment"


default_args = {
    "owner": "ssime",
    "depends_on_past": False,
    "start_date": days_ago(0),
    "retries": 1,
    "retry_delay": timedelta(seconds=5),
    "tags": ["accidents", "train_model"],
}

dag = DAG(
    "train_pipeline",
    default_args=default_args,
    tags=["road_accidents", "data_ingestion"],
    description="Training  Pipeline",
    schedule_interval="0 */1 * * * ",
    catchup=False,
)

with dag:

    # the new data are read to db by Evan
    # So in the database we have updated the 4 files
    # In any case, the training of the model runs by default every evening as 22:00
    # Regardless of new data have actually been ingested
    # so the following steps need to be done

    # 1. ingest new data --> Evan to db
    # 2. preprocess data --> Josef, incl. split for train and test
    # 3. train model --> train_model.py -> Josef
    # 4. validate model --> validate_model.py -> Josef using MLFlow
    # 5. push model --> push_model.py -> Josef using MLFlow

    # # 1. ingest new data

    # 2. preprocess data
    # the preprocessing relies on the script make_dataset_from_db.py
    # this file prepares features, cleans data and writes the train and test data
    # to Volume/data/preprocessed

    data_transformation = PythonOperator(
        task_id="data_transformation",
        python_callable=process_data,
        op_kwargs={"output_folderpath": "Volumes/data/preprocessed"},
    )

    # 3. Train model

    model_training = PythonOperator(
        task_id="model_training",
        python_callable=Train_Model,
    )

    model_metrics = PythonOperator(
        task_id="model_metrics",
        python_callable=evaluate,
    )
    # 4. Validate model
    # model_validation = BranchPythonOperator(
    #     task_id='model_validation',
    #     python_callable=validate_model,
    #     op_kwargs={
    #         'data_files': _data_files,
    #         'model': _model_name
    #     },
    # )

    # stop = DummyOperator(
    #     task_id='keep_old_model',
    #     dag=dag,
    #     trigger_rule="all_done",
    # )

    # 5. push model
    # push_to_production = PythonOperator(
    #     task_id='push_new_model',
    #     python_callable=push_model,
    #     op_kwargs={
    #         'model': _model_name
    #     },
    # )

    data_transformation >> model_training >> model_metrics
