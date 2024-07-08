from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
# Root dir of the green light ui project

green_light_ui_base = Path(__file__).parent.parent

title = "Road Accidents Data Ingestion"
sidebar_name = "Road Accidents Data Ingestion"


def run():

    st.title(title)

    st.markdown(
        """
        <style>
        .streamlit-expanderHeader p {
            font-size: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("**Introduction**"):
        st.write("""
    
    For this project (`Green Light Services` application) we made the assumption that [Road Accident data](https://www.data.gouv.fr/en/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2022/) are collected by French officials on a yearly basis.
    For each year (`{YEAR}`) a set of 4 road accident `csv` files exist:
    - `caracteristiques_{YEAR}.csv`
    - `lieux-{YEAR}.csv`
    - `usagers-{YEAR}.csv`
    - `vehicules-{YEAR}.csv`

    The `Green Light Services` application provides a directory where users can add road accident directories (a directory is for a particular year but its name is irrelevant).


    The application will then pick up newly added directories, using an Airflow DAG, and add them to the application's database (`RoadAccidents`). 

    Then other parts of this application can query the `RoadAccidents` database to pull the data, for example to train new ML models or visualize historical data.

    """)

    with st.expander("**The `road_accidents_database_ingestion` Python package**"):
        st.write("""

    The [`road_accidents_database_ingestion`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/tree/master/python-packages/road_accidents_database_ingestion) Python package contains the following functionality:

    - Code to check/parse the road accident data `csv` files.
    - Code to initialize the `RoadAccidents` database.
    - Database table [`SQLModel`](https://sqlmodel.tiangolo.com/) models and useful Python `enum`s. 
    - Code to add rows to the tables of the `RoadAccidents` database.
    - [`Pytest` files](https://github.com/DataScientest-Studio/may24_bmlops_accidents/tree/master/python-packages/road_accidents_database_ingestion/tests) to test the aforementioned functionality.

    > Configuration:
    The `road_accidents_database_ingestion` Python package is configured through environment variables which during runtime are provided by the 
    [`/.env`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/.env) file. Please refer to the [`README.md`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/tree/master/python-packages/road_accidents_database_ingestion) file for further information.

    """)

    with st.expander("**The `airflowdb.Dockerfile` Airflow base Docker Image**"):
        st.write("""

    Airflow runs in [`docker compose`](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html). 
    The recommended docker compose `yaml` file from Airflow provides the possibility to use a user-define base Docker image.
    This base image is then used by all the Airflow Docker images. 

    For this reason the [`airflowdb.Dockerfile`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/python-packages/airflowdb.Dockerfile) serves as the Airflow base image. 
    In this `Dockerfile` we install the necessary Python packages used by the Airflow DAGs.

    This docker image is part of our Continuous Integration and Continuous Delivery (CI/CD) pipeline where Docker images are build and pushed to 
    [`roadaccidentsmlops24`](https://hub.docker.com/u/roadaccidentsmlops24) Docker Hub repo

    > Configuration:
    The application is a docker compose app which means its configuration is set in the [`./docker-compose.yml`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/docker-compose.yml) file. 
    Most of its configuration is provided by the  [`./.env`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/.env) file.
        
    """)

    with st.expander("**Take a look at the Airflow Web UI in action**"):
        st.write("""
    
    Check out this [link](http://localhost:8080/)

    > To login to the Airflow Web UI use the `Green Light Services` admin credentials (`ADMIN_USERNAME`, `ADMIN_PASSWORD`) which are 
    defined in the [`./.env`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/.env) file.             
                 
    """)

    with st.expander("**The `road_accidents_data_ingestion_dag` Airflow DAG**"):

        st.image(str(green_light_ui_base / "assets" / "road_accidents_data_ingestion_dag.png"))

        st.write("""

    The [`road_accidents_data_ingestion_dag`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/airflow/dags/ingest_road_accident_csv_to_db.py) 
    Airflow DAG is responsible for checking for new Road Accident directories of `csv` files and adding them to the `Road Accidents` database. 
    
    In a nutshell the `road_accidents_data_ingestion_dag` performs the following tasks:
    - `NewFolderSensor`: a custom directory sensor that periodically checks for new Road Accident directories. If no new directories are found then it doesn't proceed to the following tasks.
    - `init_db_task`: Initializes the `Road Accidents` database.
    - `process_new_road_accidents_csv_task`: receives a list of new Road Accident directories through `xcom`, then for each new directory:
        - it will first check if the Road Accident `csv` files have already been processed by checking their `md5` hash and checking against the [`RawRoadAccidentsCsvFile`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/70f6eb33b4177cf66e26fb5343dc62c2112621dc/python-packages/road_accidents_database_ingestion/src/road_accidents_database_ingestion/models.py#L10) table.
        - if the files have already been processed and exist in the `Road Accidents` database, it will skip this "new" directory.
        - if not, it will add new rows to that `Road Accidents` database tables using the functionality provided by the [`road_accidents_database_ingestion`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/tree/master/python-packages/road_accidents_database_ingestion) Python package.
            - Set an `xcom` variable (`new_folders`) to `True` to indicate that new data have been added to the `Road Accidents` database.
    - `set_the_airflow_variable_db_updated_ts_task`: Reads the `new_folders` `xcom` variable and if set to `True` it will set an Airflow variable
     (name of the variable is defined in the `./.env` file as `AIRFLOW_NEW_DATA_IN_ROAD_ACCIDENTS_DB_VARNAME`) with the current timestamp to indicate 
    to other Airflow DAGs that new data have indeed added to the `Road Accidents` database.


    > Configuration:
    The DAG is configured through environment variables which during runtime are provided by the [`./.env`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/.env) file. More specifically:
  
    - Admin user credentials used for accessing the `Road Accidents` Database
    - `Road Accidents` DB name, host, port
    - `ROAD_ACCIDENTS_DIRS` path to the root directory inside the running Airflow Docker containers where `./Volumes/road_accidents_data_directories` is mounted to.
    - `AIRFLOW_NEW_DATA_IN_ROAD_ACCIDENTS_DB_VARNAME` contains the Airflow variable name that is created/updated when new road accidents data are added to the `Road accidents` database.

    """)

    with st.expander("**Take a look at the `road_accidents_data_ingestion_dag` Airflow DAG in action**"):
        st.write("""
    
    Check out this [link](http://localhost:8080/dags/road_accidents_data_ingestion_dag/grid?tab=graph)

    > To login to the Airflow Web UI use the `Green Light Services` admin credentials (`ADMIN_USERNAME`, `ADMIN_PASSWORD`) which are 
    defined in the [`./.env`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/.env) file.             
                 
    """)


    with st.expander("**The `Road Accidents` Database**"):
        st.write("""
                 
    The `Road Accidents` database is a [`PostgreSQL`](https://www.postgresql.org/) database which is part of the Docker compose application.
                 
    The [`pgAdmin`](https://www.pgadmin.org/) tool is used to monitor and view the `Road Accidents` database tables.
    
    """)

    with st.expander("**Take a look at the `Road Accidents` database in action using the `pgAdmin` Tool**"):
        st.write("""
    
    Check out this [link](http://localhost:8888/browser/).
                 
    > For accessing the `Road Accident` database use the `Green Light Services` admin password (`ADMIN_PASSWORD`) which is defined in the [`./.env`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/.env) file.
    
    To see or query the `Road Accidents` tables navigate to: 
    
    `Servers` -> `RoadAccidents` -> `Databases` -> `Schemas` -> `Tables`
    
    """)

    with st.expander("**Improvements**"):
        st.write("""""")
