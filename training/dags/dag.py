from airflow import DAG
from airflow.operators.python import PythonOperator

from make_dataset import process_data
from import_raw_data import import_raw_data

def get_data():
    import_raw_data('/app/data/raw',
                    [
                        "caracteristiques-2021.csv",
                        "lieux-2021.csv",
                        "usagers-2021.csv",
                        "vehicules-2021.csv"
                    ],
                    "https://mlops-project-db.s3.eu-west-1.amazonaws.com/accidents/"
                    )

def make_dataset():
    input_filepath = '/app/data/raw'
    input_filepath_users = f"{input_filepath}/usagers-2021.csv"
    input_filepath_caract = f"{input_filepath}/caracteristiques-2021.csv"
    input_filepath_places = f"{input_filepath}/lieux-2021.csv"
    input_filepath_veh = f"{input_filepath}/vehicules-2021.csv"
    output_filepath = '/app/data/processed'
    process_data(input_filepath_users, input_filepath_caract, input_filepath_places, input_filepath_veh, output_filepath)

with DAG(
        dag_id='exam_dag_retrieve_data',
        tags=['datascientest'],
        default_args={
            'owner': 'airflow'
        }
) as dag:
    import_raw_data_task = PythonOperator(
        task_id='import_raw_data',
        python_callable=get_data,
        dag=dag
    )
    # make_dataset_task = PythonOperator(
    #     task_id='get_data_task',
    #     python_callable=make_dataset,
    #     dag=dag
    # )
    # import_raw_data_task >> make_dataset_task
    import_raw_data_task