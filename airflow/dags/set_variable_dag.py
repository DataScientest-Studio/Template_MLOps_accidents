import os

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.models import Variable

import datetime


# Definition of the function to be executed
def print_date_and_hello():
    print(datetime.datetime.now())
    print("Hello from Airflow")


def print_date_and_hello_again():
    airflow_var_name = os.getenv("AIRFLOW_NEW_DATA_IN_ROAD_ACCIDENTS_DB_VARNAME")
    my_variable_value = Variable.get(airflow_var_name, None)
    print(f"current_value: {my_variable_value}")
    Variable.set(airflow_var_name, datetime.datetime.now().isoformat())
    my_updated_variable_value = Variable.get(airflow_var_name, 0)
    print(my_updated_variable_value)


with DAG(
    dag_id="my_set_variable_dag",
    description="A DAG to set a variable",
    tags=["road_accidents", "data_ingestion"],
    schedule_interval=None,
    default_args={
        "owner": "airflow",
        "start_date": days_ago(2),
    },
) as my_dag:

    my_task = PythonOperator(
        task_id="my_very_first_task",
        python_callable=print_date_and_hello,
    )

    my_task2 = PythonOperator(
        task_id="my_second_task",
        python_callable=print_date_and_hello_again,
    )

my_task >> my_task2
