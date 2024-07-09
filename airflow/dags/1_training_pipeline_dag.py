# Description: Script that defines the training Pipeline.
# ========================================================

import os
from datetime import timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
from airflow.utils.timezone import datetime
from airflow.operators.latest_only import LatestOnlyOperator
from airflow.decorators import task
from airflow.operators.email import EmailOperator
from airflow.models import Variable
from airflow.exceptions import AirflowException
from evaluate import evaluate

import sys

from datetime import timedelta

from train_model import Train_Model, push_to_production

from make_dataset_from_db import process_data

from model_evaluation import evaluate_model

import sys

import requests

import os.path

# the path to our source code directories - docker version

model_base = "/models"
data_base = "/data"

model_file = model_base + "/trained_model.joblib"

sys.path.append(data_base)
sys.path.append(model_base)

cwd = os.getcwd()
print(cwd)
sys_path = sys.path
print(sys_path)

### SET A UNIQUE MODEL NAME (e.g. "model_<YOUR NAME>"):
_model_name = "accidents_model"

### SET A UNIQUE EXPERIMENT NAME (e.g. "experiment_<YOUR NAME>"):
_mlflow_experiment_name = "accidents_experiment"

### manage authorization

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


# this is run from a worker

url_refresh = "http://model_api_from_compose:8000/refresh"


def get_jwt_token():
    # url = "http://localhost:8001/user/login"
    url = "http://model_api_from_compose:8000/user/login"
    response = requests.post(
        url, json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )
    token = response.json()["access_token"]
    print("token = ", token)
    return token


def refresh_api():
    token = get_jwt_token()
    headers = {"Authorization": f"Bearer {token}"}
    refresh = requests.get(url_refresh, headers=headers)
    print("refreshed model in api")
    return 1


def check_for_new_data():
    try:
        # Attempt to get the variable, if it doesn't exist, this will raise an AirflowException
        variable_name = os.getenv("AIRFLOW_NEW_DATA_IN_ROAD_ACCIDENTS_DB_VARNAME")
        variable_value = Variable.get(variable_name)
        print(f"Variable '{variable_name}' exists with value: {variable_value}")
        Variable.delete(variable_name)
        print("deleted variable:", variable_name)
        return True
    except:  # AirflowException:
        print("Variable does not exist in 'check_for_new_data'")
        return False


default_args = {
    "owner": "ssime",
    "depends_on_past": False,
    "start_date": days_ago(0),
    'email': [Variable.get("alert_email", "")],
    'email_on_failure': True,
    'email_on_retry': False,
    "retries": 1,
    "retry_delay": timedelta(seconds=5),
    "tags": ["accidents", "train_model"],
}

dag = DAG(
    "train_pipeline",
    default_args=default_args,
    description="Training  Pipeline",
    schedule_interval=timedelta(seconds=300),
    # schedule_interval="*/1 */1 * * * ",
    # schedule_interval=None,
    concurrency=1,  # Ensure only one instance of the DAG runs at a time
    max_active_runs=1,
    catchup=False,
    tags=["road_accidents", "train_model"],
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

    # latest_only = LatestOnlyOperator(task_id="latest_only")

    @task.branch(task_id="initiate")
    def initiate_branch(ti=None):
        new_data = check_for_new_data()
        model_there = os.path.isfile(model_file)
        print("model_there", model_there)
        if not new_data and model_there:
            return "stop_task"
        else:
            return "data_transformation"

    data_transformation = PythonOperator(
        task_id="data_transformation",
        python_callable=process_data,
        op_kwargs={"output_folderpath": data_base + "/preprocessed"},
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

    @task.branch(task_id="model_evaluation")
    def model_evaluation(ti=None):
        validation = evaluate_model()
        if not validation:
            return "stop_task"
        else:
            return "push_production"

    stop_task = DummyOperator(
        task_id="stop_task",
        trigger_rule="all_done",
    )

    # 5. push model
    push_production = PythonOperator(
        task_id="push_production",
        python_callable=push_to_production,
    )

    # 5. push model
    refresh_api = PythonOperator(
        task_id="refresh_api",
        python_callable=refresh_api,
    )

    initiate_branch() >> [data_transformation, stop_task]

    (
        data_transformation
        >> model_training
        >> model_metrics
        >> model_evaluation()
        >> [stop_task, push_production]
    )
    push_production >> refresh_api
