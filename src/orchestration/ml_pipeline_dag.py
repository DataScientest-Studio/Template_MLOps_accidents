from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Define the paths to your script files
IMPORT_RAW = "/workspaces/MLOps_accidents/src/data/import_raw_data.py"
MAKE_DATASET = "/workspaces/MLOps_accidents/src/data/make_dataset.py"
TRAIN_MODEL = "/workspaces/MLOps_accidents/src/models/train_model.py"

with DAG(
    "ml_pipeline",
    description='Orchestrate ML pipeline with Airflow',
    schedule_interval=None,  
    start_date=datetime(2025, 6, 7),
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=5)},
) as dag:

    import_data = PythonOperator(
        task_id='import_raw_data',
        python_callable=lambda: __import__('src.data.import_raw_data').main()
    )

    make_dataset = PythonOperator(
        task_id='make_dataset',
        python_callable=lambda: __import__('src.data.make_dataset').main()
    )

    train_model = PythonOperator(
        task_id='train_model',
        python_callable=lambda: __import__('src.models.train_model').main()
    )

    # Set up dependency
    import_data >> make_dataset >> train_model
