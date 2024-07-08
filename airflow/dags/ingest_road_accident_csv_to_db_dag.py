"""Raw data (road accidents CSV files) ingestion to the DB DAG.

TODO:
- The `task_process_new_road_accidents_csvs` task can be split into 4 separate tasks.
"""

import datetime
from pathlib import Path
import logging
import os

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.sensors.base import BaseSensorOperator
from airflow.utils.decorators import apply_defaults
from airflow.operators.latest_only import LatestOnlyOperator
from airflow.operators.python import PythonOperator
from airflow.models import Variable

from sqlmodel import Session

from dotenv import load_dotenv

from road_accidents_database_ingestion.db_tasks import (
    get_db_url,
    create_db_engine,
    init_db,
    update_raw_accidents_csv_files_table,
    add_data_to_db
)

from road_accidents_database_ingestion.file_tasks import get_road_accident_file2model

logger = logging.getLogger(__name__)
load_dotenv()

AIRFLOW_NEW_DATA_IN_ROAD_ACCIDENTS_DB_VARNAME = os.getenv("AIRFLOW_NEW_DATA_IN_ROAD_ACCIDENTS_DB_VARNAME")
ROAD_ACCIDENTS_DIRS = os.getenv("ROAD_ACCIDENTS_DATA_DIRECTORIES")


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': [Variable.get("alert_email", "")],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': datetime.timedelta(seconds=30),
}

class NewFolderSensor(BaseSensorOperator):
    @apply_defaults
    def __init__(self, directory, *args, **kwargs):
        super(NewFolderSensor, self).__init__(*args, **kwargs)

        self.directory = directory
        self.seen_folders = set(os.listdir(directory))

    def poke(self, context):
        logger.info(f"Looking if there is a new directory in '{self.directory}'.")
        logger.info(f"Directories seen so far: {self.seen_folders}")
        current_folders = set(os.listdir(self.directory))
        new_folders = current_folders - self.seen_folders
        if new_folders:
            logger.info(f"New directories found in '{self.directory}' ({len(new_folders)}): {new_folders}.")
            new_folders_list = list(new_folders)
            self.log.info(f"New folder detected: {new_folders_list}")
            context["ti"].xcom_push(key="new_folders", value=new_folders_list)
            self.seen_folders = current_folders
            return True

        return False


# Tasks

def task_init_db(**kwargs):
    """This task creates the DB tables for the Road Accidents App."""
    logger.info(f"Creating the DB engine.")
    db_url = get_db_url()
    logger.info(f"DB URL: {db_url}")
    engine = create_db_engine(db_url=db_url)
    logger.info(f"Creating the DB tables.")
    init_db(engine=engine)
    logger.info(f"Done.")


def process_new_folders(**kwargs):
    ti = kwargs["ti"]
    new_folders = ti.xcom_pull(task_ids="watch_for_new_data_dirs_task", key="new_folders")
    if new_folders:
        for folder in new_folders:
            print(f"Processing folder: {folder}")
            # Add your processing logic here
            print(f"{ROAD_ACCIDENTS_DIRS}")
            print(f"{type(new_folders)}")
            new_data_dir = Path(ROAD_ACCIDENTS_DIRS) / folder
            print(f"Path = '{new_data_dir}'")
            print(f"DB url='{get_db_url()}'")
    else:
        print("No new folders found.")


def task_process_new_road_accidents_csvs(**kwargs):
    ti = kwargs["ti"]
    new_folders = ti.xcom_pull(task_ids="watch_for_new_data_dirs_task", key="new_folders")
    new_data_added_to_db = False
    logger.info(f"Creating the DB engine.")
    engine = create_db_engine(db_url=get_db_url())
    for new_dir in new_folders:
        new_dir_full_path = Path(ROAD_ACCIDENTS_DIRS) / new_dir
        logger.info(f"Processing data from directory '{new_dir_full_path}'.")
        logger.info(f"{list(new_dir_full_path.glob("*"))}")

        try:
            file2model = get_road_accident_file2model(new_dir_full_path)
        except FileNotFoundError:
            logger.error(f"Directory '{new_dir}' does not contain all 4 road accidents csv files, skipping...")
            raise

        if not file2model:
            logger.info(f"Directory '{new_dir}' has no `csv` files, skipping...")
            continue

        with Session(engine) as session:
            logger.info(f"Checking DB table 'RawRoadAccidentsCsvFile' to see if files already processed.")
            update_raw_accidents_csv_files_table(db_session=session, files=file2model)
            logger.info(f"Adding Road Accident data to the DB.")
            logger.info(file2model)
            new_data_added_to_db = add_data_to_db(db_session=session, files=file2model)
            session.commit()
            if new_data_added_to_db:
                logger.info(f"New data added to the DB. Updating xcom 'new_data_added_to_db'.")
                ti.xcom_push(key="new_data_added_to_db", value=new_data_added_to_db)

def task_update_variable_new_road_accidents_data_timestamp(**kwargs):
    ti = kwargs["ti"]
    new_data_added_to_db = ti.xcom_pull(task_ids="process_new_road_accidents_csv_task", 
                                        key="new_data_added_to_db")
    if new_data_added_to_db:
        ts = datetime.datetime.now().isoformat()
        logger.info(f"New Road Accidents data added to the DB...")
        logger.info(f"Setting the Airflow variable '{AIRFLOW_NEW_DATA_IN_ROAD_ACCIDENTS_DB_VARNAME}' with the timestamp: '{ts}'.")
        Variable.set(AIRFLOW_NEW_DATA_IN_ROAD_ACCIDENTS_DB_VARNAME, ts)
        logger.info("Done!")
    else:
        logger.info("No new data added to the DB.")

# Le DAG
with DAG(
    dag_id="road_accidents_data_ingestion_dag",
    doc_md="""# Road Accidents Data Ingestion DAG
    
        The road_accidents_data_ingestion_dag is an Airflow DAG that periodically checks
        if a new directory with road accidents data (csv files) has been to the directory defined
        by the environment variable RAW_FILES_ROOT_DIR.""",
    schedule_interval=datetime.timedelta(seconds=60),
    tags=["road_accidents", "data_ingestion"],
    start_date=days_ago(0),
    concurrency=1,  # Ensure only one instance of the DAG runs at a time
    max_active_runs=1,
    catchup=False,
    default_args=default_args
    
) as dag:
    latest_only = LatestOnlyOperator(task_id="latest_only")

    watch_task = NewFolderSensor(
        task_id="watch_for_new_data_dirs_task",
        directory=ROAD_ACCIDENTS_DIRS,
        mode="poke",
        poke_interval=datetime.timedelta(seconds=30),
        timeout=datetime.timedelta(hours=24),
        retry_delay=datetime.timedelta(seconds=60),
        retries=10,
    )

    init_db_task = PythonOperator(task_id="init_db_task", python_callable=task_init_db)

    add_new_road_accidents_csvs_to_db_task = PythonOperator(
        task_id="process_new_road_accidents_csv_task",
        python_callable=task_process_new_road_accidents_csvs,
        trigger_rule='all_success'
    )

    set_the_airflow_db_updated_variable_task = PythonOperator(
        task_id="set_the_airflow_variable_db_updated_ts_task",
        python_callable=task_update_variable_new_road_accidents_data_timestamp,
        trigger_rule='all_success'
    )
    


    latest_only >> init_db_task >> watch_task >> add_new_road_accidents_csvs_to_db_task >> set_the_airflow_db_updated_variable_task
