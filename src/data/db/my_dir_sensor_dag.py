"""Raw data (road accidents CSV files) ingestion to the DB.

Whenever there is a new directory in the `./Volumes/data/raw` directory:
1. verify we have access to the `RoadAccidents` DB.
2. verify all tables exists and if they don't create them.
3. If newly added raw files have not already been added to the DB by checking their MD5
    add the filename, md5 and timestamp to the `raw_road_accident_files` with status `PROCESSING`
4. Ingest the 4 raw road accident csv files to the DB.
5. update `raw_road_accident_files` status to `PROCESSED`


"""
import datetime
from pathlib import Path

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.sensors.filesystem import FileSensor
from airflow.operators.bash import BashOperator
# from airflow.sensors.base_sensor_operator import BaseSensorOperator
from airflow.sensors.base import BaseSensorOperator
from airflow.utils.decorators import apply_defaults
import os
from airflow.operators.latest_only import LatestOnlyOperator
# from airflow.operators.python_operator import PythonOperator
from airflow.operators.python import PythonOperator
from dotenv import load_dotenv

from db_tasks import get_db_url

load_dotenv()  # take environment variables from .env.

PATH_RAW_FILES_DIR = os.getenv("RAW_FILES_ROOT_DIR")

class NewFolderSensor(BaseSensorOperator):
    @apply_defaults
    def __init__(self, directory, *args, **kwargs):
        super(NewFolderSensor, self).__init__(*args, **kwargs)
        self.directory = directory
        self.seen_folders = set(os.listdir(directory))

    def poke(self, context):
        current_folders = set(os.listdir(self.directory))
        new_folders = current_folders - self.seen_folders
        if new_folders:
            new_folders_list = list(new_folders)
            self.log.info(f"New folder detected: {new_folders_list}")
            context['ti'].xcom_push(key='new_folders', value=new_folders_list)
            self.seen_folders = current_folders

            return True
        return False
    
# Tasks

def process_init_db(**kwargs):
    pass


def process_new_folders(**kwargs):
    ti = kwargs['ti']
    new_folders = ti.xcom_pull(task_ids='watch_new_folder', key='new_folders')
    if new_folders:
        for folder in new_folders:
            print(f"Processing folder: {folder}")
            # Add your processing logic here
            new_data_dir = Path(PATH_RAW_FILES_DIR) / folder
            print(f"Path = '{new_data_dir}'")
    else:
        print("No new folders found.")

    print(f"DB url='{get_db_url()}'")

with DAG(
    dag_id='sensor_dag',
    schedule_interval=datetime.timedelta(seconds=60),
    tags=['road_accidents', 'data_ingestion'],
    start_date=days_ago(0),
    concurrency=1,  # Ensure only one instance of the DAG runs at a time
    max_active_runs=1,
    catchup=False,
) as dag:
    latest_only = LatestOnlyOperator(task_id='latest_only')

    watch_task = NewFolderSensor(
        task_id='watch_new_folder',
        directory="/opt/data/",
        poke_interval=30,
        mode='poke',
        timeout=600,
    )

    # my_sensor = FileSensor(
    #     task_id="check_raw_data_directory",
    #     fs_conn_id="raw_data_ingestion",
    #     filepath="/opt/data/",
    #     poke_interval=30,
    #     timeout=5 * 30,
    #     mode='reschedule'
    # )

    # my_task = BashOperator(
    #     task_id="print_directory_contents",
    #     bash_command="ls /opt/data/",
    # )
    process_task = PythonOperator(
        task_id='process_new_folders',
        provide_context=True,
        python_callable=process_new_folders,
    )

    latest_only >> watch_task >> process_task