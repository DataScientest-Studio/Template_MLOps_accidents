from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'you',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

with DAG(
    dag_id='mlops_accident_pipeline',
    default_args=default_args,
    schedule_interval=None,  # can be cron, e.g., '0 6 * * *'
    catchup=False
) as dag:

    make_dataset = BashOperator(
        task_id='make_dataset',
        bash_command='python src/data/make_dataset.py',
    )

    build_features = BashOperator(
        task_id='build_features',
        bash_command='python src/features/build_features.py',
    )

    train_model = BashOperator(
        task_id='train_model',
        bash_command='python src/models/train_model.py',
    )

    make_dataset >> build_features >> train_model
