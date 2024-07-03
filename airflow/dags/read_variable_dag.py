import os

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.models import Variable

import datetime

AIRFLOW_NEW_DATA_IN_ROAD_ACCIDENTS_DB_VARNAME = os.getenv("AIRFLOW_NEW_DATA_IN_ROAD_ACCIDENTS_DB_VARNAME")

def read_and_print_airflow_variable():
    new_data_in_db_timestamp = Variable.get(AIRFLOW_NEW_DATA_IN_ROAD_ACCIDENTS_DB_VARNAME, None)
    print('Hello from Airflow again')
    if new_data_in_db_timestamp is not None:
        print(f"New data added on '{new_data_in_db_timestamp}'.")
    else:
        print(f"The env variable '{AIRFLOW_NEW_DATA_IN_ROAD_ACCIDENTS_DB_VARNAME}' has not been set yet.")

with DAG(
    dag_id='read_variable_dag',
    description='A DAG to read a variable, used for development only. Feel free to remove.',
    tags=["road_accidents", "data_ingestion"],
    schedule_interval=None,
    default_args={
        'owner': 'airflow',
        'start_date': days_ago(2),
    }
) as my_dag:

    my_read_var_task = PythonOperator(
        task_id='read_airflow_var',
        python_callable=read_and_print_airflow_variable,
    )

my_read_var_task
