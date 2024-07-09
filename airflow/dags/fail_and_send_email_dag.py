from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.models import Variable

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': [Variable.get("alert_email", "")],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=20),
}

with DAG(
    'example_failure_email',
    default_args=default_args,
    description='A simple tutorial DAG',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=["road_accidents", "data_ingestion"],
) as dag:

    t1 = BashOperator(
        task_id='failing_task',
        bash_command='exit 1',
    )

    t2 = BashOperator(
        task_id='succeeding_task',
        bash_command='echo "Hello World"',
    )

    t1 >> t2